from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List
from .model_lock import model_lock

def call_llm(prompt):
    with model_lock:
        return llm.invoke(prompt)


# Model used for MCQ generation
class ResponseModel(BaseModel):
    topic: str
    summary: str
    mcqs: List[dict] = Field(default_factory=list)
    source: List[str] = Field(default_factory=list)


# Model for individual feedback items
class FeedbackItem(BaseModel):
    question: str
    your_answer: str
    correct_answer: str
    explanation: str


# Model for full quiz feedback
class FeedbackResponse(BaseModel):
    summary: str
    details: List[FeedbackItem]


# Main LLM client
llm = ChatOllama(
    model="phi3.5:latest",
    temperature=0.35,
    max_tokens=4096,
    base_url="http://host.docker.internal:11434",
)


# Parser for MCQ generation
parser = JsonOutputParser(pydantic_object=ResponseModel)


# Prompt used for generating MCQs from context
final_answer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You generate multiple-choice questions from the provided context.

Requirements:
- Use only the information in the context.
- Produce the exact number of questions requested.
- Each question must include:
  - 4 options
  - a correct answer (A/B/C/D)
  - a difficulty rating (1–10)
  - an evidence sentence taken from the context
  - a source reference (chunk ID or page number)
- Do not invent facts.
- Output only valid JSON.
            """,
        ),
        (
            "human",
            """
Context:
{context}

Generate {num_questions} questions centered at difficulty {difficulty}.
Output only the JSON.
            """,
        ),
    ]
)


# Parser for feedback generation
feedback_parser = JsonOutputParser(pydantic_object=FeedbackResponse)


# Prompt used for generating structured quiz feedback
feedback_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You generate clear feedback for a completed quiz.

Return JSON with:
- a short summary
- a list of items containing:
  - question
  - your_answer
  - correct_answer
  - explanation

Keep explanations short and focused.
Output only JSON.
            """,
        ),
        (
            "human",
            """
Here are the quiz results:

Score: {score} out of {total}

Responses:
{responses}

Generate structured feedback.
            """,
        ),
    ]
)


def generate_feedback(score: int, total: int, responses: List[dict]):
    """
    Generates structured feedback for a completed quiz.
    Each response dict must contain:
    - question
    - your_answer
    - correct_answer
    """
    formatted = "\n".join(
        [
            f"Question: {r['question']}\nYour answer: {r['your_answer']}\nCorrect answer: {r['correct_answer']}"
            for r in responses
        ]
    )

    chain = feedback_prompt | llm | feedback_parser
    return chain.invoke(
        {
            "score": score,
            "total": total,
            "responses": formatted,
        }
    )


def generate_single_feedback(question: str, your_answer: str, correct_answer: str):
    """
    Generates feedback for a single answered question.
    Useful for single-question mode.
    """
    return generate_feedback(
        score=1 if your_answer == correct_answer else 0,
        total=1,
        responses=[
            {
                "question": question,
                "your_answer": your_answer,
                "correct_answer": correct_answer,
            }
        ],
    )
