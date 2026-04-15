import time

import os

from .document_chunker import DocumentChunker

from .quiz_generator import generate_question_from_chunk



def generate_quiz_from_pdf(pdf_path: str, num_questions: int = 10) -> list[dict]:

    """

    Main function called by app.py to generate quiz questions from a PDF.

    Uses DocumentChunker for extraction and quiz_generator for question creation.

    """

    overall_start = time.time()

   

    # Initialize chunker and extract chunks from the PDF

    chunker = DocumentChunker(overlap_size=50, chunk_size=200)

   

    try:

        chunks = chunker.chunk_file(pdf_path)

    except Exception as e:

        print(f"Error chunking file: {e}")

        return []

   

    if not chunks:

        print("No chunks extracted from PDF")

        return []



    # Select evenly distributed chunks for question generation

    step = max(1, len(chunks) // num_questions) if chunks else 1

    selected = chunks[::step][:num_questions]



    questions = []

    print(f"\n✅ Starting question generation for {len(selected)} chunks...")

   

    for i, chunk in enumerate(selected):

        chunk_start = time.time()

        print(f"Generating question {i+1}/{len(selected)}... (Chunk length: {len(chunk)} chars)")

       

        try:

            q = generate_question_from_chunk(chunk)



            # Validate question structure

            if q.get("q") and len(q.get("options", [])) == 4 and q.get("answer"):

                questions.append(q)

                print(f"✓ Question {i+1} created successfully")

            else:

                print(f"✗ Question {i+1} skipped - invalid structure")



        except Exception as e:

            print(f"Error generating question {i+1}: {e}")

            continue

           

        print(f"Question {i+1} finished in {time.time() - chunk_start:.2f} seconds.\n")



    print(f"\n🎉 Total process took {time.time() - overall_start:.2f} seconds.")

    print(f"Successfully generated {len(questions)} out of {len(selected)} questions.\n")

    return questions