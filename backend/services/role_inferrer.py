"""Role inference service using Groq GPT OSS 120B + fallback rules."""

import json
from typing import Dict, List, Any, Optional
from backend.config import get_settings
from backend.prompts.role_infer import get_role_infer_prompt


# Rule-based fallback mapping
SKILL_ROLE_MAP = {
    "React": "Frontend Developer",
    "Angular": "Frontend Developer",
    "Vue.js": "Frontend Developer",
    "Next.js": "Frontend Developer",
    "JavaScript": "Frontend Developer",
    "TypeScript": "Frontend Developer",
    "Node.js": "Backend Developer",
    "Express.js": "Backend Developer",
    "FastAPI": "Backend Developer",
    "Django": "Backend Developer",
    "Flask": "Backend Developer",
    "Spring": "Backend Developer",
    "Python": "Backend Developer",
    "Java": "Backend Developer",
    "Docker": "DevOps Engineer",
    "Kubernetes": "DevOps Engineer",
    "AWS": "Cloud Engineer",
    "Azure": "Cloud Engineer",
    "GCP": "Cloud Engineer",
    "Terraform": "DevOps Engineer",
    "TensorFlow": "ML Engineer",
    "PyTorch": "ML Engineer",
    "Machine Learning": "ML Engineer",
    "Deep Learning": "ML Engineer",
    "NLP": "ML Engineer",
    "Pandas": "Data Analyst",
    "SQL": "Data Analyst",
    "Tableau": "Data Analyst",
    "Power BI": "Data Analyst",
    "React Native": "Mobile Developer",
    "Flutter": "Mobile Developer",
    "Swift": "iOS Developer",
    "Kotlin": "Android Developer",
    "MongoDB": "Backend Developer",
    "PostgreSQL": "Backend Developer",
    "GraphQL": "Full Stack Developer",
    "REST": "Full Stack Developer",
    "Solidity": "Blockchain Developer",
    "Cybersecurity": "Security Engineer",
}


async def infer_role(skills: List[str], raw_text: str) -> Dict[str, Any]:
    """Infer role, seniority, focus areas, and weak areas from skills and resume text.

    Args:
        skills: Extracted skill list
        raw_text: Full resume text

    Returns:
        Dict with possible_roles, experience_level, focus_areas, weak_areas, etc.
    """
    settings = get_settings()

    # Try LLM-based inference
    if settings.groq_api_key:
        try:
            return await _llm_infer_role(skills, raw_text, settings)
        except Exception as e:
            print(f"LLM role inference failed: {e}, falling back to rules")

    # Rule-based fallback
    return _rule_based_infer(skills, raw_text)


async def _llm_infer_role(skills: List[str], raw_text: str, settings) -> Dict[str, Any]:
    """Use Groq GPT OSS 120B for role inference."""
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.groq_api_key)

    # Extract projects summary (first 500 chars of resume)
    projects_summary = raw_text[:1500]

    system_prompt, user_prompt = get_role_infer_prompt(
        skills=skills,
        projects_summary=projects_summary,
        years="unknown"
    )

    response = await client.chat.completions.create(
        model=settings.groq_llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    # Also parse resume for name/email/education/projects
    parse_result = await _llm_parse_resume(raw_text, settings)

    # Merge results
    return {
        **parse_result,
        "possible_roles": result.get("possible_roles", [])[:3],
        "experience_level": result.get("experience_level", "junior"),
        "focus_areas": result.get("focus_areas", [])[:3],
        "weak_areas": result.get("weak_areas", [])[:3],
    }


async def _llm_parse_resume(raw_text: str, settings) -> Dict[str, Any]:
    """Use Groq GPT OSS 120B for full resume parsing."""
    from groq import AsyncGroq
    from backend.prompts.resume_parse import get_resume_parse_prompt

    client = AsyncGroq(api_key=settings.groq_api_key)

    system_prompt, user_prompt = get_resume_parse_prompt(raw_text)

    response = await client.chat.completions.create(
        model=settings.groq_llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=2048,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    return result


def _rule_based_infer(skills: List[str], raw_text: str) -> Dict[str, Any]:
    """Fallback rule-based role inference."""
    role_scores: Dict[str, int] = {}
    for skill in skills:
        role = SKILL_ROLE_MAP.get(skill)
        if role:
            role_scores[role] = role_scores.get(role, 0) + 1

    # Sort by score
    sorted_roles = sorted(role_scores.items(), key=lambda x: x[1], reverse=True)
    possible_roles = [r[0] for r in sorted_roles[:3]]

    if not possible_roles:
        possible_roles = ["Software Developer"]

    # Simple seniority estimation
    text_lower = raw_text.lower()
    years = 0
    import re
    year_match = re.search(r'(\d+)\+?\s*years?\s*(of)?\s*experience', text_lower)
    if year_match:
        years = int(year_match.group(1))

    if years >= 8:
        experience_level = "senior"
    elif years >= 4:
        experience_level = "mid"
    elif years >= 1:
        experience_level = "junior"
    else:
        experience_level = "fresher"

    # Focus and weak areas
    focus_areas = skills[:3] if skills else []
    all_categories = set(SKILL_ROLE_MAP.keys())
    found_categories = set(skills)
    weak_areas = list(all_categories - found_categories)[:3]

    return {
        "name": None,
        "email": None,
        "possible_roles": possible_roles,
        "experience_level": experience_level,
        "years_experience": years,
        "focus_areas": focus_areas,
        "weak_areas": weak_areas if weak_areas else ["System Design", "Testing", "Documentation"],
        "projects": [],
        "education": [],
        "certifications": [],
    }
