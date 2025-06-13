# analyzers/facial_metrics.py
import numpy as np
from scipy.spatial import distance as dist

class FacialMetricsAnalyzer:
    """Analyzes facial metrics like EAR and MAR"""
    @staticmethod
    def calculate_ear(landmarks, eye_indices):
        """Calculate eye aspect ratio using enhanced landmarks"""
        points = []
        for idx in eye_indices:
            point = landmarks.landmark[idx]
            points.append([point.x, point.y])
        
        points = np.array(points)
        A = dist.euclidean(points[1], points[5])
        B = dist.euclidean(points[2], points[4])
        C = dist.euclidean(points[0], points[3])
        
        ear = (A + B) / (2.0 * C)
        return ear

    @staticmethod
    def calculate_mar(landmarks, mouth_indices):
        """Calculate mouth aspect ratio using enhanced landmarks"""
        mouth_points = []
        for idx in mouth_indices:
            point = landmarks.landmark[idx]
            mouth_points.append([point.x, point.y])
            
        mouth_points = np.array(mouth_points)
        
        # Vertical distances between upper and lower lip points
        A = dist.euclidean(mouth_points[1], mouth_points[7])  # Left vertical
        B = dist.euclidean(mouth_points[2], mouth_points[6])  # Center vertical
        C = dist.euclidean(mouth_points[3], mouth_points[5])  # Right vertical
    
        # Horizontal distance between mouth corners
        D = dist.euclidean(mouth_points[0], mouth_points[4])  # Corner distance

        mar =  (A + B + C) / (2.0 * D)
        return mar