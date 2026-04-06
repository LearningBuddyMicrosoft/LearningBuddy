import fitz
from .quiz_generator import generate_question_from_chunk


def smart_chunk_by_headers(pdf_path: str) -> list[str]:
    document = fitz.open(pdf_path)
    chunks = []
    current_title = "Introduction"
    current_text = ""

    for page in document:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    if span["size"] > 14:
                        if current_text:
                            chunks.append(f"--- SECTION: {current_title} ---\n{current_text}\n")
                        current_title = text
                        current_text = ""
                    else:
                        current_text += text + " "

    if current_text:
        chunks.append(f"--- SECTION: {current_title} ---\n{current_text}\n")

    return chunks


def generate_quiz_from_pdf(pdf_path: str, num_questions: int = 10) -> list[dict]:
    chunks = smart_chunk_by_headers(pdf_path)

    # Pick evenly spaced chunks so questions cover the whole PDF
    step = max(1, len(chunks) // num_questions)
    selected = chunks[::step][:num_questions]

    questions = []
    for chunk in selected:
        try:
            q = generate_question_from_chunk(chunk)

            if q.get("q") and len(q.get("options", [])) == 4 and q.get("answer"):
                questions.append(q)
            else:
                print("⚠️ Skipped invalid question:", q)

        except Exception as e:
            print("❌ Error generating question:", e)
            continue

    return questions