from pydantic import BaseModel
from typing import List

class UserCreate(BaseModel):
    username: str

class StartAttempt(BaseModel):
    user_id: int
    quiz_mode: str = "single"  # default to single mode
    topic_ids: List[int] = []  # Optional list of topic IDs for batch mode

class FinishAttempt(BaseModel):
    attempt_id: int

class AnswerSubmission(BaseModel):
    user_id: int
    attempt_id: int
    question_id: int
    selected_option: str

class BatchSubmission(BaseModel):
    user_id: int
    attempt_id: int
    answers : List[AnswerSubmission]

class QuizAttemptSummary(BaseModel):
    attempt_id: int
    score: int
    date: str
    
class MaterialRead(BaseModel):
    id: int
    name: str
    file_path: str

class TopicDetailedRead(BaseModel):
    id: int
    name: str
    materials: List[MaterialRead] = []
    quiz_attempts: List[QuizAttemptSummary] = []

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