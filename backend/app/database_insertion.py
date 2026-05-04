from sqlmodel import Session
from .models import DocumentChunk, Question  # adjust import to your project


def questions_to_models(questions_json: list[dict], topic_id: int) -> list[Question]:
    """
    Convert LLM JSON output → SQLModel objects
    """

    models = []

    difficulty_map = {
        "easy": 1,
        "medium": 2,
        "hard": 3,
    }

    for q in questions_json:
        try:
            difficulty_value = q.get("difficulty", 2)
            if isinstance(difficulty_value, str):
                difficulty_value = difficulty_map.get(difficulty_value.strip().lower(), 2)
            else:
                difficulty_value = int(difficulty_value)

            model = Question(
                topic_id=topic_id,
                question_type=q.get("question_type", "MCQ"),
                difficulty=difficulty_value,
                question_text=q.get("question", ""),
                options=q.get("options", []),
                correct_answer=q.get("answer", ""),
                explanation=q.get("explanation", ""),
                source=q.get("source", "")
            )
            models.append(model)
        except Exception as e:
            print(f"❌ BAD QUESTION FORMAT: {q}")
            print(f"ERROR: {e}")

    return models


def store_document_embeddings(chunk_results: list[dict], material_id: int, session):
    """
    Takes a pre-generated list of chunks and vectors, and saves them to the DB.
    """    
    chunks_to_insert = []
    for result in chunk_results:
        new_chunk = DocumentChunk(
            text_content=result["text_content"],
            embedding=result["embedding"],
            material_id=material_id
        )
        chunks_to_insert.append(new_chunk)
        
    session.add_all(chunks_to_insert)
    session.commit()
    print("✅ Knowledge stored in database!")

def save_questions(session: Session, questions: list[Question]):
    session.add_all(questions)
    session.commit()