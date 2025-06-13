# detectors/facial_landmark_detector.py
import mediapipe as mp
from config import Config

class FacialLandmarkDetector:
    """Handles facial landmark detection using MediaPipe"""
    def __init__(self, config: Config):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            min_detection_confidence=config.FACE_MESH_CONFIDENCE,
            min_tracking_confidence=config.FACE_MESH_CONFIDENCE,
            refine_landmarks=True
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec = self.mp_drawing.DrawingSpec(thickness=1, circle_radius=1)
        
        # Enhanced landmark indices
        self.LEFT_EYE = [
            33,
            160,
            158,
            133,
            153,
            144,
        ]

        self.RIGHT_EYE = [
            362,
            385,
            387,
            263,
            373,
            380,
        ]

        # 4 level bottom lip indices
        # self.MOUTH = [
        #     78,
        #     81,
        #     13,
        #     311,
        #     308,
        #     402,
        #     14,
        #     178,
        # ]

        # 3 level bottom lip indices
        self.MOUTH = [
            62,
            41,
            12,
            271,
            292,
            403,
            15,
            179,
        ]