# Enhanced version of the StatisticsManager class with database integration

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
import os

class StatisticsManager:
    """Manages statistics collection and analysis for drowsiness detection system"""
    
    def __init__(self, save_dir="statistics"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        
        # Make sure the database has the needed tables
        self._ensure_statistics_table_exists()

        # Initialize metrics storage with current timestamp
        self.reset_session()
        
    def _ensure_statistics_table_exists(self):
        """Ensure the statistics table exists in the database"""
        DB_PATH = 'database/focusguard.db'
        
        try:
            # Create database directory if it doesn't exist
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Create statistics table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration_minutes INTEGER DEFAULT 0,
                drowsy_events INTEGER DEFAULT 0,
                yawn_events INTEGER DEFAULT 0,
                distraction_events INTEGER DEFAULT 0,
                completed_pomodoros INTEGER DEFAULT 0,
                visualization_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            ''')
            
            conn.commit()
            conn.close()
            
            logging.info("Statistics table checked/created successfully")
            
        except Exception as e:
            logging.error(f"Error ensuring statistics table exists: {str(e)}")
    
    def reset_session(self):
        """Reset all session data"""
        self.current_session = {
            'start_time': datetime.now(),
            'drowsy_events': [],
            'yawn_events': [],
            'distraction_events': [],
            'camera_blocked_events': [],
            'ear_values': [],
            'mar_values': [],
            'pomodoro_sessions': []
        }
        
        # Reset current state
        self.current_state = {
            'is_drowsy': False,
            'is_yawning': False,
            'is_distracted': False,
            'is_camera_blocked': False
        }
        
        # Reset session summary
        self.session_summary = {
            'total_drowsy_events': 0,
            'total_yawn_events': 0,
            'total_distraction_events': 0,
            'total_camera_blocked_events': 0,
            'average_ear': 0.0,
            'average_mar': 0.0,
            'completed_pomodoro_sessions': 0
        }

    def update_metrics(self, metrics):
        """Update statistics with new metrics from the current frame"""
        try:
            current_time = datetime.now()
        
            # Store user_id from metrics for later use with database functions
            # FIX: Store the user_id from metrics for database operations
            if 'user_id' in metrics:
                self.user_id = metrics['user_id']
            
            # Track EAR and MAR values if they are valid
            if 'ear' in metrics and metrics['ear'] and metrics['ear'] > 0:
                self.current_session['ear_values'].append({
                    'timestamp': current_time,
                    'value': metrics['ear']
                })
            
            if 'mar' in metrics and metrics['mar'] and metrics['mar'] > 0:
                self.current_session['mar_values'].append({
                    'timestamp': current_time,
                    'value': metrics['mar']
                })
        
            # Track drowsy events with state change detection
            if metrics.get('drowsy', False) and not self.current_state['is_drowsy']:
                self.current_session['drowsy_events'].append({
                    'start_time': current_time,
                    'ear_value': metrics.get('ear', 0)
                })
                self.current_state['is_drowsy'] = True
                self.session_summary['total_drowsy_events'] += 1
                logging.debug(f"Drowsy event detected. Total: {self.session_summary['total_drowsy_events']}")
            elif not metrics.get('drowsy', False):
                self.current_state['is_drowsy'] = False
            
            # Track yawning events with state change detection
            if metrics.get('yawning', False) and not self.current_state['is_yawning']:
                self.current_session['yawn_events'].append({
                    'start_time': current_time,
                    'mar_value': metrics.get('mar', 0)
                })
                self.current_state['is_yawning'] = True
                self.session_summary['total_yawn_events'] += 1
                logging.debug(f"Yawn event detected. Total: {self.session_summary['total_yawn_events']}")
            elif not metrics.get('yawning', False):
                self.current_state['is_yawning'] = False
            
            # Track distraction events with state change detection
            is_distracted = metrics.get('distracted', False)
            head_pose = metrics.get('head_pose', 'Unknown')
        
            logging.debug(f"Current head pose: {head_pose}, Is distracted (alert triggered): {is_distracted}")
        
            if is_distracted and not self.current_state['is_distracted']:
                self.current_session['distraction_events'].append({
                    'start_time': current_time,
                    'head_pose': head_pose
                })
                self.current_state['is_distracted'] = True
                self.session_summary['total_distraction_events'] += 1
                logging.debug(f"Distraction event detected. Head pose: {head_pose}. Total: {self.session_summary['total_distraction_events']}")
            elif not is_distracted:
                if self.current_state['is_distracted']:
                    logging.debug("Distraction ended")
                self.current_state['is_distracted'] = False
                
            # Track completed pomodoro sessions
            if 'pomodoro' in metrics:
                pomodoro_status = metrics['pomodoro']
                if pomodoro_status and 'sessions_completed' in pomodoro_status:
                    self.session_summary['completed_pomodoro_sessions'] = pomodoro_status['sessions_completed']

        except Exception as e:
            logging.error(f"Error updating metrics: {str(e)}")
            logging.exception("Full traceback:")

    def save_session(self):
        """Save the current session statistics to a file (legacy method)"""
        try:
            if not self.current_session['drowsy_events'] and not self.current_session['yawn_events'] and not self.current_session['distraction_events']:
                logging.warning("No events recorded in this session")
                return None

            # Calculate session duration
            end_time = datetime.now()
            duration = (end_time - self.current_session['start_time']).total_seconds() // 60
            self.session_summary['session_duration_minutes'] = duration

            # Prepare data for saving
            save_data = {
                'session_summary': self.session_summary,
                'session_details': {
                    'start_time': self.current_session['start_time'].isoformat(),
                    'end_time': end_time.isoformat(),
                    'drowsy_events': [
                        {'timestamp': event['start_time'].isoformat(), 'ear_value': event['ear_value']}
                        for event in self.current_session['drowsy_events']
                    ],
                    'yawn_events': [
                        {'timestamp': event['start_time'].isoformat(), 'mar_value': event['mar_value']}
                        for event in self.current_session['yawn_events']
                    ],
                    'distraction_events': [
                        {'timestamp': event['start_time'].isoformat(), 'head_pose': event['head_pose']}
                        for event in self.current_session['distraction_events']
                    ]
                }
            }
            
            # Generate filename with timestamp
            filename = self.save_dir / f"session_stats_{end_time.strftime('%Y%m%d_%H%M%S')}.json"
            
            # Save to file
            with open(filename, 'w') as f:
                json.dump(save_data, f, indent=4)
                
            logging.info(f"Session statistics saved to {filename}")
            return filename
            
        except Exception as e:
            logging.error(f"Failed to save session statistics: {str(e)}")
            return None
    
    # Updated methods for statistics_manager.py
    def save_session_to_db(self, user_id, session_id=None):
        """
        Save session statistics to the unified database table
        
        Args:
            user_id: The ID of the user
            session_id: Optional ID of an existing session to update with visualization data
        """
        DB_PATH = 'database/focusguard.db'

        if not user_id:
            logging.error("No user ID provided for saving statistics")
            return False
            
        try:
            # Calculate session duration if not already done
            if 'session_duration_minutes' not in self.session_summary:
                end_time = datetime.now()
                duration = (end_time - self.current_session['start_time']).total_seconds() // 60
                self.session_summary['session_duration_minutes'] = duration
            
            # Get visualization data
            viz_data = self.get_visualization_data()
            
            # Connect to the database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            if session_id:
                # Update an existing session with visualization data
                cursor.execute('''
                    UPDATE user_sessions
                    SET visualization_data = ?
                    WHERE id = ? AND user_id = ?
                ''', (
                    json.dumps(viz_data),
                    session_id,
                    user_id
                ))
            else:
                # Find the most recent session for this user that doesn't have visualization data
                cursor.execute('''
                    SELECT id FROM user_sessions
                    WHERE user_id = ? AND visualization_data IS NULL
                    ORDER BY start_time DESC LIMIT 1
                ''', (user_id,))
                
                recent_session = cursor.fetchone()
                
                if recent_session:
                    # Update the recent session
                    cursor.execute('''
                        UPDATE user_sessions
                        SET visualization_data = ?
                        WHERE id = ?
                    ''', (
                        json.dumps(viz_data),
                        recent_session[0]
                    ))
                else:
                    # Create a new session record
                    cursor.execute('''
                        INSERT INTO user_sessions 
                        (user_id, start_time, end_time, duration_minutes, drowsy_events, 
                        yawn_events, distraction_events, completed_pomodoros, points_earned, visualization_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        user_id,
                        self.current_session['start_time'].isoformat(),
                        datetime.now().isoformat(),
                        self.session_summary.get('session_duration_minutes', 0),
                        self.session_summary.get('total_drowsy_events', 0),
                        self.session_summary.get('total_yawn_events', 0),
                        self.session_summary.get('total_distraction_events', 0),
                        self.session_summary.get('completed_pomodoro_sessions', 0),
                        0,  # We don't know points earned here
                        json.dumps(viz_data)
                    ))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Statistics saved to database for user {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving statistics to database for user {user_id}: {str(e)}")
            return False

    def load_session_from_db(self, user_id):
        """
        Load the latest session statistics from the unified database table
        
        Args:
            user_id: The ID of the user to load statistics for
            
        Returns:
            dict: Visualization data if successful, None otherwise
        """
        DB_PATH = 'database/focusguard.db'
        if not user_id:
            logging.error("No user ID provided for loading statistics")
            return None
            
        try:
            # Connect to the database
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row  # Access columns by name
            cursor = conn.cursor()
            
            # Get the most recent session with visualization data
            cursor.execute('''
                SELECT * FROM user_sessions
                WHERE user_id = ? AND visualization_data IS NOT NULL
                ORDER BY start_time DESC
                LIMIT 1
            ''', (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                logging.info(f"No statistics found for user {user_id}")
                return None
                
            # Parse the visualization data
            viz_data = json.loads(row['visualization_data'])
            
            # Add session info to enhance the visualization data
            viz_data['session_info'] = {
                'id': row['id'],
                'date': row['start_time'],
                'duration': row['duration_minutes'],
                'drowsy_events': row['drowsy_events'],
                'yawn_events': row['yawn_events'],
                'distraction_events': row['distraction_events'],
                'completed_pomodoros': row['completed_pomodoros']
            }
            
            logging.info(f"Loaded statistics from database for user {user_id}")
            return viz_data
            
        except Exception as e:
            logging.error(f"Error loading statistics from database for user {user_id}: {str(e)}")
            return None

    def get_all_sessions(self, user_id, limit=10):
        """
        Get all statistics sessions for a user, with optional limit
        
        Args:
            user_id: The ID of the user
            limit: Maximum number of sessions to retrieve
        
        Returns:
            list: List of session data dictionaries
        """
        DB_PATH = 'database/focusguard.db'
        try:
            # Connect to the database
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM user_sessions
                WHERE user_id = ?
                ORDER BY start_time DESC
                LIMIT ?
            ''', (user_id, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            sessions = []
            for row in rows:
                session = dict(row)
                # Convert visualization_data to object if needed
                if 'visualization_data' in session and session['visualization_data']:
                    try:
                        session['visualization_data'] = json.loads(session['visualization_data'])
                    except:
                        # Keep as string if JSON parsing fails
                        pass
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logging.error(f"Error retrieving session history for user {user_id}: {str(e)}")
            return []
    
    def clear_user_statistics(self, user_id):
        """
        Clear all statistics for a specific user
        
        Args:
            user_id: The ID of the user to clear statistics for
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not user_id:
            logging.error("No user ID provided for clearing statistics")
            return False
            
        try:
            # Connect to the database
            DB_PATH = 'database/focusguard.db'
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Delete all statistics for the user
            cursor.execute('DELETE FROM user_statistics WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            
            logging.info(f"Cleared all statistics for user {user_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error clearing statistics for user {user_id}: {str(e)}")
            return False
        
    def get_visualization_data(self, from_db=False, user_id=None):
        """Prepare data for front-end visualization"""
        try:
            # Return empty data if no session active
            if not self.current_session['start_time']:
                return {}
                    
            # Calculate session duration
            current_time = datetime.now()
            duration_seconds = (current_time - self.current_session['start_time']).total_seconds()
            duration_minutes = int(duration_seconds // 60)
            
            # Timeline data - create time buckets (5 minute intervals)
            bucket_size = 300  # 5 minutes in seconds
            num_buckets = max(1, int(duration_seconds // bucket_size) + 1)
            
            timeline_data = []
            
            for i in range(num_buckets):
                bucket_start = self.current_session['start_time'] + timedelta(seconds=i * bucket_size)
                bucket_end = bucket_start + timedelta(seconds=bucket_size)
                
                # Count events in this time bucket
                drowsy_count = sum(1 for event in self.current_session['drowsy_events'] 
                                if bucket_start <= event['start_time'] < bucket_end)
                yawn_count = sum(1 for event in self.current_session['yawn_events'] 
                            if bucket_start <= event['start_time'] < bucket_end)
                distraction_count = sum(1 for event in self.current_session['distraction_events'] 
                                    if bucket_start <= event['start_time'] < bucket_end)
                
                # Calculate bucket label
                time_label = bucket_start.strftime('%H:%M')
                
                timeline_data.append({
                    'time': time_label,
                    'drowsy': drowsy_count,
                    'yawn': yawn_count,
                    'distraction': distraction_count
                })
            
            # Distribution data
            total_events = (self.session_summary['total_drowsy_events'] + 
                        self.session_summary['total_yawn_events'] + 
                        self.session_summary['total_distraction_events'])
            
            distribution_data = []
            
            if total_events > 0:
                distribution_data = [
                    {
                        'name': 'Drowsy Events',
                        'value': self.session_summary['total_drowsy_events'],
                        'percentage': (self.session_summary['total_drowsy_events'] / total_events) * 100 if total_events > 0 else 0
                    },
                    {
                        'name': 'Yawn Events',
                        'value': self.session_summary['total_yawn_events'],
                        'percentage': (self.session_summary['total_yawn_events'] / total_events) * 100 if total_events > 0 else 0
                    },
                    {
                        'name': 'Distraction Events',
                        'value': self.session_summary['total_distraction_events'],
                        'percentage': (self.session_summary['total_distraction_events'] / total_events) * 100 if total_events > 0 else 0
                    }
                ]
            
            # Historical sessions data - IMPORTANT FIX: Always use database for historical data
            # Only use current user's sessions when user_id is provided
            historical_data = self.get_historical_sessions(from_db=True, user_id=user_id) if user_id else []

            # Add session_info to the returned data
            session_info = {
                'duration': duration_minutes,
                'drowsy_events': self.session_summary['total_drowsy_events'],
                'yawn_events': self.session_summary['total_yawn_events'],
                'distraction_events': self.session_summary['total_distraction_events']
            }
            
            return {
                'timeline': timeline_data,
                'distribution': distribution_data,
                'historical': historical_data,
                'session_info': session_info  # Add this field
            }
            
        except Exception as e:
            logging.error(f"Error preparing visualization data: {str(e)}")
            return {}
    
    def get_historical_sessions(self, from_db=False, user_id=None):
        """
        Get data from previous sessions for comparison
        
        Args:
            from_db: Whether to get data from database instead of files
            user_id: User ID if getting from database
            
        Returns:
            list: List of historical session data
        """
        # FIX: Always prefer database method when user_id is provided
        if user_id:
            return self._get_historical_sessions_from_db(user_id)
        elif from_db and user_id:
            return self._get_historical_sessions_from_db(user_id)
        else:
            # Only fall back to files if no user_id is provided
            logging.warning("No user_id provided, falling back to file-based session history")
            return self._get_historical_sessions_from_files()
    
    def _get_historical_sessions_from_db(self, user_id):
        """Get historical sessions from database"""
        try:
            # Connect to the database
            DB_PATH = 'database/focusguard.db'
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get the 5 most recent sessions
            cursor.execute('''
                SELECT * FROM user_statistics
                WHERE user_id = ?
                ORDER BY session_date DESC
                LIMIT 5
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            history = []
            for row in dict(row):
                try:
                    # Parse date from session_date
                    session_date = datetime.fromisoformat(row['session_date'])
                    date_label = session_date.strftime('%m/%d %H:%M')
                except:
                    date_label = "Unknown"
                
                history.append({
                    'date': date_label,
                    'duration': row['duration_minutes'],
                    'drowsy': row['drowsy_events'],
                    'yawn': row['yawn_events'],
                    'distraction': row['distraction_events']
                })
            
            return history
            
        except Exception as e:
            logging.error(f"Error retrieving historical sessions from database: {str(e)}")
            return []
        
    def _get_historical_sessions_from_files(self):
        """Get historical sessions from files (legacy method)"""
        try:
            # Find all session JSON files
            session_files = list(self.save_dir.glob('session_stats_*.json'))
            
            # Sort by date (newest first)
            session_files.sort(reverse=True)
            
            # Limit to last 5 sessions
            session_files = session_files[:5]
            
            history = []
            
            for file_path in session_files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    # Extract date from filename
                    date_str = file_path.stem.replace('session_stats_', '')
                    try:
                        # Parse date from filename format YYYYMMDD_HHMMSS
                        session_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                        date_label = session_date.strftime('%m/%d %H:%M')
                    except:
                        date_label = "Unknown"
                    
                    # Extract key metrics
                    summary = data.get('session_summary', {})
                    duration = summary.get('session_duration_minutes', 0)
                    
                    history.append({
                        'date': date_label,
                        'duration': duration,
                        'drowsy': summary.get('total_drowsy_events', 0),
                        'yawn': summary.get('total_yawn_events', 0),
                        'distraction': summary.get('total_distraction_events', 0)
                    })
                    
                except Exception as e:
                    logging.error(f"Error processing session file {file_path}: {str(e)}")
                    continue
            
            return history
            
        except Exception as e:
            logging.error(f"Error retrieving historical sessions: {str(e)}")
            return []