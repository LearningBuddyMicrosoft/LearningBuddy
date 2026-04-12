import re
from ai.ollama_client import generate

FEW_SHOT = """Here are two example questions:

Q: What does RAM stand for?
A) Read Access Memory
B) Random Access Memory
C) Rapid Access Module
D) Run Active Memory
Answer: B
Explanation: RAM stands for Random Access Memory, which is temporary storage the CPU uses to run programs.

Q: Which protocol guarantees reliable delivery?
A) UDP
B) IP
C) TCP
D) DNS
Answer: C
Explanation: TCP (Transmission Control Protocol) uses acknowledgements and retransmission to guarantee delivery."""


def generate_question_from_chunk(chunk: str) -> dict:
    prompt = f"""<|user|>
You are a quiz generator for university students. Using ONLY the study text below, create one multiple choice question with exactly 4 options (A, B, C, D). One must be correct. Include a short explanation of the correct answer.

{FEW_SHOT}

Now generate one question from this text:
{chunk[:1000]}

Respond ONLY in plain text using EXACTLY this format. No extra words before or after:

Q: [question]
A) [option]
B) [option]
C) [option]
D) [option]
Answer: [A, B, C, or D]
Explanation: [one sentence]
<|end|>
<|assistant|>"""

    raw = generate(prompt)
    return parse_question(raw, chunk)


def parse_question(raw: str, source_chunk: str) -> dict:
    lines = [l.strip() for l in raw.strip().splitlines() if l.strip()]

    question = ""
    options = []
    answer_letter = ""
    explanation = ""

    for line in lines:
        if line.startswith("Q:"):
            question = line[2:].strip()
        elif re.match(r"^[A-D][\)\.]", line):
            # Remove all leading prefixes like "A) " or "A. " to handle LLM duplication
            option_text = re.sub(r"^[A-D][\)\.]\s*", "", line).strip()
            option_text = re.sub(r"^[A-D][\)\.]\s*", "", option_text).strip()
            options.append(option_text)
        elif line.startswith("Answer:"):
            answer_letter = line.replace("Answer:", "").strip().upper()
        elif line.startswith("Explanation:"):
            explanation = line.replace("Explanation:", "").strip()

    letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}
    answer_text = options[letter_map[answer_letter]] if answer_letter in letter_map and options else ""

    return {
        "q": question,
        "options": options,
        "answer": answer_text,
        "explanation": explanation,
        "source": source_chunk
    }