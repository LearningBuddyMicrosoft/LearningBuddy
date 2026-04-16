from sqlmodel import Session
from .models import Question  # adjust import to your project


def questions_to_models(questions_json: list[dict], topic_id: int) -> list[Question]:
    """
    Convert LLM JSON output → SQLModel objects
    """

    models = []

    for q in questions_json:
        try:
            model = Question(
                topic_id=topic_id,
                question_type=q["question_type"],
                difficulty=int(q["difficulty"]),
                question_text=q["question_text"],
                options=q.get("options", []),
                correct_answer=q["correct_answer"]
            )
            models.append(model)
        except Exception as e:
            print(f"Skipping invalid question: {e}")

    return models


def save_questions(session: Session, questions: list[Question]):
    session.add_all(questions)
    session.commit()