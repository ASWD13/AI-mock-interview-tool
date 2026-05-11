"""Vision analyzer — MediaPipe + DeepFace + Groq Llama 4 Scout (§8.8)."""

import base64
import json
import numpy as np
from typing import Dict, Any
from backend.config import get_settings


async def analyze_vision(video_frame_b64: str) -> Dict[str, Any]:
    """Analyze video frame for engagement, eye contact, and stress.

    Steps per §8.8:
    1. OpenCV decode → MediaPipe FaceMesh → 468 landmarks
    2. Gaze estimation from eye landmark ratios
    3. DeepFace emotion analysis
    4. Optional: Groq Llama 4 Scout VQA (blended 0.5/0.5)
    5. Heuristics for final scores

    Args:
        video_frame_b64: Base64 encoded JPEG frame

    Returns:
        Dict with engagement, eye_contact, stress_indicator
    """
    settings = get_settings()

    # Default neutral scores
    scores = {
        "engagement": 0.65,
        "eye_contact": 0.65,
        "stress_indicator": 0.3,
    }

    # Decode frame
    try:
        import cv2
        frame_bytes = base64.b64decode(video_frame_b64)
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            return scores
    except Exception as e:
        print(f"Frame decode failed: {e}")
        return scores

    # Step 1-2: MediaPipe FaceMesh + gaze estimation
    mp_scores = _mediapipe_analysis(frame)
    scores.update(mp_scores)

    # Step 3: DeepFace emotion
    df_scores = _deepface_analysis(frame)
    if df_scores:
        scores["stress_indicator"] = df_scores.get("stress_indicator", scores["stress_indicator"])
        # Blend engagement with emotion context
        if df_scores.get("dominant_emotion") in ("happy", "neutral"):
            scores["engagement"] = min(1.0, scores["engagement"] + 0.1)
        elif df_scores.get("dominant_emotion") in ("fear", "angry", "sad"):
            scores["engagement"] = max(0.1, scores["engagement"] - 0.1)

    # Step 4: Groq Llama 4 Scout VQA (optional, blended 0.5/0.5)
    if settings.groq_api_key:
        try:
            vqa_scores = await _llama_scout_vqa(video_frame_b64, settings)
            if vqa_scores:
                scores["engagement"] = 0.5 * scores["engagement"] + 0.5 * vqa_scores.get("engagement", scores["engagement"])
                scores["stress_indicator"] = 0.5 * scores["stress_indicator"] + 0.5 * vqa_scores.get("stress", scores["stress_indicator"])
        except Exception as e:
            print(f"Llama 4 Scout VQA failed: {e}")

    # Clamp scores
    for key in scores:
        scores[key] = round(max(0.0, min(1.0, scores[key])), 2)

    return scores


def _mediapipe_analysis(frame) -> Dict[str, float]:
    """MediaPipe FaceMesh analysis for gaze estimation."""
    try:
        import mediapipe as mp

        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
        )

        results = face_mesh.process(frame)
        face_mesh.close()

        if not results.multi_face_landmarks:
            return {"eye_contact": 0.3, "engagement": 0.4}

        landmarks = results.multi_face_landmarks[0].landmark

        # Gaze estimation from eye landmarks (iris tracking)
        # Left iris: landmarks 468-472, Right iris: 473-477
        # Eye corners: left eye inner 133, outer 33; right eye inner 362, outer 263
        try:
            left_iris = landmarks[468]
            right_iris = landmarks[473]
            nose_tip = landmarks[1]

            # Simple gaze heuristic: if iris centers are close to center of eye
            left_eye_inner = landmarks[133]
            left_eye_outer = landmarks[33]
            left_center_x = (left_eye_inner.x + left_eye_outer.x) / 2
            left_offset = abs(left_iris.x - left_center_x)

            # Smaller offset = more center gaze = more eye contact
            eye_contact = max(0.1, 1.0 - left_offset * 10)
        except (IndexError, AttributeError):
            eye_contact = 0.5

        # Engagement heuristic
        engagement = eye_contact * 0.8 + 0.2  # Base engagement from eye contact

        return {
            "eye_contact": round(eye_contact, 2),
            "engagement": round(engagement, 2),
        }

    except ImportError:
        return {"eye_contact": 0.65, "engagement": 0.65}
    except Exception as e:
        print(f"MediaPipe analysis failed: {e}")
        return {"eye_contact": 0.65, "engagement": 0.65}


def _deepface_analysis(frame) -> Dict[str, Any]:
    """DeepFace emotion analysis."""
    try:
        from deepface import DeepFace

        result = DeepFace.analyze(
            frame,
            actions=["emotion"],
            enforce_detection=False,
            silent=True,
        )

        if isinstance(result, list):
            result = result[0]

        dominant_emotion = result.get("dominant_emotion", "neutral")

        # Stress indicator: proportion of nervous/fearful emotions
        emotions = result.get("emotion", {})
        stress_emotions = emotions.get("fear", 0) + emotions.get("angry", 0) + emotions.get("sad", 0)
        total_emotion = sum(emotions.values()) if emotions else 100
        stress_indicator = stress_emotions / max(total_emotion, 1)

        return {
            "dominant_emotion": dominant_emotion,
            "stress_indicator": round(stress_indicator, 2),
        }

    except ImportError:
        return None
    except Exception as e:
        print(f"DeepFace analysis failed: {e}")
        return None


async def _llama_scout_vqa(frame_b64: str, settings) -> Dict[str, float]:
    """Groq Llama 4 Scout frame-level VQA."""
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.groq_api_key)

    response = await client.chat.completions.create(
        model=settings.groq_vision_model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Rate the candidate's engagement and stress level (0-1 each) from this webcam frame. Return JSON: {\"engagement\": 0.0, \"stress\": 0.0}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{frame_b64}"
                        }
                    }
                ]
            }
        ],
        temperature=0.2,
        max_tokens=128,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    return result
