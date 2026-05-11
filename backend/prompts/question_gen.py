"""Question generation prompt — §11.3"""

from typing import List, Optional


def get_question_gen_prompt(
    role: str,
    current_topic: str,
    difficulty: str,
    question_history_titles: List[str],
    weak_areas: List[str],
    rag_seed_question: str = "",
):
    """Return (system_prompt, user_prompt) for question generation."""

    system_prompt = (
        "You are a technical interviewer. Generate ONE interview question.\n"
        f"Role: {role} | Topic: {current_topic} | Difficulty: {difficulty}\n"
        f"Previous questions asked: {', '.join(question_history_titles) if question_history_titles else 'None'}\n"
        f"Candidate weak areas: {', '.join(weak_areas) if weak_areas else 'None'}\n"
        f"Context (use if relevant): {rag_seed_question}\n"
        "Rules: Do not repeat previous questions. Match difficulty exactly.\n"
        'Return ONLY JSON: {"question": "", "expected_keywords": [], "category": ""}'
    )

    user_prompt = "Generate the next question."

    return system_prompt, user_prompt
