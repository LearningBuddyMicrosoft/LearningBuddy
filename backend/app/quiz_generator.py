import json
import os
import re
import requests

from sqlmodel import Session, select

from .database_insertion import questions_to_models, save_questions
from .models import DocumentChunk, Topic
from .pdf_processor import get_embedding

OLLAMA_URL = os.getenv("OLLAMA_URL")

def generate_and_store_quiz(session, topic_id: int, material_id: int, num_questions: int = 20):
    print(f"🚀 STARTING RAG QUIZ GENERATION FOR MATERIAL #{material_id}")

    # 1. Fetch the Topic Name from the database to use as our search query
    topic = session.get(Topic, topic_id)
    if not topic:
        print(f"❌ Topic ID {topic_id} not found!")
        return
        
    topic_name = topic.name 
    print(f"🎯 Search Target: '{topic_name}'")

    # 2. RETRIEVAL: Search the Vector Database for the best paragraphs
    print("📚 Searching vector database for relevant chunks...")
    context = retrieve_relevant_context(
        topic_name=topic_name, 
        material_id=material_id, 
        session=session,
        limit=8  # Adjust this depending on how much text you want the LLM to read
    )

    if not context.strip():
        print("❌ No relevant context found in the database. Aborting.")
        return

    # 3. GENERATION: Give the LLM the "Open Book Test"
    print("🧠 Handing retrieved context to Llama3...")
    llm_questions = generate_questions_from_context(
        context_text=context,
        num_questions=num_questions
    )

    print(json.dumps(llm_questions, indent=2))
    print(f"🤖 LLM returned {len(llm_questions)} questions.")

    if not llm_questions:
        print("❌ LLM failed to generate valid JSON questions.")
        return

    # Safety check: Ensure we don't exceed the requested amount
    final_questions = llm_questions[:num_questions]

    # 4. STORAGE: Save to the relational database
    db_objects = questions_to_models(final_questions, topic_id)
    print(f"💾 SAVING {len(db_objects)} QUESTIONS TO DB...")
    
    save_questions(session, db_objects)
    
    print(f"✅ Success! RAG pipeline complete.")

def generate_questions_from_context(context_text: str, num_questions: int) -> list[dict]:
    """
    Uses Ollama to generate structured quiz questions from retrieved context.
    """

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

If you output anything other than JSON, it is invalid.

TASK:
Create {num_questions} multiple-choice questions using ONLY the facts in the context.

If the context is limited, create fewer questions rather than guessing.

OUTPUT FORMAT (STRICT):
[
  {{
    "question_type": "MCQ",
    "difficulty": 5,
    "question_text": "string",
    "options": ["A", "B", "C", "D"],
    "correct_answer": "string"
  }}
]

RULES:
- difficulty is an integer 1–5
- correct_answer must match one option exactly
- always return a JSON array
- no extra keys allowed

CONTEXT (facts only):
{context_text}
"""

    # 🔍 DEBUG: confirm prompt is correct
    print("🧠 PROMPT BEING SENT:\n", prompt[:1500])

    for attempt in range(3):
        print(f"🔁 Attempt {attempt + 1}/3")

        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": "llama3.1",  # (recommended upgrade)
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
        print("🤖 RAW OUTPUT:\n", raw_text[:1000])

        parsed_questions = parse_llm_json(raw_text)

        # strict validation
        def is_valid(q):
            return (
                isinstance(q, dict)
                and q.get("question_text")
                and isinstance(q.get("options"), list)
                and len(q.get("options", [])) >= 2
                and q.get("correct_answer")
            )

        parsed_questions = [q for q in parsed_questions if is_valid(q)]

        print(f"✅ VALID QUESTIONS: {len(parsed_questions)}")

        # 🎯 SUCCESS CONDITION
        if len(parsed_questions) >= num_questions:
            return parsed_questions

        # fallback: accept partial if decent
        if len(parsed_questions) >= 5:
            print("⚠️ Partial success, returning fallback set")
            return parsed_questions

    print("❌ All attempts failed")
    return []
    

def retrieve_relevant_context(topic_name: str, material_id: int, session: Session, limit: int = 4) -> str:
    print(f"🔍 Searching database for chunks related to: '{topic_name}'...")
    
    # 1. Turn the search topic into a vector
    augmented_query = f"{topic_name}: important educational concepts, core definitions, and main ideas."
    
    # We embed the combined string!
    query_vector = get_embedding(augmented_query)

    if not query_vector:
        return ""

    # 2. The Vector Database Query (Cosine Distance)
    # We filter by material_id so it only searches the specific PDF the user wants!
    statement = select(DocumentChunk).where(
        DocumentChunk.material_id == material_id
    ).order_by(
        DocumentChunk.embedding.cosine_distance(query_vector)
    ).limit(limit)

    # ✅ ALWAYS assign results
    results = session.exec(statement).all()

    if not results:
        print("⚠️ No chunks found")
        return ""

    # ✅ FILTER CLEANLY
    filtered_results = []

    for chunk in results:
        text = chunk.text_content.lower()

        if any(bad in text for bad in [
            "hello", "founder", "students", "academy",
            "courses", "career", "welcome"
        ]):
            continue

        filtered_results.append(chunk)

    # fallback if everything got filtered out
    if not filtered_results:
        print("⚠️ All chunks filtered out, using original results")
        filtered_results = results

    # ✅ BUILD CONTEXT
    combined_context = "\n".join(
        chunk.text_content[:300]
        for chunk in filtered_results
    )

    return combined_context

def parse_llm_json(raw_text: str) -> list:
    """
    Cleans up Llama 3's dirty output, strips markdown, 
    and handles unwanted root dictionary wrappers.
    """
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
        
        # --- THE NEW UNWRAPPING LOGIC ---
        if isinstance(data, dict):
            # If Llama wrapped it in {"questions": [...]}, pull the array out!
            if "questions" in data and isinstance(data["questions"], list):
                return data["questions"]
            elif "Questions" in data and isinstance(data["Questions"], list):
                return data["Questions"]
            else:
                # Otherwise, it genuinely generated a single question object.
                return [data]
                
        if isinstance(data, list):
            return data
            
        return []
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing Error: {e}")
        print(f"RAW TEXT WAS:\n{raw_text}") 
        return []