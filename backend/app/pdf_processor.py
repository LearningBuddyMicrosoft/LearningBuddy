import os
from typing import List
import requests
from .document_chunker import DocumentChunker

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_TIMEOUT = int(os.getenv("EMBEDDING_TIMEOUT", "60"))


def _parse_embedding_response(data) -> List[float]:
    if isinstance(data, dict):
        if "embedding" in data and isinstance(data["embedding"], list):
            return data["embedding"]
        if "data" in data and isinstance(data["data"], list) and data["data"]:
            first_item = data["data"][0]
            if isinstance(first_item, dict) and "embedding" in first_item:
                return first_item["embedding"]
    return []


def _make_embedding_request(url: str, payload: dict) -> List[float]:
    response = requests.post(url, json=payload, timeout=EMBEDDING_TIMEOUT)
    response.raise_for_status()
    return _parse_embedding_response(response.json())


def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> List[float]:
    """
    Sends a chunk of text to Ollama and returns a vector embedding.
    Supports both OpenAI-compatible `/v1/embeddings` and legacy `/api/embeddings`.
    """
    if not text:
        return []

    normalized_url = OLLAMA_URL.rstrip("/")
    endpoints = [
        {
            "url": f"{normalized_url}/v1/embeddings",
            "payload": {"model": model, "input": text},
        },
        {
            "url": f"{normalized_url}/api/embeddings",
            "payload": {
                "model": model,
                "prompt": text,
                "options": {"num_ctx": 8192},
                "truncate": True,
            },
        },
    ]

    last_error = None

    for endpoint in endpoints:
        try:
            print(f"🔎 Trying Ollama embedding endpoint: {endpoint['url']}")
            embedding = _make_embedding_request(endpoint["url"], endpoint["payload"])
            if embedding:
                return embedding
        except requests.exceptions.Timeout:
            print(f"⏱️ ERROR: Embedding request timed out after {EMBEDDING_TIMEOUT} seconds for text: {text[:50]}...")
            return []
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            print(f"❌ Ollama embedding endpoint failed ({status}): {e}")
            last_error = e
            continue
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to generate embedding: {e}")
            last_error = e
            continue

    if last_error:
        print("❌ All Ollama embedding endpoints failed. Confirm your model and Ollama server configuration.")
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
                "embedding": embedding,
            })
        else:
            print(f"⚠️ Skipping chunk {i+1} because embedding failed.")

    return results