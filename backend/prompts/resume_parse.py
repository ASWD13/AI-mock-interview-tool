"""Resume parse prompt — §11.1"""


RESUME_PARSE_SCHEMA = {
    "name": "string or null",
    "email": "string or null",
    "years_experience": "integer or null",
    "projects": [{"title": "str", "tech_stack": ["str"], "description": "str"}],
    "education": [{"degree": "str", "institution": "str", "year": "str"}],
    "certifications": ["str"],
}


def get_resume_parse_prompt(resume_text: str):
    """Return (system_prompt, user_prompt) for resume parsing."""

    system_prompt = (
        "You are a resume parser. Extract structured data from the resume text below.\n"
        f"Return ONLY valid JSON matching this schema exactly: {RESUME_PARSE_SCHEMA}\n"
        "Do not add commentary. If a field is unknown, use null or []."
    )

    user_prompt = resume_text

    return system_prompt, user_prompt
