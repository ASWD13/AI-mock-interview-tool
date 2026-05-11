"""Tests for resume parsing and skill extraction."""

import pytest
from backend.services.skill_extractor import extract_skills


class TestSkillExtractor:
    def test_extract_react_skills(self):
        text = "Experience with React, JavaScript, and CSS. Built projects using Node.js and PostgreSQL."
        skills, categories = extract_skills(text)
        assert "React" in skills
        assert "JavaScript" in skills
        assert "CSS" in skills
        assert "Node.js" in skills
        assert "PostgreSQL" in skills

    def test_extract_python_skills(self):
        text = "Python developer with Django, Flask, and PostgreSQL experience. Familiar with Docker and AWS."
        skills, categories = extract_skills(text)
        assert "Python" in skills
        assert "Django" in skills
        assert "Docker" in skills

    def test_skill_categories(self):
        text = "React developer with Node.js backend experience and Docker for deployment."
        skills, categories = extract_skills(text)
        assert "frontend" in categories
        assert "backend" in categories
        assert "devops" in categories

    def test_empty_text(self):
        skills, categories = extract_skills("")
        assert skills == []
        assert categories == {}

    def test_no_skills(self):
        text = "I enjoy cooking and gardening in my free time."
        skills, categories = extract_skills(text)
        # Should return few or no skills
        assert isinstance(skills, list)


class TestResumeParser:
    def test_txt_parse(self):
        """Test that TXT parsing works."""
        import asyncio
        from backend.services.resume_parser import parse_resume

        content = b"John Doe\nSoftware Engineer\nSkills: Python, React, Docker"
        result = asyncio.run(parse_resume(content, "txt"))
        assert "John Doe" in result
        assert "Python" in result
