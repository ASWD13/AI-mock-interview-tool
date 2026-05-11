"""Resume upload and parsing API endpoint."""

from fastapi import APIRouter, UploadFile, File, HTTPException
from uuid import uuid4

from backend.models.schemas import ResumeUploadResponse, CandidateProfile
from backend.services.resume_parser import parse_resume
from backend.services.skill_extractor import extract_skills
from backend.services.role_inferrer import infer_role
from backend.utils.redis_client import redis_client
from backend.utils.file_utils import detect_file_type

router = APIRouter()


@router.post("/resume/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
):
    """Upload and parse a resume (PDF/DOCX/TXT)."""
    content = await file.read()
    filename = file.filename or "resume.txt"

    # Detect file type
    file_type = detect_file_type(filename, content)
    if file_type not in ("pdf", "docx", "txt"):
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, DOCX, or TXT.")

    # Parse resume text
    try:
        raw_text = await parse_resume(content, file_type)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse resume: {str(e)}")

    if not raw_text or len(raw_text.strip()) < 50:
        raise HTTPException(status_code=422, detail="Could not extract sufficient text from resume. Please upload a text-based resume.")

    # Extract skills
    skills, skill_categories = extract_skills(raw_text)

    # Infer role + seniority
    candidate_id = uuid4()
    try:
        role_data = await infer_role(skills, raw_text)
    except Exception as e:
        print(f"Role inference error: {e}")
        role_data = {
            "possible_roles": [],
            "experience_level": "junior",
            "focus_areas": skills[:5] if skills else [],
            "weak_areas": []
        }

    # Generate profile embedding (optional — may be slow on first run)
    embedding = None
    try:
        import os
        os.environ["USE_TF"] = "0"
        os.environ["TRANSFORMERS_NO_TF"] = "1"
        from ml.embeddings.embed_utils import generate_embedding
        embedding = generate_embedding(raw_text[:2000])
    except Exception as e:
        print(f"Embedding generation skipped: {e}")

    # Build profile
    profile = CandidateProfile(
        candidate_id=candidate_id,
        name=role_data.get("name"),
        email=role_data.get("email"),
        experience_level=role_data.get("experience_level", "junior"),
        years_experience=role_data.get("years_experience"),
        skills=skills,
        skill_categories=skill_categories,
        projects=role_data.get("projects", []),
        education=role_data.get("education", []),
        certifications=role_data.get("certifications", []),
        possible_roles=role_data.get("possible_roles", []),
        focus_areas=role_data.get("focus_areas", skills[:5] if skills else []),
        weak_areas=role_data.get("weak_areas", []),
        profile_embedding=embedding,
    )

    # Store in Redis (optional — graceful failure)
    try:
        await redis_client.set_json(
            f"candidate:{candidate_id}:profile",
            profile.model_dump(mode="json"),
            expire=7200
        )
    except Exception as e:
        print(f"Redis profile store skipped: {e}")

    # Share with interview module's in-memory store
    from backend.api.interview import store_profile
    store_profile(str(candidate_id), profile.model_dump(mode="json"))

    # Store in DB (optional — graceful failure)
    try:
        from backend.models.database import get_db
        from backend.models.db_models import CandidateProfileDB

        async for db in get_db():
            db_profile = CandidateProfileDB(
                candidate_id=candidate_id,
                name=profile.name,
                email=profile.email,
                experience_level=profile.experience_level,
                years_experience=profile.years_experience,
                skills=profile.skills,
                skill_categories=profile.skill_categories,
                projects=[p.model_dump() for p in profile.projects] if profile.projects else [],
                education=[e.model_dump() for e in profile.education] if profile.education else [],
                certifications=profile.certifications,
                possible_roles=profile.possible_roles,
                focus_areas=profile.focus_areas,
                weak_areas=profile.weak_areas,
                profile_embedding=embedding,
                raw_text=raw_text,
            )
            db.add(db_profile)
            await db.commit()
            break
    except Exception as e:
        print(f"DB profile store skipped: {e}")

    return ResumeUploadResponse(candidate_id=candidate_id, profile=profile)
