"""
Hallucination detection for AI responses.
"""

from typing import List, Dict, Any
from ai.llm import llm
from langchain_core.prompts import ChatPromptTemplate


def calculate_hallucination_score(response: str, context: List[Dict[str, Any]]) -> float:
    """
    Calculate a hallucination score for the AI response based on the provided context.

    Args:
        response: The AI-generated response text.
        context: List of context chunks, each with 'text' key.

    Returns:
        A score between 0 and 1, where 0 means fully grounded (no hallucination)
        and 1 means completely hallucinated.
    """
    # Combine context texts
    context_text = "\n".join([chunk.get('text', '') for chunk in context])

    # Prompt for hallucination detection
    hallucination_prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are an expert fact-checker. Evaluate if the given response is fully supported by the provided context.
Rate the hallucination level on a scale from 0 to 1, where:
- 0: The response is completely grounded in the context, no unsupported claims.
- 1: The response contains significant hallucinations or fabrications not present in the context.

Consider:
- Factual accuracy: Does the response contain information not in the context?
- Consistency: Does the response contradict the context?
- Completeness: Is the response based only on the provided information?

Provide only a number between 0 and 1 as your response.
            """,
        ),
        (
            "human",
            """
Context:
{context_text}

Response:
{response}

Hallucination score:
            """,
        ),
    ])

    # Format prompt with context and response values
    messages = hallucination_prompt.format_messages(
        context_text=context_text,
        response=response,
    )

    result = llm.invoke(messages)

    try:
        score = float(result.content.strip())
        # Clamp to 0-1
        score = max(0.0, min(1.0, score))
    except ValueError:
        # If parsing fails, assume some default
        score = 0.5

    return score


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