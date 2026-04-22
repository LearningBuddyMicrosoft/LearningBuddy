import os
import json
from typing import List

from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.concurrency import asynccontextmanager
import requests
from sqlmodel import Session, select, func

from .database_insertion import store_document_embeddings

from .pdf_processor import  generate_chunks_and_embeddings
from .quiz_generator import generate_and_store_quiz
from .security import create_access_token, get_current_user, get_password_hash, verify_password
from .database import create_db_and_tables, get_session, engine
from datetime import date
from .models import Material, Question, Quiz, Response, Subject, Topic, User, QuizAttempt # From your previous steps
from.schemas import DashboardRead, QuizAttemptsGroup, QuizCreate, QuizRead, SubjectCreate, TopicCreate, TopicDetailedRead, TopicMastery, UserCreate, StartAttempt, AnswerSubmission, FinishAttempt, BatchSubmission

app = FastAPI()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Everything BEFORE 'yield' happens when the server TURNS ON
    print("🚀 App starting up: Creating database and tables...")
    create_db_and_tables()
    
    yield # This is where the app actually runs!
    
    # Everything AFTER 'yield' happens when the server TURNS OFF
    print("👋 App shutting down: Cleaning up resources...")     

app = FastAPI(lifespan=lifespan)

OLLAMA_URL = os.getenv("OLLAMA_URL")
FEEDBACK_MODEL = os.getenv("OLLAMA_FEEDBACK_MODEL", "llama3.1")

@app.post("/register/")
def register_user(user_create: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.username == user_create.username)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = get_password_hash(user_create.password)
    new_user = User(username=user_create.username, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id}

@app.post("/login/")
def login_user(user_create: UserCreate, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == user_create.username)).first()
    if not user or not verify_password(user_create.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    access_token = create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

#called everytime a quiz is started(used to update db with user attempts)
@app.post("/start-attempt/")
def start_attempt(payload: StartAttempt, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    quiz = session.get(Quiz, payload.quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if quiz.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this quiz")  
        
    new_attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_id=payload.quiz_id,
        date=date.today().isoformat(),
        score=0,
        feedback=""
    )
    session.add(new_attempt)
    session.commit()
    session.refresh(new_attempt)
    return new_attempt

#called everytime a question is answered in single mode
@app.post("/submit-answer/")
def submit_answer(submission: AnswerSubmission, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    attempt = session.get(QuizAttempt, submission.attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    if attempt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this attempt")
    
    new_response = grade_and_build_response(submission,current_user.id, session)
    session.add(new_response)
    session.commit()
    session.refresh(new_response)
    return new_response

#called only when quiz is finished in single mode
@app.post("/finish-attempt/")
def finish_attempt(submission: FinishAttempt, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    attempt = session.get(QuizAttempt, submission.attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    if attempt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this attempt")
    
    # Calculate score based on responses
    statement = select(func.count()).where(
        Response.attempt_id == submission.attempt_id,
        Response.is_correct == True
    )
    correct_count = session.exec(statement).one() or 0
    total_count = session.exec(
        select(func.count()).where(Response.attempt_id == submission.attempt_id)
    ).one() or 0

    wrong_question_rows = session.exec(
        select(Question.question_text, Response.selected_option, Question.correct_answer).join(
            Response, Response.question_id == Question.id
        ).where(
            Response.attempt_id == submission.attempt_id,
            Response.is_correct == False
        )
    ).all()
    wrong_questions = [
        {
            "question": question_text,
            "selected_answer": selected_option,
            "correct_answer": correct_answer,
        }
        for question_text, selected_option, correct_answer in wrong_question_rows
    ]

    # Update the attempt with the final score and feedback
    attempt.score = int(correct_count)
    attempt.feedback = generate_feedback(wrong_questions, attempt.score, int(total_count))

    quiz = session.get(Quiz, attempt.quiz_id)
    if quiz:
        quiz.highscore = max(quiz.highscore, attempt.score)
        session.add(quiz)
    session.add(attempt)
    session.commit()
    session.refresh(attempt)

    return attempt

#called when quiz is finished in batch mode
@app.post("/submit-batch-answers/")
def submit_batch_answers(batch_submission: BatchSubmission, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    new_attempt = session.get(QuizAttempt, batch_submission.attempt_id)
    if not new_attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if new_attempt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this attempt")
    score = 0
    wrong_questions = []
    response_list = []
    for answer in batch_submission.answers:
        question = session.get(Question, answer.question_id)
        new_response = grade_and_build_response(answer,current_user.id, session)
        response_list.append(new_response)

        is_correct = new_response.is_correct

        if is_correct:
            score += 1
        else:
            wrong_questions.append(
                {
                    "question": question.question_text,
                    "selected_answer": answer.selected_option,
                    "correct_answer": question.correct_answer,
                }
            )
        
    total_answers = len(batch_submission.answers)
    overall_feedback = generate_feedback(wrong_questions, score, total_answers)

    new_attempt.score = score
    new_attempt.feedback = overall_feedback

    quiz = session.get(Quiz, new_attempt.quiz_id)
    if quiz:
        quiz.highscore = max(quiz.highscore, new_attempt.score)
        session.add(quiz)

    session.add_all(response_list)
    session.add(new_attempt)
    session.commit()
    session.refresh(new_attempt)

    return new_attempt

def grade_and_build_response(submission: AnswerSubmission, current_user_id: int, session: Session):
    question = session.get(Question, submission.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    is_correct = submission.selected_option == question.correct_answer

    #TODO:hardcoded feedback for now, will be calling AI for this in the future
    if is_correct:
        feedback = "Correct!"
    else:
        feedback = "Incorrect. Review the material and try again."
    
    response = Response(
        user_id=current_user_id,
        attempt_id=submission.attempt_id,
        question_id=submission.question_id,
        selected_option=submission.selected_option,
        is_correct=is_correct,
        feedback=feedback   
        )
    return response

def build_fallback_feedback(score: int, total: int) -> str:
    if total == 0:
        return "No answers were submitted."

    percentage = score / total
    if percentage == 1:
        return f"Perfect score: {score} out of {total} correct."
    if percentage >= 0.7:
        return f"Nice work: {score} out of {total} correct."
    if percentage >= 0.4:
        return f"Good effort: {score} out of {total} correct. Keep practicing."
    return f"{score} out of {total} correct. Review the material and try again."

def generate_feedback(wrong_questions, score: int, total: int) -> str:
    if total == 0:
        return "No questions were answered."

    if not wrong_questions:
        return f"Excellent work - you scored {score}/{total} with no mistakes."

    if not OLLAMA_URL:
        return build_fallback_feedback(score, total)

    prompt = f"""
You are an expert tutor.

A student scored {score}/{total}.

They got the following questions wrong:

{json.dumps(wrong_questions, indent=2)}

Provide:
1. A short performance summary
2. Key weak concepts
3. Specific advice for improvement

Keep it concise, structured, and encouraging.
"""

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": FEEDBACK_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": 300
                }
            },
            timeout=60,
        )
        response.raise_for_status()
        content = response.json().get("response", "")
        return content.strip() if content else build_fallback_feedback(score, total)
    except Exception:
        return build_fallback_feedback(score, total)

@app.get("/dashboard", response_model=DashboardRead)
def get_user_dashboard(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return current_user

@app.get("/topics/{topic_id}/details", response_model=TopicDetailedRead)
def get_topic_details(topic_id: int, session: Session = Depends(get_session),current_user: User = Depends(get_current_user)):
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    if topic.subject.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this topic")
    return topic

@app.post("/subjects/")
def create_subject(payload: SubjectCreate, session: Session = Depends(get_session),current_user: User = Depends(get_current_user)):
    new_subject = Subject(
        user_id=current_user.id,
        name=payload.name)
    session.add(new_subject)
    session.commit()
    session.refresh(new_subject)
    return new_subject

@app.post("/topics/")
def create_topic(payload: TopicCreate, session: Session = Depends(get_session),current_user: User = Depends(get_current_user)):
    subject = session.get(Subject, payload.subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if subject.user_id != current_user.id:
        raise HTTPException(status_code=403, detpiail="You do not have access to this subject")
    new_topic = Topic(
        subject_id=payload.subject_id,
        name=payload.name)
    session.add(new_topic)
    session.commit()
    session.refresh(new_topic)
    return new_topic


def process_pdf_in_background(file_path: str, topic_id: int, material_id: int):
    with Session(engine) as background_session:
        try:
            # 1. AI Layer: Extract text and vectors
            chunk_results = generate_chunks_and_embeddings(file_path)
            
            # 2. Database Layer: Save the results
            store_document_embeddings(
                chunk_results=chunk_results, 
                material_id=material_id, 
                session=background_session
            )
            
            # 2. THEN, generate the quiz (Generation)
            print("📝 Step 2: Generating quiz based on stored knowledge...")
            generate_and_store_quiz(
                session=background_session, 
                topic_id=topic_id, 
                material_id=material_id, # Pass the material_id instead of pdf_path!
                num_questions=50 
            )
            
        except Exception as e:
            print(f"❌ Background AI Task Failed: {e}")
            background_session.rollback()
            
@app.post("/materials/upload")
def add_material(background_tasks: BackgroundTasks, topic_id: int = Form(...), file: UploadFile = File(...), session: Session = Depends(get_session),current_user: User = Depends(get_current_user)):
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    if topic.subject.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this topic")

   #store physically on computer for now, will be moving to cloud storage in the future
    upload_dir = "materials"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    new_material = Material(
        name=file.filename,
        file_path=file_path,
        topic_id=topic_id
    )
    
    session.add(new_material)
    session.commit()
    session.refresh(new_material)

    background_tasks.add_task(process_pdf_in_background, file_path, topic_id, new_material.id)

    return new_material

@app.post("/quizzes/generate")
def generate_quiz(payload:QuizCreate, session: Session = Depends(get_session),current_user: User = Depends(get_current_user)):
    verified_topics = []
    for topic_id in payload.topic_ids:
        topic = session.get(Topic, topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail=f"Topic with ID {topic_id} not found")
        if topic.subject.user_id != current_user.id:
            raise HTTPException(status_code=403, detail=f"You do not have access to topic with ID {topic_id}")
        verified_topics.append(topic)
    if payload.difficulty_level == 1:
        min_diff, max_diff = 1, 2
    elif payload.difficulty_level == 2:
        min_diff, max_diff = 3, 4
    elif payload.difficulty_level == 3:
        min_diff, max_diff = 5, 5
    else:
        raise HTTPException(status_code=400, detail="Invalid difficulty level")
    
    statement = select(Question).where(
        Question.topic_id.in_(payload.topic_ids),
        Question.difficulty >= min_diff,
        Question.difficulty <= max_diff
    ).order_by(func.random()).limit(payload.length)
    
    selected_questions = session.exec(statement).all()

    if len(selected_questions) < payload.length:
         raise HTTPException(
             status_code=400, 
             detail=f"Not enough {payload.difficulty_level} questions in the bank. Please upload more materials!"
         )
    
    new_quiz = Quiz(
        topics =verified_topics,
        user_id=current_user.id,
        name=payload.name,
        difficulty_level =payload.difficulty_level,
        open_ended=payload.open_ended,
        length=payload.length,
        questions=selected_questions
    )

    session.add(new_quiz)
    session.commit()
    session.refresh(new_quiz)

    return new_quiz

#called to display quiz questions when quiz is started(used to display quiz questions)
@app.get("/quizzes/{quiz_id}/start-quiz", response_model=QuizRead)
def start_quiz(quiz_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    quiz = session.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this quiz")
    quiz.questions
    return quiz

@app.delete("/subjects/{subject_id}")
def delete_subject(subject_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    subject = session.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if subject.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this subject")
    for topic in subject.topics:
        for material in topic.materials:
            if material.file_path and os.path.exists(material.file_path):
                try:
                    os.remove(material.file_path)
                except Exception as e:
                    print(f"Failed to delete physical file {material.file_path}: {e}")
    session.delete(subject)
    session.commit()
    return {"message": f"Subject '{subject.name}' successfully deleted."}

@app.delete("/topics/{topic_id}")
def delete_topic(topic_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    if topic.subject.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this topic")
    for material in topic.materials:
            if material.file_path and os.path.exists(material.file_path):
                try:
                    os.remove(material.file_path)
                except Exception as e:
                    print(f"Failed to delete physical file {material.file_path}: {e}")
    session.delete(topic)
    session.commit()
    return {"message": f"Topic '{topic.name}' successfully deleted."}

@app.delete("/quizzes/{quiz_id}")
def delete_quiz(quiz_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    quiz = session.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this quiz")
    session.delete(quiz)
    session.commit()
    return {"message": f"Quiz '{quiz.name}' successfully deleted."}

@app.delete("/materials/{material_id}")
def delete_material(
    material_id: int, 
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    # SECURITY: Follow the chain up to the user (Material -> Topic -> Subject -> User)
    if material.topic.subject.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this material")

    # 1. DELETE THE PHYSICAL FILE FIRST
    # If the database delete fails later, it's better to have a ghost record 
    # than a ghost file permanently eating up server space.
    if material.file_path and os.path.exists(material.file_path):
        try:
            os.remove(material.file_path)
        except Exception as e:
            print(f"Failed to delete physical file {material.file_path}: {e}")
            # Depending on your strictness, you could raise an HTTP error here

    # 2. DELETE FROM DATABASE
    session.delete(material)
    session.commit()

    return {"message": f"Material '{material.name}' successfully deleted."}

@app.get("/attempts", response_model=List[QuizAttemptsGroup])
def get_user_attempts(
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    # 1. Join and sort chronologically 
    statement = (
        select(Quiz, QuizAttempt)
        .join(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
        .where(QuizAttempt.user_id == current_user.id)
        .order_by(Quiz.id, QuizAttempt.date.asc())
    )
    
    results = session.exec(statement).all()
    grouped_data = {}
    
    for quiz, attempt in results:
        if quiz.id not in grouped_data:
            grouped_data[quiz.id] = {
                "quiz_id": quiz.id,
                "quiz_name": quiz.name,
                "total_questions": quiz.length, # ⬅️ Just grab your column directly!
                "attempts": []
            }
        
        grouped_data[quiz.id]["attempts"].append({
            "id": attempt.id,
            "date": attempt.date,  
            "score": attempt.score
        })
        
    return list(grouped_data.values())

@app.get("/users/me/mastery", response_model=List[TopicMastery])
def get_user_mastery(
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    # 1. Grab every single answer this user has ever submitted, 
    # joined with the Question and the Topic.
    statement = (
        select(Topic, Question, Response)
        .join(Question, Question.topic_id == Topic.id)
        .join(Response, Response.question_id == Question.id)
        .join(QuizAttempt, Response.attempt_id == QuizAttempt.id) # <-- Bridge to the attempt!
        .where(QuizAttempt.user_id == current_user.id) # <-- Filter by the logged-in user
    )
    
    results = session.exec(statement).all()

    # 2. Group the math by Topic
    mastery_data = {}
    
    for topic, question, response in results:
        if topic.id not in mastery_data:
            mastery_data[topic.id] = {
                "topic_id": topic.id,
                "topic_name": topic.name,
                "total_attempted": 0,
                "total_correct": 0
            }
            
        # Tally up the score
        mastery_data[topic.id]["total_attempted"] += 1
        if response.is_correct:
            mastery_data[topic.id]["total_correct"] += 1

    # 3. Calculate the final percentage and format for Pydantic
    final_output = []
    for data in mastery_data.values():
        # Prevent division by zero just in case!
        if data["total_attempted"] > 0:
            pct = (data["total_correct"] / data["total_attempted"]) * 100
        else:
            pct = 0.0
            
        data["mastery_percentage"] = round(pct, 1) # Round to 1 decimal place
        final_output.append(data)

    return final_output

@app.get("/users/me/mastery-history")
def get_topic_mastery_history(
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    # 1. Grab every response, joined with Topic and Attempt, sorted by Date!
    statement = (
        select(Topic, QuizAttempt, Response)
        .join(Question, Question.topic_id == Topic.id)
        .join(Response, Response.question_id == Question.id)
        .join(QuizAttempt, Response.attempt_id == QuizAttempt.id)
        .where(QuizAttempt.user_id == current_user.id)
        .order_by(Topic.id, QuizAttempt.date.asc(), QuizAttempt.id.asc())
    )
    
    results = session.exec(statement).all()

    topics_dict = {}

    for topic, attempt, response in results:
        # Initialize the topic if we haven't seen it yet
        if topic.id not in topics_dict:
            topics_dict[topic.id] = {
                "topic_id": topic.id,
                "topic_name": topic.name,
                "running_correct": 0,
                "running_total": 0,
                "history": [] 
            }
            
        t = topics_dict[topic.id]
        
        # Add to the running math
        t["running_total"] += 1
        if response.is_correct:
            t["running_correct"] += 1
            
        # If this is a new attempt for this topic, create a new dot on the chart
        if not t["history"] or t["history"][-1]["attempt_id"] != attempt.id:
            t["history"].append({
                "attempt_id": attempt.id,
                "date": attempt.date,
                "percentage": 0.0
            })
            
        # Constantly update the latest dot's percentage based on the running total
        t["history"][-1]["percentage"] = round((t["running_correct"] / t["running_total"]) * 100, 1)

    return list(topics_dict.values())
    return list(grouped_data.values())
