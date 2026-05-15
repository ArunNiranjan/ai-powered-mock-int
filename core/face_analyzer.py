"""
core/face_analyzer.py
MediaPipe + DeepFace engagement/emotion analyser.
Identical logic to the Flask backend - no web-framework dependency.
"""

import os
import time
import threading
import urllib.request

import cv2
import numpy as np
from scipy.spatial import distance

import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision as mp_vision

try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False

# Model download ---------------------
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "face_landmarker.task")

_MODEL_URL = (
"https://storage.googleapis.com/mediapipe-models/" 
"face_landmarker/face_landmarker/float16/1/face_landmarker.task"
)

def _ensure_model() -> bool:
    """Download the FaceLandmarker task model if not already present."""
    if os.path.exists(MODEL_PATH):
        return True
    try:
        urllib.request.urlretrieve(_MODEL_URL,_MODEL_PATH)
        return True
    except Exception:
        return False

def create_landmarker():
    """Create a FaceLandmarker instance; returns None on failure."""
    if not ensure_model():
        return None
    try:
        options = mp_vision.FaceLandmarkerOptions(
            base_options = mp_tasks.BaseOptions(model_asset_path=_MODEL_PATH), 
            running_mode= mp_vision.RunningMode.IMAGE,
            num_faces=1
        )
        return mp_vision.FaceLandmarker.create_from_options(options)
    except Exception:
        return None


LEFT_EYE  = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]
NOSE_TIP  = 1
CHIN      = 199
LEFT_EAR  = 234
RIGHT_EAR = 454

EMOTION_WEIGHTS = {
    "happy": 1.0, "surprise": 0.8, "neutral": 0.5,
    "angry": 0.2, "sad": 0.1, "fear": 0.3, "disgust": 0.2,
}


class FaceAnalyzer:
    """
    Computes engagement and emotion from raw BGR video frames.
    Thread-safe via an internal lock so it can be used from a
    streamlit-webrtc VideoProcessor running in a background thread.
    """

    def __init__(self) -> None:
        self.prev_center = None
        self.blink_count = 0
        self.start_time  = time.time()
        self.history: list[float] = []
        self.last_emotion = "neutral"
        self.frame_count = 0
        self.lock = threading.Lock()
        self.last_result: dict = {
            "status": "ok",
            "emotion": "neutral",
            "engagement_score": 0.5,
            "positivity_score": 0.5,
        }
        self._landmarker = _create_landmarker()

    # -- helpers
    def _ear(self, lm: dict, pts: list) -> float:
        A = distance.euclidean(lm[pts[1]], lm[pts[5]])
        B = distance.euclidean(lm[pts[2]], lm[pts[4]])
        C = distance.euclidean(lm[pts[0]], lm[pts[3]])
        return (A + B) / (2.0 * C)

    def _head_tilt_penalty(self, lm: dict) -> float:
        nose = lm[NOSE_TIP]; chin = lm[CHIN]
        le = lm[LEFT_EAR]; re = lm[RIGHT_EAR]
        ratio = abs(nose[1] - chin[1]) / (abs(le[0] - re[0]) + 1e-6)
        return -0.5 if ratio < 0.8 else 0.0

    def _engagement(self, emotion: str, bps: float, movement: float, tilt: float) -> float:
        e = EMOTION_WEIGHTS.get(emotion, 0.0)
        b = min(bps / 5.0, 1.0)
        m = max(1.0 - min(movement / 50.0, 1.0), 0.1)
        score = 0.5 * e + 0.2 * b + 0.1 * m + 0.2 * tilt
        return max(0.0, min(score, 1.0))

    # -- public
    def process_frame(self, frame: np.ndarray) -> dict | None:
        self.frame_count += 1
        if self.frame_count % 3 != 0:
            return None

        if self._landmarker is None:
            return {
                "status": "ok",
                "emotion": "neutral",
                "engagement_score": 0.5,
                "positivity_score": 0.5
            }
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = mp.Image(image_format= mp.ImageFormat.SRGB, data=rgb)
            results = self._landmarker.detect(mp_img)
            h, w = frame.shape[:2]
            movement = 0.0
            tilt = 0.0

            if results.face_landmarks:
                for fl in results.face_landmarks:
                    lm = {i: (l.x * w, l.y * h) for i, l in enumerate(fl)}
                    
                    left_ear = self._ear(lm, LEFT_EYE)
                    right_ear = self._ear(lm, RIGHT_EYE)
                    if (left_ear + right_ear) / 2 < 0.25:
                        self.blink_count += 1
                    
                    center = np.mean([lm[i] for i in range(468)], axis=0)
                    if self.prev_center is not None:
                        movement = float(np.linalg.norm(center - self.prev_center))
                    self.prev_center = center
                    tilt = self._head_tilt_penalty(lm)
                    break # first face only

            elapsed = time.time() - self.start_time
            bps = self.blink_count / elapsed if elapsed > 0 else 0
            if elapsed > 10:
                self.blink_count = 0
                self.start_time = time.time()

            # DeepFace - every 15 frames to avoid lag
            if self.frame_count % 15 == 0 and DEEPFACE_AVAILABLE:
                try:
                    res = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False, silent=True)
                    self.last_emotion = res[0]["dominant_emotion"]
                except Exception:
                    pass

            eng = self._engagement(self.last_emotion, bps, movement, tilt)
            self.history.append(eng)
            if len(self.history) > 5:
                self.history.pop(0)

            avg_eng = float(np.mean(self.history)) if self.history else 0.5
            pos_wt = {"happy": 1.0, "surprise": 0.8, "neutral": 0.8,
                      "sad": 0.3, "angry": 0.1, "fear": 0.2, "disgust": -0.1}
            positivity = 0.6 * pos_wt.get(self.last_emotion, 0.5) + 0.4 * avg_eng

            result = {
                "status": "ok",
                "emotion": self.last_emotion,
                "engagement_score": round(avg_eng, 3),
                "positivity_score": round(max(0.0, min(positivity, 1.0)), 3),
            }
            with self.lock:
                self.last_result = result
                return result

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_last_result(self) -> dict:
        with self.lock:
            return self.last_result.copy()