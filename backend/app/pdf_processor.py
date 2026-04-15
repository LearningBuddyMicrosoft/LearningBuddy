from .document_chunker import DocumentChunker
from .quiz_generator import generate_multiple_questions_from_chunk
import time

def generate_quiz_from_pdf(pdf_path: str, num_questions: int = 10) -> list[dict]:
    """
    Generate quiz questions from a PDF file.
    Now generates MULTIPLE questions per chunk for better coverage.
    """
    overall_start = time.time()
    
    # Initialize the chunker
    chunker = DocumentChunker(chunk_size=800, overlap_size=100)
    chunks = chunker.chunk_file(pdf_path)
    
    if not chunks:
        print("No text could be extracted from the PDF")
        return []
    
    questions = []
    
    # Generate multiple questions per chunk
    questions_per_chunk = max(1, num_questions // len(chunks))
    
    print(f"\nGenerating {num_questions} questions from {len(chunks)} chunks...")
    print(f"   (~{questions_per_chunk} questions per chunk)\n")
    
    for i, chunk in enumerate(chunks):
        chunk_start = time.time()
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        
        try:
            # Generate multiple questions from this chunk
            chunk_questions = generate_multiple_questions_from_chunk(chunk, num_questions=questions_per_chunk)
            questions.extend(chunk_questions)
            print(f"Generated {len(chunk_questions)} questions")
            
        except Exception as e:
            print(f"Error: {e}")
            continue
        
        print(f"Chunk {i+1} finished in {time.time() - chunk_start:.2f} seconds.\n")
        
        # Stop if we have enough questions
        if len(questions) >= num_questions:
            questions = questions[:num_questions]
            break
    
    total_time = time.time() - overall_start
    print(f"Total process took {total_time:.2f} seconds.")
    print(f"Successfully generated {len(questions)}/{num_questions} questions\n")
    
    return questions