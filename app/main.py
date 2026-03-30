from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select, func
from .database import engine
from datetime import date
from .models import Question, Response, Topic, User, QuizAttempt # From your previous steps
from.schemas import UserCreate, StartAttempt, AnswerSubmission, FinishAttempt, BatchSubmission

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
def start_attempt(start_attempt: StartAttempt, session: Session = Depends(get_session)):
    user = session.get(User, start_attempt.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")   
    new_attempt = QuizAttempt(
        user_id=start_attempt.user_id,
        quiz_mode=start_attempt.quiz_mode,
        date=date.today().isoformat(),
        score=0,
        feedback=""
    )
    for topic_id in start_attempt.topic_ids:
        topic = session.get(Topic, topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail=f"Topic with ID {topic_id} not found")
        new_attempt.topics.append(topic)

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