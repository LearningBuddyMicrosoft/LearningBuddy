"""
Hallucination detection for AI responses.
"""

from typing import List, Dict, Any
from ai.llm import llm
from langchain_core.prompts import ChatPromptTemplate


import re
import difflib
from typing import List, Dict, Any, Tuple
from ai.llm import llm  # ensure this exposes the correct call for your wrapper

# Deterministic verification: returns fraction of sentences supported by context
def deterministic_verify(response: str, context_text: str, threshold: float = 0.6) -> Tuple[float, List[str]]:
    sentences = [s.strip() for s in re.split(r'[.?!]\s+', response) if s.strip()]
    supported = []
    unsupported_reasons = []
    for s in sentences:
        if s in context_text:
            supported.append(s)
            continue
        # fuzzy match: check best substring similarity
        best_ratio = 0.0
        for i in range(0, len(context_text), 1000):  # sample windows to speed up
            window = context_text[i:i+2000]
            ratio = difflib.SequenceMatcher(None, s, window).quick_ratio()
            if ratio > best_ratio:
                best_ratio = ratio
            if best_ratio >= threshold:
                break
        if best_ratio >= threshold:
            supported.append(s)
        else:
            unsupported_reasons.append(f"Not found or low similarity: '{s[:80]}...'")
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
    # Use the correct llm call for your wrapper. Example below assumes llm.generate or llm.predict
    messages = [{"role":"system","content":system}, {"role":"user","content":human}]
    gen = llm.generate([messages])  # adapt to your llm API
    raw = gen.generations[0][0].text if gen.generations else ""
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
    # If deterministic verification is decisive, skip LLM
    if det_ratio >= 0.95:
        return {"score": 0.0, "deterministic_ratio": det_ratio, "reasons": []}
    if det_ratio <= 0.1:
        return {"score": 1.0, "deterministic_ratio": det_ratio, "reasons": det_reasons}
    # Otherwise call LLM and combine
    llm_score, llm_reasons = llm_hallucination_score(response, context)
    # Weighted average: deterministic gets higher weight
    final_score = 0.6 * (1 - det_ratio) + 0.4 * llm_score
    reasons = det_reasons + llm_reasons
    return {"score": round(final_score, 3), "deterministic_ratio": round(det_ratio, 3), "reasons": reasons}



def is_hallucinating(response: str, context: List[Dict[str, Any]], threshold: float = 0.5) -> bool:
    """
    Determine if the response is hallucinating based on a threshold.

    Args:
        response: The AI-generated response.
        context: List of context chunks.
        threshold: Score above which it's considered hallucinating.

    Returns:
        True if hallucinating, False otherwise.
    """
    score = calculate_hallucination_score(response, context)
    return score > threshold