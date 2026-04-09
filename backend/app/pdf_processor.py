import fitz  # PyMuPDF
import time
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


from .quiz_generator import generate_question_from_chunk

def chunk_by_slide(file_path: str) -> list[str]:
    print(f"\nReading {file_path}...")
    start_time = time.time()
    documents = []
    
    try:
        doc = fitz.open(file_path)
        for page_num, page in enumerate(doc):
            text = page.get_text().strip()
            
            if text: 
                metadata = {
                    "page_number": page_num + 1,
                    "source": file_path
                }
                documents.append(Document(page_content=text, metadata=metadata))
        
        doc.close()
                
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return []

    print(f"PDF read and extracted in {time.time() - start_time:.2f} seconds.")
    
    split_start = time.time()
    safety_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""] 
    )
    
    final_chunks = safety_splitter.split_documents(documents)
    print(f"Text split by LangChain in {time.time() - split_start:.2f} seconds.")
    
    string_chunks = []
    for chunk in final_chunks:
        slide_num = chunk.metadata.get("page_number", "Unknown")
        formatted_text = f"--- SLIDE {slide_num} ---\n{chunk.page_content}\n"
        string_chunks.append(formatted_text)
        
    return string_chunks


def generate_quiz_from_pdf(pdf_path: str, num_questions: int = 10) -> list[dict]:
    overall_start = time.time()
    chunks = chunk_by_slide(pdf_path)

    step = max(1, len(chunks) // num_questions) if chunks else 1
    selected = chunks[::step][:num_questions]

    questions = []
    print(f"\nStarting question generation for {len(selected)} chunks...")
    
    for i, chunk in enumerate(selected):
        chunk_start = time.time()
        print(f"Generating question {i+1}/{len(selected)}... (Chunk length: {len(chunk)} chars)")
        
        try:
            q = generate_question_from_chunk(chunk)

            if q.get("q") and len(q.get("options", [])) == 4 and q.get("answer"):
                questions.append(q)
            else:
                print("Skipped invalid question")

        except Exception as e:
            print("Error generating question:", e)
            continue
            
        print(f"Question {i+1} finished in {time.time() - chunk_start:.2f} seconds.")

    print(f"\nTotal process took {time.time() - overall_start:.2f} seconds.")
    return questions