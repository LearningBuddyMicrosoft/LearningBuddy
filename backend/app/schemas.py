from pydantic import BaseModel
from typing import List

from sqlmodel import SQLModel

class UserCreate(BaseModel):
    username: str
    password: str

class StartAttempt(BaseModel):
    quiz_id: int

class FinishAttempt(BaseModel):
    attempt_id: int

class AnswerSubmission(BaseModel):
    attempt_id: int
    question_id: int
    selected_option: str

class BatchSubmission(BaseModel):
    attempt_id: int
    answers : List[AnswerSubmission]

class QuizSummary(BaseModel):
    id: int
    name: str
    highscore: int
    
class MaterialRead(BaseModel):
    id: int
    name: str
    file_path: str

class TopicDetailedRead(BaseModel):
    id: int
    name: str
    materials: List[MaterialRead] = []
    quizzes: List[QuizSummary] = []

class TopicRead(BaseModel):
    id: int
    name: str

class SubjectRead(BaseModel):
    id: int
    name: str
    topics: List[TopicRead] = []

class DashboardRead(BaseModel):
    id: int
    username: str
    subjects: List[SubjectRead] = []

class SubjectCreate(BaseModel):
    name: str

class TopicCreate(BaseModel):
    name: str
    subject_id: int

class QuizCreate(BaseModel):
    name: str
    topic_ids: list[int]
    open_ended: bool
    length: int
    difficulty_level: int # 1-scale

class QuestionRead(SQLModel):
    id: int
    question_text: str
    options: List[str] = []
    correct_answer: str

class QuizRead(SQLModel):
    id: int
    name: str
    difficulty_level: int
    open_ended: bool
    length: int
    highscore: int
    questions: List[QuestionRead] = []