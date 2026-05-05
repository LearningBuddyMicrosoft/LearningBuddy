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


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "180"))


def call_llm(
    prompt: str,
    model: str,
    num_ctx: int = 1024,
    num_predict: int = 512,
    num_thread: int = 16,
    temperature: float = 0.0,
    timeout: int | None = None,
) -> str:
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_ctx": num_ctx,
                "num_predict": num_predict,
                "num_thread": num_thread,
            },
        },
        timeout=timeout or OLLAMA_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["response"].strip()



BASE_INSTRUCTIONS = textwrap.dedent("""
You are generating multiple-choice questions (MCQs) for a university-level quiz.

CRITICAL RULES — violating any of these will make the question INVALID:

1. Do NOT include the answer options in the question text itself.
   - WRONG: "Which is correct? A) The force is X, B) The force is Y, C) The force is Z, D) The force is W"
   - RIGHT: Ask the question cleanly, then put the 4 options ONLY in the "options" JSON field.

2. Do NOT use LaTeX, special symbols, formatting codes, or escape sequences (like \\(, \\), \\textbf, &, etc).
   - Use plain English and standard ASCII math notation only (like 2 m/s², not \\(2\\, m/s^2\\)).

3. Every question MUST be fully self-contained. The student has NOT seen the PDF.
   - If the question refers to a table → include the full table in the question text.
   - If the question refers to a formula → include the formula in the question text.
   - If variables are used → define them in the question text.

4. NEVER reference page numbers, figures, or the source document.
   - FORBIDDEN: "as shown on Page 7", "based on the example on Page 12", "from the PDF", "in the notes", etc.

5. All 4 options must be plausible and distinct. Do not use "All of the above" or "None of the above".

6. The answer must exactly match one of the options (character-for-character).

EXAMPLE of CORRECT JSON format:
{
  "question": "An object of mass 5 kg is pushed horizontally with a force of 20 N. If there is no friction, what is the acceleration of the object?",
  "options": [
    "2 m/s²",
    "4 m/s²",
    "10 m/s²",
    "20 m/s²"
  ],
  "answer": "4 m/s²",
  "explanation": "Using F = ma, we have a = F/m = 20 N / 5 kg = 4 m/s².",
  "difficulty": "medium",
  "source": "Physics - Newton's Laws"
}

Each question MUST have exactly these fields:
- "question": string — the question itself, WITHOUT answer options included.
- "options": array of exactly 4 distinct strings (the answer choices).
- "answer": string — must match one option exactly.
- "explanation": string — brief explanation of why the answer is correct.
- "difficulty": one of ["easy", "medium", "hard"].
- "source": short label from the provided context (filename, topic name, or page hint when available).

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
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[-1] if cleaned.count("```") >= 2 else cleaned
        cleaned = cleaned.lstrip("json").strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

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

            q_lower = q.lower()
            if any(phrase in q_lower for phrase in BAD_PHRASES):
                print(f"Rejected question with PDF/page reference: {q[:80]}")
                continue

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
    max_attempts: int = 30,
) -> List[MCQ]:
    if num_questions <= 0:
        return []

    collected: List[MCQ] = []
    attempts = 0
    CHUNKS_PER_BATCH = 5
    QUESTIONS_PER_BATCH = 5

    while attempts < max_attempts and len(collected) < num_questions:
        attempts += 1

        start = ((attempts - 1) * CHUNKS_PER_BATCH) % max(len(context_chunks), 1)
        batch_chunks = context_chunks[start:start + CHUNKS_PER_BATCH]
        if not batch_chunks:
            batch_chunks = context_chunks[:CHUNKS_PER_BATCH]

        remaining = num_questions - len(collected)
        ask_for = min(QUESTIONS_PER_BATCH, remaining)

        prompt = build_prompt(batch_chunks, ask_for)

        try:
            raw = call_llm(prompt, model=os.getenv("OLLAMA_MODEL_MCQ", OLLAMA_MODEL))
            print(f"Raw LLM response (attempt {attempts}): {raw[:500]}...")
        except Exception as e:
            print(f"LLM call failed (attempt {attempts}): {e}")
            continue

        batch = parse_mcqs(raw)
        if not batch:
            print(f"LLM returned no valid MCQs (attempt {attempts})")
            continue

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
    # Count correct answers
    total = len(questions_payload)
    correct_count = sum(
        1 for q in questions_payload
        if answers_payload.get(str(q["id"]), "").strip().lower()
        == q["correct_answer"].strip().lower()
    )

    # Build detail lines for the LLM
    detail_lines = []
    wrong_lines = []
    correct_nums = []
    sources = set()

    for q in questions_payload:
        qid = str(q["id"])
        qnum = q["question_number"]
        your = answers_payload.get(qid, "No answer")
        correct = q["correct_answer"]
        src = q.get("source", "")
        if src:
            sources.add(src)

        is_correct = your.strip().lower() == correct.strip().lower()
        if is_correct:
            correct_nums.append(str(qnum))
        else:
            wrong_lines.append(f"Q{qnum}: chose '{your}', correct '{correct}'")

        detail_lines.append(
            f"Q{qnum}={'OK' if is_correct else 'WRONG'} src={src}"
        )

    sources_str = ", ".join(sources) if sources else material_name
    correct_str = ", ".join(correct_nums) if correct_nums else "none"
    wrong_str = "; ".join(wrong_lines) if wrong_lines else "none"

    # Build structured feedback prompt
    prompt = (
        f"You are a tutor. Analyze this quiz result and respond in JSON format ONLY.\n\n"
        f"Quiz: {material_name}\n"
        f"Score: {correct_count}/{total}\n"
        f"Correct: Q{correct_str}\n"
        f"Wrong: {wrong_str}\n\n"
        f"Provide feedback in this exact JSON format (no other text):\n"
        f'{{\n'
        f'  "summary": "One line summary with score percentage and overall performance.",\n'
        f'  "strengths": ["List 1-2 topics or areas where the student did well"],\n'
        f'  "weaknesses": ["List 1-2 areas where the student struggled and why"],\n'
        f'  "tips": ["One actionable tip for improvement"]\n'
        f'}}\n'
    )

    feedback_models = [
        os.getenv("OLLAMA_MODEL_FEEDBACK", OLLAMA_MODEL),
        os.getenv("OLLAMA_MODEL_MCQ", "qwen2.5:1.5b-instruct"),
    ]

    import re
    def extract_json_body(text: str) -> str | None:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return text[start:end + 1]

    model_feedback = {}
    for model in feedback_models:
        try:
            raw = call_llm(
                prompt,
                model=model,
                num_ctx=1024,
                num_predict=500,
                num_thread=4,
                temperature=0.0,
                timeout=60,
            )
        except Exception:
            continue

        cleaned = raw.strip()
        json_text = extract_json_body(cleaned)
        if not json_text:
            continue

        try:
            result = json.loads(json_text)
            if "summary" not in result:
                continue
            model_feedback = result
            break
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
        except Exception:
            continue

    # Build summary with strengths/weaknesses from model, but keep score deterministic
    percent = round((correct_count / total) * 100) if total > 0 else 0
    strengths = model_feedback.get("strengths", [])
    weaknesses = model_feedback.get("weaknesses", [])
    model_summary = model_feedback.get("summary", "")

    if model_summary:
        summary_text = f"You scored {correct_count}/{total} ({percent}%). {model_summary}"
    else:
        summary_text = f"You scored {correct_count}/{total} ({percent}%). Review the results below for the key strengths and areas to improve."

    # Format with better HTML structure for visual appeal
    full_summary = f"<div style='line-height: 1.8; font-size: 1.1em;'>"
    full_summary += f"<p><b>{summary_text}</b></p>"
    
    if strengths:
        full_summary += "<p style='margin-top: 1.5rem;'><b>✨ Strengths:</b></p><ul style='margin-left: 1.5rem;'>"
        for s in strengths:
            full_summary += f"<li style='margin-bottom: 0.5rem;'>{s}</li>"
        full_summary += "</ul>"
    
    if weaknesses:
        full_summary += "<p style='margin-top: 1.5rem;'><b>🎯 Areas to Improve:</b></p><ul style='margin-left: 1.5rem;'>"
        for w in weaknesses:
            full_summary += f"<li style='margin-bottom: 0.5rem;'>{w}</li>"
        full_summary += "</ul>"
    
    full_summary += "</div>"
    
    # Build details array with ALL questions, sources, and answers
    details = []
    for q in questions_payload:
        qid = str(q["id"])
        your_answer = answers_payload.get(qid, "No answer")
        correct_answer = q["correct_answer"]
        is_correct = your_answer.strip().lower() == correct_answer.strip().lower()
        
        details.append({
            "question": q.get("question", ""),
            "your_answer": your_answer,
            "correct_answer": correct_answer,
            "explanation": q.get("explanation", ""),
            "practice_tip": "" if is_correct else model_feedback.get("tips", [""])[0] if model_feedback.get("tips") else "Review this topic.",
            "source": q.get("source", ""),
        })
    
    return {
        "summary": full_summary,
        "details": details,
    }


def fallback_feedback(
    questions_payload: List[Dict[str, Any]],
    answers_payload: Dict[str, str],
) -> Dict[str, Any]:
    total = len(questions_payload)
    correct = sum(
        1 for q in questions_payload
        if answers_payload.get(str(q["id"]), "").strip().lower()
        == q["correct_answer"].strip().lower()
    )
    pct = (correct / total * 100) if total > 0 else 0

    if pct == 100:
        summary = f"You scored {correct}/{total} ({pct}%) — perfect score! Outstanding work."
    elif pct >= 80:
        summary = f"You scored {correct}/{total} ({pct}%) — excellent work! Just a few areas to polish."
    elif pct >= 60:
        summary = f"You scored {correct}/{total} ({pct}%) — good effort. Review the questions you missed and try again."
    elif pct >= 40:
        summary = f"You scored {correct}/{total} ({pct}%) — keep going. Focus on the explanations for incorrect answers."
    else:
        summary = f"You scored {correct}/{total} ({pct}%) — review the material carefully and try again."

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