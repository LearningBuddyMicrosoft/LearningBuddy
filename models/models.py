"""Data models for the AI Study Assistant."""

from pydantic import BaseModel
from typing import List


class MCQModel(BaseModel):
    """Multiple Choice Question model."""
    question: str
    options: List[str]
    answer: str
    evidence: str
    source: str


class ResponseModel(BaseModel):
    """AI response model with quiz data."""
    topic: str
    summary: str
    mcqs: List[MCQModel]
    source: List[str]
