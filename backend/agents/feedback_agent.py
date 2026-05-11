"""Feedback agent — generates detailed coaching feedback (§8.11, §9)."""

import json
from uuid import UUID
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.config import get_settings
from backend.models.db_models import (
    InterviewSessionDB, AnswerDB, QuestionDB,
    CandidateProfileDB, ScoringOutputDB, FeedbackOutputDB
)
from backend.scoring.score_aggregator import compute_final_scores
from backend.prompts.feedback_gen import get_feedback_gen_prompt


async def generate_feedback_report(session_id: UUID, db: AsyncSession):
    """Generate complete feedback report for a session.

    Steps per §8.11:
    1. Compute per-dimension rolling averages
    2. Compute final_score using formula from §10
    3. Assign rating
    4. Call FeedbackAgent with Groq GPT OSS 120B
    5. Store results in DB
    """
    settings = get_settings()

    # Load session
    result = await db.execute(
        select(InterviewSessionDB).where(InterviewSessionDB.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # Load all answers
    answers_result = await db.execute(
        select(AnswerDB).where(AnswerDB.session_id == session_id)
    )
    answers = answers_result.scalars().all()

    # Load all questions
    questions_result = await db.execute(
        select(QuestionDB).where(QuestionDB.session_id == session_id)
    )
    questions = questions_result.scalars().all()
    question_map = {str(q.question_id): q for q in questions}

    # Load candidate profile
    profile_result = await db.execute(
        select(CandidateProfileDB).where(CandidateProfileDB.candidate_id == session.candidate_id)
    )
    profile = profile_result.scalar_one_or_none()

    # Compute scores per §10
    scoring = compute_final_scores(answers)

    # Store scoring output
    scoring_db = ScoringOutputDB(
        session_id=session_id,
        technical_score=scoring["technical_score"],
        depth_score=scoring["depth_score"],
        communication_score=scoring["communication_score"],
        confidence_score=scoring["confidence_score"],
        engagement_score=scoring["engagement_score"],
        final_score=scoring["final_score"],
        rating=scoring["rating"],
    )
    db.add(scoring_db)

    # Build transcript for feedback prompt
    transcript_parts = []
    for answer in answers:
        q = question_map.get(str(answer.question_id))
        q_text = q.text if q else "Unknown question"
        transcript_parts.append(f"Q: {q_text}\nA: {answer.transcript or 'No answer'}")
    full_transcript = "\n\n".join(transcript_parts)

    profile_summary = ""
    if profile:
        profile_summary = f"Name: {profile.name}, Skills: {', '.join(profile.skills or [])}, Role: {session.role}"

    # Generate feedback with LLM
    feedback_data = await _generate_llm_feedback(
        profile_summary=profile_summary,
        transcript=full_transcript,
        scoring=scoring,
        settings=settings,
    )

    # Store feedback
    feedback_db = FeedbackOutputDB(
        session_id=session_id,
        overall_rating=feedback_data.get("overall_rating", scoring["rating"]),
        technical_feedback=feedback_data.get("technical_feedback", []),
        communication_feedback=feedback_data.get("communication_feedback", []),
        behavioral_feedback=feedback_data.get("behavioral_feedback", []),
        improvement_plan=feedback_data.get("improvement_plan", []),
        strengths=feedback_data.get("strengths", []),
        generated_at=datetime.utcnow(),
    )
    db.add(feedback_db)

    # Update session
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    session.technical_score = scoring["technical_score"]
    session.communication_score = scoring["communication_score"]
    session.confidence_score = scoring["confidence_score"]
    session.engagement_score = scoring["engagement_score"]

    await db.commit()


async def _generate_llm_feedback(
    profile_summary: str,
    transcript: str,
    scoring: Dict[str, float],
    settings,
) -> Dict[str, Any]:
    """Generate feedback using Groq GPT OSS 120B."""
    if not settings.groq_api_key:
        return _template_feedback(scoring)

    try:
        from groq import AsyncGroq

        client = AsyncGroq(api_key=settings.groq_api_key)

        system_prompt, user_prompt = get_feedback_gen_prompt(
            profile_summary=profile_summary,
            transcript=transcript[:4000],  # Truncate to avoid token limit
            tech_score=scoring["technical_score"],
            comm_score=scoring["communication_score"],
            conf_score=scoring["confidence_score"],
            eng_score=scoring["engagement_score"],
        )

        response = await client.chat.completions.create(
            model=settings.groq_llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=2048,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        print(f"LLM feedback generation failed: {e}")
        return _template_feedback(scoring)


def _template_feedback(scoring: Dict[str, float]) -> Dict[str, Any]:
    """Template-based fallback feedback for GPT failure."""
    rating = scoring.get("rating", "Average")
    tech = scoring.get("technical_score", 0.5)
    comm = scoring.get("communication_score", 0.5)

    return {
        "overall_rating": rating,
        "technical_feedback": [
            {
                "topic": "Technical Knowledge",
                "observation": f"Your technical score was {tech:.0%}.",
                "suggestion": "Review core concepts and practice explaining them clearly."
            }
        ],
        "communication_feedback": [
            {
                "observation": f"Your communication clarity was {comm:.0%}.",
                "suggestion": "Practice articulating your thoughts in a structured manner."
            }
        ],
        "behavioral_feedback": [
            {
                "observation": "Your responses showed adequate professionalism.",
                "suggestion": "Use the STAR method for behavioral questions."
            }
        ],
        "improvement_plan": [
            "Practice coding problems daily on LeetCode or HackerRank.",
            "Record yourself answering mock interview questions to improve delivery.",
            "Study system design patterns for your target role."
        ],
        "strengths": [
            f"Demonstrated {'strong' if tech >= 0.7 else 'developing'} technical knowledge.",
            f"Maintained {'good' if comm >= 0.6 else 'adequate'} communication throughout."
        ],
    }
