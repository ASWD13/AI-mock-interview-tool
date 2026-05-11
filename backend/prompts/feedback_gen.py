"""Feedback generation prompt — §11.5"""

from typing import Dict, Any


def get_feedback_gen_prompt(
    profile_summary: str,
    transcript: str,
    tech_score: float,
    comm_score: float,
    conf_score: float,
    eng_score: float,
):
    """Return (system_prompt, user_prompt) for feedback generation."""

    system_prompt = (
        "You are an interview coach. Generate specific, actionable feedback.\n"
        f"Candidate profile: {profile_summary}\n"
        f"Interview transcript (Q&A pairs): {transcript}\n"
        f"Scores: technical={tech_score:.2f}, communication={comm_score:.2f}, "
        f"confidence={conf_score:.2f}, engagement={eng_score:.2f}\n"
        "Rules:\n"
        "- Reference specific questions and topics from this interview\n"
        "- Never give generic advice\n"
        "- Be encouraging but honest\n"
        "- improvement_plan must have exactly 3 actionable steps\n"
        "Return ONLY JSON:\n"
        "{\n"
        '  "overall_rating": "Excellent|Good|Average|Needs Improvement",\n'
        '  "technical_feedback": [{"topic": "str", "observation": "str", "suggestion": "str"}],\n'
        '  "communication_feedback": [{"observation": "str", "suggestion": "str"}],\n'
        '  "behavioral_feedback": [{"observation": "str", "suggestion": "str"}],\n'
        '  "improvement_plan": ["str", "str", "str"],\n'
        '  "strengths": ["str"]\n'
        "}"
    )

    user_prompt = "Generate feedback report."

    return system_prompt, user_prompt
