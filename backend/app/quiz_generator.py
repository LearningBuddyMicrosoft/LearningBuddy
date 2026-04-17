import json
import requests

OLLAMA_URL = "http://host.docker.internal:11434"


def generate_multiple_questions_from_chunk(chunk: str, num_questions: int = 3) -> list[dict]:
    """
    Uses Ollama to generate structured quiz questions from a text chunk.
    Returns list of dicts ready for DB insertion.
    """

    prompt = f"""
You are a quiz generator.

Generate exactly {num_questions} multiple-choice questions from the text below.

RULES:
- Output ONLY valid JSON
- No explanations
- No markdown
- Must be a JSON list
- Each item must follow this schema:

{{
  "question_type": "MCQ",
  "difficulty": 1-10,
  "question_text": "...",
  "options": ["A", "B", "C", "D"],
  "correct_answer": "one of the options"
}}

TEXT:
\"\"\"{chunk}\"\"\"
"""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate", 
        json={
            "model": "phi3.5",
            "prompt": prompt,
            "stream": False
        }
    )

    raw_text = response.json()["response"]

    try:
        data = json.loads(raw_text)
        if isinstance(data, dict):
            data = [data]
        return data
    except Exception as e:
        print("Failed to parse LLM output:", raw_text)
        return []