"""Job recommender — embedding similarity + skill overlap (§8.3, §12)."""

import json
import os
from typing import Dict, Any, List, Optional
from backend.config import get_settings
from backend.models.schemas import JobRecommendation


async def get_job_recommendations(
    profile_embedding: Optional[List[float]],
    skills: List[str],
    possible_roles: List[str],
    experience_level: Optional[str],
    limit: int = 5,
) -> List[JobRecommendation]:
    """Get job recommendations using ChromaDB semantic search + skill overlap reranking.

    Implements §12 ranking formula:
    1. Semantic retrieval from ChromaDB (top 20)
    2. Re-rank by skill overlap: match_score = 0.5 * semantic_similarity + 0.5 * coverage
    3. Compute why_matched + missing_skills deterministically
    """
    try:
        return await _chroma_recommendations(
            profile_embedding, skills, possible_roles, experience_level, limit
        )
    except Exception as e:
        print(f"ChromaDB recommendations failed: {e}")
        return _fallback_recommendations(skills, possible_roles, experience_level, limit)


async def _chroma_recommendations(
    profile_embedding, skills, possible_roles, experience_level, limit
) -> List[JobRecommendation]:
    """ChromaDB-based recommendations with semantic + skill overlap."""
    from backend.utils.chroma_client import chroma_client

    collection = chroma_client.get_collection("jobs")

    # Query with profile embedding or text
    query_params = {}
    if profile_embedding:
        query_params["query_embeddings"] = [profile_embedding]
    else:
        query_text = f"{' '.join(possible_roles)} {' '.join(skills)}"
        query_params["query_texts"] = [query_text]

    query_params["n_results"] = 20

    # Optional filter by experience level
    if experience_level:
        query_params["where"] = {"experience_level": experience_level}

    try:
        results = collection.query(**query_params)
    except Exception:
        # Retry without filter
        query_params.pop("where", None)
        results = collection.query(**query_params)

    if not results or not results.get("documents") or not results["documents"][0]:
        return _fallback_recommendations(skills, possible_roles, experience_level, limit)

    # Re-rank by skill overlap
    jobs = []
    distances = results.get("distances", [[]])[0]
    documents = results["documents"][0]
    metadatas = results.get("metadatas", [[]])[0]
    ids = results.get("ids", [[]])[0]

    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        job_skills = meta.get("required_skills", "").split(",") if meta.get("required_skills") else []
        job_skills = [s.strip() for s in job_skills if s.strip()]

        # Skill overlap
        candidate_set = set(s.lower() for s in skills)
        job_set = set(s.lower() for s in job_skills)
        overlap = len(candidate_set & job_set)
        coverage = overlap / max(len(job_set), 1)

        # Semantic similarity (convert distance to similarity)
        semantic_sim = max(0, 1 - dist) if dist else 0.5

        # Match score per §12
        match_score = 0.5 * semantic_sim + 0.5 * coverage

        # Why matched + missing skills (deterministic per §12)
        why_matched = [s for s in skills if s.lower() in job_set]
        missing_skills = [s for s in job_skills if s.lower() not in candidate_set]

        jobs.append(JobRecommendation(
            job_id=ids[i] if i < len(ids) else str(i),
            job_title=meta.get("job_title", "Unknown"),
            company=meta.get("company", "Unknown"),
            location=meta.get("location", "Remote"),
            required_skills=[s.strip() for s in job_skills],
            match_score=round(match_score, 2),
            why_matched=why_matched[:5],
            missing_skills=missing_skills[:5],
        ))

    # Sort descending, take top limit
    jobs.sort(key=lambda j: j.match_score, reverse=True)
    return jobs[:limit]


def _fallback_recommendations(
    skills: List[str],
    possible_roles: List[str],
    experience_level: Optional[str],
    limit: int = 5,
) -> List[JobRecommendation]:
    """Fallback: load jobs_dataset.json, compute skill overlap only."""
    data_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "jobs_dataset.json")

    try:
        with open(data_path, "r") as f:
            jobs_data = json.load(f)
    except FileNotFoundError:
        return []

    candidate_set = set(s.lower() for s in skills)
    scored_jobs = []

    for job in jobs_data:
        job_skills = [s.lower() for s in job.get("required_skills", [])]
        overlap = len(candidate_set & set(job_skills))
        coverage = overlap / max(len(job_skills), 1)

        why_matched = [s for s in skills if s.lower() in set(job_skills)]
        missing = [s for s in job.get("required_skills", []) if s.lower() not in candidate_set]

        scored_jobs.append(JobRecommendation(
            job_id=job.get("job_id", ""),
            job_title=job.get("job_title", ""),
            company=job.get("company", ""),
            location=job.get("location", "Remote"),
            required_skills=job.get("required_skills", []),
            match_score=round(coverage, 2),
            why_matched=why_matched[:5],
            missing_skills=missing[:5],
        ))

    scored_jobs.sort(key=lambda j: j.match_score, reverse=True)
    return scored_jobs[:limit]
