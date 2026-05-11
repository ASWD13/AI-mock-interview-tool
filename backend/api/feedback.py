"""Feedback API endpoint — works without PostgreSQL."""

from fastapi import APIRouter, HTTPException
from uuid import UUID
from typing import Dict, Any
from datetime import datetime

from backend.models.schemas import (
    FeedbackReportResponse, ScoringOutput, FeedbackOutput,
    TechnicalFeedbackItem, ObservationItem
)

router = APIRouter()

# In-memory feedback cache
_feedback_cache: Dict[str, Dict[str, Any]] = {}


@router.get("/interview/{session_id}/feedback", response_model=FeedbackReportResponse)
async def get_feedback(session_id: UUID):
    """Get feedback report for a completed session."""
    sid = str(session_id)

    # Check cache
    if sid in _feedback_cache:
        return _feedback_cache[sid]

    # Get session state and answers from interview module
    from backend.api.interview import _sessions, _answers, _profiles

    state = _sessions.get(sid)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    answers = _answers.get(sid, [])
    profile = _profiles.get(state.get("candidate_id", ""), {})

    # Compute scores from answers
    if answers:
        n = len(answers)
        tech_scores = [a.get("correctness", 0.5) for a in answers]
        depth_scores = [a.get("depth", 0.5) for a in answers]
        comm_scores = [a.get("audio_scores", {}).get("clarity", 0.65) for a in answers]
        conf_scores = [a.get("audio_scores", {}).get("confidence", 0.65) for a in answers]
        eng_scores = [a.get("vision_scores", {}).get("engagement", 0.65) for a in answers]

        technical_score = sum(tech_scores) / n
        depth_score = sum(depth_scores) / n
        communication_score = sum(comm_scores) / n
        confidence_score = sum(conf_scores) / n
        engagement_score = sum(eng_scores) / n
    else:
        technical_score = state.get("technical_score", 0.5)
        depth_score = 0.5
        communication_score = state.get("communication_score", 0.5)
        confidence_score = state.get("confidence_score", 0.5)
        engagement_score = state.get("engagement_score", 0.5)

    # Final score (§10 formula)
    final_score = (
        technical_score * 0.40 +
        depth_score * 0.20 +
        communication_score * 0.15 +
        confidence_score * 0.15 +
        engagement_score * 0.10
    )

    # Rating
    if final_score >= 0.80:
        rating = "Excellent"
    elif final_score >= 0.65:
        rating = "Good"
    elif final_score >= 0.50:
        rating = "Average"
    else:
        rating = "Needs Improvement"

    # Clamp
    def clamp(v): return max(0.1, min(1.0, v))

    scoring = ScoringOutput(
        session_id=session_id,
        technical_score=clamp(technical_score),
        depth_score=clamp(depth_score),
        communication_score=clamp(communication_score),
        confidence_score=clamp(confidence_score),
        engagement_score=clamp(engagement_score),
        final_score=clamp(final_score),
        rating=rating,
    )

    # Generate feedback content
    role = state.get("role", "Software Developer")
    skills = profile.get("skills", [])
    strong = state.get("strong_topics", [])
    weak = state.get("weak_topics", [])

    tech_feedback = []
    if weak:
        for topic in weak[:3]:
            tech_feedback.append(TechnicalFeedbackItem(
                topic=topic,
                observation=f"You showed some uncertainty when discussing {topic}.",
                suggestion=f"Practice {topic} concepts with hands-on projects and review documentation.",
            ))
    if strong:
        for topic in strong[:2]:
            tech_feedback.append(TechnicalFeedbackItem(
                topic=topic,
                observation=f"You demonstrated strong knowledge of {topic}.",
                suggestion=f"Continue deepening your expertise in {topic} and consider mentoring others.",
            ))

    comm_feedback = []
    if communication_score < 0.6:
        comm_feedback.append(ObservationItem(
            observation="Your answers could benefit from more structure and clarity.",
            suggestion="Use the STAR method (Situation, Task, Action, Result) to organize your responses.",
        ))
    else:
        comm_feedback.append(ObservationItem(
            observation="You communicated your ideas clearly and concisely.",
            suggestion="Continue practicing structured responses to maintain this strength.",
        ))

    behavioral_feedback = []
    if confidence_score < 0.5:
        behavioral_feedback.append(ObservationItem(
            observation="You appeared somewhat uncertain during the interview.",
            suggestion="Practice mock interviews to build confidence. Record yourself and review.",
        ))

    strengths = []
    if technical_score >= 0.6:
        strengths.append(f"Strong technical foundation in {role}-related concepts")
    if communication_score >= 0.6:
        strengths.append("Clear and articulate communication style")
    if confidence_score >= 0.6:
        strengths.append("Confident delivery and composed demeanor")
    if len(skills) >= 5:
        strengths.append(f"Diverse skill set spanning {len(skills)} technologies")
    if not strengths:
        strengths.append("Willingness to engage with challenging questions")

    improvement_plan = [
        f"Focus on strengthening weak areas: {', '.join(weak[:3]) if weak else 'fundamentals'}",
        "Practice explaining concepts out loud — clarity improves with repetition",
        "Build 2-3 small projects using technologies you're less familiar with",
        "Do weekly mock interviews to build confidence and reduce hesitation",
        f"Target roles: {', '.join(profile.get('possible_roles', [role])[:3])}",
    ]

    # Try LLM-powered feedback in background (but return immediately)
    feedback = FeedbackOutput(
        session_id=session_id,
        overall_rating=rating,
        technical_feedback=tech_feedback,
        communication_feedback=comm_feedback,
        behavioral_feedback=behavioral_feedback,
        improvement_plan=improvement_plan,
        strengths=strengths,
        generated_at=datetime.utcnow(),
    )

    result = FeedbackReportResponse(scoring=scoring, feedback=feedback)

    # Cache
    _feedback_cache[sid] = result

    return result
