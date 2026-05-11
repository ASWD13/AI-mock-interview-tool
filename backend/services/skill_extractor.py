"""Skill extractor using spaCy NER + skill taxonomy lookup."""

import json
import re
from typing import List, Dict, Tuple

# Skill categories taxonomy (100+ skills mapped to categories)
SKILL_TAXONOMY = {
    "frontend": [
        "react", "react.js", "reactjs", "angular", "vue", "vue.js", "vuejs",
        "javascript", "typescript", "html", "css", "sass", "scss", "less",
        "tailwind", "tailwindcss", "bootstrap", "material ui", "mui",
        "next.js", "nextjs", "nuxt", "nuxtjs", "svelte", "jquery",
        "webpack", "vite", "babel", "redux", "zustand", "mobx",
        "storybook", "cypress", "jest", "testing library",
        "responsive design", "web accessibility", "a11y", "figma",
    ],
    "backend": [
        "node.js", "nodejs", "express", "express.js", "fastapi", "flask",
        "django", "spring", "spring boot", "rails", "ruby on rails",
        "asp.net", ".net", "laravel", "php", "go", "golang", "rust",
        "java", "python", "c#", "c++", "kotlin", "scala",
        "graphql", "rest", "restful", "api", "microservices",
        "grpc", "websocket", "oauth", "jwt",
    ],
    "database": [
        "sql", "mysql", "postgresql", "postgres", "mongodb", "redis",
        "elasticsearch", "dynamodb", "cassandra", "sqlite", "oracle",
        "firebase", "firestore", "supabase", "prisma", "sequelize",
        "typeorm", "sqlalchemy", "mongoose", "neo4j",
    ],
    "devops": [
        "docker", "kubernetes", "k8s", "aws", "azure", "gcp",
        "google cloud", "terraform", "ansible", "jenkins", "ci/cd",
        "github actions", "gitlab ci", "circleci", "nginx",
        "linux", "bash", "shell scripting", "cloudformation",
        "helm", "istio", "prometheus", "grafana", "datadog",
    ],
    "data_science": [
        "pandas", "numpy", "scipy", "scikit-learn", "sklearn",
        "tensorflow", "pytorch", "keras", "matplotlib", "seaborn",
        "jupyter", "r", "tableau", "power bi", "spark", "pyspark",
        "hadoop", "airflow", "dbt", "sql", "statistics",
        "data visualization", "data modeling", "etl",
    ],
    "machine_learning": [
        "machine learning", "deep learning", "nlp",
        "natural language processing", "computer vision", "cv",
        "reinforcement learning", "gans", "transformers", "bert",
        "gpt", "llm", "langchain", "hugging face", "openai",
        "neural networks", "cnn", "rnn", "lstm",
        "feature engineering", "model deployment", "mlops",
    ],
    "mobile": [
        "react native", "flutter", "swift", "swiftui", "kotlin",
        "android", "ios", "xamarin", "ionic", "capacitor",
        "expo", "objective-c", "cocoapods",
    ],
    "tools": [
        "git", "github", "gitlab", "bitbucket", "jira",
        "confluence", "slack", "notion", "vscode", "vim",
        "postman", "swagger", "figma", "adobe xd",
    ],
    "security": [
        "cybersecurity", "penetration testing", "owasp",
        "encryption", "ssl", "tls", "firewall",
        "iam", "sso", "ldap", "security audit",
    ],
    "blockchain": [
        "blockchain", "solidity", "ethereum", "web3",
        "smart contracts", "defi", "nft", "hardhat", "truffle",
    ],
}

# Flatten for quick lookup
ALL_SKILLS = {}
for category, skills in SKILL_TAXONOMY.items():
    for skill in skills:
        ALL_SKILLS[skill.lower()] = category


def extract_skills(text: str) -> Tuple[List[str], Dict[str, List[str]]]:
    """Extract skills from resume text using taxonomy lookup + spaCy NER.

    Args:
        text: Raw resume text

    Returns:
        Tuple of (flat skills list, categorized skills dict)
    """
    text_lower = text.lower()
    found_skills = set()
    skill_categories: Dict[str, List[str]] = {}

    # Taxonomy-based extraction
    for skill, category in ALL_SKILLS.items():
        # Word boundary matching to avoid partial matches
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            # Use proper casing
            proper_skill = _proper_case(skill)
            found_skills.add(proper_skill)
            if category not in skill_categories:
                skill_categories[category] = []
            if proper_skill not in skill_categories[category]:
                skill_categories[category].append(proper_skill)

    # Try spaCy NER for additional extraction
    try:
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            nlp = None

        if nlp:
            doc = nlp(text)
            for ent in doc.ents:
                if ent.label_ in ("ORG", "PRODUCT", "WORK_OF_ART"):
                    skill_name = ent.text.strip()
                    if len(skill_name) > 1 and skill_name.lower() in ALL_SKILLS:
                        proper = _proper_case(skill_name.lower())
                        found_skills.add(proper)
                        cat = ALL_SKILLS[skill_name.lower()]
                        if cat not in skill_categories:
                            skill_categories[cat] = []
                        if proper not in skill_categories[cat]:
                            skill_categories[cat].append(proper)
    except ImportError:
        pass

    return sorted(list(found_skills)), skill_categories


def _proper_case(skill: str) -> str:
    """Convert skill to proper display case."""
    special_cases = {
        "javascript": "JavaScript",
        "typescript": "TypeScript",
        "react": "React",
        "react.js": "React",
        "reactjs": "React",
        "node.js": "Node.js",
        "nodejs": "Node.js",
        "vue.js": "Vue.js",
        "vuejs": "Vue.js",
        "angular": "Angular",
        "next.js": "Next.js",
        "nextjs": "Next.js",
        "nuxt": "Nuxt",
        "nuxtjs": "Nuxt.js",
        "express": "Express",
        "express.js": "Express.js",
        "fastapi": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "python": "Python",
        "java": "Java",
        "c#": "C#",
        "c++": "C++",
        "go": "Go",
        "golang": "Go",
        "rust": "Rust",
        "kotlin": "Kotlin",
        "swift": "Swift",
        "html": "HTML",
        "css": "CSS",
        "sass": "Sass",
        "scss": "SCSS",
        "sql": "SQL",
        "mysql": "MySQL",
        "postgresql": "PostgreSQL",
        "postgres": "PostgreSQL",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "k8s": "Kubernetes",
        "aws": "AWS",
        "azure": "Azure",
        "gcp": "GCP",
        "git": "Git",
        "github": "GitHub",
        "gitlab": "GitLab",
        "graphql": "GraphQL",
        "rest": "REST",
        "restful": "RESTful",
        "api": "API",
        "jwt": "JWT",
        "oauth": "OAuth",
        "ci/cd": "CI/CD",
        "tensorflow": "TensorFlow",
        "pytorch": "PyTorch",
        "keras": "Keras",
        "pandas": "Pandas",
        "numpy": "NumPy",
        "scipy": "SciPy",
        "nlp": "NLP",
        "llm": "LLM",
        "langchain": "LangChain",
        "tailwind": "Tailwind",
        "tailwindcss": "TailwindCSS",
        "bootstrap": "Bootstrap",
        "webpack": "Webpack",
        "vite": "Vite",
        "redux": "Redux",
        "zustand": "Zustand",
        "jest": "Jest",
        "cypress": "Cypress",
        "jira": "Jira",
        "figma": "Figma",
        "svelte": "Svelte",
        "firebase": "Firebase",
        "supabase": "Supabase",
        "prisma": "Prisma",
        "linux": "Linux",
        "bash": "Bash",
        "nginx": "Nginx",
        "elasticsearch": "Elasticsearch",
        "react native": "React Native",
        "flutter": "Flutter",
        "machine learning": "Machine Learning",
        "deep learning": "Deep Learning",
        "computer vision": "Computer Vision",
        "microservices": "Microservices",
    }
    return special_cases.get(skill.lower(), skill.title())
