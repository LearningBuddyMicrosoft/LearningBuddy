import os
import json
import time
from typing import List, Dict, Any

from pydantic import BaseModel, ValidationError
from pydantic import model_validator
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_ollama import ChatOllama

from ai.hallucination import is_hallucinating


# model settings
MODEL_NAME = os.getenv("OLLAMA_QUIZ_MODEL", "qwen2.5:1.5b-instruct")
LLM_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.18"))
MODEL_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "2048"))
BASE_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")

# llm client
llm = ChatOllama(
    model=MODEL_NAME,
    temperature=LLM_TEMPERATURE,
    max_tokens=MODEL_MAX_TOKENS,
    base_url=BASE_URL,
)


# mcq model
class MCQ(BaseModel):
    question: str
    options: List[str]
    answer: str
    explanation: str
    difficulty: int
    source: str

    @model_validator(mode="after")
    def validate_mcq(self):
        if not self.question.strip():
            raise ValueError("Question text cannot be empty")

        if len(self.options) != 4:
            raise ValueError("Options must contain exactly 4 items")

        if len(set(self.options)) != 4:
            raise ValueError("Options must be unique")

        if self.answer.strip().lower() not in [opt.strip().lower() for opt in self.options]:
            raise ValueError("Answer must be one of the options")

        if not self.explanation.strip():
            raise ValueError("Explanation cannot be empty")

        if not isinstance(self.difficulty, int) or not (1 <= self.difficulty <= 3):
            raise ValueError("Difficulty must be an integer between 1 and 3")

        if not self.source.strip():
            raise ValueError("Source cannot be empty")

        return self


# quiz + feedback models
class QuizResponse(BaseModel):
    mcqs: List[MCQ]


class FeedbackItem(BaseModel):
    question: str
    your_answer: str
    correct_answer: str
    explanation: str
    source: str
    practice_tip: str = ""  # default empty so old data doesn't break


class FeedbackResponse(BaseModel):
    summary: str
    details: List[FeedbackItem]


quiz_parser = JsonOutputParser(pydantic_object=QuizResponse)
feedback_parser = JsonOutputParser(pydantic_object=FeedbackResponse)


# quiz prompt
quiz_batch_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert quiz writer for university-level statistics.
Use ONLY the provided context.

Rules:
- Return ONLY valid JSON. Do not include any introductory text, explanations, or formatting.
- JSON must contain "mcqs".
- Each MCQ must include:
  question, options (4 unique), answer (must match exactly), explanation, difficulty (1-3), source (the page number from the context, e.g., 'Page 5').
- Do NOT use A/B/C/D labels.
- The answer must be the full option string.
- Keep questions grounded in the context.
"""
        ),
        (
            "human",
            """
Context:
{context}

Generate {batch_size} grounded MCQs.
If the context cannot support all {batch_size}, return as many valid MCQs as possible.
"""
        ),
    ]
)


# feedback prompt
feedback_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
"""
Return feedback in JSON ONLY:

{{
  "summary": "string",
  "details": [
    {{
      "question": "string",
      "your_answer": "string",
      "correct_answer": "string",
      "explanation": "string",
      "source": "string",
      "practice_tip": "string"
    }}
  ]
}}

For the "summary" field, write a personal, encouraging message to the student. 
- Start with their score performance (e.g. "You scored 3/10")
- Then identify the specific topics they struggled with based on wrong answers
- For each struggled topic say "I noticed you struggled with [topic] - I recommend reviewing [source]"
- End with an encouraging note
- Example: "You scored 3/10. I noticed you struggled with mutually exclusive events - I recommend reviewing Probability - Page 47, and conditional probability - I recommend reviewing Probability - Page 20. Keep at it, these concepts will click with practice!"

For each incorrect answer, the "practice_tip" field must give a specific, actionable study suggestion referencing the topic and source.
For correct answers, set "practice_tip" to "".
"""
        ),
        ("human", """Questions and answers:
{qa_json}

For every item where the user's answer is WRONG, you MUST write a specific practice_tip.
For correct answers set practice_tip to "".
"""),
    ]
)


# llm helpers
def _invoke_llm(prompt) -> str:
    raw = llm.invoke(prompt.to_messages())
    return raw.content


def _extract_json(text: str) -> str:
    import re
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    # Remove LaTeX math delimiters before JSON parsing
    text = re.sub(r'\\\(', '(', text)
    text = re.sub(r'\\\)', ')', text)
    text = re.sub(r'\\\[', '[', text)
    text = re.sub(r'\\\]', ']', text)
    # Remove other common bad escapes the model produces
    text = re.sub(r'\\frac', 'frac', text)
    text = re.sub(r'\\binom', 'binom', text)
    text = re.sub(r'\\cdot', '*', text)
    text = re.sub(r'\\times', 'x', text)
    text = re.sub(r'\\lambda', 'lambda', text)
    text = re.sub(r'\\mu', 'mu', text)
    text = re.sub(r'\\sigma', 'sigma', text)

    if text.startswith("{"):
        return text
    idx = text.find("{")
    return text[idx:] if idx != -1 else text


def _normalize_question_text(text: str) -> str:
    return " ".join(text.strip().lower().split())


def _build_quiz_batch_prompt(context_text: str, batch_size: int):
    return quiz_batch_prompt.format_prompt(
        context=context_text,
        batch_size=batch_size,
    )


# batch parsing + validation
def _parse_and_validate_batch(raw_text: str, context_chunks: List[Dict[str, Any]], hallucination_threshold: float) -> List[MCQ]:
    try:
        json_text = _extract_json(raw_text)
        # Parse as plain dict first - no Pydantic validation yet
        import json as json_lib
        raw_dict = json_lib.loads(json_text)
        mcqs_raw = raw_dict.get("mcqs", [])
    except Exception as e:
        print(f"  ❌ Batch parse failed: {e}")
        return []

    valid_mcqs = []

    for mcq_data in mcqs_raw:
        try:
            # Strip "A. " / "A) " / "A: " style prefixes from options
            options = mcq_data.get("options", [])
            cleaned_options = []
            for opt in options:
                opt = str(opt)
                if len(opt) > 2 and opt[1] in '.):' and opt[2] == ' ':
                    cleaned_options.append(opt[3:])
                else:
                    cleaned_options.append(opt)
            mcq_data["options"] = cleaned_options

            # Resolve single letter answer like "A", "B", "C", "D" or "A." / "A)"
            answer = str(mcq_data.get("answer", "")).strip()
            if len(answer) == 1 and answer.upper() in "ABCD":
                idx = ord(answer.upper()) - ord('A')
                if 0 <= idx < len(cleaned_options):
                    mcq_data["answer"] = cleaned_options[idx]
            elif len(answer) == 2 and answer[0].upper() in "ABCD" and answer[1] in ').':
                idx = ord(answer[0].upper()) - ord('A')
                if 0 <= idx < len(cleaned_options):
                    mcq_data["answer"] = cleaned_options[idx]

            # Ensure difficulty is int
            if "difficulty" in mcq_data:
                mcq_data["difficulty"] = int(mcq_data["difficulty"])

            # Now validate with Pydantic
            validated = MCQ(**mcq_data)

            hallucinating = is_hallucinating(
                response=f"{validated.question} {' '.join(validated.options)}",
                context=context_chunks,
                threshold=hallucination_threshold,
            )

            if hallucinating:
                print(f"  ⚠️ Filtered hallucination: {validated.question[:60]}...")
                continue

            valid_mcqs.append(validated)

        except Exception as e:
            print(f"  ❌ Question validation error: {e}")
            continue

    return valid_mcqs


# main quiz generator
def generate_quiz_fast(
    context_chunks: List[Dict[str, Any]],
    num_questions: int = 10,
    max_attempts: int = 40,
    hallucination_threshold: float = 0.10,
) -> List[MCQ]:

    context_text = "\n".join([f"[Source: {c.get('filename', 'Document')}] {c['text']}" for c in context_chunks])
    batch_size = 5

    accumulated = []
    seen_questions = set()

    for attempt in range(1, max_attempts + 1):
        remaining = num_questions - len(accumulated)
        if remaining <= 0:
            break

        current_batch = min(batch_size, remaining)
        prompt = _build_quiz_batch_prompt(context_text, current_batch)

        try:
            raw_text = _invoke_llm(prompt)
            print(f"DEBUG: Raw LLM response for attempt {attempt}: {raw_text[:400]}...")

            batch_mcqs = _parse_and_validate_batch(raw_text, context_chunks, hallucination_threshold)

            for mcq in batch_mcqs:
                normalized = _normalize_question_text(mcq.question)
                if normalized in seen_questions:
                    continue

                seen_questions.add(normalized)
                accumulated.append(mcq)

                if len(accumulated) >= num_questions:
                    break

            print(
                f"Attempt {attempt}: collected {len(accumulated)} / {num_questions} "
                f"(batch returned {len(batch_mcqs)} valid items)."
            )

            time.sleep(0.4)

        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            time.sleep(0.8)

    # Just return whatever was collected
    return accumulated[:num_questions]


# feedback generator
def generate_feedback_fast(questions: List[Dict[str, Any]], answers: Dict[str, Any], material_name: str = "your material") -> FeedbackResponse:
    # Enrich questions with material name for context
    for q in questions:
        if "source" in q and not q["source"].startswith(material_name):
            q["source"] = f"{material_name} - {q['source']}"

    qa_json = json.dumps({"questions": questions, "answers": answers})
    prompt = feedback_prompt.format_prompt(qa_json=qa_json)
    raw_text = _invoke_llm(prompt)
    json_text = _extract_json(raw_text)
    feedback_dict = feedback_parser.parse(json_text)
    return FeedbackResponse(**feedback_dict)
