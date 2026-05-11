"""Vision feature extraction helpers using MediaPipe/DeepFace."""

import cv2
import numpy as np
from typing import Dict, Any, Optional


def extract_face_landmarks(frame) -> Dict[str, Any]:
    """Extract face landmarks using MediaPipe FaceMesh.

    Args:
        frame: OpenCV BGR image

    Returns:
        Dict with landmark data, face_detected flag
    """
    try:
        import mediapipe as mp

        mp_face_mesh = mp.solutions.face_mesh
        face_mesh = mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
        )

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)
        face_mesh.close()

        if not results.multi_face_landmarks:
            return {"face_detected": False}

        landmarks = results.multi_face_landmarks[0].landmark
        return {
            "face_detected": True,
            "landmark_count": len(landmarks),
            "nose_tip": {"x": landmarks[1].x, "y": landmarks[1].y, "z": landmarks[1].z},
        }

    except ImportError:
        return {"face_detected": False}
    except Exception:
        return {"face_detected": False}


def analyze_emotion(frame) -> Dict[str, Any]:
    """Analyze facial emotion using DeepFace.

    Args:
        frame: OpenCV BGR image

    Returns:
        Dict with dominant_emotion and emotion scores
    """
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

        return {
            "dominant_emotion": result.get("dominant_emotion", "neutral"),
            "emotions": result.get("emotion", {}),
        }

    except ImportError:
        return {"dominant_emotion": "neutral", "emotions": {}}
    except Exception:
        return {"dominant_emotion": "neutral", "emotions": {}}
