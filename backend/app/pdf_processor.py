import time
from document_chunker import DocumentChunker
from quiz_generator import generate_multiple_questions_from_chunk
from database_insertion import questions_to_models, save_questions


def generate_and_store_quiz(pdf_path: str, session, topic_id: int, num_questions: int = 10):

    print("🚀 STARTING QUIZ GENERATION")
    print("PDF PATH:", pdf_path)
    print("TOPIC ID:", topic_id)

    chunker = DocumentChunker(chunk_size=800, overlap_size=100)
    chunks = chunker.chunk_file(pdf_path)

    print("📄 CHUNKS CREATED:", len(chunks))

    if not chunks:
        print("❌ No chunks extracted")
        return

    all_questions = []

    questions_per_chunk = max(1, num_questions // len(chunks))

    for i, chunk in enumerate(chunks):
        print(f"⚙️ Processing chunk {i+1}/{len(chunks)}")

        llm_questions = generate_multiple_questions_from_chunk(
            chunk,
            num_questions=questions_per_chunk
        )

        print("🤖 LLM OUTPUT:", llm_questions)

        all_questions.extend(llm_questions)

        if len(all_questions) >= num_questions:
            break

    print("✅ TOTAL QUESTIONS GENERATED:", len(all_questions))

    all_questions = all_questions[:num_questions]

    db_objects = questions_to_models(all_questions, topic_id)

    print("💾 SAVING TO DB:", len(db_objects))

    save_questions(session, db_objects)

    print(f"✅ Inserted {len(db_objects)} questions into DB")