import json
import os
import re
import requests

from sqlmodel import Session, select

from .database_insertion import questions_to_models, save_questions
from .models import DocumentChunk, Topic
from .pdf_processor import get_embedding

OLLAMA_URL = os.getenv("OLLAMA_URL")

def generate_and_store_quiz(session, topic_id: int, material_id: int, num_questions: int = 10):
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
        limit=5  # Adjust this depending on how much text you want the LLM to read
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
    Uses Ollama to generate structured quiz questions from the RETRIEVED database context.
    """
    if not context_text.strip():
        print("⚠️ No context provided. Skipping generation.")
        return []

    # Notice the emphasis on "Based ONLY on the provided context"
    prompt = f"""You are a strict, automated JSON-generating API. You do not converse. You do not greet the user. You ONLY output data.

Generate exactly {num_questions} multiple-choice questions based ONLY on the CONTEXT below.

CRITICAL RULES:
1. ABSOLUTELY NO conversational text, preambles, or explanations.
2. The output MUST be a JSON array starting exactly with '[' and ending with ']'.
3. Do NOT wrap the output in a root dictionary. 
4. Every item MUST have these exact 5 keys: "question_type", "difficulty", "question_text", "options", "correct_answer".
5. Evaluate the "difficulty" as an integer from 1 to 10.

EXAMPLE OUTPUT (Copy this exact shape):
[
  {{
    "question_type": "MCQ",
    "difficulty": 6,
    "question_text": "What is the main focus of incremental development?",
    "options": ["Adding new features", "Fixing bugs", "Writing documentation", "Hardware design"],
    "correct_answer": "Adding new features"
  }}
]

CONTEXT:
\"\"\"{context_text}\"\"\"
"""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate", 
        json={
            "model": "phi3.5",
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 2048  # <--- ADD THIS: Let it write a much longer response!
            }
        }
    )

    raw_text = response.json().get("response", "")
    
    # Use the new sanitizer instead of trusting json.loads directly!
    parsed_questions = parse_llm_json(raw_text)
    
    return parsed_questions
    

def retrieve_relevant_context(topic_name: str, material_id: int, session: Session, limit: int = 4) -> str:
    """
    1. Embeds the user's topic.
    2. Searches Postgres for the closest matching chunks.
    3. Combines them into one giant string for the LLM to read.
    """
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
    
    results = session.exec(statement).all()
    
    # 3. Mash all the retrieved chunks together separated by a line
    combined_context = "\n\n--- NEXT CHUNK ---\n\n".join([chunk.text_content for chunk in results])
    
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