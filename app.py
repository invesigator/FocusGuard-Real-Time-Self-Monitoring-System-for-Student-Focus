from flask import Flask, render_template, Response, send_from_directory, redirect, url_for, flash, request, jsonify
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, login_required, current_user
import cv2
import threading
import time
import logging
import os
from datetime import datetime, timedelta
import pandas as pd
import io
from flask import send_file
import psutil

# Import custom modules
from main import DrowsinessDetector
from utils.statistics_manager import StatisticsManager
from utils.audio_manager import AudioManager
from utils.pomodoro_timer import PomodoroTimer
from utils.achievement_manager import AchievementManager
from utils.analytics_manager import AnalyticsManager


# Import auth modules
from models.user import User, init_db
from auth_routes import auth_bp
from profile_routes import profile_bp

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_123')  # Change this in production
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login_page'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Initialize database
init_db()

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)

# Set up socket.io with CORS
socketio = SocketIO(app, cors_allowed_origins="*")


@login_manager.user_loader
def load_user(user_id):
    """Load user from database for Flask-Login"""
    return User.get_by_id(int(user_id))


class WebDrowsinessDetector:
    """
    Web interface for drowsiness detection system.
    Handles camera feed processing, event detection, and messaging.
    """
    def __init__(self, user_id=None):
        # Initialize core components
        self.detector = DrowsinessDetector()
        self.stats_manager = StatisticsManager()
        self.audio_manager = AudioManager()
        self.pomodoro = PomodoroTimer(self.audio_manager)
        
        # Store user ID for statistics tracking
        self.user_id = user_id

        # Initialize achievement manager with user_id
        self.achievement_manager = AchievementManager(user_id)
    
        # Initialize analytics manager
        self.analytics_manager = AnalyticsManager()
        
        # Camera and processing variables
        self.camera = None
        self.is_running = False
        self.frame_lock = threading.Lock()
        self.current_frame = None
        self.thread = None
        
        # State tracking variables
        self.prev_state = {
            'drowsy': False,
            'yawning': False,
            'distracted': False
        }
        
        # Alert status tracking
        self.alarm_status = False
        self.alarm_status2 = False
        self.distraction_start_time = None
        self.camera_blocked_status = False

        # Add to existing initialization code
        self.current_fps = 0
        self.cpu_usage = 0
    
        # Add CPU monitoring thread
        self.cpu_monitor_thread = None
        
        # Apply user settings if available
        if user_id:
            self.load_user_settings()

    def start_cpu_monitoring(self):
        """Start the CPU monitoring thread"""
        self.cpu_monitor_thread = threading.Thread(target=self.monitor_cpu_usage)
        self.cpu_monitor_thread.daemon = True
        self.cpu_monitor_thread.start()
    
    def monitor_cpu_usage(self):
        """Monitor CPU usage in a separate thread"""
        process = psutil.Process(os.getpid())
        
        while self.is_running:
            try:
                # Get process CPU usage
                self.cpu_usage = process.cpu_percent(interval=1.0)
                logging.info(f"CPU Usage: {self.cpu_usage:.1f}%")
            except Exception as e:
                logging.error(f"Error monitoring CPU usage: {str(e)}")
            
            # Sleep to avoid too frequent updates
            time.sleep(1.0)

    def start_performance_logging(self, duration_minutes=5, interval_seconds=1.0):
        """
        Log FPS and CPU usage for a specified duration
        
        Args:
            duration_minutes: How long to log performance data (minutes)
            interval_seconds: How frequently to record measurements (seconds)
        """
        import csv
        import time
        from datetime import datetime
        
        # Create CSV file with timestamp in filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"performance_log_{timestamp}.csv"
        
        logging.info(f"Starting performance logging for {duration_minutes} minutes. Data will be saved to {filename}")
        
        # Calculate end time
        end_time = time.time() + (duration_minutes * 60)
        
        # Ensure CPU monitoring is active
        if not self.cpu_monitor_thread or not self.cpu_monitor_thread.is_alive():
            self.start_cpu_monitoring()
        
        # Open CSV file
        with open(filename, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'fps', 'cpu_usage_percent']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Log data until duration expires
            while time.time() < end_time:
                # Record current timestamp, FPS and CPU usage
                writer.writerow({
                    'timestamp': datetime.now().isoformat(),
                    'fps': round(self.current_fps, 2),
                    'cpu_usage_percent': round(self.cpu_usage, 2)
                })
                
                # Log to console as well
                logging.info(f"Performance: FPS={self.current_fps:.2f}, CPU={self.cpu_usage:.2f}%")
                
                # Flush to ensure data is written to disk
                csvfile.flush()
                
                # Wait for next interval
                time.sleep(interval_seconds)
        
        logging.info(f"Performance logging completed. Data saved to {filename}")
        return filename

    def load_user_settings(self):
        """Load and apply user settings"""
        user = User.get_by_id(self.user_id)
        if user:
            settings = user.get_settings()
            if settings:
                # Apply detection settings
                self.detector.config.EYE_AR_THRESH = settings.get('eye_ar_thresh', 0.15)
                self.detector.config.MOUTH_AR_THRESH = settings.get('mouth_ar_thresh', 1.35)
                self.detector.config.HEAD_POSE_THRESHOLD = settings.get('head_pose_threshold', 10.0)
                
                # Apply pomodoro settings
                self.pomodoro.work_duration = settings.get('work_duration', 25)
                self.pomodoro.short_break_duration = settings.get('short_break_duration', 5)
                self.pomodoro.long_break_duration = settings.get('long_break_duration', 15)
                self.pomodoro.long_break_interval = settings.get('long_break_interval', 4)
    
    def save_user_settings(self, settings_dict):
        """Save user settings"""
        if not self.user_id:
            return False
            
        user = User.get_by_id(self.user_id)
        if user:
            return user.update_settings(settings_dict)
        return False

    def process_frame(self, image):
        """
        Process frame and emit events when state changes
        
        Args:
            image: Camera image frame to process
                
        Returns:
            Processed frame with annotations
        """
        frame = self.detector.process_frame(image)

        # Add performance metrics to the frame
        cv2.putText(frame, f"FPS: {self.current_fps:.2f}", 
                (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, f"CPU: {self.cpu_usage:.1f}%", 
                (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Check if person is distracted based on head pose
        is_looking_away = False
        if self.detector.head_pose_text:  # Make sure head_pose_text exists
            is_looking_away = self.detector.head_pose_text not in ['Forward', 'forward', 'Center', 'center']
        
        # Update distraction timing
        current_time = time.time()
        if is_looking_away and self.distraction_start_time is None:
            self.distraction_start_time = current_time
        elif not is_looking_away:
            self.distraction_start_time = None
        
        # Only count as distracted if it's been 5 seconds
        is_distracted = False
        if is_looking_away and self.distraction_start_time is not None:
            elapsed_time = current_time - self.distraction_start_time
            # Only mark as distracted if they've been looking away for at least 5 seconds
            is_distracted = elapsed_time >= 5.0
        
        # Get current metrics
        metrics = {
            'ear': self.detector.current_ear,
            'mar': self.detector.current_mar,
            'drowsy': self.detector.alarm_status,
            'yawning': self.detector.alarm_status2,
            'distracted': is_distracted,  # Now this is only True after 5 seconds
            'camera_blocked': self.camera_blocked_status,
            'head_pose': self.detector.head_pose_text,
            'pomodoro': self.pomodoro.get_timer_status(),
            # Add performance metrics
            'fps': self.current_fps,
            'cpu_usage': self.cpu_usage
        }

        # FIX: Store user ID in metrics for session tracking
        metrics['user_id'] = self.user_id

        # Update statistics manager
        self.stats_manager.update_metrics(metrics)
        
        # Check for state changes and emit events
        if metrics['drowsy'] and not self.prev_state['drowsy']:
            socketio.emit('drowsy_event')
        if metrics['yawning'] and not self.prev_state['yawning']:
            socketio.emit('yawn_event')
        if metrics['distracted'] and not self.prev_state['distracted']:
            socketio.emit('distraction_event')
            
        # Update previous states
        self.prev_state = {
            'drowsy': metrics['drowsy'],
            'yawning': metrics['yawning'],
            'distracted': metrics['distracted']
        }
        
        return frame
    
    def initialize_camera(self):
        """
        Initialize the camera with specific settings
        
        Raises:
            RuntimeError: If camera cannot be started or read
        """
        if self.camera is None:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                raise RuntimeError("Could not start camera")
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 640x480
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Read a test frame
            ret, _ = self.camera.read()
            if not ret:
                self.camera.release()
                self.camera = None
                raise RuntimeError("Could not read from camera")
                
            logging.info("Camera successfully initialized")
    
    def release_camera(self):
        """Properly release the camera resources"""
        if self.camera is not None:
            self.is_running = False
            time.sleep(0.1)  # Allow time for the processing loop to stop
            self.camera.release()
            self.camera = None
            self.current_frame = None
            logging.info("Camera released")
            
    def process_camera_feed(self):
        """Process frames from camera in a continuous loop with FPS tracking"""
        # Initialize FPS tracking variables
        frame_count = 0
        fps = 0
        fps_start_time = time.time()
        
        while self.is_running:
            if self.camera is None or not self.camera.isOpened():
                logging.error("Camera is not available")
                break
                
            ret, frame = self.camera.read()
            if not ret:
                logging.warning("Failed to read frame")
                continue
                
            try:
                # Process frame with drowsiness detection
                processed_frame = self.process_frame(frame)
                
                # Calculate FPS
                frame_count += 1
                elapsed_time = time.time() - fps_start_time
                
                # Update FPS every second
                if elapsed_time > 1.0:
                    fps = frame_count / elapsed_time
                    self.current_fps = fps  # Store current FPS as instance variable
                    frame_count = 0
                    fps_start_time = time.time()
                    
                    # Log FPS
                    logging.info(f"Current FPS: {self.current_fps:.2f}")
                
                # Add FPS text to frame
                cv2.putText(processed_frame, f"FPS: {self.current_fps:.2f}", 
                            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                # Encode frame
                with self.frame_lock:
                    _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    self.current_frame = buffer.tobytes()
                    
            except Exception as e:
                logging.error(f"Error processing frame: {str(e)}")
                continue
                
            # Add a small delay to prevent high CPU usage
            time.sleep(0.01)
    
    def get_frame(self):
        """
        Safely get the current frame
        
        Returns:
            bytes: JPEG encoded frame data or None
        """
        with self.frame_lock:
            return self.current_frame


# Initialize global detector instance
detector_instances = {}


def get_detector_for_user(user_id):
    """Get or create a detector instance for the specified user"""
    if user_id not in detector_instances:
        detector_instances[user_id] = WebDrowsinessDetector(user_id)
    return detector_instances[user_id]


def generate_frames(detector):
    """
    Generator function for video streaming
    
    Yields:
        bytes: MJPEG frame chunks for streaming
    """
    while detector.is_running:
        frame = detector.get_frame()
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.01)  # Small delay to prevent overwhelming the browser


#======================================================
# FLASK ROUTES
#======================================================

@app.route('/')
@login_required
def index():
    """Render the main application page"""
    # Make sure the detector is initialized for the user
    detector = get_detector_for_user(current_user.id)
    
    # Pre-load gamification data to ensure it's initialized
    if detector.achievement_manager:
        detector.achievement_manager.load_profile_from_db()
    
    return render_template('index.html', user=current_user)


@app.route('/<path:filename>')
def serve_css(filename):
    """Serve the CSS file"""
    return send_from_directory('templates', filename)


@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve any JavaScript file from the js directory"""
    return send_from_directory('templates/js', filename)


@app.route('/video_feed')
@login_required
def video_feed():
    """Stream video feed"""
    detector = get_detector_for_user(current_user.id)
    if not detector.is_running:
        return Response(status=204)  # No content
    return Response(generate_frames(detector),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/profile')
@login_required
def profile():
    """Render user profile page"""
    return render_template('profile.html', user=current_user)


@app.route('/api/user/settings', methods=['GET'])
@login_required
def get_user_settings():
    """Get user settings API endpoint"""
    user = User.get_by_id(current_user.id)
    settings = user.get_settings() if user else None
    
    if not settings:
        return {'success': False, 'message': 'Settings not found'}, 404
        
    return {'success': True, 'settings': settings}


#======================================================
# SOCKET.IO EVENT HANDLERS
#======================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    if current_user.is_authenticated:
        # Send initial data on connection
        try:
            # Get detector for user
            detector = get_detector_for_user(current_user.id)
            
            # Send gamification data right after connection
            if detector and detector.achievement_manager:
                try:
                    # Make sure profile is loaded from database
                    detector.achievement_manager.load_profile_from_db()
                    
                    # Get and send gamification status
                    gamification_status = detector.achievement_manager.get_gamification_status()
                    emit('gamification_update', gamification_status)
                    
                    # Check daily status
                    today = datetime.now().date()
                    last_check_in = detector.achievement_manager.user_profile.get('last_check_in_date')
                    
                    already_checked_in = False
                    if last_check_in:
                        try:
                            check_in_date = datetime.fromisoformat(last_check_in).date()
                            already_checked_in = (check_in_date == today)
                        except (ValueError, TypeError):
                            already_checked_in = False
                    
                    emit('daily_status_check', {
                        'already_checked_in': already_checked_in
                    })
                    
                    logging.info(f"Initial gamification data sent to user {current_user.id}")
                except Exception as e:
                    logging.error(f"Error sending initial gamification data: {str(e)}")
        except Exception as e:
            logging.error(f"Error in connect handler: {str(e)}")
        
        emit('connection_status', {'status': 'connected', 'user_id': current_user.id})
    else:
        emit('connection_status', {'status': 'unauthorized'})


@socketio.on('start_detection')
@login_required
def start_detection():
    """Start the drowsiness detection"""
    detector = get_detector_for_user(current_user.id)
    
    with detector.frame_lock:
        if not detector.is_running:
            try:
                # Reset statistics manager for new session
                detector.stats_manager = StatisticsManager()

                # Initialize camera
                detector.initialize_camera()
                detector.is_running = True

                # Start CPU monitoring thread - ADD THIS LINE
                detector.start_cpu_monitoring()

                # Start processing thread
                detector.thread = threading.Thread(target=detector.process_camera_feed)
                detector.thread.daemon = True
                detector.thread.start()

                # Give time for camera to start
                time.sleep(0.5)

                # Start statistics update thread
                socketio.start_background_task(send_periodic_statistics, detector)

                # Emit status
                emit('detection_status', {'status': 'started'})
                logging.info(f"Detection started for user {current_user.id}")

            except Exception as e:
                logging.error(f"Failed to start detection: {str(e)}")
                emit('detection_status', {'status': 'error', 'message': str(e)})


def send_periodic_statistics(detector):
    """Send statistics updates every second while detection is running"""
    while detector.is_running:
        try:
            if detector.stats_manager.current_session['start_time']:
                # Get base statistics
                stats = {
                    'session_duration': int((datetime.now() - detector.stats_manager.current_session['start_time']).total_seconds() // 60),
                    'total_drowsy_events': detector.stats_manager.session_summary['total_drowsy_events'],
                    'total_yawn_events': detector.stats_manager.session_summary['total_yawn_events'],
                    'total_distraction_events': detector.stats_manager.session_summary['total_distraction_events'],
                    # Add current metrics
                    'current_metrics': {
                        'ear': detector.detector.current_ear,
                        'mar': detector.detector.current_mar,
                        'head_pose': detector.detector.head_pose_text,
                        'drowsy': detector.detector.alarm_status,
                        'yawning': detector.detector.alarm_status2,
                        'distracted': detector.detector.head_pose_text not in ['Forward', 'forward', 'Center', 'center'] if detector.detector.head_pose_text else False
                    }
                }
            
                # Emit the statistics update
                socketio.emit('statistics_update', stats)

                socketio.sleep(0.5)  # Update every half second
                
        except Exception as e:
            logging.error(f"Error sending statistics: {str(e)}")
            socketio.sleep(0.5)  # Wait before retrying


@socketio.on('stop_detection')
@login_required
def stop_detection():
    """Stop the drowsiness detection and collect session data"""
    detector = get_detector_for_user(current_user.id)
    
    with detector.frame_lock:
        if detector.is_running:
            detector.is_running = False
            if detector.thread:
                detector.thread.join(timeout=1.0)
            detector.release_camera()
            
            # Get session statistics
            stats_file = detector.stats_manager.save_session()
            
            # FIX: Also save to database with the correct user_id
            if hasattr(detector.stats_manager, 'user_id') and detector.stats_manager.user_id:
                detector.stats_manager.save_session_to_db(detector.stats_manager.user_id)
            else:
                detector.stats_manager.save_session_to_db(current_user.id)
                
            session_stats = detector.stats_manager.session_summary
            
            # Calculate points for the session
            points_result = detector.achievement_manager.calculate_session_points(session_stats)
            
            # Track session in analytics
            detector.analytics_manager.track_session(
                session_stats, 
                points_result.get('total_points', 0)
            )
            
            # Save session to user history if authenticated
            session_id = None
            if current_user.is_authenticated:
                user = User.get_by_id(current_user.id)
                if user:
                    session_data = {
                        'start_time': detector.stats_manager.current_session['start_time'].isoformat(),
                        'end_time': datetime.now().isoformat(),
                        'duration_minutes': session_stats.get('session_duration_minutes', 0),
                        'drowsy_events': session_stats.get('total_drowsy_events', 0),
                        'yawn_events': session_stats.get('total_yawn_events', 0),
                        'distraction_events': session_stats.get('total_distraction_events', 0),
                        'completed_pomodoros': session_stats.get('completed_pomodoro_sessions', 0),
                        'points_earned': points_result.get('total_points', 0)
                    }
                    session_id = user.save_session(session_data)
            
            # Check for achievements based on session stats
            achievements = detector.achievement_manager.check_session_achievements(session_stats)
            
            # Track achievements in analytics
            if achievements:
                detector.analytics_manager.track_achievement(len(achievements))
            
            # Check pomodoro achievements if applicable
            completed_pomodoros = session_stats.get('completed_pomodoro_sessions', 0)
            if completed_pomodoros > 0:
                pomodoro_achievements = detector.achievement_manager.check_pomodoro_achievements(completed_pomodoros)
                achievements.extend(pomodoro_achievements)
                
                # Track badges if any were earned
                badges_earned = sum(1 for a in pomodoro_achievements if a.get('type') == 'badge')
                if badges_earned > 0:
                    detector.analytics_manager.track_badge(badges_earned)
            
            # Track level up if it occurred
            if points_result.get('level_up'):
                detector.analytics_manager.track_level_up()
            
            # Save updated profile
            detector.achievement_manager.save_profile()
            
            # Send response with stats and achievements
            emit('detection_status', {
                'status': 'stopped',
                'stats_file': str(stats_file) if stats_file else None,
                'points': points_result,
                'achievements': achievements
            })
            
            # Additionally, emit gamification status update
            emit('gamification_update', detector.achievement_manager.get_gamification_status())
            
            # FIX: Request an update of the session history after the session completes
            emit('session_history_data', {'sessions': User.get_by_id(current_user.id).get_session_history()})
            
            logging.info(f"Detection stopped for user {current_user.id}")

@app.route('/api/stop_detection_emergency', methods=['POST'])
@login_required
def emergency_stop_detection():
    """Emergency endpoint to stop detection when page is unloaded"""
    try:
        # Get current user's detector
        detector = get_detector_for_user(current_user.id)
        
        if detector and detector.is_running:
            # Forcefully stop the detection
            detector.is_running = False
            
            # Release camera resources immediately
            detector.release_camera()
            
            # Log the emergency stop
            logging.warning(f"Emergency detection stop triggered for user {current_user.id}")
            
            # Save session data if possible
            try:
                # Try to save to database with a minimal session record
                detector.stats_manager.save_session_to_db(current_user.id)
                
                # Create a minimal session record in user history
                user = User.get_by_id(current_user.id)
                if user:
                    session_data = {
                        'start_time': detector.stats_manager.current_session['start_time'].isoformat(),
                        'end_time': datetime.now().isoformat(),
                        'duration_minutes': int((datetime.now() - detector.stats_manager.current_session['start_time']).total_seconds() // 60),
                        'drowsy_events': detector.stats_manager.session_summary.get('total_drowsy_events', 0),
                        'yawn_events': detector.stats_manager.session_summary.get('total_yawn_events', 0),
                        'distraction_events': detector.stats_manager.session_summary.get('total_distraction_events', 0),
                        'completed_pomodoros': detector.stats_manager.session_summary.get('completed_pomodoro_sessions', 0),
                        'points_earned': 0  # No points earned for emergency stops
                    }
                    user.save_session(session_data)
                    logging.info(f"Emergency session saved for user {current_user.id}")
                
            except Exception as e:
                logging.error(f"Error saving emergency session: {str(e)}")
            
            return jsonify({'success': True, 'message': 'Detection stopped in emergency mode'})
        else:
            return jsonify({'success': False, 'message': 'Detection was not running'}), 400
            
    except Exception as e:
        logging.error(f"Error in emergency stop detection: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Add this code to app.py after the existing socket.io event handlers
@socketio.on('get_visualization_data')
@login_required
def handle_get_visualization_data():
    """Handle request for visualization data"""
    detector = get_detector_for_user(current_user.id)
    
    if not detector or not detector.stats_manager:
        emit('visualization_data', {})
        return
        
    # Get visualization data
    # IMPORTANT FIX: Always pass from_db=True and user_id to ensure database is used
    visualization_data = detector.stats_manager.get_visualization_data(from_db=True, user_id=current_user.id)
    
    # Emit back to client
    emit('visualization_data', visualization_data)

@socketio.on('check_daily_status')
@login_required
def check_daily_status():
    """Check if user has already checked in today"""
    detector = get_detector_for_user(current_user.id)
    
    if not detector or not detector.achievement_manager:
        emit('daily_status_check', {'error': 'Gamification system not initialized'})
        return
    
    today = datetime.now().date()
    last_check_in = detector.achievement_manager.user_profile.get('last_check_in_date')
    
    already_checked_in = False
    if last_check_in:
        try:
            # Support both date and datetime objects
            if isinstance(last_check_in, str):
                check_in_date = datetime.fromisoformat(last_check_in).date()
            elif hasattr(last_check_in, 'date'):
                check_in_date = last_check_in.date()
            else:
                check_in_date = last_check_in
                
            already_checked_in = (check_in_date == today)
            logging.info(f"Check-in status for user {current_user.id}: last={check_in_date}, today={today}, already_checked_in={already_checked_in}")
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Error parsing last_check_in_date: {e}, value: {last_check_in}")
            already_checked_in = False
    
    # Get current streak to send with the response
    current_streak = detector.achievement_manager.user_profile['streaks'].get('daily_login', 0)
    
    emit('daily_status_check', {
        'already_checked_in': already_checked_in,
        'current_streak': current_streak
    })


@socketio.on('daily_check_in')
@login_required
def handle_daily_check_in():
    """Handle daily streak check-in"""
    detector = get_detector_for_user(current_user.id)
    
    if not detector or not detector.achievement_manager:
        emit('daily_check_in_response', {
            'success': False,
            'message': 'Error initializing achievement system'
        })
        return
    
    # Check if user has already checked in today
    today = datetime.now().date()
    last_check_in = detector.achievement_manager.user_profile.get('last_check_in_date')
    
    already_checked_in = False
    if last_check_in:
        try:
            # Support both string dates and datetime objects
            if isinstance(last_check_in, str):
                check_in_date = datetime.fromisoformat(last_check_in).date()
            elif hasattr(last_check_in, 'date'): 
                check_in_date = last_check_in.date()
            else:
                check_in_date = last_check_in
                
            already_checked_in = (check_in_date == today)
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Error parsing last_check_in_date: {e}, value: {last_check_in}")
            already_checked_in = False
    
    if already_checked_in:
        emit('daily_check_in_response', {
            'success': False,
            'message': 'You have already checked in today',
            'already_checked_in': True
        })
        return
    
    try:
        # Get the current streak before check-in for logging
        current_streak = detector.achievement_manager.user_profile['streaks'].get('daily_login', 0)
        
        # Process daily check-in and update streak
        streak_result = detector.achievement_manager.check_daily_login()
        
        # Get the new streak after check-in
        new_streak = detector.achievement_manager.user_profile['streaks'].get('daily_login', 0)
        
        # Log streak change
        logging.info(f"Streak updated: {current_streak} -> {new_streak}, result: {streak_result}")
        
        # Save achievement manager profile
        detector.achievement_manager.save_profile()
        
        # Check for streak achievements
        achievements = detector.achievement_manager.check_streak_achievements()
        
        # Calculate total points earned (base + streak bonus)
        base_points = detector.achievement_manager.point_rules.get('daily_login', 20)
        streak_bonus = detector.achievement_manager.point_rules.get('streak_bonus', 10) * new_streak
        total_points = base_points + streak_bonus
        
        # Prepare response with TOTAL points (base + streak bonus)
        response = {
            'success': True,
            'message': 'Daily check-in successful!',
            'streak': new_streak,
            'previous_streak': current_streak,
            'points_earned': total_points,  # Now includes both base and streak bonus
            'base_points': base_points,     # Optional: Include breakdown details
            'streak_bonus': streak_bonus,   # Optional: Include breakdown details
            'achievements': achievements
        }
        
        # Emit response
        emit('daily_check_in_response', response)
        
        # Also emit updated gamification status
        emit('gamification_update', detector.achievement_manager.get_gamification_status())
        
        logging.info(f"Daily check-in processed for user {current_user.id}, streak: {response['streak']}, points: {total_points}")
    except Exception as e:
        logging.error(f"Error processing daily check-in: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        
        emit('daily_check_in_response', {
            'success': False,
            'message': f'Error processing check-in: {str(e)}'
        })

# Add these socket event handlers to app.py
@socketio.on('get_analytics_data')
@login_required
def handle_get_analytics_data():
    """Handle request for analytics data"""
    detector = get_detector_for_user(current_user.id)
    
    if not detector or not detector.analytics_manager:
        emit('analytics_data', {})
        return
    
    # Get analytics summary
    analytics_summary = detector.analytics_manager.get_analytics_summary()
    
    # Add some additional data
    if detector.achievement_manager:
        analytics_summary['focus_minutes'] = detector.achievement_manager.user_profile.get('total_focus_minutes', 0)
        analytics_summary['sessions'] = detector.achievement_manager.user_profile.get('total_sessions', 0)
        analytics_summary['points'] = detector.achievement_manager.user_profile['points']
        analytics_summary['level'] = detector.achievement_manager.user_profile['level']
        analytics_summary['experience'] = detector.achievement_manager.user_profile['experience']
        analytics_summary['daily_streak'] = detector.achievement_manager.user_profile['streaks']['daily_login']
        analytics_summary['pomodoro_streak'] = detector.achievement_manager.user_profile['streaks']['pomodoro_sessions']
    
    # Emit the analytics data
    emit('analytics_data', analytics_summary)
    
    logging.info(f"Analytics data sent to user {current_user.id}")

@socketio.on('export_analytics')
@login_required
def handle_export_analytics():
    """Handle request to export analytics data"""
    detector = get_detector_for_user(current_user.id)
    
    if not detector or not detector.analytics_manager:
        emit('analytics_export_ready', {
            'status': 'error',
            'message': 'Analytics manager not initialized'
        })
        return
    
    # Export analytics to CSV
    csv_file = detector.analytics_manager.export_analytics_to_csv()
    
    if csv_file:
        emit('analytics_export_ready', {
            'status': 'success',
            'message': 'Analytics exported successfully',
            'file': str(csv_file)
        })
    else:
        emit('analytics_export_ready', {
            'status': 'error',
            'message': 'Failed to export analytics'
        })

# Make sure get_analytics_data is called when loading the analytics tab
@socketio.on('load_analytics_tab')
@login_required
def handle_load_analytics_tab():
    """Handle request to load analytics tab data"""
    handle_get_analytics_data()


@socketio.on('get_gamification_status')
@login_required
def handle_get_gamification_status():
    """Handle request for gamification status"""
    detector = get_detector_for_user(current_user.id)
    
    if not detector or not detector.achievement_manager:
        logging.error(f"Gamification system not initialized for user {current_user.id}")
        emit('gamification_update', {'error': 'Gamification system not initialized'})
        return
    
    try:
        # Make sure achievement manager is loaded from DB
        detector.achievement_manager.load_profile_from_db()
        
        # Get gamification status
        gamification_status = detector.achievement_manager.get_gamification_status()
        
        # Log the data being sent
        logging.info(f"Sending gamification status to user {current_user.id}: level={gamification_status.get('level')}, points={gamification_status.get('points')}")
        
        # Emit back to client
        emit('gamification_update', gamification_status)
    except Exception as e:
        logging.error(f"Error getting gamification status: {str(e)}")
        emit('gamification_update', {'error': str(e)})

@socketio.on('save_gamification_data')
@login_required
def handle_save_gamification_data():
    """Force save the gamification data"""
    detector = get_detector_for_user(current_user.id)
    
    if not detector or not detector.achievement_manager:
        logging.error(f"Cannot save gamification data - system not initialized for user {current_user.id}")
        emit('gamification_save_status', {'success': False, 'error': 'Gamification system not initialized'})
        return
        
    try:
        # Force save to database
        success = detector.achievement_manager.save_profile()
        
        if success:
            logging.info(f"Gamification data saved for user {current_user.id}")
            emit('gamification_save_status', {'success': True})
        else:
            logging.error(f"Failed to save gamification data for user {current_user.id}")
            emit('gamification_save_status', {'success': False, 'error': 'Save operation returned False'})
    except Exception as e:
        logging.error(f"Error saving gamification data: {str(e)}")
        emit('gamification_save_status', {'success': False, 'error': str(e)})

@socketio.on('get_leaderboard_data')
@login_required
def handle_get_leaderboard_data(data=None):
    """Handle request for leaderboard data"""
    # Log the current user for debugging
    logging.info(f"Leaderboard requested by: {current_user.username} (ID: {current_user.id})")
    
    detector = get_detector_for_user(current_user.id)
    
    if not detector or not detector.analytics_manager:
        logging.error(f"Analytics manager not initialized for user {current_user.id}")
        emit('leaderboard_data', {'error': 'Analytics manager not initialized'})
        return
    
    try:
        # Set current user ID on the analytics manager
        detector.analytics_manager.current_user_id = current_user.id
        
        # Get leaderboard data - passing None as limit to get all users
        users = detector.analytics_manager.get_leaderboard_data(limit=None)
        
        # Filter out admin user if it somehow got through the SQL filter
        users = [user for user in users if user.get('username') != 'admin']
        
        # Debug log about the returned users
        logging.info(f"Returning {len(users)} users for leaderboard")
        
        # Check if current user is correctly marked
        current_user_in_list = False
        for user in users:
            if user.get('is_current_user'):
                current_user_in_list = True
                logging.info(f"Current user in leaderboard data: {user['name']} (ID: {user['id']})")
        
        if not current_user_in_list and current_user.username != 'admin':
            logging.warning(f"Current user {current_user.id} not marked in leaderboard data!")
            
            # Fix issue by manually marking the current user
            for user in users:
                if user['id'] == current_user.id:
                    user['is_current_user'] = True
                    current_user_in_list = True
                    logging.info(f"Manually marked current user: {user['name']} (ID: {user['id']})")
                    break
        
        # Emit to client
        emit('leaderboard_data', {'users': users})
        
    except Exception as e:
        logging.error(f"Error getting leaderboard data: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        emit('leaderboard_data', {'error': str(e)})

# Add this new socket event handler in app.py
@socketio.on('get_session_history')
@login_required
def handle_get_session_history():
    """Handle request for user's session history"""
    if not current_user.is_authenticated:
        emit('session_history_data', {'error': 'User not authenticated'})
        return
        
    try:
        # Get session history for the current user
        user = User.get_by_id(current_user.id)
        if not user:
            emit('session_history_data', {'error': 'User not found'})
            return
            
        # Get session history with increased limit
        sessions = user.get_session_history(limit=20)
        
        # Format session data for frontend
        formatted_sessions = []
        for session in sessions:
            # Format datetime objects to strings if they exist
            start_time = session.get('start_time')
            if start_time:
                if isinstance(start_time, datetime):
                    start_time = start_time.strftime('%b %d, %Y %I:%M %p')
                    
            # Create a formatted entry for the frontend
            formatted_session = {
                'date': start_time,
                'duration': session.get('duration_minutes', 0),
                'drowsy': session.get('drowsy_events', 0),
                'yawn': session.get('yawn_events', 0),
                'distraction': session.get('distraction_events', 0),
                'id': session.get('id')
            }
            formatted_sessions.append(formatted_session)
            
        # Send to frontend
        logging.info(f"Sending {len(formatted_sessions)} session history records to user {current_user.id}")
        emit('session_history_data', {'sessions': formatted_sessions})
        
    except Exception as e:
        logging.error(f"Error retrieving session history: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        emit('session_history_data', {'error': str(e)})

#======================================================
# POMODORO TIMER EVENTS
#======================================================

@socketio.on('pomodoro_start')
@login_required
def handle_pomodoro_start():
    """Start or resume Pomodoro timer"""
    detector = get_detector_for_user(current_user.id)
    try:
        # If the timer is paused, this will resume it from its current state
        detector.pomodoro.start_timer()
        emit('pomodoro_update', detector.pomodoro.get_timer_status())
        logging.info(f"Pomodoro timer started/resumed for user {current_user.id}")
    except Exception as e:
        logging.error(f"Error starting Pomodoro timer: {str(e)}")
        emit('pomodoro_update', {'error': str(e)})


@socketio.on('pomodoro_pause')
@login_required
def handle_pomodoro_pause():
    """Pause Pomodoro timer"""
    detector = get_detector_for_user(current_user.id)
    try:
        detector.pomodoro.pause_timer()
        emit('pomodoro_update', detector.pomodoro.get_timer_status())
        logging.info(f"Pomodoro timer paused for user {current_user.id}")
    except Exception as e:
        logging.error(f"Error pausing Pomodoro timer: {str(e)}")
        emit('pomodoro_update', {'error': str(e)})


@socketio.on('pomodoro_stop')
@login_required
def handle_pomodoro_stop():
    """Stop Pomodoro timer"""
    detector = get_detector_for_user(current_user.id)
    try:
        detector.pomodoro.stop_timer()
        emit('pomodoro_update', detector.pomodoro.get_timer_status())
        logging.info(f"Pomodoro timer stopped for user {current_user.id}")
    except Exception as e:
        logging.error(f"Error stopping Pomodoro timer: {str(e)}")
        emit('pomodoro_update', {'error': str(e)})


@socketio.on('pomodoro_custom_start')
@login_required
def handle_pomodoro_custom_start(data):
    """Start custom Pomodoro timer mode"""
    detector = get_detector_for_user(current_user.id)
    try:
        mode = data.get('mode', 'pomodoro')
        
        # Reset the timer first
        detector.pomodoro.stop_timer()
        
        # Call the start_custom_session method that preserves mode selection info
        detector.pomodoro.start_custom_session(
            "work" if mode == 'pomodoro' else 
            "short_break" if mode == 'short-break' else 
            "long_break"
        )
        
        # Emit status update
        emit('pomodoro_update', detector.pomodoro.get_timer_status())
        logging.info(f"Pomodoro timer started in {mode} mode for user {current_user.id}")
        
    except Exception as e:
        logging.error(f"Error starting custom Pomodoro mode: {str(e)}")
        emit('pomodoro_update', {'error': str(e)})


@socketio.on('get_timer_status')
@login_required
def handle_get_timer_status():
    """Get current timer status"""
    detector = get_detector_for_user(current_user.id)
    try:
        status = detector.pomodoro.get_timer_status()
        emit('pomodoro_update', status)
    except Exception as e:
        logging.error(f"Error getting timer status: {str(e)}")
        emit('pomodoro_update', {'error': str(e)})


#======================================================
# SETTINGS ROUTES
#======================================================

@socketio.on('update_detection_settings')
@login_required
def update_detection_settings(data):
    """Update detection settings"""
    detector = get_detector_for_user(current_user.id)
    try:
        # Update the configuration
        detector.detector.config.EYE_AR_THRESH = float(data.get('eye_threshold', 0.15))
        detector.detector.config.MOUTH_AR_THRESH = float(data.get('mouth_threshold', 1.35))
        detector.detector.config.HEAD_POSE_THRESHOLD = float(data.get('head_pose_threshold', 10.0))
        
        # Save to user settings if authenticated
        if current_user.is_authenticated:
            detector.save_user_settings({
                'eye_ar_thresh': detector.detector.config.EYE_AR_THRESH,
                'mouth_ar_thresh': detector.detector.config.MOUTH_AR_THRESH,
                'head_pose_threshold': detector.detector.config.HEAD_POSE_THRESHOLD
            })
        
        # Emit confirmation
        emit('settings_updated', {'status': 'success', 'message': 'Detection settings updated successfully'})
        logging.info(f"Detection settings updated for user {current_user.id}")
        
    except Exception as e:
        logging.error(f"Error updating detection settings: {str(e)}")
        emit('settings_updated', {'status': 'error', 'message': str(e)})


@socketio.on('update_pomodoro_settings')
@login_required
def update_pomodoro_settings(data):
    """Update pomodoro timer settings"""
    detector = get_detector_for_user(current_user.id)
    try:
        # Update the pomodoro settings
        work_duration = int(data.get('work_duration', 25))
        short_break = int(data.get('short_break', 5))
        long_break = int(data.get('long_break', 15))
        sessions_before_long_break = int(data.get('sessions_before_long_break', 4))
        
        # Apply the settings
        detector.pomodoro.set_durations(
            work=work_duration,
            short_break=short_break,
            long_break=long_break,
            long_break_interval=sessions_before_long_break
        )
        
        # Save to user settings if authenticated
        if current_user.is_authenticated:
            detector.save_user_settings({
                'work_duration': work_duration,
                'short_break_duration': short_break,
                'long_break_duration': long_break,
                'long_break_interval': sessions_before_long_break
            })
        
        # Emit confirmation
        emit('settings_updated', {'status': 'success', 'message': 'Pomodoro settings updated successfully'})
        logging.info(f"Pomodoro settings updated for user {current_user.id}")
        
    except Exception as e:
        logging.error(f"Error updating pomodoro settings: {str(e)}")
        emit('settings_updated', {'status': 'error', 'message': str(e)})


@socketio.on('get_current_settings')
@login_required
def get_current_settings():
    """Get current settings values"""
    detector = get_detector_for_user(current_user.id)
    try:
        settings = {
            'detection': {
                'eye_threshold': detector.detector.config.EYE_AR_THRESH,
                'mouth_threshold': detector.detector.config.MOUTH_AR_THRESH,
                'head_pose_threshold': detector.detector.config.HEAD_POSE_THRESHOLD
            },
            'pomodoro': {
                'work_duration': detector.pomodoro.work_duration,
                'short_break': detector.pomodoro.short_break_duration,
                'long_break': detector.pomodoro.long_break_duration,
                'sessions_before_long_break': detector.pomodoro.long_break_interval
            }
        }
        
        emit('current_settings', settings)
        
    except Exception as e:
        logging.error(f"Error retrieving current settings: {str(e)}")
        emit('current_settings', {'status': 'error', 'message': str(e)})


#======================================================
# MAIN ENTRY POINT
#======================================================

def send_timer_updates():
    """Send timer updates every second while the timer is active"""
    while True:
        try:
            # Check all active detector instances
            for user_id, detector in detector_instances.items():
                if detector.pomodoro and detector.pomodoro.is_active:
                    status = detector.pomodoro.get_timer_status()
                    socketio.emit('pomodoro_update', status, room=user_id)
        except Exception as e:
            logging.error(f"Error sending timer updates: {str(e)}")
        socketio.sleep(1)  # Update every second


def create_test_data(force=False):
    """Create test data for the app if in development mode or forced - but only if no test users exist"""
    # Check if we're in development mode or if force is True
    if os.environ.get('FLASK_ENV') == 'development' or force:
        try:
            # First check if any test users already exist
            from models.user import User
            # Check for one of the test users (e.g., "samsmith")
            existing_user = User.get_by_username("samsmith")
            
            if existing_user:
                logging.info("Test users already exist, skipping test data creation")
                return
                
            # If no test users exist, then create them
            logging.info("No test users found, creating test data...")
            from utils.test_data import create_test_users
            
            users = create_test_users()
            
            logging.info(f"Successfully created test data for leaderboard and achievements")
        except Exception as e:
            logging.error(f"Error creating test data: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())

@app.route('/api/export_session_history')
@login_required
def export_session_history():
    """Export session history as Excel file"""
    if not current_user.is_authenticated:
        return {"error": "User not authenticated"}, 401
        
    try:
        # Get session history for the current user
        user = User.get_by_id(current_user.id)
        if not user:
            return {"error": "User not found"}, 404
            
        # Get all session history
        sessions = user.get_session_history(limit=100)  # Increase limit to get more history
        
        # Prepare data for export
        export_data = []
        for session in sessions:
            # Format timestamps
            start_time = session.get('start_time')
            if isinstance(start_time, datetime):
                start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
                
            end_time = session.get('end_time')
            if isinstance(end_time, datetime):
                end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # Create a row for the export
            export_row = {
                'Date': start_time,
                'End Time': end_time,
                'Duration (minutes)': session.get('duration_minutes', 0),
                'Drowsy Events': session.get('drowsy_events', 0),
                'Yawn Events': session.get('yawn_events', 0),
                'Distraction Events': session.get('distraction_events', 0),
                'Completed Pomodoros': session.get('completed_pomodoros', 0),
                'Points Earned': session.get('points_earned', 0)
            }
            export_data.append(export_row)
            
        # Create a DataFrame
        df = pd.DataFrame(export_data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Session History', index=False)
            
            # Auto-adjust columns' width
            worksheet = writer.sheets['Session History']
            for i, col in enumerate(df.columns):
                # Get maximum column width
                column_len = max(df[col].astype(str).map(len).max(), len(col))
                worksheet.set_column(i, i, column_len + 2)  # Set width with padding
        
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"focus_guard_sessions_{timestamp}.xlsx"
        
        # Return the Excel file
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logging.error(f"Error exporting session history: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return {"error": f"Failed to export data: {str(e)}"}, 500

# Then in the main block, add:
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    socketio.start_background_task(send_timer_updates)
    
    # Add this line to create test data
    create_test_data()
    
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)