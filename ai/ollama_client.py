import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:1.5b-instruct"

def generate(prompt: str, max_tokens: int = 500) -> str:
    try:
        response = requests.post(
            OLLAMA_URL, 
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_predict": max_tokens
                }
            },
            timeout=120  # 2 minute timeout
        )
        response.raise_for_status()
        return response.json()["response"].strip()
    except requests.exceptions.Timeout:
        print(f"⏱️ ERROR: Ollama request timed out after 120 seconds")
        raise
    except Exception as e:
        print(f"❌ ERROR in Ollama generate: {e}")
        raise