from typing import List, Dict, Any
from sqlmodel import Session, select

from .database_insertion import questions_to_models, save_questions
from .models import DocumentChunk, Topic, Material
from .pdf_processor import get_embedding
from ai.llm import generate_quiz_fast


def generate_and_store_quiz(session, topic_id: int, material_id: int, num_questions: int = 10):
    # starts the RAG quiz generation process for a material
    print(f"🚀 STARTING RAG QUIZ GENERATION FOR MATERIAL #{material_id}")

    topic = session.get(Topic, topic_id)
    if not topic:
        print(f"❌ Topic ID {topic_id} not found!")
        return

    topic_name = topic.name
    print(f"🎯 Search Target: '{topic_name}'")

    # retrieves the most relevant text chunks from the vector DB
    print("📚 Searching vector database for relevant chunks...")
    context_chunks = retrieve_relevant_context(
        topic_name=topic_name,
        material_id=material_id,
        session=session,
        limit=30,
    )

    if not context_chunks:
        print("❌ No relevant context found in the database. Aborting.")
        return

    # generates MCQs using the LLM
    print(f"🧠 Generating exactly {num_questions} questions in batched LLM calls...")

    try:
        mcqs = generate_quiz_fast(
            context_chunks=context_chunks,
            num_questions=num_questions,
            max_attempts=20,
        )
    except Exception as e:
        print(f"❌ LLM error while generating quiz: {e}")
        return

    if not mcqs:
        print("❌ No questions generated.")
        return

    # gets the material name for source labels and fallback values
    material = session.get(Material, material_id)
    material_filename = material.name.replace(".pdf", "") if material else "Document"

    # converts MCQ objects into dicts ready for DB insertion
    final_questions = []
    for mcq in mcqs:
        source_label = mcq.source.strip()
        lower_source = source_label.lower()
        fallback_source = f"{material_filename} ({topic_name})"

        # Keep LLM source when it is informative and not just the topic name repeated.
        if not source_label or lower_source in {
            topic_name.lower(),
            material_filename.lower(),
            f"{material_filename} - {topic_name}".lower(),
            f"{topic_name} - {topic_name}".lower(),
        }:
            source_label = fallback_source
        elif material_filename.lower() not in lower_source:
            source_label = f"{material_filename} - {source_label}"

        final_questions.append({
            "question": mcq.question,
            "options": mcq.options,
            "answer": mcq.answer,
            "explanation": mcq.explanation,
            "difficulty": mcq.difficulty,
            "source": source_label,
        })

    print(f"\n💾 SAVING {len(final_questions)} QUESTIONS TO DB...")

    # converts dicts into SQLModel objects and saves them
    db_objects = questions_to_models(final_questions, topic_id)
    save_questions(session, db_objects)

    print("✅ Success! RAG pipeline complete.")


def retrieve_relevant_context(
    topic_name: str,
    material_id: int,
    session: Session,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    # retrieves the most relevant chunks for a topic using vector similarity
    print(f"🔍 Retrieving chunks for topic '{topic_name}'")

    query_text = f"{topic_name}: key concepts, definitions, and core ideas"
    query_vector = get_embedding(query_text)

    if not query_vector:
        return []

    # selects chunks ordered by similarity to the query vector
    statement = (
        select(DocumentChunk)
        .where(DocumentChunk.material_id == material_id)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(limit)
    )

    results = session.exec(statement).all()
    if not results:
        print("⚠️ No chunks found")
        return []

    # filters out irrelevant boilerplate text
    filtered = []
    for chunk in results:
        text = chunk.text_content.lower()
        if any(bad in text for bad in ["hello", "welcome", "academy", "career", "students", "founder"]):
            continue
        filtered.append(chunk)

    # if filtering removed everything, fall back to all results
    if not filtered:
        filtered = results

    # attaches the filename for source tracking, including page hints when available
    material = session.get(Material, material_id)
    base_filename = material.name.replace(".pdf", "") if material else "Document"

    context = []
    for c in filtered:
        text = c.text_content or ""
        page_label = ""
        if isinstance(text, str):
            import re
            match = re.match(r"Page\s*(\d+):", text)
            if match:
                page_label = f"Page {match.group(1)}"

        filename = base_filename
        if page_label:
            filename = f"{base_filename} - {page_label}"

        context.append({"id": c.id, "text": text, "filename": filename})

    return context