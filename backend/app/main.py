import os
from typing import List

from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.concurrency import asynccontextmanager
from sqlmodel import Session, select, func

from .pdf_processor import generate_and_store_quiz

from .security import create_access_token, get_current_user, get_password_hash, verify_password
from .database import create_db_and_tables, get_session, engine
from datetime import date
from .models import Material, Question, Quiz, Response, Subject, Topic, User, QuizAttempt # From your previous steps
from .schemas import DashboardRead, QuizAttemptsGroup, QuizCreate, QuizRead, SubjectCreate, TopicCreate, TopicDetailedRead, UserCreate, StartAttempt, AnswerSubmission, FinishAttempt, BatchSubmission



'''
#mastery logic will be discussed and updated later
@app.get("/mastery/{user_id}")
def get_user_mastery(user_id: int, session: Session = Depends(get_session)):
    # 1. Logic to find the user in your 'Users' table
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # 2. Logic to calculate mastery from 'QuizAttempt' history 
    # We select the average score where the user_id matches
    statement = select(func.avg(QuizAttempt.score)).where(QuizAttempt.user_id == user_id)
    average_score = session.exec(statement).first()

    return {
        "username": user.username,
        "average_mastery": average_score or 0.0,
        "total_attempts": len(user.attempts)
    }\
'''

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Everything BEFORE 'yield' happens when the server TURNS ON
    print("🚀 App starting up: Creating database and tables...")
    create_db_and_tables()
    
    yield # This is where the app actually runs!
    
    # Everything AFTER 'yield' happens when the server TURNS OFF
    print("👋 App shutting down: Cleaning up resources...")     

app = FastAPI(lifespan=lifespan)

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
        feedback="",
        

        quiz_snapshot={
        "quiz_name": quiz.name,
        "difficulty": quiz.difficulty_level,
        "questions": [
            {
                "id": q.id,
                "text": q.question_text,
                "options": q.options,
                "correct_answer": q.correct_answer
            }
            for q in quiz.questions
        ]
    }
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

    # Update the attempt with the final score and feedback
    attempt.score = int(correct_count)
    #TODO:hardcoded overall feedback for now, will be calling AI for this in the future
    attempt.feedback = f"You got {attempt.score} correct answers."

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
    graded_responses = []
    response_list = []
    for answer in batch_submission.answers:
        question = session.get(Question, answer.question_id)
        new_response = grade_and_build_response(answer,current_user.id, session)
        response_list.append(new_response)

        is_correct = new_response.is_correct

        if is_correct:
            score += 1
            graded_responses.append(question.question_text + ": Correct")
        else:
            graded_responses.append(question.question_text + ": Incorrect")
        
    #TODO:hardcoded feedback for now, will be calling AI for this in the future
    overall_feedback = f"{score} out of {len(batch_submission.answers)} correct. {'; '.join(graded_responses)}"

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
        raise HTTPException(status_code=403, detail="You do not have access to this subject")
    new_topic = Topic(
        subject_id=payload.subject_id,
        name=payload.name)
    session.add(new_topic)
    session.commit()
    session.refresh(new_topic)
    return new_topic


def process_pdf_in_background(file_path: str, topic_id: int):
    with Session(engine) as background_session:
        try:
            generate_and_store_quiz(
                pdf_path=file_path, 
                session=background_session, 
                topic_id=topic_id, 
                num_questions=10 # Adjust if needed
            )
        except Exception as e:
            print(f"❌ Background AI Task Failed: {e}")
            
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

    background_tasks.add_task(process_pdf_in_background, file_path, topic_id)

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
        min_diff, max_diff = 1, 3
    elif payload.difficulty_level == 2:
        min_diff, max_diff = 4, 7
    elif payload.difficulty_level == 3:
        min_diff, max_diff = 8, 10
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

#Called to get saved user Attempts(used to display past quiz attempts and scores)

@app.get("/attempts", response_model=List[QuizAttemptsGroup])
def get_user_attempts(
    session: Session = Depends(get_session), 
    current_user: User = Depends(get_current_user)
):
    statement = (
        select(Quiz, QuizAttempt)
        .join(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
        .where(QuizAttempt.user_id == current_user.id)
    )
    
    results = session.exec(statement).all()

    # 2. THE GROUPING: Reorganize the flat SQL rows into our nested dictionary
    grouped_data = {}

    for quiz, attempt in results:
        if quiz.id not in grouped_data:
            grouped_data[quiz.id] = {
                "quiz_id": quiz.id,
                "quiz_name": quiz.name,
                "attempts": []
            }
        
        grouped_data[quiz.id]["attempts"].append({
            "id": attempt.id,
            "date": attempt.date,
            "score": attempt.score
        })

    return list(grouped_data.values())