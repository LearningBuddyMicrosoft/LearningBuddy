import os

from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile
from sqlmodel import Session, select, func
from .database import engine
from datetime import date
from .models import Material, Question, Response, Subject, Topic, User, QuizAttempt # From your previous steps
from.schemas import DashboardRead, SubjectCreate, TopicCreate, TopicDetailedRead, UserCreate, StartAttempt, AnswerSubmission, FinishAttempt, BatchSubmission

app = FastAPI()

# This is your 'Dependency'. It manages the connection for each request.
def get_session():
    with Session(engine) as session:
        yield session

#will likely be updated later
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
    }

@app.post("/create-user")
def create_user(user_data: UserCreate, session: Session = Depends(get_session)):
    new_user = User(username=user_data.username)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

#called everytime a quiz is started
@app.post("/start-attempt/")
def start_attempt(payload: StartAttempt, session: Session = Depends(get_session)):
    user = session.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")   
    new_attempt = QuizAttempt(
        user_id=payload.user_id,
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
def submit_answer(submission: AnswerSubmission, session: Session = Depends(get_session)):
    new_response = grade_and_build_response(submission, session)
    session.add(new_response)
    session.commit()
    session.refresh(new_response)
    return new_response

#called only when quiz is finished in single mode
@app.post("/finish-attempt/")
def finish_attempt(submission: FinishAttempt, session: Session = Depends(get_session)):
    attempt = session.get(QuizAttempt, submission.attempt_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    # Calculate score based on responses
    statement = select(func.count()).where(
        Response.attempt_id == submission.attempt_id,
        Response.is_correct == True
    )
    correct_count = session.exec(statement).first() or 0

    # Update the attempt with the final score and feedback
    attempt.score = correct_count
    #hardcoded overall feedback for now, will be calling AI for this in the future
    attempt.feedback = f"You got {correct_count} correct answers."
    session.add(attempt)
    session.commit()
    session.refresh(attempt)

    return attempt

#called when quiz is finished in batch mode
@app.post("/submit-batch-answers/")
def submit_batch_answers(batch_submission: BatchSubmission, session: Session = Depends(get_session)):
    new_attempt = session.get(QuizAttempt, batch_submission.attempt_id)
    if not new_attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    score = 0
    graded_responses = []
    response_list = []
    for answer in batch_submission.answers:
        question = session.get(Question, answer.question_id)
        new_response = grade_and_build_response(answer, session)
        response_list.append(new_response)

        is_correct = new_response.is_correct

        if is_correct:
            score += 1
            graded_responses.append(question.question_text + ": Correct")
        else:
            graded_responses.append(question.question_text + ": Incorrect")
        
    #hardcoded feedback for now, will be calling AI for this in the future
    overall_feedback = f"{score} out of {len(batch_submission.answers)} correct. {'; '.join(graded_responses)}"

    new_attempt.score = score
    new_attempt.feedback = overall_feedback

    session.add_all(response_list)
    session.add(new_attempt)
    session.commit()
    session.refresh(new_attempt)

    return new_attempt

def grade_and_build_response(submission: AnswerSubmission, session: Session):
    question = session.get(Question, submission.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    is_correct = submission.selected_option == question.correct_answer

    #hardcoded feedback for now, will be calling AI for this in the future
    if is_correct:
        feedback = "Correct!"
    else:
        feedback = "Incorrect. Review the material and try again."
    
    response = Response(
        user_id=submission.user_id,
        attempt_id=submission.attempt_id,
        question_id=submission.question_id,
        selected_option=submission.selected_option,
        is_correct=is_correct,
        feedback=feedback   
        )
    return response

@app.get("/user/{user_id}/mainpage", response_model=DashboardRead)
def get_user_dashboard(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@app.get("/user/{user_id}/topic/{topic_id}/details", response_model=TopicDetailedRead)
def get_topic_details(user_id: int, topic_id: int, session: Session = Depends(get_session)):
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return topic

@app.post("/subjects/")
def create_subject(payload: SubjectCreate, session: Session = Depends(get_session)):
    user = session.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    new_subject = Subject(
        user_id=payload.user_id,
        name=payload.name)
    session.add(new_subject)
    session.commit()
    session.refresh(new_subject)
    return new_subject

@app.post("/topics/")
def create_topic(payload: TopicCreate, session: Session = Depends(get_session)):
    subject = session.get(Subject, payload.subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    new_topic = Topic(
        subject_id=payload.subject_id,
        name=payload.name)
    session.add(new_topic)
    session.commit()
    session.refresh(new_topic)
    return new_topic

@app.post("/materials/upload")
def add_material(topic_id: int = Form(...), file: UploadFile = File(...), session: Session = Depends(get_session)):
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    
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
    return new_material