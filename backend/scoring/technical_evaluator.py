"""Technical evaluator — keyword match + Groq GPT OSS 120B evaluation (§8.9, §10)."""

import json
from typing import Dict, Any, List
from backend.config import get_settings
from backend.prompts.answer_eval import get_answer_eval_prompt


async def evaluate_answer(
    transcript: str,
    expected_keywords: List[str],
    question_text: str,
) -> Dict[str, Any]:
    """Evaluate a candidate's answer for correctness, depth, relevance.

    Implements §8.9:
    1. Keyword match
    2. LLM evaluation (Groq GPT OSS 120B)
    3. Blend: correctness = 0.6 * llm_correctness + 0.4 * keyword_score

    Returns dict with correctness, depth, relevance, keyword_hits, keyword_miss.
    """
    # Handle empty transcript
    if not transcript or len(transcript.strip()) < 5:
        return {
            "correctness": 0.0,
            "depth": 0.0,
            "relevance": 0.0,
            "keyword_hits": [],
            "keyword_miss": expected_keywords or [],
        }

    # Step 1: Keyword match
    keyword_hits = [k for k in expected_keywords if k.lower() in transcript.lower()]
    keyword_miss = [k for k in expected_keywords if k.lower() not in transcript.lower()]
    keyword_score = len(keyword_hits) / max(len(expected_keywords), 1)

    # Step 2: LLM evaluation
    settings = get_settings()
    llm_correctness = keyword_score  # default fallback
    llm_depth = 0.5
    llm_relevance = 0.5

    if settings.groq_api_key:
        try:
            llm_result = await _llm_evaluate(transcript, expected_keywords, question_text, settings)
            llm_correctness = llm_result.get("correctness", keyword_score)
            llm_depth = llm_result.get("depth", 0.5)
            llm_relevance = llm_result.get("relevance", 0.5)
        except Exception as e:
            print(f"LLM evaluation failed: {e}")

    # Step 3: Blend (§8.9)
    correctness = 0.6 * llm_correctness + 0.4 * keyword_score

    # Clamp all scores to [0.0, 1.0]
    correctness = max(0.0, min(1.0, correctness))
    depth = max(0.0, min(1.0, llm_depth))
    relevance = max(0.0, min(1.0, llm_relevance))

    return {
        "correctness": correctness,
        "depth": depth,
        "relevance": relevance,
        "keyword_hits": keyword_hits,
        "keyword_miss": keyword_miss,
    }


async def _llm_evaluate(
    transcript: str,
    expected_keywords: List[str],
    question_text: str,
    settings,
) -> Dict[str, float]:
    """Evaluate answer using Groq GPT OSS 120B."""
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.groq_api_key)

    system_prompt, user_prompt = get_answer_eval_prompt(
        question=question_text,
        expected_keywords=expected_keywords,
        transcript=transcript[:2000],  # Truncate for token limit
    )

    response = await client.chat.completions.create(
        model=settings.groq_llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=512,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    # Validate LLM vs keyword gap (§15)
    keyword_score = len([k for k in expected_keywords if k.lower() in transcript.lower()]) / max(len(expected_keywords), 1)
    llm_correctness = result.get("correctness", 0.5)
    if abs(llm_correctness - keyword_score) > 0.4:
        # Keyword match overrides LLM if gap > 0.4
        result["correctness"] = keyword_score

    return result
