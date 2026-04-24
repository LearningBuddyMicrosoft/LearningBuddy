import json
import os
import re
import requests
from collections import defaultdict

from sqlmodel import Session, select

from .database_insertion import questions_to_models, save_questions
from .models import DocumentChunk, Topic
from .pdf_processor import get_embedding
from ai.llm import llm, final_answer_prompt

OLLAMA_URL = os.getenv("OLLAMA_URL")


def generate_and_store_quiz(session, topic_id: int, material_id: int, num_questions: int = 50):
    print(f"🚀 STARTING RAG QUIZ GENERATION FOR MATERIAL #{material_id}")

    topic = session.get(Topic, topic_id)
    if not topic:
        print(f"❌ Topic ID {topic_id} not found!")
        return

    topic_name = topic.name
    print(f"🎯 Search Target: '{topic_name}'")

    print("📚 Searching vector database for relevant chunks...")
    context = retrieve_relevant_context(
        topic_name=topic_name,
        material_id=material_id,
        session=session,
        limit=8
    )

    if not context.strip():
        print("❌ No relevant context found in the database. Aborting.")
        return

    print("🧠 Generating questions per difficulty level...")

    all_questions = []

    # ✅ Generate 10 questions per difficulty level (1–3)
    for difficulty in range(1, 4):
        print(f"\n🎯 Generating difficulty {difficulty} questions...")

        questions = generate_questions_from_context(
            context_text=context,
            num_questions=20,
            difficulty=difficulty
        )

        all_questions.extend(questions)

    print(f"\n🤖 Total generated questions: {len(all_questions)}")

    if not all_questions:
        print("❌ No valid questions generated.")
        return

    # ✅ Safety rebalance (ensures max 10 per difficulty)
    bucket = defaultdict(list)

    for q in all_questions:
        bucket[q["difficulty"]].append(q)

    final_questions = []

    for d in range(1, 4):
        selected = bucket[d][:10]
        print(f"✅ Difficulty {d}: {len(selected)} questions")
        final_questions.extend(selected)

    print(f"\n💾 SAVING {len(final_questions)} QUESTIONS TO DB...")

    db_objects = questions_to_models(final_questions, topic_id)
    save_questions(session, db_objects)

    print("✅ Success! RAG pipeline complete.")


def generate_questions_from_context(context_text: str, num_questions: int, difficulty: int) -> list[dict]:
    if not context_text.strip():
        return []

    for attempt in range(3):
        print(f"🔁 Attempt {attempt + 1}/3 for difficulty {difficulty}")

        try:
            prompt = final_answer_prompt.format_prompt(
                context=context_text,
                num_questions=num_questions,
                difficulty=difficulty
            )

            generation = llm.generate([prompt.to_messages()])
            raw_text = generation.generations[0][0].text if generation.generations else ""

        except Exception as e:
            print(f"❌ LLM error: {e}")
            continue

        if not raw_text:
            continue

        raw_text = raw_text.strip()

        # Parse JSON using your ResponseModel
        try:
            data = json.loads(raw_text)
            mcqs = data.get("mcqs", [])
        except Exception:
            print("❌ JSON parse error")
            continue

        # Validate MCQs
        def is_valid(q):
            return (
                isinstance(q, dict)
                and q.get("question")
                and isinstance(q.get("options"), list)
                and len(q.get("options", [])) == 4
                and q.get("answer") in ["A", "B", "C", "D"]
                and q.get("evidence")
                and q.get("source")
            )

        valid = [q for q in mcqs if is_valid(q)]
        print(f"🧪 Valid MCQs before hallucination filtering: {len(valid)}")

        # Hallucination filtering
        grounded = []
        for q in valid:
            score_info = calculate_hallucination_score(
                response=q["evidence"],
                context=[{"text": context_text}]
            )
            if score_info["score"] <= 0.5:
                grounded.append(q)

        print(f"🛡️ Grounded MCQs after hallucination filtering: {len(grounded)}")

        if len(grounded) == num_questions:
            return grounded

        if len(grounded) >= 5:
            return grounded

    print(f"❌ Failed to generate difficulty {difficulty} questions")
    return []



def retrieve_relevant_context(topic_name: str, material_id: int, session: Session, limit: int = 8) -> str:
    print(f"🔍 Retrieving chunks for topic '{topic_name}'")

    query_text = f"{topic_name}: key concepts, definitions, and core ideas"
    query_vector = get_embedding(query_text)

    if not query_vector:
        return ""

    statement = (
        select(DocumentChunk)
        .where(DocumentChunk.material_id == material_id)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(limit)
    )

    results = session.exec(statement).all()
    if not results:
        print("⚠️ No chunks found")
        return ""

    filtered = []
    for chunk in results:
        text = chunk.text_content.lower()
        if any(bad in text for bad in ["hello", "welcome", "academy", "career", "students", "founder"]):
            continue
        filtered.append(chunk)

    if not filtered:
        filtered = results

    combined = []
    for chunk in filtered:
        combined.append(f"[Chunk {chunk.id}]\n{chunk.text_content}")

    return "\n\n--- NEXT CHUNK ---\n\n".join(combined)


