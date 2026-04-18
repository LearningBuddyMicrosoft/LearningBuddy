from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import JSON, Column
from pgvector.sqlalchemy import Vector

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    hashed_password: str

    attempts: List["QuizAttempt"] = Relationship(back_populates="user")
    responses: List["Response"] = Relationship(back_populates="user")
    subjects: List["Subject"] = Relationship(back_populates="user")
    quizzes: List["Quiz"] = Relationship(back_populates="user")

    username: str

class Subject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    user_id:int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="subjects")

    topics: List["Topic"] = Relationship(
        back_populates="subject",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"})

    name: str

class Quiz_TopicLink(SQLModel, table=True):
    topic_id: Optional[int] = Field(foreign_key="topic.id", primary_key=True)
    quiz_id: Optional[int] = Field(foreign_key="quiz.id", primary_key=True)

class Topic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    subject_id: int = Field(foreign_key="subject.id")
    subject: Subject = Relationship(back_populates="topics")
    materials: List["Material"] = Relationship(
        back_populates="topic",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    quiz_questions: List["Question"] = Relationship(
        back_populates="topic",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    quizzes: List["Quiz"] = Relationship(
        back_populates="topics",
        link_model=Quiz_TopicLink)


    name: str

class Question_QuizLink(SQLModel, table=True):
    question_id: Optional[int] = Field(foreign_key="question.id", primary_key=True)
    quiz_id : Optional[int] = Field(foreign_key="quiz.id", primary_key=True)

class Quiz(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="quizzes")
    questions: List["Question"] = Relationship(back_populates="quizzes", link_model=Question_QuizLink)
    topics: List["Topic"] = Relationship(back_populates="quizzes", link_model=Quiz_TopicLink)
    attempts: List["QuizAttempt"] = Relationship(back_populates="quiz")

    name: str
    difficulty_level: int
    open_ended: bool = Field(default=False) #Indicates if the quiz allows open-ended responses
    length: int = Field(default=10) #number of questions
    highscore: int = Field(default=0) #highest score achieved on this quiz

class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    topic_id: int = Field(foreign_key="topic.id")
    topic: Topic = Relationship(back_populates="quiz_questions")

    responses: List["Response"] = Relationship(back_populates="question")
    quizzes: List["Quiz"] = Relationship(back_populates="questions", link_model=Question_QuizLink)

    question_type: str
    difficulty: int
    question_text: str
    options: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSON))
    correct_answer: str


# This class defines both a Python Object AND a Database Table
class QuizAttempt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="attempts") 
    responses: List["Response"] = Relationship(back_populates="attempt")
    quiz_id: int = Field(foreign_key="quiz.id")
    quiz: Quiz = Relationship(back_populates="attempts")


    date: str
    score: int
    feedback: str  # Linked to Mistake Analysis  


class Material(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    topic_id: int = Field(foreign_key="topic.id")
    topic: Topic = Relationship(back_populates="materials")
    chunks: List["DocumentChunk"] = Relationship(back_populates="material")

    name: str
    file_path: str

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
