# config.py
from dataclasses import dataclass

@dataclass
class Config:
    """Configuration parameters for drowsiness detection"""
    EYE_AR_THRESH: float = 0.15
    EYE_AR_CONSEC_FRAMES: int = 30
    MOUTH_AR_THRESH: float = 1.35
    FACE_MESH_CONFIDENCE: float = 0.5
    HEAD_POSE_THRESHOLD: float = 10.0