import json
import os
import re
import requests
from collections import defaultdict

from sqlmodel import Session, select

from .database_insertion import questions_to_models, save_questions
from .models import DocumentChunk, Topic
from .pdf_processor import get_embedding

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
    if not context_text or not context_text.strip():
        print("⚠️ Empty context provided.")
        return []

    prompt = f"""
You are an exam question generator.

You must output ONLY a valid JSON array.

No explanations.
No text.
No markdown.
No comments.

TASK:
Create {num_questions} multiple-choice questions using ONLY the facts in the context.

IMPORTANT:
- ALL questions must have difficulty = {difficulty}
- Do NOT mix difficulty levels
- If context is insufficient, return fewer questions

OUTPUT FORMAT (STRICT):
[
  {{
    "question_type": "MCQ",
    "difficulty": {difficulty},
    "question_text": "string",
    "options": ["A", "B", "C", "D"],
    "correct_answer": "string"
  }}
]

RULES:
- correct_answer must match one option exactly
- always return a JSON array
- no extra keys allowed

CONTEXT:
{context_text}
"""

    print("🧠 PROMPT (truncated):\n", prompt[:800])

    for attempt in range(3):
        print(f"🔁 Attempt {attempt + 1}/3 (difficulty {difficulty})")

        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": "llama3.1:8b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 2048,
                        "temperature": 0,
                        "top_p": 1
                    }
                },
                timeout=120
            )

            response.raise_for_status()

        except Exception as e:
            print(f"❌ Request failed: {e}")
            continue

        raw_text = response.json().get("response", "")
        print("🤖 RAW OUTPUT:\n", raw_text[:800])

        parsed_questions = parse_llm_json(raw_text)

        def is_valid(q):
            return (
                isinstance(q, dict)
                and q.get("question_text")
                and isinstance(q.get("options"), list)
                and len(q.get("options", [])) >= 2
                and q.get("correct_answer")
                and q.get("difficulty") == difficulty
            )

        parsed_questions = [q for q in parsed_questions if is_valid(q)]

        print(f"✅ VALID QUESTIONS: {len(parsed_questions)}")

        # ✅ STRICT success condition
        if len(parsed_questions) == num_questions:
            return parsed_questions

        # ⚠️ fallback if decent output
        if len(parsed_questions) >= 5:
            print("⚠️ Partial success, returning fallback set")
            return parsed_questions

    print(f"❌ Failed to generate difficulty {difficulty} questions")
    return []


def retrieve_relevant_context(topic_name: str, material_id: int, session: Session, limit: int = 4) -> str:
    print(f"🔍 Searching database for chunks related to: '{topic_name}'...")

    augmented_query = f"{topic_name}: important educational concepts, core definitions, and main ideas."
    query_vector = get_embedding(augmented_query)

    if not query_vector:
        return ""

    statement = select(DocumentChunk).where(
        DocumentChunk.material_id == material_id
    ).order_by(
        DocumentChunk.embedding.cosine_distance(query_vector)
    ).limit(limit)

    results = session.exec(statement).all()

    if not results:
        print("⚠️ No chunks found")
        return ""

    filtered_results = []

    for chunk in results:
        text = chunk.text_content.lower()

        if any(bad in text for bad in [
            "hello", "founder", "students", "academy",
            "courses", "career", "welcome"
        ]):
            continue

        filtered_results.append(chunk)

    if not filtered_results:
        print("⚠️ All chunks filtered out, using original results")
        filtered_results = results

    combined_context = "\n".join(
        chunk.text_content[:300]
        for chunk in filtered_results
    )

    return combined_context


def parse_llm_json(raw_text: str) -> list:
    clean_text = re.sub(r"```json\n?|\n?```", "", raw_text).strip()

    start_idx = clean_text.find('[')
    alt_start = clean_text.find('{')

    if start_idx == -1 and alt_start == -1:
        print("❌ No JSON brackets found in output.")
        return []

    if start_idx != -1 and (alt_start == -1 or start_idx < alt_start):
        clean_text = clean_text[start_idx:]
    else:
        clean_text = clean_text[alt_start:]

    try:
        data = json.loads(clean_text)

        if isinstance(data, dict):
            if "questions" in data and isinstance(data["questions"], list):
                return data["questions"]
            elif "Questions" in data and isinstance(data["Questions"], list):
                return data["Questions"]
            else:
                return [data]

        if isinstance(data, list):
            return data

        return []

    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing Error: {e}")
        print(f"RAW TEXT WAS:\n{raw_text}")
        return []