import cv2
import numpy as np
from datetime import datetime

class DrowsinessUI:
    """Enhanced UI class for drowsiness detection system"""
    def __init__(self):
        # Colors (BGR format)
        self.COLORS = {
            'primary': (59, 89, 152),    # Dark blue
            'success': (40, 167, 69),    # Green
            'warning': (0, 165, 255),    # Orange
            'danger': (0, 0, 255),       # Red
            'white': (255, 255, 255),    # White
            'gray': (128, 128, 128),     # Gray
            'black': (0, 0, 0)           # Black
        }
        
        # Fonts
        self.FONT = cv2.FONT_HERSHEY_SIMPLEX
        self.FONT_SMALL = 0.6
        self.FONT_MEDIUM = 0.8
        self.FONT_LARGE = 1.0
        
    def create_status_panel(self, width, height=80):
        """Create a semi-transparent status panel"""
        panel = np.zeros((height, width, 3), np.uint8)
        overlay = panel.copy()
        cv2.rectangle(overlay, (0, 0), (width, height), self.COLORS['primary'], -1)
        panel = cv2.addWeighted(overlay, 0.8, panel, 0.2, 0)
        return panel
    
    def draw_metric_box(self, image, text, value, threshold, x, y, width=120, height=60):
        """Draw a metric box with label and value"""
        # Draw background box
        cv2.rectangle(image, (x, y), (x + width, y + height), 
                     self.COLORS['white'], -1)
        cv2.rectangle(image, (x, y), (x + width, y + height), 
                     self.COLORS['gray'], 1)
        
        # Draw label
        cv2.putText(image, text, (x + 10, y + 20), self.FONT, 
                    self.FONT_SMALL, self.COLORS['black'], 1)
        
        # Draw value with color based on threshold
        color = self.COLORS['success'] if value >= threshold else self.COLORS['danger']
        cv2.putText(image, f"{value:.2f}", (x + 10, y + 45), self.FONT, 
                    self.FONT_MEDIUM, color, 2)
    
    def draw_alert(self, image, text, y_position):
        """Draw an attention-grabbing alert"""
        text_size = cv2.getTextSize(text, self.FONT, self.FONT_MEDIUM, 2)[0]
        x = (image.shape[1] - text_size[0]) // 2
        
        # Draw alert background
        cv2.rectangle(image, 
                     (x - 10, y_position - 30), 
                     (x + text_size[0] + 10, y_position + 10),
                     self.COLORS['danger'], -1)
        
        # Draw alert text
        cv2.putText(image, text, (x, y_position), self.FONT, 
                    self.FONT_MEDIUM, self.COLORS['white'], 2)
    
    def draw_time_and_date(self, image):
        """Draw current time and date"""
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        cv2.putText(image, current_time, (10, 25), self.FONT, 
                    self.FONT_MEDIUM, self.COLORS['white'], 1)
        cv2.putText(image, current_date, (10, 50), self.FONT, 
                    self.FONT_SMALL, self.COLORS['white'], 1)
    
    def enhance_frame(self, frame, metrics):
        """Apply UI enhancements to the frame"""
        height, width = frame.shape[:2]
        
        # Create top status panel
        status_panel = self.create_status_panel(width)
        frame[0:status_panel.shape[0], 0:width] = status_panel
        
        # Draw time and date
        self.draw_time_and_date(frame)
        
        # Draw metrics boxes
        metrics_start_y = height - 80
        self.draw_metric_box(frame, "EAR", metrics['ear'], metrics['ear_thresh'], 
                           10, metrics_start_y)
        self.draw_metric_box(frame, "MAR", metrics['mar'], metrics['mar_thresh'], 
                           140, metrics_start_y)
        
        # Draw alerts if necessary
        if metrics['drowsy']:
            self.draw_alert(frame, "DROWSINESS ALERT!", 120)
        if metrics['yawning']:
            self.draw_alert(frame, "YAWNING DETECTED!", 180)
        if metrics['distracted']:
            self.draw_alert(frame, "FOCUS ALERT!", 240)
        if metrics['camera_blocked']:
            self.draw_alert(frame, "CAMERA BLOCKED!", 300)
        
        # Draw head pose indicator if available
        if 'head_pose' in metrics:
            cv2.putText(frame, f"Head Pose: {metrics['head_pose']}", 
                       (width - 250, 30), self.FONT, self.FONT_SMALL, 
                       self.COLORS['white'], 1)
        
        return frame