from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import JSON, Column

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    attempts: List["QuizAttempt"] = Relationship(back_populates="user")
    responses: List["Response"] = Relationship(back_populates="user")

    username: str

class Subject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    topics: List["Topic"] = Relationship(back_populates="subject")

    name: str

class Topic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    subject_id: int = Field(foreign_key="subject.id")
    subject: Subject = Relationship(back_populates="topics")
    materials: List["Material"] = Relationship(back_populates="topic")
    quiz_questions: List["Question"] = Relationship(back_populates="topic")
    quiz_attempts: List["QuizAttempt"] = Relationship(back_populates="topic")


    name: str


# This class defines both a Python Object AND a Database Table
class QuizAttempt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    topic_id: int = Field(foreign_key="topic.id")
    topic: Topic = Relationship(back_populates="quiz_attempts")
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="attempts") 
    responses: List["Response"] = Relationship(back_populates="attempt")

    date: str
    score: int
    feedback: str  # Linked to Mistake Analysis  


class Material(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    topic_id: int = Field(foreign_key="topic.id")
    topic: Topic = Relationship(back_populates="materials")

    name: str
    file_path: str

class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    topic_id: int = Field(foreign_key="topic.id")
    topic: Topic = Relationship(back_populates="quiz_questions")

    responses: List["Response"] = Relationship(back_populates="question")

    question_type: str
    question_text: str
    options: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSON))
    correct_answer: str

class Response(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    attempt_id: int = Field(foreign_key="quizattempt.id")
    attempt: QuizAttempt = Relationship(back_populates="responses")

    question_id: int = Field(foreign_key="question.id")
    question: Question = Relationship(back_populates="responses")

    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="responses")

    selected_option: str
    is_correct: bool
    feedback: str