import fitz  # PyMuPDF
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def process_slides_perfectly(file_path, course_name, topic_name):
    print(f"Reading {file_path}...")
    documents = []
    
    try:
        doc = fitz.open(file_path)
        
        # Step 1: Create one document per slide directly
        for page_num, page in enumerate(doc):
            text = page.get_text().strip()
            
            if text: # Only process if the slide actually has text
                # Build the rich metadata
                metadata = {
                    "course": course_name,
                    "topic": topic_name,
                    "page_number": page_num + 1,
                    "source": file_path
                }
                
                # Create the LangChain Document immediately
                documents.append(Document(page_content=text, metadata=metadata))
                
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return []

    # Step 2: The Safety Slicer
    # Most slides won't hit 3000 chars, so they remain whole.
    safety_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""] 
    )
    
    # This will only split slides that are exceptionally dense
    final_chunks = safety_splitter.split_documents(documents)
    return final_chunks

# --- TEST IT NOW ---
if __name__ == "__main__":
    pdf_path = r"C:\Users\hp\OneDrive\Desktop\Maynooth work\Microsoft Mentored Learning Buddy\ChunkerByPage\lecture.pdf"
    
    chunks = process_slides_perfectly(pdf_path, "CS335", "Agile Software Development")
    
    print(f"\nSuccess! Generated {len(chunks)} chunks.")
    if chunks:
        print("\n--- Sample of the first chunk ---")
        print("Metadata:", chunks[0].metadata)
        print("Content:", chunks[0].page_content[:200] + "...")