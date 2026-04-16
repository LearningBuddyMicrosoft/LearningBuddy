"""LLM setup and AI prompts for the AI Study Assistant."""

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional

# Response model for LLM output
class ResponseModel(BaseModel):
    topic: str
    summary: str
    mcqs: List[dict] = Field(default_factory=list)
    source: List[str] = Field(default_factory=list)


# Setup LLM with Ollama
llm = ChatOllama(    
    model="qwen2.5:7b-instruct",
    temperature=0.4,
    options={"num_ctx": 4096},
)

# Parser for converting AI responses to structured objects
parser = JsonOutputParser(pydantic_object=ResponseModel)


# =========================================
# AI PROMPT SYSTEM - QUIZ GENERATION
# =========================================

final_answer_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a helpful study assistant. Based on the provided context, generate a structured response.

IMPORTANT: Adjust the number of multiple-choice questions based on document length:
- SHORT documents (< 2000 characters): Generate 5-10 questions. Try to maximize coverage.
- MEDIUM documents (2000-5000 characters): Generate 15-20 questions. Balance coverage with quality.
- LONG documents (> 5000 characters): Generate 25-30 questions. Try to make as many as possible while maintaining quality. If you cannot generate 25 questions, generate the minimum of 15.

Output ONLY and EXACTLY valid JSON matching this format. DO NOT add any text before or after the JSON:

{{
  "topic": "A short topic title",
  "summary": "A brief summary of the key points",
  "mcqs": [
    {{
      "question": "The question text",
      "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
      "answer": "A",
      "evidence": "One sentence of grounding from the context justifying the answer",
      "source": "Page X of document name or section"
    }}
  ],
  "source": ["Source 1", "Source 2"]
}}

CRITICAL RULES:
1. ONLY use field names: topic, summary, mcqs, source
2. In each MCQ, ONLY use: question, options, answer, evidence, source
3. The "answer" field MUST be ONLY "A", "B", "C", or "D" (exactly one letter)
4. The "options" field MUST be a list of exactly 4 strings, NO prefixes like "A)" or "A."
5. ONLY output JSON, no other text
6. Ensure all MCQs are grounded in the context. Do not invent facts.
            """,
        ),
        (
            "human",
            """
Context: {context}

User query: {query}

Analyze the context length and generate the appropriate number of questions based on the guidelines.
Output ONLY the JSON response, nothing else.
            """,
        ),
    ]
)

