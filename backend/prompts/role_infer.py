"""Role inference prompt — §11.2"""

from typing import List


def get_role_infer_prompt(skills: List[str], projects_summary: str, years: str):
    """Return (system_prompt, user_prompt) for role inference."""

    system_prompt = (
        "You are a technical recruiter. Given a candidate's skills and projects, infer:\n"
        "1. Top 3 most suitable job roles (ordered by fit)\n"
        "2. Seniority level: fresher/junior/mid/senior\n"
        "3. Top 3 strong focus areas\n"
        "4. Top 3 weak/missing areas\n"
        'Return ONLY JSON: {"possible_roles": [], "experience_level": "", "focus_areas": [], "weak_areas": []}'
    )

    user_prompt = (
        f"Skills: {', '.join(skills)}\n"
        f"Projects: {projects_summary}\n"
        f"Years experience: {years}"
    )

    return system_prompt, user_prompt
