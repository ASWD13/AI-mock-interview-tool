"""Score aggregator — session-level scoring (§10)."""

from typing import Dict, Any, List


def update_session_scores(
    state: Dict[str, Any],
    eval_result: Dict[str, Any],
    audio_scores: Dict[str, Any],
    vision_scores: Dict[str, Any],
) -> Dict[str, Any]:
    """Update rolling session scores after each answer.

    Rolling average formula (§9):
    session.score = 0.7 * session.score + 0.3 * answer.score
    """
    # Technical score update
    correctness = eval_result.get("correctness", 0.5)
    state["technical_score"] = 0.7 * state.get("technical_score", 0.5) + 0.3 * correctness

    # Communication score (based on clarity)
    clarity = audio_scores.get("clarity", 0.65)
    state["communication_score"] = 0.7 * state.get("communication_score", 0.5) + 0.3 * clarity

    # Confidence score
    confidence = audio_scores.get("confidence", 0.65)
    state["confidence_score"] = 0.7 * state.get("confidence_score", 0.5) + 0.3 * confidence

    # Engagement score
    engagement = vision_scores.get("engagement", 0.65)
    state["engagement_score"] = 0.7 * state.get("engagement_score", 0.5) + 0.3 * engagement

    return state


def compute_final_scores(answers) -> Dict[str, float]:
    """Compute final session scores from all answers.

    Implements the exact formulas from §10:
    - Per-dimension arithmetic mean across all answers
    - Weighted final score
    - Rating assignment
    """
    if not answers:
        return {
            "technical_score": 0.0,
            "depth_score": 0.0,
            "communication_score": 0.0,
            "confidence_score": 0.0,
            "engagement_score": 0.0,
            "final_score": 0.0,
            "rating": "Needs Improvement",
        }

    n = len(answers)

    # Per answer scores
    correctness_scores = []
    depth_scores = []
    communication_scores = []
    confidence_scores = []
    engagement_scores = []

    for answer in answers:
        correctness_scores.append(answer.correctness or 0.0)
        depth_scores.append(answer.depth or 0.0)

        # Audio scores
        audio = answer.audio_scores if isinstance(answer.audio_scores, dict) else {}
        comm = audio.get("clarity", 0.65)
        conf = audio.get("confidence", 0.65)

        # Heuristics for missing data (§10)
        if not audio:
            conf = (answer.correctness or 0.0) * 0.8  # proxy
            comm = 0.65

        communication_scores.append(comm)
        confidence_scores.append(conf)

        # Vision scores
        vision = answer.vision_scores if isinstance(answer.vision_scores, dict) else {}
        eng = vision.get("engagement", 0.65)  # neutral default if missing
        engagement_scores.append(eng)

    # Session aggregation (arithmetic mean)
    technical_score = sum(correctness_scores) / n
    depth_score = sum(depth_scores) / n
    communication_score = sum(communication_scores) / n
    confidence_score = sum(confidence_scores) / n
    engagement_score = sum(engagement_scores) / n

    # Final score (weighted per §10)
    final_score = (
        technical_score * 0.40 +
        depth_score * 0.20 +
        communication_score * 0.15 +
        confidence_score * 0.15 +
        engagement_score * 0.10
    )

    # Rating assignment
    if final_score >= 0.80:
        rating = "Excellent"
    elif final_score >= 0.65:
        rating = "Good"
    elif final_score >= 0.50:
        rating = "Average"
    else:
        rating = "Needs Improvement"

    # Floor at 0.1, cap at 1.0 (§15)
    def clamp(v):
        return max(0.1, min(1.0, v))

    return {
        "technical_score": clamp(technical_score),
        "depth_score": clamp(depth_score),
        "communication_score": clamp(communication_score),
        "confidence_score": clamp(confidence_score),
        "engagement_score": clamp(engagement_score),
        "final_score": clamp(final_score),
        "rating": rating,
    }
