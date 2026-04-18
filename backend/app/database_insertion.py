from sqlmodel import Session
from .models import DocumentChunk, Question  # adjust import to your project


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