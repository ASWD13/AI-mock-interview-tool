"""Job recommendations API endpoint — works without PostgreSQL."""

from fastapi import APIRouter, HTTPException, Query
from uuid import UUID
from typing import List

from backend.models.schemas import JobRecommendation
from backend.services.job_recommender import get_job_recommendations

router = APIRouter()


@router.get("/jobs/recommendations", response_model=List[JobRecommendation])
async def get_recommendations(
    candidate_id: UUID = Query(...),
    limit: int = Query(default=5, le=10),
):
    """Get job recommendations based on candidate profile."""
    cid = str(candidate_id)

    # Get profile from interview module's in-memory store
    from backend.api.interview import _profiles
    profile_data = _profiles.get(cid)

    if not profile_data:
        # Try Redis
        try:
            from backend.utils.redis_client import redis_client
            profile_data = await redis_client.get_json(f"candidate:{cid}:profile")
        except Exception:
            pass

    if not profile_data:
        raise HTTPException(status_code=404, detail="Candidate not found. Upload a resume first.")

    recommendations = await get_job_recommendations(
        profile_embedding=profile_data.get("profile_embedding"),
        skills=profile_data.get("skills", []),
        possible_roles=profile_data.get("possible_roles", []),
        experience_level=profile_data.get("experience_level"),
        limit=limit,
    )

    return recommendations
