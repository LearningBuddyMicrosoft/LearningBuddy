from pydantic import BaseModel
from typing import List
from sqlmodel import SQLModel


class UserCreate(BaseModel):
    # payload for registering or logging in a user
    username: str
    password: str


class StartAttempt(BaseModel):
    # payload for starting a quiz attempt
    quiz_id: int


class FinishAttempt(BaseModel):
    # payload for finishing an attempt and requesting feedback
    attempt_id: int


class AnswerSubmission(BaseModel):
    # single answer inside a batch submission
    attempt_id: int
    question_id: int
    selected_option: str


class BatchSubmission(BaseModel):
    # list of answers submitted at once
    attempt_id: int
    answers: List[AnswerSubmission]


class QuizSummary(BaseModel):
    # lightweight quiz info for topic details
    id: int
    name: str
    highscore: int


class MaterialRead(BaseModel):
    # material info returned to frontend
    id: int
    name: str
    file_path: str
    processing_status: str


class TopicDetailedRead(BaseModel):
    # full topic info including materials and quizzes
    id: int
    name: str
    materials: List[MaterialRead] = []
    quizzes: List[QuizSummary] = []


class TopicRead(BaseModel):
    # simple topic info for subject list
    id: int
    name: str


class SubjectRead(BaseModel):
    # subject info including topics
    id: int
    name: str
    topics: List[TopicRead] = []


class DashboardRead(BaseModel):
    # dashboard info for logged-in user
    id: int
    username: str
    subjects: List[SubjectRead] = []


class SubjectCreate(BaseModel):
    # payload for creating a subject
    name: str


class TopicCreate(BaseModel):
    # payload for creating a topic
    name: str
    subject_id: int


class QuizCreate(BaseModel):
    # payload for generating a quiz
    name: str
    topic_ids: list[int]
    open_ended: bool
    length: int
    difficulty_level: int


class QuestionRead(SQLModel):
    # question returned when starting a quiz
    id: int
    question_text: str
    options: List[str] = []
    correct_answer: str
    explanation: str


class QuizRead(SQLModel):
    # full quiz returned when user starts a quiz
    id: int
    name: str
    difficulty_level: int
    open_ended: bool
    length: int
    highscore: int
    questions: List[QuestionRead] = []


class AttemptDetail(BaseModel):
    # attempt info for history tables
    id: int
    date: str
    score: int


class QuizAttemptsGroup(BaseModel):
    # grouped attempts for a quiz
    quiz_id: int
    quiz_name: str
    total_questions: int
    attempts: List[AttemptDetail]


class TopicMastery(BaseModel):
    # mastery stats for a topic
    topic_id: int
    topic_name: str
    total_attempted: int
    total_correct: int
    mastery_percentage: float
