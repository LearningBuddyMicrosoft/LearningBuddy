import fitz  # PyMuPDF

def smart_chunk_by_headers(pdf_path):
    print(f"Processing: {pdf_path}...\n")
    document = fitz.open(pdf_path)
    
    chunks = []
    current_section_title = "Introduction"
    current_section_text = ""

    # Loop through every page
    for page in document:
        # get_text("dict") gives us the exact font size of every word!
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        font_size = span["size"]
                        
                        if not text:
                            continue

                        # If the font is bigger than a standard paragraph (e.g., > 14pt)
                        # We assume it's a new Header!
                        if font_size > 14:
                            # Save the previous section
                            if current_section_text:
                                chunks.append(f"--- SECTION: {current_section_title} ---\n{current_section_text}\n")
                            
                            # Start a new section
                            current_section_title = text
                            current_section_text = ""
                        else:
                            # It's regular text, just add it to the current section
                            current_section_text += text + " "

    # Don't forget to save the very last section!
    if current_section_text:
        chunks.append(f"--- SECTION: {current_section_title} ---\n{current_section_text}\n")

    return chunks

# --- How to run it ---
my_messy_pdf = "lecture_notes.pdf" # Put a real lecture PDF here
semantic_chunks = smart_chunk_by_headers(my_messy_pdf)

# Print out the structured chunks!
for chunk in semantic_chunks:
    print(chunk)
