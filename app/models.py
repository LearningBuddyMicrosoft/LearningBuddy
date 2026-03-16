from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

class Users(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    attempts: List["QuizAttempt"] = Relationship(back_populates="user")


# This class defines both a Python Object AND a Database Table
class QuizAttempt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    topic_id: str
    score: int
    feedback: str  # Linked to Mistake Analysis
    user_id: int = Field(foreign_key="users.id")
    user: Users = Relationship(back_populates="attempts")   