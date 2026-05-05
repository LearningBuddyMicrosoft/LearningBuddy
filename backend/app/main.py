import os
import time
import requests
from typing import List
from datetime import date

from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.concurrency import asynccontextmanager
from sqlmodel import Session, select, func

from .database_insertion import store_document_embeddings
from .pdf_processor import generate_chunks_and_embeddings
from .quiz_generator import generate_and_store_quiz
from .security import create_access_token, get_current_user, get_password_hash, verify_password
from .database import create_db_and_tables, get_session, engine
from .models import Material, Question, Quiz, Response, Subject, Topic, User, QuizAttempt
from .schemas import (
    DashboardRead, QuizAttemptsGroup, QuizCreate, QuizRead,
    SubjectCreate, TopicCreate, TopicDetailedRead,
    TopicMastery,
    UserCreate, StartAttempt, AnswerSubmission,
    FinishAttempt, BatchSubmission
)
from ai.llm import generate_quiz_fast, generate_feedback_fast


# App lifecycle (startup/shutdown)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 App starting up: Creating database and tables...")
    create_db_and_tables()
    yield
    print("👋 App shutting down: Cleaning up resources...")

app = FastAPI(lifespan=lifespan)


# Register a new user
@app.post("/register/")
def register_user(user_create: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(
        select(User).where(User.username == user_create.username)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = get_password_hash(user_create.password)
    new_user = User(username=user_create.username, hashed_password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return {"message": "User registered successfully", "user_id": new_user.id}


# Log in and return JWT
@app.post("/login/")
def login_user(user_create: UserCreate, session: Session = Depends(get_session)):
    user = session.exec(
        select(User).where(User.username == user_create.username)
    ).first()
    if not user or not verify_password(user_create.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


# Start a new quiz attempt
@app.post("/start-attempt/")
def start_attempt(
    payload: StartAttempt,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
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


# Submit all answers in one go (exam-style)
@app.post("/submit-batch-answers/")
def submit_batch_answers(
    batch_submission: BatchSubmission,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    attempt = session.get(QuizAttempt, batch_submission.attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    if attempt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this attempt")

    score = 0
    response_list: List[Response] = []

    for answer in batch_submission.answers:
        question = session.get(Question, answer.question_id)
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")

        new_response = grade_and_build_response(answer, current_user.id, session)
        response_list.append(new_response)

        if new_response.is_correct:
            score += 1

    total_answers = len(batch_submission.answers)
    attempt.score = score

    quiz = session.get(Quiz, attempt.quiz_id)
    if quiz:
        quiz.highscore = max(quiz.highscore, attempt.score)
        session.add(quiz)

    session.add_all(response_list)
    session.add(attempt)
    session.commit()
    session.refresh(attempt)

    return {
        "attempt_id": attempt.id,
        "score": score,
        "total": total_answers,
    }


# Finish attempt and generate AI feedback for the results page
@app.post("/finish-attempt/")
def finish_attempt(
    submission: FinishAttempt,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    # Load attempt and check ownership
    attempt = session.get(QuizAttempt, submission.attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this attempt")

    # Load all questions + responses for this attempt in submission order
    rows = session.exec(
        select(Question, Response)
        .join(Response, Response.question_id == Question.id)
        .where(Response.attempt_id == submission.attempt_id)
        .order_by(Response.id.asc())
    ).all()

    if not rows:
        raise HTTPException(status_code=400, detail="No responses found for this attempt")

    # Get material name for feedback context
    quiz = session.get(Quiz, attempt.quiz_id)
    material = session.exec(
        select(Material)
        .where(Material.topic_id == quiz.topics[0].id)
        .order_by(Material.id.desc())
    ).first()
    material_name = material.name.replace(".pdf", "") if material else "your material"

    # Build payloads for the LLM
    questions_payload = []
    answers_payload = {}
 
    for i, (question, response) in enumerate(rows, start=1):
        questions_payload.append({
            "id": question.id,
            "question_number": i,
            "question": question.question_text,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "source": question.source,
        })
        answers_payload[str(question.id)] = response.selected_option

    # Try generating AI feedback via LLM
    try:
        feedback = generate_feedback_fast(
            questions_payload,
            answers_payload,
            material_name=material_name,
        )
        # Expecting feedback as a dict: {"summary": str, "details": [ ... ]}
    except Exception as e:
        print(f"LLM feedback failed, using fallback: {e}")

        score = attempt.score
        total = len(rows)
        pct = (score / total * 100) if total > 0 else 0

        if pct == 100:
            summary = f"You scored {score}/{total} — perfect score!"
        elif pct >= 80:
            summary = f"You scored {score}/{total} — excellent work!"
        elif pct >= 60:
            summary = f"You scored {score}/{total} — good effort!"
        elif pct >= 40:
            summary = f"You scored {score}/{total} — keep going!"
        else:
            summary = f"You scored {score}/{total} — review the material and try again."

        # Build fallback details in the same shape as LLM output
        details = []
        for question, response in rows:
            details.append({
                "question": question.question_text,
                "your_answer": answers_payload.get(str(question.id), "No answer"),
                "correct_answer": question.correct_answer,
                "explanation": question.explanation,
                "source": question.source,
                "practice_tip": "",
            })

        feedback = {
            "summary": summary,
            "details": details,
        }

    # Persist summary to attempt
    attempt.feedback = feedback["summary"]
    session.add(attempt)
    session.commit()
    session.refresh(attempt)

    # Convert feedback details into graded_questions for the frontend
    graded_questions = []
    for item in feedback["details"]:
        graded_questions.append({
            "question_text":  item.get("question") or item.get("question_text", ""),
            "your_answer":    item.get("your_answer", ""),
            "correct_answer": item.get("correct_answer", ""),
            "explanation":    item.get("explanation", ""),
            "practice_tip":   item.get("practice_tip", ""),
            "source":         item.get("source", ""),
        })

    # Return structure the results page expects
    return {
        "score": attempt.score,
        "summary": feedback["summary"],
        "graded_questions": graded_questions,
    }


# Build a Response row and basic per-question feedback (no LLM)
def grade_and_build_response(
    submission: AnswerSubmission,
    current_user_id: int,
    session: Session,
):
    question = session.get(Question, submission.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    is_correct = (
        str(submission.selected_option).strip().lower()
        == str(question.correct_answer).strip().lower()
    )

    if is_correct:
        feedback = f"Correct! '{submission.selected_option}' is the right answer."
    else:
        feedback = (
            f"Incorrect. You chose '{submission.selected_option}', "
            f"but the correct answer is '{question.correct_answer}'."
        )

    response = Response(
        user_id=current_user_id,
        attempt_id=submission.attempt_id,
        question_id=submission.question_id,
        selected_option=submission.selected_option,
        is_correct=is_correct,
        feedback=feedback,
    )
    return response


# Add this endpoint to main.py (paste it anywhere after the /finish-attempt/ route)

@app.get("/attempts/{attempt_id}/review")
def get_attempt_review(
    attempt_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    attempt = session.get(QuizAttempt, attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this attempt")

    rows = session.exec(
        select(Question, Response)
        .join(Response, Response.question_id == Question.id)
        .where(Response.attempt_id == attempt_id)
        .order_by(Response.id.asc())
    ).all()

    if not rows:
        raise HTTPException(status_code=400, detail="No responses found for this attempt")

    quiz = session.get(Quiz, attempt.quiz_id)

    graded_questions = []
    for question, response in rows:
        graded_questions.append({
            "question_text": question.question_text,
            "your_answer": response.selected_option,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "source": question.source,
            "practice_tip": "" if response.is_correct else f"Review this topic: {question.source}" ,
        })

    return {
        "attempt_id": attempt_id,
        "quiz_name": quiz.name if quiz else "Quiz",
        "score": attempt.score,
        "total": len(rows),
        "summary": attempt.feedback or "",
        "graded_questions": graded_questions,
    }

# Return current user's dashboard data
@app.get("/dashboard", response_model=DashboardRead)
def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return current_user


# Return detailed info for a topic
@app.get("/topics/{topic_id}/details", response_model=TopicDetailedRead)
def get_topic_details(
    topic_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    if topic.subject.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this topic")
    return topic


# Create a new subject
@app.post("/subjects/")
def create_subject(
    payload: SubjectCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    new_subject = Subject(
        user_id=current_user.id,
        name=payload.name,
    )
    session.add(new_subject)
    session.commit()
    session.refresh(new_subject)
    return new_subject


# Create a new topic under a subject
@app.post("/topics/")
def create_topic(
    payload: TopicCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    subject = session.get(Subject, payload.subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    if subject.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this subject")

    new_topic = Topic(
        subject_id=payload.subject_id,
        name=payload.name,
    )
    session.add(new_topic)
    session.commit()
    session.refresh(new_topic)
    return new_topic


# Wait for Ollama to be ready before heavy LLM work
def _wait_for_ollama_ready(timeout_seconds: int = 90, poll_interval: int = 5) -> bool:
    ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434").rstrip("/")
    tags_url = f"{ollama_url}/api/tags"
    deadline = time.time() + timeout_seconds

    while time.time() < deadline:
        try:
            response = requests.get(tags_url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(poll_interval)

    return False


# Background task: process PDF, embed, and generate quiz
def process_pdf_in_background(file_path: str, topic_id: int, material_id: int):
    with Session(engine) as background_session:
        try:
            # Mark material as embedding
            material = background_session.get(Material, material_id)
            if material:
                material.processing_status = "embedding"
                background_session.add(material)
                background_session.commit()

            chunk_results = generate_chunks_and_embeddings(file_path)

            store_document_embeddings(
                chunk_results=chunk_results,
                material_id=material_id,
                session=background_session,
            )

            # Mark material as generating_quiz
            if material:
                material.processing_status = "generating_quiz"
                background_session.add(material)
                background_session.commit()

            print("📝 Embeddings saved. Waiting for Ollama to become ready for quiz generation...")
            if not _wait_for_ollama_ready():
                print("⚠️ Ollama did not become ready in time. Quiz generation will retry later or require manual intervention.")
                if material:
                    material.processing_status = "failed"
                    background_session.add(material)
                    background_session.commit()
                return

            print("🧠 Ollama is ready. Starting background quiz generation for uploaded PDF...")
            chunk_count = len(chunk_results)
            if chunk_count < 20:
                num_questions = 20
            elif chunk_count < 40:
                num_questions = 40
            else:
                num_questions = 60

            print(f"📊 PDF has {chunk_count} chunks — generating {num_questions} questions.")

            generate_and_store_quiz(
                session=background_session,
                topic_id=topic_id,
                material_id=material_id,
                num_questions=num_questions,
            )

            # Mark material as ready
            if material:
                material.processing_status = "ready"
                background_session.add(material)
                background_session.commit()

            print("✅ Upload background task complete: embeddings stored and quiz generated.")

        except Exception as e:
            print(f"❌ Background AI Task Failed: {e}")
            background_session.rollback()
            # Try to mark status as failed
            try:
                with Session(engine) as error_session:
                    material = error_session.get(Material, material_id)
                    if material:
                        material.processing_status = "failed"
                        error_session.add(material)
                        error_session.commit()
            except Exception as status_error:
                print(f"❌ Failed to update status to failed: {status_error}")


# Upload a PDF and kick off background processing
@app.post("/materials/upload")
def add_material(
    background_tasks: BackgroundTasks,
    topic_id: int = Form(...),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    topic = session.get(Topic, topic_id)
    print(f"📤 Upload request: topic_id={topic_id}, filename={file.filename}, user_id={current_user.id}")
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    if topic.subject.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this topic")

    upload_dir = "materials"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())

    new_material = Material(
        name=file.filename,
        file_path=file_path,
        topic_id=topic_id,
    )

    session.add(new_material)
    session.commit()
    session.refresh(new_material)

    background_tasks.add_task(process_pdf_in_background, file_path, topic_id, new_material.id)

    return new_material


# Generate a quiz from existing questions (no LLM call here)
@app.post("/quizzes/generate")
def generate_quiz(
    payload: QuizCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    import random

    verified_topics = []
    for topic_id in payload.topic_ids:
        topic = session.get(Topic, topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail=f"Topic with ID {topic_id} not found")
        if topic.subject.user_id != current_user.id:
            raise HTTPException(status_code=403, detail=f"You do not have access to topic with ID {topic_id}")
        verified_topics.append(topic)

    topic_id = payload.topic_ids[0]

    # Ensure material exists
    material = session.exec(
        select(Material)
        .where(Material.topic_id == topic_id)
        .order_by(Material.id.desc())
    ).first()
    if not material:
        raise HTTPException(status_code=400, detail="No materials uploaded for this topic")

    # Ensure material is ready
    if material.processing_status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Material is still processing ({material.processing_status}). Please wait and try again.",
        )

    # Pull existing questions
    all_questions = session.exec(
        select(Question).where(Question.topic_id == topic_id)
    ).all()

    if not all_questions:
        raise HTTPException(
            status_code=400,
            detail="No questions available for this topic. Please wait for upload processing to complete.",
        )

    selected_questions = random.sample(
        all_questions,
        min(payload.length, len(all_questions)),
    )

    quiz = Quiz(
        topics=verified_topics,
        user_id=current_user.id,
        name=payload.name,
        difficulty_level=payload.difficulty_level,
        open_ended=payload.open_ended,
        length=payload.length,
        questions=selected_questions,
    )

    session.add(quiz)
    session.commit()
    session.refresh(quiz)

    return quiz


# Return quiz details + questions when a quiz is started
@app.get("/quizzes/{quiz_id}/start-quiz", response_model=QuizRead)
def start_quiz(
    quiz_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    quiz = session.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this quiz")
    quiz.questions  # force load
    return quiz


# Delete a subject and its materials (including files)
@app.delete("/subjects/{subject_id}")
def delete_subject(
    subject_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
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


# Delete a topic and its materials
@app.delete("/topics/{topic_id}")
def delete_topic(
    topic_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
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


# Delete a quiz
@app.delete("/quizzes/{quiz_id}")
def delete_quiz(
    quiz_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    quiz = session.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have access to this quiz")

    session.delete(quiz)
    session.commit()
    return {"message": f"Quiz '{quiz.name}' successfully deleted."}


# Delete a material and its physical file
@app.delete("/materials/{material_id}")
def delete_material(
    material_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    if material.topic.subject.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this material")

    if material.file_path and os.path.exists(material.file_path):
        try:
            os.remove(material.file_path)
        except Exception as e:
            print(f"Failed to delete physical file {material.file_path}: {e}")

    session.delete(material)
    session.commit()

    return {"message": f"Material '{material.name}' successfully deleted."}


# Return grouped quiz attempts for the current user
@app.get("/attempts", response_model=List[QuizAttemptsGroup])
def get_user_attempts(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
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
                "total_questions": quiz.length,
                "attempts": [],
            }

        grouped_data[quiz.id]["attempts"].append({
            "id": attempt.id,
            "date": attempt.date,
            "score": attempt.score,
        })

    return list(grouped_data.values())


# Return mastery per topic for the current user
@app.get("/users/me/mastery", response_model=List[TopicMastery])
def get_user_mastery(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    statement = (
        select(Topic, Question, Response)
        .join(Question, Question.topic_id == Topic.id)
        .join(Response, Response.question_id == Question.id)
        .join(QuizAttempt, Response.attempt_id == QuizAttempt.id)
        .where(QuizAttempt.user_id == current_user.id)
    )

    results = session.exec(statement).all()
    mastery_data = {}

    for topic, question, response in results:
        if topic.id not in mastery_data:
            mastery_data[topic.id] = {
                "topic_id": topic.id,
                "topic_name": topic.name,
                "total_attempted": 0,
                "total_correct": 0,
            }

        mastery_data[topic.id]["total_attempted"] += 1
        if response.is_correct:
            mastery_data[topic.id]["total_correct"] += 1

    final_output = []
    for data in mastery_data.values():
        pct = (
            (data["total_correct"] / data["total_attempted"]) * 100
            if data["total_attempted"] > 0 else 0.0
        )
        data["mastery_percentage"] = round(pct, 1)
        final_output.append(data)

    return final_output


# Return mastery history over time per topic
@app.get("/users/me/mastery-history")
def get_topic_mastery_history(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
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
        if topic.id not in topics_dict:
            topics_dict[topic.id] = {
                "topic_id": topic.id,
                "topic_name": topic.name,
                "running_correct": 0,
                "running_total": 0,
                "history": [],
            }

        t = topics_dict[topic.id]

        t["running_total"] += 1
        if response.is_correct:
            t["running_correct"] += 1

        if not t["history"] or t["history"][-1]["attempt_id"] != attempt.id:
            t["history"].append({
                "attempt_id": attempt.id,
                "date": attempt.date,
                "percentage": 0.0,
            })

        t["history"][-1]["percentage"] = round(
            (t["running_correct"] / t["running_total"]) * 100, 1
        )

    return list(topics_dict.values())
