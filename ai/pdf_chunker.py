import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter

def process_lecture_pdf(file_path):
    print(f"Processing: {file_path}")
    
    # 1. Rip the text out of the PDF
    try:
        doc = fitz.open(file_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
    except Exception as e:
        return f"Error opening PDF: {e}"

    # 2. Quick & dirty cleanup (Slides often have terrible line breaks)
    clean_text = " ".join(full_text.split())

    # 3. The Slicer (LangChain)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = text_splitter.split_text(clean_text)
    return chunks

# TESTING
if __name__ == "__main__":
    sample_pdf = r"C:\Users\hp\OneDrive\Desktop\Maynooth work\Microsoft Mentored Learning Buddy\pdfReaderLocal\Lecture4.pdf" 
    
    my_chunks = process_lecture_pdf(sample_pdf)
    
    print(f"Total chunks generated: {len(my_chunks)}\n")
    print("--- CHUNK 1 ---")
    print(my_chunks[0] if len(my_chunks) > 0 else "No text found.")
    print("\n--- CHUNK 2 ---")
    print(my_chunks[1] if len(my_chunks) > 1 else "No text found.")