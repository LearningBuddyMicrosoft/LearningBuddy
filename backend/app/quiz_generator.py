import re
from ai.ollama_client import generate
from ai.hallucination import calculate_hallucination_score

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
    """Generate a SINGLE question from a chunk"""
    prompt = f"""<|user|>
You are a quiz generator for university students. Using ONLY the study text below, create one multiple choice question with exactly 4 options (A, B, C, D). One must be correct. Include a short explanation.

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


def generate_multiple_questions_from_chunk(chunk: str, num_questions: int = 3) -> list[dict]:
    """Generate MULTIPLE questions from a single chunk"""
    questions = []
    
    # Split chunk into sub-chunks if it's long enough
    sentences = chunk.split(". ")
    
    for i in range(num_questions):
        # Create a different sub-prompt for each question to get variety
        start_idx = (i * len(sentences)) // num_questions
        end_idx = ((i + 1) * len(sentences)) // num_questions
        sub_chunk = ". ".join(sentences[start_idx:end_idx])
        
        if not sub_chunk.strip():
            continue
            
        prompt = f"""<|user|>
You are a quiz generator for university students. Using ONLY the study text below, create one multiple choice question with exactly 4 options (A, B, C, D). One must be correct. Include a short explanation.

IMPORTANT: This is question {i+1} of {num_questions}. Generate a DIFFERENT question than previous ones.

{FEW_SHOT}

Now generate one question from this text:
{sub_chunk[:500]}

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

        try:
            raw = generate(prompt)
            q = parse_question(raw, chunk)
            if q.get("q") and len(q.get("options", [])) == 4 and q.get("answer"):
                questions.append(q)
        except Exception as e:
            print(f"Error generating question {i+1}: {e}")
            continue
    
    return questions


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
            options.append(line[3:].strip())
        elif line.startswith("Answer:"):
            answer_letter = line.replace("Answer:", "").strip().upper()
        elif line.startswith("Explanation:"):
            explanation = line.replace("Explanation:", "").strip()

    letter_map = {"A": 0, "B": 1, "C": 2, "D": 3}
    answer_text = options[letter_map[answer_letter]] if answer_letter in letter_map and options else ""

    # 🔥 ADD THIS PART
    response_text = f"Question: {question}\nAnswer: {answer_text}\nExplanation: {explanation}"
    
    try:
        score = calculate_hallucination_score(
            response=response_text,
            context=[{"text": source_chunk}]
        )
    except Exception as e:
        print(f"Error calculating hallucination score: {e}")
        score = None

    return {
        "q": question,
        "options": options,
        "answer": answer_text,
        "explanation": explanation,
        "source": source_chunk[:200],
        "hallucination_score": score  
    }