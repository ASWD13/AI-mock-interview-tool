"""Audio feature extraction helpers using librosa."""

import numpy as np
from typing import Dict, Any, Optional


def extract_audio_features(audio_path: str) -> Dict[str, Any]:
    """Extract audio features from a WAV file using librosa.

    Features:
    - RMS energy (loudness proxy)
    - Zero-crossing rate
    - Spectral centroid
    - Duration
    - Pause detection
    """
    try:
        import librosa

        y, sr = librosa.load(audio_path, sr=16000)
        duration = librosa.get_duration(y=y, sr=sr)

        # RMS energy
        rms = librosa.feature.rms(y=y)
        rms_mean = float(np.mean(rms))
        rms_std = float(np.std(rms))

        # Zero-crossing rate
        zcr = librosa.feature.zero_crossing_rate(y)
        zcr_mean = float(np.mean(zcr))

        # Spectral centroid
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        sc_mean = float(np.mean(spectral_centroid))

        # Pause detection (simple: segments where RMS < threshold)
        rms_frames = rms[0]
        threshold = rms_mean * 0.3
        silent_frames = np.sum(rms_frames < threshold)
        total_frames = len(rms_frames)
        pause_ratio = silent_frames / max(total_frames, 1)

        return {
            "duration": duration,
            "rms_mean": rms_mean,
            "rms_std": rms_std,
            "zcr_mean": zcr_mean,
            "spectral_centroid_mean": sc_mean,
            "pause_ratio": float(pause_ratio),
            "pause_count": int(silent_frames),
        }

    except ImportError:
        return {"duration": 0, "rms_mean": 0.5, "rms_std": 0.1, "zcr_mean": 0, "spectral_centroid_mean": 0, "pause_ratio": 0.1, "pause_count": 0}
    except Exception as e:
        print(f"Audio feature extraction failed: {e}")
        return {"duration": 0, "rms_mean": 0.5, "rms_std": 0.1, "zcr_mean": 0, "spectral_centroid_mean": 0, "pause_ratio": 0.1, "pause_count": 0}
