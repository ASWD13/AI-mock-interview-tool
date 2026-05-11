"""Question generator — RAG + Groq GPT OSS 120B (§8.5, §11.3)."""

import json
from uuid import uuid4, UUID
from typing import Dict, List, Any, Optional
from backend.config import get_settings
from backend.prompts.question_gen import get_question_gen_prompt


# Fallback question templates per topic/difficulty
FALLBACK_QUESTIONS = {
    "fundamentals": {
        "easy": [
            {"question": "Can you explain the basic concepts of {topic}?", "expected_keywords": ["definition", "use case", "example"], "category": "fundamentals"},
            {"question": "What is {topic} and why is it important in modern development?", "expected_keywords": ["purpose", "benefits", "usage"], "category": "fundamentals"},
        ],
        "medium": [
            {"question": "How would you explain the internal workings of {topic}?", "expected_keywords": ["mechanism", "architecture", "flow"], "category": "fundamentals"},
            {"question": "What are the key trade-offs when using {topic}?", "expected_keywords": ["pros", "cons", "alternatives"], "category": "fundamentals"},
        ],
        "hard": [
            {"question": "What are some advanced patterns or optimizations in {topic}?", "expected_keywords": ["optimization", "pattern", "performance"], "category": "fundamentals"},
        ],
    },
    "architecture": {
        "easy": [
            {"question": "How would you structure a simple application using {topic}?", "expected_keywords": ["structure", "components", "layers"], "category": "architecture"},
        ],
        "medium": [
            {"question": "Describe a scalable architecture using {topic}.", "expected_keywords": ["scalability", "design", "patterns"], "category": "architecture"},
        ],
        "hard": [
            {"question": "Design a system that handles millions of users using {topic}.", "expected_keywords": ["distributed", "scaling", "fault tolerance"], "category": "architecture"},
        ],
    },
    "behavioral": {
        "medium": [
            {"question": "Tell me about a challenging project you worked on.", "expected_keywords": ["challenge", "solution", "outcome"], "category": "behavioral"},
            {"question": "How do you handle disagreements with team members?", "expected_keywords": ["communication", "compromise", "resolution"], "category": "behavioral"},
            {"question": "Describe a time you had to learn a new technology quickly.", "expected_keywords": ["learning", "adaptation", "result"], "category": "behavioral"},
        ],
    },
    "scenario": {
        "medium": [
            {"question": "If a production system goes down, what steps would you take?", "expected_keywords": ["debugging", "monitoring", "recovery"], "category": "scenario"},
        ],
    },
}


async def generate_question(
    session_id: UUID,
    role: str,
    topic: str,
    difficulty: str,
    question_history: List[str],
    weak_areas: List[str],
    profile_data: Dict[str, Any],
    category: str = "fundamentals",
    is_intro: bool = False,
    is_followup: bool = False,
    parent_question_id: Optional[UUID] = None,
) -> Dict[str, Any]:
    """Generate an interview question using RAG + Groq GPT OSS 120B.

    Returns dict with question_id, text, expected_keywords, category, topic.
    """
    settings = get_settings()
    question_id = uuid4()

    # Try RAG from ChromaDB for seed question
    rag_seed = ""
    try:
        from backend.utils.chroma_client import chroma_client
        collection = chroma_client.get_collection("questions")
        results = collection.query(
            query_texts=[f"{topic} {difficulty} {category}"],
            n_results=3,
            where={"difficulty": difficulty} if difficulty else None,
        )
        if results and results.get("documents") and results["documents"][0]:
            rag_seed = results["documents"][0][0]
    except Exception:
        pass

    # Try LLM generation
    if settings.groq_api_key and not is_intro:
        try:
            return await _llm_generate(
                question_id, session_id, role, topic, difficulty,
                question_history, weak_areas, rag_seed, category,
                is_followup, parent_question_id, settings
            )
        except Exception as e:
            print(f"LLM question generation failed: {e}")

    # Fallback to template
    return _fallback_generate(
        question_id, session_id, topic, difficulty, category,
        is_followup, parent_question_id, is_intro, role
    )


async def _llm_generate(
    question_id, session_id, role, topic, difficulty,
    question_history, weak_areas, rag_seed, category,
    is_followup, parent_question_id, settings
) -> Dict[str, Any]:
    """Generate question via Groq GPT OSS 120B."""
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.groq_api_key)

    system_prompt, user_prompt = get_question_gen_prompt(
        role=role,
        current_topic=topic,
        difficulty=difficulty,
        question_history_titles=question_history[-5:],  # Last 5
        weak_areas=weak_areas,
        rag_seed_question=rag_seed,
    )

    response = await client.chat.completions.create(
        model=settings.groq_llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=512,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)

    return {
        "question_id": question_id,
        "session_id": session_id,
        "text": result.get("question", f"Tell me about your experience with {topic}."),
        "expected_keywords": result.get("expected_keywords", []),
        "category": result.get("category", category),
        "topic": topic,
        "difficulty": difficulty,
        "is_followup": is_followup,
        "parent_question_id": parent_question_id,
    }


def _fallback_generate(
    question_id, session_id, topic, difficulty, category,
    is_followup, parent_question_id, is_intro, role
) -> Dict[str, Any]:
    """Fallback template-based question generation."""
    if is_intro:
        return {
            "question_id": question_id,
            "session_id": session_id,
            "text": f"Welcome! Tell me about yourself and what draws you to the {role} role.",
            "expected_keywords": ["experience", "skills", "motivation"],
            "category": "fundamentals",
            "topic": topic,
            "difficulty": "easy",
            "is_followup": False,
            "parent_question_id": None,
        }

    # Pick from templates
    cat_questions = FALLBACK_QUESTIONS.get(category, FALLBACK_QUESTIONS.get("fundamentals", {}))
    diff_questions = cat_questions.get(difficulty, cat_questions.get("medium", []))

    import random
    if diff_questions:
        template = random.choice(diff_questions)
        text = template["question"].replace("{topic}", topic)
        keywords = template["expected_keywords"]
        cat = template["category"]
    else:
        text = f"Can you explain your understanding of {topic}?"
        keywords = [topic.lower()]
        cat = category

    return {
        "question_id": question_id,
        "session_id": session_id,
        "text": text,
        "expected_keywords": keywords,
        "category": cat,
        "topic": topic,
        "difficulty": difficulty,
        "is_followup": is_followup,
        "parent_question_id": parent_question_id,
    }
