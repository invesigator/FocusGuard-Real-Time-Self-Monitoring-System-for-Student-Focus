# FocusGuard: Real-Time Self-Monitoring System for Student Focus

FocusGuard is an innovative real-time computer vision system designed to enhance student focus and productivity during study sessions. Using advanced facial recognition and behavioral analysis, it monitors drowsiness, yawning, and distraction patterns while integrating the proven Pomodoro Technique for optimal study management.

## 🎯 Features

### Core Monitoring Capabilities
- **Drowsiness Detection**: Real-time Eye Aspect Ratio (EAR) analysis to detect when students are becoming drowsy
- **Yawn Detection**: Mouth Aspect Ratio (MAR) monitoring to identify fatigue indicators
- **Distraction Monitoring**: Head pose estimation to detect when attention drifts away from study materials
- **Real-time Alerts**: Immediate audio and visual notifications to refocus attention

### Productivity Tools
- **Integrated Pomodoro Timer**: Configurable work/break cycles to maintain optimal focus
- **Session Management**: Start, pause, and stop monitoring sessions with detailed tracking
- **Statistics Dashboard**: Comprehensive analytics on focus patterns and study habits
- **Session History**: Detailed logs of all study sessions with exportable data

### Gamification System
- **Points & Levels**: Earn experience points based on focus performance
- **Achievements & Badges**: Unlock rewards for consistent study habits
- **Daily Streaks**: Track consecutive days of productive studying
- **Leaderboard**: Compare progress with other users (privacy-focused)

### User Experience
- **Web-based Interface**: Accessible through any modern browser
- **Customizable Settings**: Adjust detection sensitivity and timer preferences
- **User Profiles**: Personal accounts with secure authentication
- **Real-time Updates**: Live statistics and status updates via WebSocket communication

## 🔧 Technology Stack

### Backend
- **Python 3.10+**: Core programming language
- **Flask**: Lightweight web framework
- **Flask-SocketIO**: Real-time bidirectional communication
- **SQLite**: Database for user data and session storage
- **OpenCV**: Computer vision and image processing
- **MediaPipe**: Advanced facial landmark detection (468 landmarks)
- **NumPy**: Mathematical operations for image processing
- **Pygame**: Audio alert management

### Frontend
- **HTML5/CSS3**: Structure and styling
- **JavaScript (ES6+)**: Client-side interactivity
- **Tailwind CSS**: Utility-first CSS framework
- **Socket.IO Client**: Real-time communication
- **Chart.js**: Data visualization for statistics
- **Font Awesome**: Vector icons

## 📋 Prerequisites

- Python 3.10 or higher
- Webcam (minimum 720p resolution recommended)
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Minimum 4GB RAM, 8GB recommended
- Stable lighting conditions for optimal detection

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/invesigator/FocusGuard-Real-Time-Self-Monitoring-System-for-Student-Focus.git
   cd FocusGuard-Real-Time-Self-Monitoring-System-for-Student-Focus
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python utils/create_db.py
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## 📁 Project Structure
```
FocusGuard-Real-Time-Self-Monitoring-System-for-Student-Focus/
├── app.py                    # Main Flask application
├── auth_routes.py            # Authentication endpoints
├── auth.py                   # Authentication utilities
├── config.py                 # Configuration settings
├── create_db.py              # Database initialization
├── main.py                   # Application entry point
├── profile_routes.py         # User profile management
├── analyzers/                # Facial analysis components
│   ├── facial_metrics.py         # EAR/MAR calculations
│   └── head_pose_analyzer.py     # Head pose estimation
├── assets/                 # Static assets
│   └── audio/              # Alert sound files
│       ├── break_complete.wav            # Break completion sound
│       ├── camera_blocked.wav            # Camera blocked alert
│       ├── stay_focus.wav                # Focus reminder
│       ├── take_some_fresh_air_sir.wav   # Break suggestion
│       ├── wake_up_sir.wav               # Drowsiness alert
│       └── work_complete.wav             # Work completion sound
├── database/               # Database storage
│   └── focusguard.db       # SQLite database file
├── detectors/              # Computer vision detection modules
│   └── facial_landmark_detector.py   # MediaPipe face detection
├── models/
│   └── user.py             # User model and database operations
├── templates/              # HTML templates and frontend assets
│   ├── js/                 # JavaScript modules
│   │   ├── modules/        # Modular JS components
│   │   │   ├── app-state.js         # Application state management
│   │   │   ├── auth.js              # Authentication logic
│   │   │   ├── detection.js         # Detection controls
│   │   │   ├── gamification.js      # Gamification features
│   │   │   ├── notifications.js     # Notification system
│   │   │   ├── pomodoro.js          # Pomodoro timer
│   │   │   ├── profile.js           # Profile management
│   │   │   ├── settings.js          # Settings controls
│   │   │   ├── socket-handlers.js   # WebSocket communication
│   │   │   ├── statistics.js        # Statistics display
│   │   │   ├── tabs.js              # Tab navigation
│   │   │   ├── ui-utils.js          # UI utilities
│   │   │   ├── user_dropdown.js     # User dropdown menu
│   │   │   └── user-menu.js         # User menu controls
│   │   └── main.js                  # Main JavaScript entry point
│   ├── forgot_password.html         # Password recovery page
│   ├── index.html                   # Main dashboard
│   ├── login.html                   # Login page
│   ├── profile.html                 # User profile page
│   ├── register.html                # Registration page
│   ├── user_dropdown.html           # User dropdown component
│   ├── styles.css                   # Main stylesheet
│   └── user_dropdown.css            # User dropdown styles
├── ui/# User interface components
│   ├── ui.py           # UI utility functions
├── utils/
│   ├── achievement_manager.py
│   ├── analytics_manager.py       # Database initialization
│   ├── audio_manager.py           # Audio alert management
│   ├── logging_setup.py           # Application logging configuration
│   ├── podomoro_timer.py          # Pomodoro timer functionality
│   ├── statistics_manager.py      # Session statistics processing
│   └──  test_data.py              # Test data and validation
```

## 🎮 Usage

### Getting Started
1. **Register an Account**: Create a new user account with your email and preferred username
2. **Login**: Access your personal dashboard
3. **Camera Setup**: Position your camera at eye level, 50-70cm away from your face
4. **Start Monitoring**: Click "Start" in the Detection tab to begin focus monitoring

### Detection Features
- **Eye Monitoring**: System tracks your eye aspect ratio to detect drowsiness
- **Yawn Detection**: Monitors mouth movements to identify fatigue
- **Head Pose Tracking**: Alerts when you look away from your study materials
- **Custom Thresholds**: Adjust sensitivity in Settings tab for personalized detection

### Pomodoro Timer
- **Work Sessions**: Default 25-minute focused work periods
- **Short Breaks**: 5-minute breaks between work sessions
- **Long Breaks**: 15-30 minute breaks after 4 completed sessions
- **Customizable**: Modify all timer durations in Settings

### Analytics & Progress
- **Session Statistics**: View detailed focus metrics for each study session
- **Progress Tracking**: Monitor improvements in focus duration and quality
- **Data Export**: Download your session data in Excel format
- **Visual Charts**: Interactive graphs showing focus trends over time

## ⚙️ Configuration

### Detection Settings (Adjustable in UI)
```python
# Default thresholds - customizable per user
EYE_AR_THRESH = 0.15        # Eye aspect ratio for drowsiness detection
MOUTH_AR_THRESH = 1.35      # Mouth aspect ratio for yawn detection
HEAD_POSE_THRESHOLD = 10.0  # Head pose angle for distraction (degrees)
```

### Pomodoro Settings (Configurable)
```python
# Default timer durations - customizable per user
WORK_DURATION = 25          # Work session duration (minutes)
SHORT_BREAK_DURATION = 5    # Short break duration (minutes)
LONG_BREAK_DURATION = 15    # Long break duration (minutes)
LONG_BREAK_INTERVAL = 4     # Work sessions before long break
```

## 📊 Performance Metrics

Based on comprehensive testing:

### Detection Accuracy
- **Eye Aspect Ratio (EAR)**: 98.5% accuracy on Driver-Drowsiness-Dataset-D3S
- **Mouth Aspect Ratio (MAR)**: 93.8% overall accuracy on YawnDD dataset
- **Head Pose Estimation**: 96% accuracy for directional detection

### System Performance
- **Frame Processing Rate**: 15-30 FPS on recommended hardware
- **CPU Usage**: ~82% during active monitoring (Intel i5-10300H)
- **Detection Latency**: <100ms for real-time alerts
- **Memory Usage**: ~150MB typical operation

## 🔬 Research & Validation

This project was developed as part of a Bachelor's thesis at Universiti Tunku Abdul Rahman (UTAR), supervised by Ms. Lai Siew Cheng. The system has been evaluated through:

- Systematic testing on established computer vision datasets
- Performance benchmarking on various hardware configurations
- Qualitative user experience assessment
- Comparison with existing focus monitoring solutions

### Key Research Findings
- Integrating multiple detection modalities (EAR, MAR, Head Pose) provides more robust focus monitoring than single-metric approaches
- Gamification elements significantly enhance user engagement with productivity tools
- Real-time feedback is crucial for effective attention training
- Configurable thresholds are essential for individual adaptation

## 🙏 Acknowledgments

- **Supervisor**: Ms. Lai Siew Cheng (UTAR)
- **Moderator**: Mr. Luke Lee Chee Chien (UTAR)
- **Google MediaPipe Team**: For the excellent facial landmark detection framework
- **OpenCV Community**: For comprehensive computer vision tools
- **Dataset Contributors**: Driver-Drowsiness-Dataset-D3S and YawnDD datasets

## 📚 Citation

If you use this work in your research, please cite:
Soo Jia Sheng. _FocusGuard: Real-Time Self-Monitoring System for Enhancing Student Focus Using Computer Vision_. 2025. Available at: https://github.com/invesigator/FocusGuard-Real-Time-Self-Monitoring-System-for-Student-Focus/

---

**⭐ If you find FocusGuard helpful, please consider giving it a star!**
