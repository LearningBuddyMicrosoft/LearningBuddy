import fitz  # This is the PyMuPDF library

def extract_text_from_pdf(pdf_path):
    print(f"Opening {pdf_path}...")
    
    # 1. Open the PDF file
    document = fitz.open(pdf_path)
    full_text = ""

    # 2. Loop through every page in the document
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        
        # 3. Extract the text from that specific page
        page_text = page.get_text()
        
        # 4. Add it to our giant wall of text, with a gap between pages
        full_text += page_text + "\n\n--- Next Page ---\n\n"

    return full_text

my_file = r"C:\Users\hp\OneDrive\Desktop\Maynooth work\Microsoft Mentored Learning Buddy\pdfReaderLocal\Lecture4.pdf" 
extracted_notes = extract_text_from_pdf(my_file)

# Print just the first 1000 characters for now
print("Here is what the computer sees:\n")
print(extracted_notes[:1000])

