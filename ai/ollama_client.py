import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3.5"

def generate(prompt: str, max_tokens: int = 500) -> str:
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.5,
            "num_predict": max_tokens
        }
    })
    response.raise_for_status()
    return response.json()["response"].strip()