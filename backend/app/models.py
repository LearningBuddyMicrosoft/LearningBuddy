from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import JSON, Column
from pgvector.sqlalchemy import Vector


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # hashed password for authentication
    hashed_password: str

    # relationships to user-owned data
    attempts: List["QuizAttempt"] = Relationship(back_populates="user")
    responses: List["Response"] = Relationship(back_populates="user")
    subjects: List["Subject"] = Relationship(back_populates="user")
    quizzes: List["Quiz"] = Relationship(back_populates="user")

    # username used for login
    username: str


class Subject(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # owner of the subject
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="subjects")

    # topics under this subject
    topics: List["Topic"] = Relationship(
        back_populates="subject",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # subject name
    name: str


class Quiz_TopicLink(SQLModel, table=True):
    # link table connecting quizzes and topics
    topic_id: Optional[int] = Field(foreign_key="topic.id", primary_key=True)
    quiz_id: Optional[int] = Field(foreign_key="quiz.id", primary_key=True)


class Topic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # parent subject
    subject_id: int = Field(foreign_key="subject.id")
    subject: Subject = Relationship(back_populates="topics")

    # uploaded materials for this topic
    materials: List["Material"] = Relationship(
        back_populates="topic",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # questions generated for this topic
    quiz_questions: List["Question"] = Relationship(
        back_populates="topic",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # quizzes that include this topic
    quizzes: List["Quiz"] = Relationship(
        back_populates="topics",
        link_model=Quiz_TopicLink
    )

    # topic name
    name: str


class Question_QuizLink(SQLModel, table=True):
    # link table connecting questions and quizzes
    question_id: Optional[int] = Field(foreign_key="question.id", primary_key=True)
    quiz_id: Optional[int] = Field(foreign_key="quiz.id", primary_key=True)


class Quiz(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # owner of the quiz
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="quizzes")

    # questions included in this quiz
    questions: List["Question"] = Relationship(
        back_populates="quizzes",
        link_model=Question_QuizLink
    )

    # topics this quiz is based on
    topics: List["Topic"] = Relationship(
        back_populates="quizzes",
        link_model=Quiz_TopicLink
    )

    # attempts made on this quiz
    attempts: List["QuizAttempt"] = Relationship(back_populates="quiz")

    # quiz metadata
    name: str
    difficulty_level: int
    open_ended: bool = Field(default=False)
    length: int = Field(default=10)
    highscore: int = Field(default=0)


class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # topic this question belongs to
    topic_id: int = Field(foreign_key="topic.id")
    topic: Topic = Relationship(back_populates="quiz_questions")

    # responses submitted for this question
    responses: List["Response"] = Relationship(back_populates="question")

    # quizzes that include this question
    quizzes: List["Quiz"] = Relationship(
        back_populates="questions",
        link_model=Question_QuizLink
    )

    # question metadata
    question_type: str
    difficulty: int
    question_text: str

    # multiple-choice options stored as JSON
    options: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSON))

    # correct answer and explanation
    correct_answer: str
    explanation: str = Field(default="")
    source: str = Field(default="")


class QuizAttempt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # user who made the attempt
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="attempts")

    # responses submitted in this attempt
    responses: List["Response"] = Relationship(back_populates="attempt")

    # quiz being attempted
    quiz_id: int = Field(foreign_key="quiz.id")
    quiz: Quiz = Relationship(back_populates="attempts")

    # attempt metadata
    date: str
    score: int
    feedback: str


class Material(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # topic this material belongs to
    topic_id: int = Field(foreign_key="topic.id")
    topic: Topic = Relationship(back_populates="materials")

    # chunks extracted from the PDF
    chunks: List["DocumentChunk"] = Relationship(
        back_populates="material",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # file info and processing status
    name: str
    file_path: str
    processing_status: str = Field(default="uploaded")


class Response(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # attempt this response belongs to
    attempt_id: int = Field(foreign_key="quizattempt.id")
    attempt: QuizAttempt = Relationship(back_populates="responses")

    # question being answered
    question_id: int = Field(foreign_key="question.id")
    question: Question = Relationship(back_populates="responses")

    # user who submitted the response
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="responses")

    # selected option and correctness
    selected_option: str
    is_correct: bool
    feedback: str


class DocumentChunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # text extracted from the PDF
    text_content: str

    # vector embedding for similarity search
    embedding: List[float] = Field(sa_column=Column(Vector(768)))

    # material this chunk belongs to
    material_id: int = Field(foreign_key="material.id")
    material: Material = Relationship(back_populates="chunks")
