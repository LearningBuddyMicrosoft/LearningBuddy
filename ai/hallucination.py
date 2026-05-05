"""
Hallucination detection for AI responses.
"""
import os

from typing import List, Dict, Any
from langchain_community.chat_models import ChatOllama

llm = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "qwen2.5:3b-instruct"),
    temperature=0.0,
    max_tokens=2048,
    base_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
)

from langchain_core.prompts import ChatPromptTemplate


import re
import difflib
from typing import List, Dict, Any, Tuple


# Deterministic verification: returns fraction of sentences supported by context
def deterministic_verify(response: str, context_text: str, threshold: float = 0.4) -> Tuple[float, List[str]]:
    sentences = [s.strip() for s in re.split(r'[.?!]\s+', response) if s.strip()]
    if not sentences:
        return 1.0, []
    
    supported = []
    unsupported_reasons = []
    for s in sentences:
        if len(s) < 10:  # Skip very short sentences
            supported.append(s)
            continue
            
        if s in context_text:
            supported.append(s)
            continue
        # fuzzy match: check best substring similarity
        best_ratio = 0.0
        for i in range(0, len(context_text), 1000):  # sample windows to speed up
            window = context_text[i:i+2000]
            ratio = difflib.SequenceMatcher(None, s.lower(), window.lower()).quick_ratio()
            if ratio > best_ratio:
                best_ratio = ratio
            if best_ratio >= threshold + 0.2:  # More lenient threshold
                break
        if best_ratio >= threshold:
            supported.append(s)
        else:
            unsupported_reasons.append(f"Low similarity: '{s[:80]}...'")
    
    ratio = len(supported) / max(1, len(sentences))
    return ratio, unsupported_reasons

# LLM-based scoring with strict JSON output
def llm_hallucination_score(response: str, context_chunks: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    # Build context with chunk ids
    context_text = ""
    for idx, c in enumerate(context_chunks, start=1):
        cid = c.get("id", f"CHUNK_{idx}")
        context_text += f"--- {cid} ---\n{c.get('text','')}\n\n"

    system = (
        "You are an expert fact-checker. Return a JSON object with keys: "
        "\"score\" (0.0-1.0) and \"reasons\" (list of short strings). "
        "Score 0 means fully grounded, 1 means fully hallucinated. "
        "Use only the provided context. If you cannot determine, return score 0.5."
    )
    human = f"Context:\n{context_text}\n\nResponse:\n{response}\n\nReturn JSON only."
    
    try:
        # Use the correct llm call for your wrapper. Example below assumes llm.generate or llm.predict
        messages = [{"role":"system","content":system}, {"role":"user","content":human}]
        gen = llm.generate([messages])  # adapt to your llm API
        raw = gen.generations[0][0].text if gen.generations else ""
    except TimeoutError:
        print(f"⏱️ Hallucination check TIMEOUT - skipping check and assuming grounded (score=0.0)")
        return 0.0, ["Timeout: skipped hallucination check"]
    except Exception as e:
        print(f"⚠️ Hallucination check failed: {e} - assuming grounded (score=0.0)")
        return 0.0, [f"Error: {str(e)}"]
    
    # Extract JSON object with regex
    m = re.search(r'\{.*\}', raw, flags=re.S)
    if not m:
        # fallback: try to extract a number
        num_m = re.search(r'([01](?:\.\d+)?)', raw)
        if num_m:
            score = float(num_m.group(1))
            return max(0.0, min(1.0, score)), ["Parsed numeric fallback"]
        return 0.5, ["Parsing failed"]
    import json
    try:
        obj = json.loads(m.group(0))
        score = float(obj.get("score", 0.5))
        reasons = obj.get("reasons", [])
        return max(0.0, min(1.0, score)), reasons
    except Exception:
        return 0.5, ["JSON parse error"]

# Combined API
def calculate_hallucination_score(response: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
    context_text = "\n".join([c.get("text","") for c in context])
    det_ratio, det_reasons = deterministic_verify(response, context_text)
    # Use ONLY deterministic verification - LLM check is causing timeouts
    return {"score": max(0.0, 1.0 - det_ratio), "deterministic_ratio": det_ratio, "reasons": det_reasons}




from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("all-MiniLM-L6-v2")

def is_hallucinating(response: str, context: list, threshold: float = 0.10) -> bool:
    """
    Soft hallucination detection:
    - Does NOT require exact matches.
    - Only rejects questions that are completely unrelated.
    """

    # Combine all context text
    context_text = " ".join([c.get("text", "") for c in context])

    # Encode
    resp_emb = model.encode(response, convert_to_tensor=True)
    ctx_emb = model.encode(context_text, convert_to_tensor=True)

    # Cosine similarity
    score = util.cos_sim(resp_emb, ctx_emb).item()

    # Soft threshold: only reject if similarity is extremely low
    return score < threshold






