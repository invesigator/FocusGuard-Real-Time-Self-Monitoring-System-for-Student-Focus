import cv2
import numpy as np
from config import Config

class HeadPoseAnalyzer:
    """Analyzes head pose using facial landmarks"""
    def __init__(self, config: Config):
        self.config = config

    def analyze_head_pose(self, face_landmarks, image):
        """Process head pose estimation with accurate 3D projection"""
        img_h, img_w, _ = image.shape
        face_2d = []
        face_3d = []
        
        # Collect facial landmarks for pose estimation
        for idx, lm in enumerate(face_landmarks.landmark):
            if idx in [33, 263, 1, 61, 291, 199]:
                x, y = int(lm.x * img_w), int(lm.y * img_h)
                if idx == 1:  # Nose landmark
                    nose_2d = (lm.x * img_w, lm.y * img_h)
                    # Create two 3D points: one at the nose, one projected forward
                    nose_3d = (lm.x * img_w, lm.y * img_h, lm.z * 3000)
                    nose_3d_forward = (lm.x * img_w, lm.y * img_h, (lm.z + 1) * 3000)  # Point projected forward
                face_2d.append([x, y])
                face_3d.append([x, y, lm.z])

        face_2d = np.array(face_2d, dtype=np.float64)
        face_3d = np.array(face_3d, dtype=np.float64)
        
        # Camera matrix calculation
        focal_length = 1 * img_w
        cam_matrix = np.array([
            [focal_length, 0, img_h/2],
            [0, focal_length, img_w/2],
            [0, 0, 1]
        ])
        dist_matrix = np.zeros((4, 1), dtype=np.float64)

        # Solve for pose
        success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
        
        if not success:
            return "Failed", False, None, None

        # Calculate rotation matrix and angles
        rmat, _ = cv2.Rodrigues(rot_vec)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)
        x, y = angles[0] * 360, angles[1] * 360
        
        # Determine head direction based on angles
        if y < -self.config.HEAD_POSE_THRESHOLD:
            text = "Looking Left"
        elif y > self.config.HEAD_POSE_THRESHOLD:
            text = "Looking Right"
        elif x < -self.config.HEAD_POSE_THRESHOLD:
            text = "Looking Down"
        elif x > self.config.HEAD_POSE_THRESHOLD:
            text = "Looking Up"
        else:
            text = "Forward"

        # Project both nose point and forward point
        nose_points = np.array([nose_3d, nose_3d_forward], dtype=np.float64)
        nose_projections, _ = cv2.projectPoints(nose_points, rot_vec, trans_vec, cam_matrix, dist_matrix)
        
        # Extract the projected points for visualization
        p1 = (int(nose_projections[0][0][0]), int(nose_projections[0][0][1]))  # Current nose position
        p2 = (int(nose_projections[1][0][0]), int(nose_projections[1][0][1]))  # Projected forward point

        # Determine distraction status
        is_distracted = text != "Forward"
        
        return text, is_distracted, p1, p2