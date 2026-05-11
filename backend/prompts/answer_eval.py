"""Answer evaluation prompt — §11.4"""

from typing import List


def get_answer_eval_prompt(
    question: str,
    expected_keywords: List[str],
    transcript: str,
):
    """Return (system_prompt, user_prompt) for answer evaluation."""

    system_prompt = (
        "You are a technical interviewer evaluating an answer.\n"
        f"Question: {question}\n"
        f"Expected concepts: {', '.join(expected_keywords)}\n"
        f"Candidate answer transcript: {transcript}\n"
        "Rate 0.0-1.0 for each. Return ONLY JSON:\n"
        '{"correctness": 0.0, "depth": 0.0, "relevance": 0.0, "reasoning": ""}'
    )

    user_prompt = "Evaluate this answer."

    return system_prompt, user_prompt
