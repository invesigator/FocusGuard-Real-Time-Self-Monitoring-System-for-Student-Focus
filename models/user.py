import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
import sqlite3
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DB_PATH = 'database/focusguard.db'

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Table creation and column addition code here
        # Create users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )
        ''')
        
        # Create user settings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            eye_ar_thresh REAL DEFAULT 0.15,
            mouth_ar_thresh REAL DEFAULT 1.35,
            head_pose_threshold REAL DEFAULT 10.0,
            work_duration INTEGER DEFAULT 25,
            short_break_duration INTEGER DEFAULT 5,
            long_break_duration INTEGER DEFAULT 15,
            long_break_interval INTEGER DEFAULT 4,
            profile_points INTEGER DEFAULT 0,
            profile_level INTEGER DEFAULT 1,
            profile_experience INTEGER DEFAULT 0,
            daily_streak INTEGER DEFAULT 0,
            pomodoro_streak INTEGER DEFAULT 0,
            last_session_date TEXT,
            last_check_in_date TEXT,
            total_focus_minutes INTEGER DEFAULT 0,
            total_sessions INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # Create unified session history table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration_minutes INTEGER DEFAULT 0,
            drowsy_events INTEGER DEFAULT 0,
            yawn_events INTEGER DEFAULT 0,
            distraction_events INTEGER DEFAULT 0,
            completed_pomodoros INTEGER DEFAULT 0,
            points_earned INTEGER DEFAULT 0,
            visualization_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Create achievements table (if it doesn't exist)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            achievement_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            points INTEGER DEFAULT 0,
            completed BOOLEAN DEFAULT 0,
            completed_at TIMESTAMP,
            UNIQUE(user_id, achievement_id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Create badges table (if it doesn't exist)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            unlocked BOOLEAN DEFAULT 0,
            unlocked_at TIMESTAMP,
            UNIQUE(user_id, badge_id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')

        # Check if all columns exist in user_settings, if not add them
        cursor.execute("PRAGMA table_info(user_settings)")
        columns = {row[1] for row in cursor.fetchall()}
        
        # Add any missing columns
        missing_columns = {
            'profile_points': 'INTEGER DEFAULT 0',
            'profile_level': 'INTEGER DEFAULT 1',
            'profile_experience': 'INTEGER DEFAULT 0',
            'daily_streak': 'INTEGER DEFAULT 0',
            'pomodoro_streak': 'INTEGER DEFAULT 0',
            'last_session_date': 'TEXT',
            'last_check_in_date': 'TEXT',
            'total_focus_minutes': 'INTEGER DEFAULT 0',
            'total_sessions': 'INTEGER DEFAULT 0'
        }
        
        for column, data_type in missing_columns.items():
            if column not in columns:
                try:
                    cursor.execute(f"ALTER TABLE user_settings ADD COLUMN {column} {data_type}")
                    logging.info(f"Added missing column {column} to user_settings")
                except sqlite3.OperationalError:
                    logging.warning(f"Column {column} already exists or couldn't be added")

        conn.commit()
        logger.info("Database initialized successfully")
    except sqlite3.Error as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise
    finally:
        conn.close()


class User(UserMixin):
    """User model for authentication and profile management"""
    
    def __init__(self, id=None, username=None, email=None, full_name=None, password_hash=None, 
                 created_at=None, last_login=None, is_active=True):
        self.id = id
        self.username = username
        self.email = email
        self.full_name = full_name
        self.password_hash = password_hash
        self.created_at = created_at
        self.last_login = last_login
        # Don't set is_active directly since it's handled by UserMixin
        self._is_active = is_active
    
    # Override is_active property from UserMixin
    @property
    def is_active(self):
        return self._is_active
    
    @staticmethod
    def get_by_id(user_id):
        """Retrieve a user by their ID"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        conn.close()
        
        if user_data:
            # Convert timestamp strings to datetime objects if they exist
            created_at = user_data['created_at']
            last_login = user_data['last_login']
            
            # Convert created_at to datetime if it's a string
            if created_at and isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except ValueError:
                    # Keep as string if conversion fails
                    pass
                    
            # Convert last_login to datetime if it's a string
            if last_login and isinstance(last_login, str):
                try:
                    last_login = datetime.fromisoformat(last_login)
                except ValueError:
                    # Keep as string if conversion fails
                    pass
            
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                password_hash=user_data['password_hash'],
                created_at=created_at,
                last_login=last_login,
                is_active=bool(user_data['is_active'])
            )
        
        return None
    
    @staticmethod
    def get_by_username(username):
        """Retrieve a user by their username"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                password_hash=user_data['password_hash'],
                created_at=user_data['created_at'],
                last_login=user_data['last_login'],
                is_active=bool(user_data['is_active'])
            )
        
        return None
    
    @staticmethod
    def get_by_email(email):
        """Retrieve a user by their email"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user_data = cursor.fetchone()
        
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                full_name=user_data['full_name'],
                password_hash=user_data['password_hash'],
                created_at=user_data['created_at'],
                last_login=user_data['last_login'],
                is_active=bool(user_data['is_active'])
            )
        
        return None
    
    @staticmethod
    def create(username, email, full_name, password):
        """Create a new user"""
        # Check if username or email already exists
        if User.get_by_username(username) or User.get_by_email(email):
            return None
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            # Generate password hash
            password_hash = generate_password_hash(password)
            
            # Get current timestamp
            current_time = datetime.now()
            
            # Insert new user with explicit is_active value
            cursor.execute(
                "INSERT INTO users (username, email, full_name, password_hash, created_at, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                (username, email, full_name, password_hash, current_time, 1)
            )
            
            user_id = cursor.lastrowid
            
            # Create default settings for the user
            cursor.execute(
                "INSERT INTO user_settings (user_id) VALUES (?)",
                (user_id,)
            )
            
            conn.commit()
            
            # Create and return a user object directly
            return User(
                id=user_id,
                username=username,
                email=email,
                full_name=full_name,
                password_hash=password_hash,
                created_at=current_time,
                last_login=None,
                is_active=True
            )
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating user: {str(e)}")
            return None
        finally:
            conn.close()
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update the last login timestamp for the user"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now(), self.id)
            )
            conn.commit()
            self.last_login = datetime.now()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating last login: {str(e)}")
            return False
        finally:
            conn.close()
            
    def _get_db_connection(self):
        """Get a database connection for direct use"""
        return sqlite3.connect(DB_PATH)
    
    def get_settings(self):
        """Get user settings"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (self.id,))
        settings = cursor.fetchone()
        
        conn.close()
        
        if settings:
            return dict(settings)
        
        return None
    
    def update_settings(self, settings_dict):
        """Update user settings"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            # Create SET clause dynamically from provided settings
            set_clause = ", ".join([f"{key} = ?" for key in settings_dict.keys()])
            values = list(settings_dict.values())
            values.append(self.id)  # Add user_id for WHERE clause
            
            cursor.execute(
                f"UPDATE user_settings SET {set_clause} WHERE user_id = ?",
                values
            )
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating settings: {str(e)}")
            return False
        finally:
            conn.close()
    
    def save_session(self, session_data):
        """Save a completed focus session to the unified table"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """
                INSERT INTO user_sessions 
                (user_id, start_time, end_time, duration_minutes, drowsy_events, 
                yawn_events, distraction_events, completed_pomodoros, points_earned)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.id,
                    session_data.get('start_time'),
                    session_data.get('end_time'),
                    session_data.get('duration_minutes', 0),
                    session_data.get('drowsy_events', 0),
                    session_data.get('yawn_events', 0),
                    session_data.get('distraction_events', 0),
                    session_data.get('completed_pomodoros', 0),
                    session_data.get('points_earned', 0)
                )
            )
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving session: {str(e)}")
            return None
        finally:
            conn.close()
    
    def get_session_history(self, limit=10):
        """Get user's session history from the unified table"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM user_sessions WHERE user_id = ? ORDER BY start_time DESC LIMIT ?",
            (self.id, limit)
        )
        sessions = cursor.fetchall()
        
        conn.close()
        
        # Convert sessions to dictionaries with properly formatted timestamps
        result = []
        for session in sessions:
            session_dict = dict(session)
            
            # Convert start_time to datetime if it's a string
            if 'start_time' in session_dict and session_dict['start_time']:
                if isinstance(session_dict['start_time'], str):
                    try:
                        session_dict['start_time'] = datetime.fromisoformat(session_dict['start_time'])
                    except ValueError:
                        # Keep as string if conversion fails
                        pass
                    
            # Convert end_time to datetime if it's a string
            if 'end_time' in session_dict and session_dict['end_time']:
                if isinstance(session_dict['end_time'], str):
                    try:
                        session_dict['end_time'] = datetime.fromisoformat(session_dict['end_time'])
                    except ValueError:
                        # Keep as string if conversion fails
                        pass
                    
            result.append(session_dict)
        
        return result
    

# Add these methods to the User class in user.py if they don't exist
# Otherwise, make sure they're defined correctly and properly integrated

    def get_achievements(self):
        """Get user achievements from database"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM user_achievements WHERE user_id = ?",
            (self.id,)
        )
        achievements = cursor.fetchall()
        
        conn.close()
        
        return [dict(achievement) for achievement in achievements]

    def save_achievement(self, achievement_data):
        """Save or update a user achievement"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            # Check if achievement exists
            cursor.execute(
                "SELECT id FROM user_achievements WHERE user_id = ? AND achievement_id = ?",
                (self.id, achievement_data['id'])
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing achievement
                cursor.execute(
                    """
                    UPDATE user_achievements
                    SET completed = ?, completed_at = ?
                    WHERE user_id = ? AND achievement_id = ?
                    """,
                    (
                        achievement_data['completed'],
                        datetime.now() if achievement_data['completed'] else None,
                        self.id,
                        achievement_data['id']
                    )
                )
            else:
                # Insert new achievement
                cursor.execute(
                    """
                    INSERT INTO user_achievements
                    (user_id, achievement_id, name, description, points, completed, completed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.id,
                        achievement_data['id'],
                        achievement_data['name'],
                        achievement_data['description'],
                        achievement_data['points'],
                        achievement_data['completed'],
                        datetime.now() if achievement_data['completed'] else None
                    )
                )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving achievement: {str(e)}")
            return False
        finally:
            conn.close()

    def get_badges(self):
        """Get user badges from database"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM user_badges WHERE user_id = ?",
            (self.id,)
        )
        badges = cursor.fetchall()
        
        conn.close()
        
        return [dict(badge) for badge in badges]

    def save_badge(self, badge_data):
        """Save or update a user badge"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            # Check if badge exists
            cursor.execute(
                "SELECT id FROM user_badges WHERE user_id = ? AND badge_id = ?",
                (self.id, badge_data['id'])
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing badge
                cursor.execute(
                    """
                    UPDATE user_badges
                    SET unlocked = ?, unlocked_at = ?
                    WHERE user_id = ? AND badge_id = ?
                    """,
                    (
                        badge_data['unlocked'],
                        datetime.now() if badge_data['unlocked'] else None,
                        self.id,
                        badge_data['id']
                    )
                )
            else:
                # Insert new badge
                cursor.execute(
                    """
                    INSERT INTO user_badges
                    (user_id, badge_id, name, description, unlocked, unlocked_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.id,
                        badge_data['id'],
                        badge_data['name'],
                        badge_data['description'],
                        badge_data['unlocked'],
                        datetime.now() if badge_data['unlocked'] else None
                    )
                )
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving badge: {str(e)}")
            return False
        finally:
            conn.close()