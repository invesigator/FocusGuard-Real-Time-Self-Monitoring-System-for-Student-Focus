import pygame
import logging
import time
from pathlib import Path
from threading import Lock

class AudioManager:
    """Handles audio playback for alerts with cooldown periods"""
    def __init__(self):
        """Initialize audio manager with sound files from assets directory"""
        pygame.mixer.init()
        
        # Get the project root directory
        project_root = Path(__file__).parent.parent
        
        # Define paths to audio files
        self.audio_dir = project_root / 'assets' / 'audio'
        self.drowsy_sound_path = self.audio_dir / 'wake_up_sir.wav'
        self.yawn_sound_path = self.audio_dir / 'take_some_fresh_air_sir.wav'
        self.camera_blocked_sound_path = self.audio_dir / 'camera_blocked.wav'
        self.focus_sound_path = self.audio_dir / 'stay_focus.wav'
        # Add new Pomodoro sound paths
        self.work_complete_sound_path = self.audio_dir / 'work_complete.wav'
        self.break_complete_sound_path = self.audio_dir / 'break_complete.wav'
        
        # Create audio directory if it doesn't exist
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize sounds
        try:
            self.drowsy_sound = pygame.mixer.Sound(str(self.drowsy_sound_path))
            self.yawn_sound = pygame.mixer.Sound(str(self.yawn_sound_path))
            self.camera_blocked_sound = pygame.mixer.Sound(str(self.camera_blocked_sound_path))
            self.focus_sound = pygame.mixer.Sound(str(self.focus_sound_path))

            # Initialize Pomodoro sounds
            self.work_complete_sound = pygame.mixer.Sound(str(self.work_complete_sound_path))
            self.break_complete_sound = pygame.mixer.Sound(str(self.break_complete_sound_path))
            logging.info("Audio files loaded successfully")

        except Exception as e:
            logging.error(f"Error loading audio files: {e}")
            logging.error(f"Expected audio files at: {self.audio_dir}")
            
            self.drowsy_sound = None
            self.yawn_sound = None
            self.camera_blocked_sound = None
            self.focus_sound = None
            self.work_complete_sound = None
            self.break_complete_sound = None

        # Cooldown tracking
        self.last_yawn_alert = 0
        self.last_drowsy_alert = 0
        self.last_camera_blocked_alert = 0
        self.last_focus_alert = 0
        self.last_pomodoro_alert = 0
        self.yawn_cooldown = 3.0  # Cooldown period in seconds
        self.drowsy_cooldown = 3.0  # Cooldown period for drowsiness alerts
        self.camera_blocked_cooldown = 3.0  # Cooldown period for camera blocking alerts
        self.focus_cool_down = 3.0  # Cooldown period for focus alerts
        self.pomodoro_cooldown = 1.0  # Cooldown period for pomodoro alerts
        self.lock = Lock()  # Thread-safe lock for cooldown checking

    def play_alarm(self, alarm_type: str, alarm_status: bool, saying: bool = False):
        """Play alarm sound based on the type of alert with cooldown consideration"""
        try:
            current_time = time.time()
            
            if alarm_type == 'drowsy' and alarm_status:
                with self.lock:
                    if current_time - self.last_drowsy_alert >= self.drowsy_cooldown:
                        if self.drowsy_sound:
                            self.drowsy_sound.play()
                            self.last_drowsy_alert = current_time
                            logging.info("Playing drowsiness alarm")
                    else:
                        logging.debug("Drowsy alert skipped - in cooldown period")
                    
            elif alarm_type == 'yawn' and alarm_status:
                with self.lock:
                    if current_time - self.last_yawn_alert >= self.yawn_cooldown:
                        if self.yawn_sound and not saying:
                            self.yawn_sound.play()
                            self.last_yawn_alert = current_time
                            logging.info("Playing yawn alarm")
                    else:
                        logging.debug("Yawn alert skipped - in cooldown period")
            
            elif alarm_type == 'camera_blocked' and alarm_status:
                with self.lock:
                    if current_time - self.last_camera_blocked_alert >= self.camera_blocked_cooldown:
                        if self.camera_blocked_sound:
                            self.camera_blocked_sound.play()
                            self.last_camera_blocked_alert = current_time
                            logging.info("Playing camera blocked alarm")
                    else:
                        logging.debug("Camera blocked alert skipped - in cooldown period")
            
            elif alarm_type == 'focus' and alarm_status:
                with self.lock:
                    if current_time - self.last_focus_alert >= self.focus_cool_down:
                        if self.focus_sound:
                            self.focus_sound.play()
                            self.last_focus_alert = current_time
                            logging.info("Playing focus alarm")
                    else:
                        logging.debug("Focus alert skipped - in cooldown period")

            # Add Pomodoro alerts
            elif alarm_type == 'work_complete' and alarm_status:
                with self.lock:
                    if current_time - self.last_pomodoro_alert >= self.pomodoro_cooldown:
                        if self.work_complete_sound:
                            self.work_complete_sound.play()
                            self.last_pomodoro_alert = current_time
                            logging.info("Playing work session complete alarm")
                    else:
                        logging.debug("Work complete alert skipped - in cooldown period")

            elif alarm_type == 'break_complete' and alarm_status:
                with self.lock:
                    if current_time - self.last_pomodoro_alert >= self.pomodoro_cooldown:
                        if self.break_complete_sound:
                            self.break_complete_sound.play()
                            self.last_pomodoro_alert = current_time
                            logging.info("Playing break complete alarm")
                    else:
                        logging.debug("Break complete alert skipped - in cooldown period")
                        
        except Exception as e:
            logging.error(f"Error playing audio: {e}")

    def check_audio_files(self):
        """Check if audio files exist and log their status"""
        missing_files = []
        
        if not self.drowsy_sound_path.exists():
            missing_files.append('wake_up_sir.wav')
        if not self.yawn_sound_path.exists():
            missing_files.append('take_some_fresh_air_sir.wav')
        if not self.camera_blocked_sound_path.exists():
            missing_files.append('camera_blocked.wav')
        if not self.work_complete_sound_path.exists():
            missing_files.append('work_complete.wav')
        if not self.break_complete_sound_path.exists():
            missing_files.append('break_complete.wav')
            
        if missing_files:
            logging.warning(f"Missing audio files: {missing_files}")
            logging.info(f"Please place audio files in: {self.audio_dir}")
            return False
        return True

    def cleanup(self):
        """Clean up pygame mixer"""
        pygame.mixer.quit()

    def set_yawn_cooldown(self, seconds: float):
        """Allow adjustment of yawn cooldown period"""
        self.yawn_cooldown = seconds

    def set_drowsy_cooldown(self, seconds: float):
        """Allow adjustment of drowsy cooldown period"""
        self.drowsy_cooldown = seconds

    def set_camera_blocked_cooldown(self, seconds: float):
        """Allow adjustment of camera blocked cooldown period"""
        self.camera_blocked_cooldown = seconds

    def set_pomodoro_cooldown(self, seconds: float):
        """Allow adjustment of pomodoro alert cooldown period"""
        self.pomodoro_cooldown = seconds