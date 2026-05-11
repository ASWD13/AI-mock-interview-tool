"""Celery async tasks for audio/video processing (§8.7, §8.8)."""

from celery import Celery
from backend.config import get_settings

settings = get_settings()

celery_app = Celery(
    "iphipi",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=120,  # 2 min timeout
    task_soft_time_limit=90,
)


@celery_app.task(name="process_audio", bind=True, max_retries=3)
def process_audio(self, audio_path: str, answer_id: str, session_id: str):
    """Async task: process audio file for STT + scoring.

    Steps:
    1. Groq Whisper STT
    2. librosa feature extraction
    3. Compute heuristic scores
    4. Update Answer.audio_scores in DB
    """
    import asyncio
    from backend.services.audio_analyzer import analyze_audio

    try:
        result = asyncio.run(analyze_audio(audio_path))
        # In production, update DB here
        return {
            "answer_id": answer_id,
            "transcript": result.get("transcript", ""),
            "audio_scores": result.get("audio_scores", {}),
            "duration": result.get("duration", 0),
        }
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@celery_app.task(name="process_vision", bind=True, max_retries=3)
def process_vision(self, frame_b64: str, answer_id: str, session_id: str):
    """Async task: process video frame for engagement scoring.

    Steps:
    1. MediaPipe FaceMesh
    2. DeepFace emotion
    3. Groq Llama 4 Scout VQA
    4. Blend scores
    5. Update Answer.vision_scores in DB
    """
    import asyncio
    from backend.services.vision_analyzer import analyze_vision

    try:
        result = asyncio.run(analyze_vision(frame_b64))
        return {
            "answer_id": answer_id,
            "vision_scores": result,
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
