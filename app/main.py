from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select, func
from .database import engine
from .models import Users, QuizAttempt # From your previous steps

app = FastAPI()

# This is your 'Dependency'. It manages the connection for each request.
def get_session():
    with Session(engine) as session:
        yield session

@app.get("/mastery/{user_id}")
def get_user_mastery(user_id: int, session: Session = Depends(get_session)):
    # 1. Logic to find the user in your 'Users' table
    user = session.get(Users, user_id)
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

@app.post("/submit-attempt")
def submit_attempt(quiz_attempt: QuizAttempt, session: Session = Depends(get_session)):
    user_id = session.get(Users, quiz_attempt.user_id)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    session.add(quiz_attempt)
    session.commit()
    session.refresh(quiz_attempt)
    return quiz_attempt

@app.post("/create-user")
def create_user(username: str, session: Session = Depends(get_session)):
    new_user = Users(username=username)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user