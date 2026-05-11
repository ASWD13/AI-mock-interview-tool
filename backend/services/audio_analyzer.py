"""Audio analyzer — Groq Whisper STT + librosa features + heuristics (§8.7)."""

import os
import re
from typing import Dict, Any
from backend.config import get_settings


# Filler words for hesitation detection
FILLER_WORDS = {"um", "uh", "like", "you know", "basically", "actually", "literally", "so", "well", "hmm", "ah", "er"}


async def analyze_audio(audio_path: str) -> Dict[str, Any]:
    """Analyze audio file: STT + prosodic features + heuristics.

    Steps per §8.7:
    1. Groq Whisper Large v3 Turbo API → transcript
    2. librosa: RMS energy, zero-crossing, spectral features
    3. Heuristics: speaking_rate_wpm, hesitation_score, confidence_score, clarity_score

    Args:
        audio_path: Path to audio file (WAV/WEBM)

    Returns:
        Dict with transcript, audio_scores, duration
    """
    settings = get_settings()
    transcript = ""
    duration = 0.0

    # Step 1: STT via Groq Whisper
    if settings.groq_api_key:
        try:
            transcript = await _groq_stt(audio_path, settings)
        except Exception as e:
            print(f"Groq STT failed: {e}")

    # Step 2: librosa analysis
    rms_mean = 0.5
    try:
        import librosa
        import numpy as np

        y, sr = librosa.load(audio_path, sr=16000)
        duration = librosa.get_duration(y=y, sr=sr)

        # RMS energy
        rms = librosa.feature.rms(y=y)
        rms_mean = float(np.mean(rms))

        # Zero-crossing rate
        zcr = librosa.feature.zero_crossing_rate(y)
        zcr_mean = float(np.mean(zcr))

    except Exception as e:
        print(f"librosa analysis failed: {e}")

    # Step 3: Heuristics
    words = transcript.split()
    word_count = len(words)

    # speaking_rate_wpm
    speaking_rate_wpm = (word_count / (duration / 60)) if duration > 0 else 0

    # hesitation_score
    filler_count = sum(1 for w in words if w.lower().strip(".,!?") in FILLER_WORDS)
    pause_count = transcript.count("...") + transcript.count(",") // 3
    hesitation_score = (pause_count * 0.5 + filler_count) / max(word_count, 1)
    hesitation_score = min(1.0, hesitation_score)

    # confidence_score = normalize(RMS_mean)
    confidence_score = min(1.0, rms_mean * 5)  # Capped heuristic
    confidence_score = max(0.1, confidence_score)

    # clarity_score = 1 - hesitation_score
    clarity_score = max(0.1, 1 - hesitation_score)

    audio_scores = {
        "confidence": round(confidence_score, 2),
        "clarity": round(clarity_score, 2),
        "hesitation": round(hesitation_score, 2),
        "speaking_rate_wpm": round(speaking_rate_wpm, 1),
    }

    return {
        "transcript": transcript,
        "audio_scores": audio_scores,
        "duration": duration,
    }


async def _groq_stt(audio_path: str, settings) -> str:
    """Transcribe audio using Groq Whisper Large v3 Turbo API."""
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.groq_api_key)

    with open(audio_path, "rb") as audio_file:
        response = await client.audio.transcriptions.create(
            model=settings.groq_whisper_model,
            file=audio_file,
            response_format="text",
        )

    return str(response).strip()
