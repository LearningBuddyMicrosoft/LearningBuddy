import fitz
from .quiz_generator import generate_question_from_chunk
import os
from typing import List
import hashlib
from ai.hallucination import calculate_hallucination_score


# Simple cache for processed PDFs
_pdf_cache = {}


def _get_pdf_hash(pdf_path: str) -> str:
    """Get hash of PDF file for caching."""
    with open(pdf_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def smart_chunk_by_headers(pdf_path: str) -> list[str]:
    """Optimized PDF chunking using PyMuPDF's built-in text extraction."""
    cache_key = _get_pdf_hash(pdf_path)

    if cache_key in _pdf_cache:
        return _pdf_cache[cache_key]

    document = fitz.open(pdf_path)
    chunks = []

    # Use PyMuPDF's more efficient text extraction
    for page in document:
        # Get text with structure preservation but simpler processing
        text = page.get_text("text")
        if not text.strip():
            continue

        # Split by paragraphs (double newlines) more efficiently
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

        for para in paragraphs:
            if len(para) > 50:  # Filter out very short fragments
                chunks.append(para)

    # Cache the result
    _pdf_cache[cache_key] = chunks
    return chunks


def generate_quiz_from_pdf(pdf_path: str, num_questions: int = 10) -> list[dict]:
    """Generate quiz questions from PDF with optimized chunking."""
    chunks = smart_chunk_by_headers(pdf_path)

    if not chunks:
        return []

    # Filter chunks to ensure quality content
    filtered_chunks = [chunk for chunk in chunks if len(chunk.split()) > 20]  # At least 20 words

    if len(filtered_chunks) < num_questions:
        # If we don't have enough quality chunks, use what we have
        selected_chunks = filtered_chunks
    else:
        # Select chunks more intelligently - prefer middle sections and avoid very short chunks
        step = max(1, len(filtered_chunks) // num_questions)
        selected_chunks = filtered_chunks[::step][:num_questions]

    # If some generated questions are filtered out for hallucination,
    # continue evaluating additional chunks until we have enough questions.
    candidate_chunks = selected_chunks[:]
    if len(selected_chunks) < len(filtered_chunks):
        candidate_chunks.extend([chunk for chunk in filtered_chunks if chunk not in selected_chunks])

    questions = []
    hallucination_threshold = 0.5
    for chunk in candidate_chunks:
        if len(questions) >= num_questions:
            break

        try:
            # Limit chunk size to avoid LLM token limits and improve speed
            if len(chunk) > 2000:  # ~500-600 tokens
                chunk = chunk[:2000] + "..."

            q = generate_question_from_chunk(chunk)

            if q.get("q") and len(q.get("options", [])) == 4 and q.get("answer"):
                response = q["q"] + " " + " ".join(q["options"])
                context = [{"text": chunk}]
                score = calculate_hallucination_score(response, context)
                q["hallucination_score"] = score
                q["hallucination_context"] = chunk

                if score > hallucination_threshold:
                    print(f"⚠️ Skipped hallucinating question (score: {score:.2f}): {q['q'][:100]}...")
                    continue

                questions.append(q)
            else:
                print(f"⚠️ Skipped invalid question from chunk: {chunk[:100]}...")

        except Exception as e:
            print(f"⚠️ Error generating question from chunk: {str(e)}")
            continue

    return questions