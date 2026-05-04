import os
import json
import textwrap
import requests
from dataclasses import dataclass
from typing import List, Dict, Any

from ai.hallucination import is_hallucinating


@dataclass
class MCQ:
    question: str
    options: List[str]
    answer: str
    explanation: str
    difficulty: str
    source: str


# Ollama connection settings — override via environment variables if needed
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))


def call_llm(prompt: str) -> str:
    """Send a prompt to Ollama and return the raw text response."""
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_ctx": 4096,
            },
        },
        timeout=OLLAMA_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["response"]


BASE_INSTRUCTIONS = textwrap.dedent("""
You are generating multiple-choice questions (MCQs) for a university-level quiz.

STRICT RULES — violating any of these will make the question invalid:

1. ONLY generate multiple-choice questions. Never open-ended, never yes/no, never true/false.
2. Every question MUST be fully self-contained. The student has NOT seen the PDF.
   - If the question refers to a table → include the full table in the question text.
   - If the question refers to a pmf → include the full pmf in the question text.
   - If the question refers to a formula → include the formula in the question text.
   - If the question refers to variables X and Y → define X and Y in the question text.
   - If the question refers to a distribution → state the distribution fully in the question text.
3. NEVER reference page numbers, figures, or the source document in any way.
   - FORBIDDEN: "as shown on Page 7", "based on the example on Page 12", "from the PDF", "in the notes", "as defined earlier", "given in the lecture".
   - If a question depends on the PDF to be answerable, rewrite it so it is fully standalone.
4. NEVER write questions like "What is shown on Page X?" or "Based on the example on Page Y?".
   Rewrite them as standalone probability/statistics/mathematics questions with all context included.
5. All 4 options must be plausible and distinct. Do not use "All of the above" or "None of the above".
6. The answer must exactly match one of the options (character-for-character).
7. Use clear, precise mathematical notation where needed.

Each question MUST be a JSON object with:
- "question": string — fully self-contained question text including any needed tables, formulas, or definitions.
- "options": array of exactly 4 distinct strings.
- "answer": string — must match one option exactly.
- "explanation": string — brief explanation of why the answer is correct.
- "difficulty": one of ["easy", "medium", "hard"].
- "source": short label from the provided context (e.g. filename or topic name, NOT a page number).

Respond with ONLY a valid JSON array. No prose, no markdown, no code fences, no extra text.
""").strip()


def build_prompt(context_chunks: List[Dict[str, Any]], num_questions: int) -> str:
    parts = []
    for chunk in context_chunks:
        filename = chunk.get("filename", "Document")
        text = chunk.get("text", "")
        parts.append(f"[Source: {filename}]\n{text}")

    context_block = "\n\n".join(parts)

    return (
        f"{BASE_INSTRUCTIONS}\n\n"
        f"Generate exactly {num_questions} questions.\n\n"
        f"Use only the following material:\n\n{context_block}"
    )


def parse_mcqs(raw: str) -> List[MCQ]:
    """Extract a list of MCQ objects from raw LLM output."""
    # Strip markdown code fences if present
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[-1] if cleaned.count("```") >= 2 else cleaned
        cleaned = cleaned.lstrip("json").strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

    # Find the JSON array boundaries
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1:
        return []

    try:
        data = json.loads(cleaned[start:end + 1])
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    # Phrases that indicate a question is not self-contained
    BAD_PHRASES = [
        "page ", "page\xa0", "the pdf", "the example on", "as shown",
        "as defined", "in the notes", "in the lecture", "from the lecture",
        "based on the", "refer to", "see figure", "figure ", "the table above",
        "the following table", "as above", "given above", "shown above",
    ]

    mcqs = []
    for item in data:
        try:
            q = item.get("question", "").strip()
            opts = item.get("options", [])
            ans = item.get("answer", "").strip()
            expl = item.get("explanation", "").strip()
            diff = item.get("difficulty", "medium").strip().lower()
            src = item.get("source", "Document").strip()

            if not q or not isinstance(opts, list) or len(opts) != 4:
                continue
            opts = [str(o) for o in opts]
            if ans not in opts:
                continue
            if diff not in ("easy", "medium", "hard"):
                diff = "medium"

            # Reject questions that reference the PDF or page numbers
            q_lower = q.lower()
            if any(phrase in q_lower for phrase in BAD_PHRASES):
                print(f"Rejected question with PDF/page reference: {q[:80]}")
                continue

            # Reject yes/no and true/false questions
            opts_lower = [o.strip().lower() for o in opts]
            if set(opts_lower) <= {"yes", "no"} or set(opts_lower) <= {"true", "false"}:
                print(f"Rejected yes/no or true/false question: {q[:80]}")
                continue

            mcqs.append(MCQ(q, opts, ans, expl, diff, src))
        except Exception:
            continue

    return mcqs


def generate_quiz_fast(
    context_chunks: List[Dict[str, Any]],
    num_questions: int,
    max_attempts: int = 10,
    batch_size: int = 10,
) -> List[MCQ]:
    """Generate MCQs from context chunks, filtering out hallucinated questions."""
    if num_questions <= 0:
        return []

    collected: List[MCQ] = []
    attempts = 0

    while attempts < max_attempts and len(collected) < num_questions:
        attempts += 1
        remaining = num_questions - len(collected)
        request_count = min(batch_size, remaining)
        prompt = build_prompt(context_chunks, request_count)

        try:
            raw = call_llm(prompt)
        except Exception as e:
            print(f"LLM call failed (attempt {attempts}): {e}")
            continue

        batch = parse_mcqs(raw)
        if not batch:
            print(f"LLM returned no valid MCQs (attempt {attempts})")
            continue

        print(f"LLM returned {len(batch)} parsed MCQs on attempt {attempts}")
        for mcq in batch:
            if len(collected) >= num_questions:
                break
            combined_text = mcq.question + " " + mcq.explanation
            if is_hallucinating(combined_text, context_chunks):
                print("Rejected hallucinated question.")
                continue
            collected.append(mcq)

    return collected[:num_questions]


def generate_feedback_fast(
    questions_payload: List[Dict[str, Any]],
    answers_payload: Dict[str, str],
    material_name: str = "your material",
) -> Dict[str, Any]:
    """
    Ask the LLM to summarise the student's quiz attempt.
    Returns {"summary": str, "details": [...]}.
    Falls back to a static summary if the LLM call fails.
    """
    # Build a compact Q&A block to keep the prompt within the context window
    qa_block = []
    for q in questions_payload:
        qid = str(q["id"])
        qa_block.append({
            "question_number": q["question_number"],
            "question": q["question"],
            "your_answer": answers_payload.get(qid, "No answer"),
            "correct_answer": q["correct_answer"],
            "explanation": q["explanation"],
            "source": q.get("source", ""),
        })

    qa_json = json.dumps(qa_block, indent=2)

    prompt = textwrap.dedent(f"""
    You are an encouraging university tutor generating detailed feedback for a student's quiz attempt on "{material_name}".

    Return a JSON object with exactly two keys:
    - "summary": a rich HTML string (using <b>, <ul>, <li>, <br> tags) structured as follows:
        * One sentence overall performance comment
        * A "✅ <b>Strengths:</b>" section listing questions the student got right and why
        * A "❌ <b>Areas to Improve:</b>" section listing each wrong question, what the student chose, what was correct, and a brief explanation
        * A "📚 <b>Study Recommendation:</b>" section with 2-3 specific actionable tips referencing the material topics
        * End with a short motivational sentence
    - "details": a list with one object per question, each containing:
        - "question"
        - "your_answer"
        - "correct_answer"
        - "explanation"
        - "practice_tip" (one specific actionable sentence of advice, or empty string if correct)
        - "source"

    Rules:
    - Be specific — mention question numbers, the student's actual wrong answers, and the correct answers.
    - Reference topic areas from the material name when giving study tips.
    - Be encouraging but honest.
    - Only use the information provided below.
    - Do not invent new facts.
    - Do not use the characters '<' or '>' in any returned string values.
    - Return ONLY valid JSON. No markdown. No code fences. No extra text.

    Student attempt:
    {qa_json}
    """).strip()

    try:
        raw = call_llm(prompt)
    except Exception as e:
        print(f"LLM feedback call failed: {e}")
        return fallback_feedback(questions_payload, answers_payload)

    # Strip markdown fences if the model wrapped its output
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        cleaned = parts[1].lstrip("json").strip() if len(parts) >= 3 else cleaned

    try:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("No JSON object found in response")
        result = json.loads(cleaned[start:end + 1])
        # Validate expected keys exist
        if "summary" not in result or "details" not in result:
            raise ValueError("Missing required keys in LLM response")
        return result
    except Exception as e:
        print(f"LLM feedback parse failed: {e}\nRaw response: {raw[:500]}")
        return fallback_feedback(questions_payload, answers_payload)
        return result
    except Exception as e:
        print(f"LLM feedback parse failed: {e}\nRaw response: {raw[:500]}")
        return fallback_feedback(questions_payload, answers_payload)


def fallback_feedback(
    questions_payload: List[Dict[str, Any]],
    answers_payload: Dict[str, str],
) -> Dict[str, Any]:
    """Static feedback used when the LLM is unavailable or returns bad output."""
    total = len(questions_payload)
    correct = sum(
        1 for q in questions_payload
        if answers_payload.get(str(q["id"]), "").strip().lower()
        == q["correct_answer"].strip().lower()
    )
    pct = (correct / total * 100) if total > 0 else 0

    if pct == 100:
        summary = f"You scored {correct}/{total} — perfect score! Outstanding work."
    elif pct >= 80:
        summary = f"You scored {correct}/{total} — excellent work! Just a few areas to polish."
    elif pct >= 60:
        summary = f"You scored {correct}/{total} — good effort. Review the questions you missed and try again."
    elif pct >= 40:
        summary = f"You scored {correct}/{total} — keep going. Focus on the explanations for incorrect answers."
    else:
        summary = f"You scored {correct}/{total} — review the material carefully and try again."

    details = []
    for q in questions_payload:
        qid = str(q["id"])
        details.append({
            "question": q["question"],
            "your_answer": answers_payload.get(qid, "No answer"),
            "correct_answer": q["correct_answer"],
            "explanation": q["explanation"],
            "practice_tip": "",
            "source": q.get("source", ""),
        })

    return {"summary": summary, "details": details}