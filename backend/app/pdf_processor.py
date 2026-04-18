import os
from typing import List
import requests
from .document_chunker import DocumentChunker

OLLAMA_URL = os.getenv("OLLAMA_URL")

def get_embedding(text: str, model: str = "nomic-embed-text") -> List[float]:
    """
    Sends a chunk of text to Ollama's embedding API 
    and returns a 768-dimension vector array.
    """
    url = f"{OLLAMA_URL}/api/embeddings"
    
    payload = {
        "model": model,
        "prompt": text,
        "options": {
            "num_ctx": 8192  # Expand memory to Nomic's true maximum
        },
        "truncate": True # 🌟 CRITICAL: Tells Ollama to truncate instead of crashing!
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Safely catch HTTP errors like 404 or 500
        
        # Ollama returns a JSON dictionary like: {"embedding": [0.12, -0.05, ...]}
        data = response.json()
        return data.get("embedding", [])
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to generate embedding: {e}")
        return []
    
def generate_chunks_and_embeddings(pdf_path: str) -> List[dict]:
    """
    Combines chunking and embedding generation for a PDF file.
    Returns a list of dicts with 'text_content' and 'embedding'.
    """
    chunker = DocumentChunker(chunk_size=200, overlap_size=40)
    chunks = chunker.chunk_file(pdf_path)

    results = []
    
    for i, chunk in enumerate(chunks):
        print(f"⚙️ Processing chunk {i+1}/{len(chunks)} for embedding")
        embedding = get_embedding(chunk)
        if embedding: 
            results.append({
                "text_content": chunk,
                "embedding": embedding
            })
        else:
            print(f"⚠️ Skipping chunk {i+1} because embedding failed.")
    
    return results