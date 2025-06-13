import cv2
import time
from threading import Thread
import logging
from config import Config
from utils.logging_setup import setup_logging
from utils.audio_manager import AudioManager
from detectors.facial_landmark_detector import FacialLandmarkDetector
from analyzers.facial_metrics import FacialMetricsAnalyzer
from analyzers.head_pose_analyzer import HeadPoseAnalyzer
from ui.ui import DrowsinessUI
from utils.pomodoro_timer import PomodoroTimer
from utils.statistics_manager import StatisticsManager

class DrowsinessDetector:
    """Main class for drowsiness detection system"""
    def __init__(self):
        setup_logging()
        self.config = Config()
        self.detector = FacialLandmarkDetector(self.config)
        self.facial_metrics = FacialMetricsAnalyzer()
        self.head_pose_analyzer = HeadPoseAnalyzer(self.config)
        self.ui = DrowsinessUI()

        # Add new attributes for camera blocking detection
        self.block_detection_counter = 0
        self.MIN_BRIGHTNESS_THRESHOLD = 30  # Adjust this value based on testing
        self.BLOCK_DETECTION_FRAMES = 5  # Number of consecutive dark frames to trigger alert
        self.camera_blocked_status = False

        self.distraction_start_time = None
        self.focus_alert_active = False  # Add this new flag
        self.focus_alert_interval = 5  # Time in seconds to trigger focus alert

        self.stats_manager = StatisticsManager()
        
        # Initialize audio manager and check audio files
        self.audio_manager = AudioManager()
        if not self.audio_manager.check_audio_files():
            logging.warning("Some audio files are missing. Alerts may not work properly.")

        # Initialize Pomodoro timer
        self.pomodoro = PomodoroTimer(self.audio_manager)
        
        # State tracking
        self.counter = 0
        self.alarm_status = False
        self.alarm_status2 = False
        self.saying = False

    def detect_camera_blocking(self, frame):
        """
        Detect if the camera is being blocked by checking frame brightness
        Returns: bool indicating if camera appears to be blocked
        """
        # Convert frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate average brightness
        average_brightness = cv2.mean(gray)[0]
        
        # Check if brightness is below threshold
        if average_brightness < self.MIN_BRIGHTNESS_THRESHOLD:
            self.block_detection_counter += 1
        else:
            self.block_detection_counter = 0
            
        # Return True if camera has been dark for several consecutive frames
        return self.block_detection_counter >= self.BLOCK_DETECTION_FRAMES
    

    def process_frame(self, image):
        """Process a single frame and perform drowsiness detection"""
        # Initialize variables with default values
        self.current_ear = 0.0
        self.current_mar = 0.0
        self.head_pose_text = "No face detected"
        is_distracted = False
        p1 = (0, 0)
        p2 = (0, 0)

        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.detector.face_mesh.process(image_rgb)

        # Check for camera blocking before other processing
        if self.detect_camera_blocking(image):
            if not self.camera_blocked_status:
                self.camera_blocked_status = True
                t = Thread(target=self.audio_manager.play_alarm, args=('camera_blocked', True))
                t.daemon = True
                t.start()

        else:
            self.camera_blocked_status = False

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Get head pose
                self.head_pose_text, is_distracted, p1, p2 = self.head_pose_analyzer.analyze_head_pose(
                    face_landmarks, image
                )
                # cv2.line(image, p1, p2, (255, 0, 0), 3)
                cv2.putText(image, self.head_pose_text, (20, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                # Calculate EAR for both eyes
                left_ear = self.facial_metrics.calculate_ear(
                    face_landmarks, self.detector.LEFT_EYE
                )
                right_ear = self.facial_metrics.calculate_ear(
                    face_landmarks, self.detector.RIGHT_EYE
                )
                self.current_ear = (left_ear + right_ear) / 2.0

                # Calculate MAR
                self.current_mar = self.facial_metrics.calculate_mar(
                    face_landmarks, self.detector.MOUTH
                )

                # Draw facial landmarks
                self.detector.mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=self.detector.mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=self.detector.drawing_spec,
                    connection_drawing_spec=self.detector.drawing_spec
                )

                # Handle drowsiness detection
                self.handle_drowsiness(self.current_ear, image)
                
                # Handle yawning detection
                self.handle_yawning(self.current_mar, image)

                # Handle focus using head pose
                self.handle_focus_using_head_pose(is_distracted, image)

                # Display measurements
                cv2.putText(image, f"EAR: {self.current_ear:.2f}", (300, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                cv2.putText(image, f"MAR: {self.current_mar:.2f}", (300, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Get Pomodoro timer status
        timer_status = self.pomodoro.get_timer_status()

        # Prepare metrics dictionary
        metrics = {
            'ear': self.current_ear,
            'mar': self.current_mar,
            'ear_thresh': self.config.EYE_AR_THRESH,
            'mar_thresh': self.config.MOUTH_AR_THRESH,
            'drowsy': self.alarm_status,
            'yawning': self.alarm_status2,
            'distracted': self.focus_alert_active,
            'camera_blocked': self.camera_blocked_status,
            'head_pose': self.head_pose_text,
            'pomodoro': timer_status
        }

        # Display Pomodoro timer status
        if timer_status['active']:
            session_type = timer_status['session_type'].replace('_', ' ').title()
            status_text = f"Pomodoro: {session_type} - {timer_status['time_remaining']}"
            if timer_status['paused']:
                status_text += " (Paused)"
            cv2.putText(image, status_text, (10, 120),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
            sessions_text = f"Sessions: {timer_status['sessions_completed']}"
            cv2.putText(image, sessions_text, (10, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Update statistics
        self.stats_manager.update_metrics(metrics)

        # Enhance the frame with UI elements
        image = self.ui.enhance_frame(image, metrics)

        return image

    def handle_drowsiness(self, ear, image):
      """Handle drowsiness detection and repeated alerts"""
      current_time = time.time()

      # If eyes are closed
      if ear < self.config.EYE_AR_THRESH:
        # Start tracking drowsy state if not already started
        if not hasattr(self, 'drowsy_start_time'):
            self.drowsy_start_time = current_time
        
        # Calculate how long the eyes have been closed
        drowsy_duration = current_time - self.drowsy_start_time

        # Trigger repeated alerts if drowsy state persists
        alert_interval = 3  # Interval between repeated alerts in seconds
        if drowsy_duration >= self.config.EYE_AR_CONSEC_FRAMES / 30.0:  # Assuming 30 FPS
            # Check if enough time has passed since the last alert
            if not hasattr(self, 'last_drowsy_alert_time') or (
                current_time - self.last_drowsy_alert_time >= alert_interval
            ):
                self.last_drowsy_alert_time = current_time
                self.alarm_status = True
                t = Thread(target=self.audio_manager.play_alarm, args=('drowsy', self.alarm_status))
                t.daemon = True
                t.start()

            # Display alert text
            cv2.putText(image, "DROWSINESS ALERT!", (10, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

      # If eyes are open, reset tracking
      else:
        if hasattr(self, 'drowsy_start_time'):
            del self.drowsy_start_time
        self.alarm_status = False

    def handle_yawning(self, mar, image):
        """
        Handle yawning detection and alerts with proper event tracking.
        A yawn is counted as a single event when MAR exceeds threshold for a minimum duration.
        """
        current_time = time.time()
        YAWN_MIN_DURATION = 1.0  # Minimum duration in seconds to confirm a yawn
        YAWN_COOLDOWN = 2.0      # Minimum time between distinct yawn events

        # Initialize yawn tracking attributes if they don't exist
        if not hasattr(self, 'yawn_start_time'):
            self.yawn_start_time = None
        if not hasattr(self, 'last_yawn_time'):
            self.last_yawn_time = 0
        if not hasattr(self, 'is_yawning'):
            self.is_yawning = False

        # Check if mouth is open wide (potential yawn)
        if mar > self.config.MOUTH_AR_THRESH:
            # Start tracking new yawn if not already tracking
            if self.yawn_start_time is None:
                self.yawn_start_time = current_time
        
            # Always show the text when MAR is above threshold
            cv2.putText(image, "YAWNING ALERT!", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
            # Check if this is a valid yawn (longer than minimum duration)
            yawn_duration = current_time - self.yawn_start_time
            if yawn_duration >= YAWN_MIN_DURATION:
                # Only trigger alert if we're not already in a yawn event and cooldown has passed
                if not self.is_yawning and (current_time - self.last_yawn_time) >= YAWN_COOLDOWN:
                    self.is_yawning = True
                    self.last_yawn_time = current_time
                    # Trigger yawn alert
                    t = Thread(target=self.audio_manager.play_alarm, 
                          args=('yawn', True, self.saying))
                    t.daemon = True
                    t.start()
                    self.alarm_status2 = True
        else:
            # Reset yawn tracking when mouth closes
            self.yawn_start_time = None
            self.is_yawning = False
            self.alarm_status2 = False

    def handle_focus_using_head_pose(self, is_distracted, image):
        """Track distraction time and alert if necessary"""
        current_time = time.time()

        if is_distracted:
            if self.distraction_start_time is None:
                self.distraction_start_time = current_time
                self.focus_alert_active = False  # Reset alert state when distraction starts
            
            elapsed_time = current_time - self.distraction_start_time

            # Only trigger alerts when elapsed time exceeds threshold
            if elapsed_time >= self.focus_alert_interval:
                if not hasattr(self, 'last_focus_alert_time') or (
                    current_time - self.last_focus_alert_time >= self.audio_manager.focus_cool_down
                ):
                    self.last_focus_alert_time = current_time
                    self.focus_alert_active = True  # Set flag to show alert
                    
                    # Trigger sound alert
                    t = Thread(target=self.audio_manager.play_alarm, args=('focus', True))
                    t.daemon = True
                    t.start()
            else:
                # Important: Keep focus_alert_active as False until threshold is reached
                self.focus_alert_active = False  # Don't show alert if not enough time has passed
        else:
            self.distraction_start_time = None
            self.focus_alert_active = False

    def run(self):
        """Main execution loop"""
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            logging.error("Failed to open camera")
            return

        # Display initial instructions
        print("\nPomodoro Timer Controls:")
        print("P - Start/Pause timer")
        print("S - Stop timer")
        print("ESC - Exit program\n")

        try:
            while cap.isOpened():
                success, image = cap.read()
                if not success:
                    logging.warning("Failed to capture frame")
                    continue

                # Process frame
                image = self.process_frame(image)

                cv2.imshow('FocusGuard - Drowsiness Detection', image)
            
                # Handle keyboard input
                key = cv2.waitKey(5) & 0xFF
                if key == 27:  # ESC
                    break
                elif key == ord('p'):  # Start/pause timer
                    if not self.pomodoro.is_active:
                        self.pomodoro.start_timer()
                        logging.info("Pomodoro timer started")
                    else:
                        if self.pomodoro.is_paused:
                            self.pomodoro.start_timer()  # Resume
                            logging.info("Pomodoro timer resumed")
                        else:
                            self.pomodoro.pause_timer()
                            logging.info("Pomodoro timer paused")
                elif key == ord('s'):  # Stop timer
                    self.pomodoro.stop_timer()
                    logging.info("Pomodoro timer stopped")

        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
        finally:
            cap.release()
            cv2.destroyAllWindows()

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'stats_manager'):
            self.stats_manager.save_session()
        cv2.destroyAllWindows()
        if hasattr(self, 'audio_manager'):
            self.audio_manager.cleanup()

if __name__ == "__main__":
    detector = None
    try:
        detector = DrowsinessDetector()
        detector.run()
    except KeyboardInterrupt:
        logging.info("Application terminated by user")
    except Exception as e:
        logging.error(f"Application crashed: {str(e)}")
    finally:
        if detector:
            detector.cleanup()