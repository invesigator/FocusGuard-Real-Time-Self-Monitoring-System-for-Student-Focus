# utils/achievement_manager.py
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

class AchievementManager:
    """Manages the gamification and reward system for FocusGuard"""
    
    def __init__(self, user_id=None, save_dir="gamification"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        
        # Store user ID for database operations
        self.user_id = user_id
        self.user = None
        
        # Get user object if user_id is provided
        if user_id:
            from models.user import User
            self.user = User.get_by_id(user_id)
        
        # User profile (in-memory cache)
        self.user_profile = {
            'points': 0,
            'level': 1,
            'experience': 0,
            'streaks': {
                'daily_login': 0,
                'pomodoro_sessions': 0,
            },
            'last_session_date': None,
            'last_check_in_date': None,  # Add this line
        }
        
        # Define achievements list (template)
        self.achievements = [
            {
                'id': 'first_session',
                'name': 'First Steps',
                'description': 'Complete your first focus session',
                'icon': 'baby-carriage',
                'points': 50,
                'completed': False
            },
            {
                'id': 'focus_30m',
                'name': 'Focused Mind',
                'description': 'Stay focused for 30 minutes with less than 3 distractions',
                'icon': 'bullseye',
                'points': 100,
                'completed': False
            },
            {
                'id': 'pomodoro_5',
                'name': 'Pomodoro Novice',
                'description': 'Complete 5 Pomodoro sessions',
                'icon': 'clock',
                'points': 150,
                'completed': False
            },
            {
                'id': 'pomodoro_20',
                'name': 'Pomodoro Master',
                'description': 'Complete 20 Pomodoro sessions',
                'icon': 'stopwatch',
                'points': 300,
                'completed': False
            },
            {
                'id': 'no_drowsy_session',
                'name': 'Wide Awake',
                'description': 'Complete a session with no drowsiness events',
                'icon': 'eye',
                'points': 200,
                'completed': False
            },
            {
                'id': 'streak_3',
                'name': 'Consistency is Key',
                'description': 'Use FocusGuard for 3 days in a row',
                'icon': 'calendar-check',
                'points': 250,
                'completed': False
            }
        ]
        
        # Define badges list (template)
        self.badges = [
            {
                'id': 'focus_novice',
                'name': 'Focus Novice',
                'description': 'Reach level 5',
                'icon': 'medal',
                'unlocked': False,
                'level_required': 5
            },
            {
                'id': 'focus_intermediate',
                'name': 'Focus Intermediate',
                'description': 'Reach level 10',
                'icon': 'medal',
                'unlocked': False,
                'level_required': 10
            },
            {
                'id': 'focus_master',
                'name': 'Focus Master',
                'description': 'Reach level 20',
                'icon': 'crown',
                'unlocked': False,
                'level_required': 20
            },
            {
                'id': 'productivity_champion',
                'name': 'Productivity Champion',
                'description': 'Complete 50 Pomodoro sessions',
                'icon': 'trophy',
                'unlocked': False,
                'pomodoro_required': 50
            }
        ]
        
        # Level thresholds (XP needed for each level)
        self.level_thresholds = [0, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500, 5500, 
                                6600, 7800, 9100, 10500, 12000, 13600, 15300, 17100, 19000, 21000]
        
        # Point rules
        self.point_rules = {
            'minute_focused': 2,          # 2 points per minute of focus
            'pomodoro_complete': 50,      # 50 points per completed pomodoro session
            'drowsy_penalty': -10,        # -10 points per drowsy event
            'distraction_penalty': -5,    # -5 points per distraction event
            'daily_login': 20,            # 20 points for logging in each day
            'streak_bonus': 10            # 10 bonus points per day in streak
        }
        
        # Initialize from database if user is provided
        if self.user:
            self.load_profile_from_db()

        
    def load_profile_from_db(self):
        """Load user profile from database"""
        if not self.user:
            logging.warning("No user provided for load_profile_from_db")
            return False
        
        try:
            # Log start of loading
            logging.info(f"Loading profile from database for user {self.user.id}")
            
            # Load achievements from database
            user_achievements = self.user.get_achievements()
            if user_achievements:
                # Update achievement completion status
                for saved in user_achievements:
                    achievement_found = False
                    for achievement in self.achievements:
                        if achievement['id'] == saved['achievement_id']:
                            achievement['completed'] = bool(saved['completed'])
                            achievement_found = True
                            logging.info(f"Loaded achievement: {saved['achievement_id']}, completed: {saved['completed']}")
                    
                    if not achievement_found:
                        logging.warning(f"Achievement {saved['achievement_id']} found in DB but not in local list")
            else:
                # Initialize achievements in database
                logging.info("No achievements found in database, initializing...")
                for achievement in self.achievements:
                    self.user.save_achievement({
                        'id': achievement['id'],
                        'name': achievement['name'],
                        'description': achievement['description'],
                        'points': achievement['points'],
                        'completed': achievement['completed']
                    })
                    
            # Load badges from database
            user_badges = self.user.get_badges()
            if user_badges:
                # Update badge unlock status
                for saved in user_badges:
                    badge_found = False
                    for badge in self.badges:
                        if badge['id'] == saved['badge_id']:
                            badge['unlocked'] = bool(saved['unlocked'])
                            badge_found = True
                            logging.info(f"Loaded badge: {saved['badge_id']}, unlocked: {saved['unlocked']}")
                    
                    if not badge_found:
                        logging.warning(f"Badge {saved['badge_id']} found in DB but not in local list")
            else:
                # Initialize badges in database
                logging.info("No badges found in database, initializing...")
                for badge in self.badges:
                    self.user.save_badge({
                        'id': badge['id'],
                        'name': badge['name'],
                        'description': badge['description'],
                        'unlocked': badge['unlocked']
                    })
                    
            # Load user's profile data from settings
            settings = self.user.get_settings()
            if settings:
                # Log the settings loaded
                logging.info(f"Loaded settings: {settings}")
                
                if 'profile_points' in settings:
                    self.user_profile['points'] = settings['profile_points']
                if 'profile_level' in settings:
                    self.user_profile['level'] = settings['profile_level']
                if 'profile_experience' in settings:
                    self.user_profile['experience'] = settings['profile_experience']
                if 'daily_streak' in settings:
                    self.user_profile['streaks']['daily_login'] = settings['daily_streak']
                if 'pomodoro_streak' in settings:
                    self.user_profile['streaks']['pomodoro_sessions'] = settings['pomodoro_streak']
                if 'last_session_date' in settings and settings['last_session_date']:
                    try:
                        self.user_profile['last_session_date'] = datetime.fromisoformat(settings['last_session_date'])
                    except (ValueError, TypeError):
                        logging.error(f"Invalid last_session_date format: {settings['last_session_date']}")
                        self.user_profile['last_session_date'] = None
                if 'last_check_in_date' in settings and settings['last_check_in_date']:
                    self.user_profile['last_check_in_date'] = settings['last_check_in_date']
                        
                logging.info(f"Loaded user profile: points={self.user_profile['points']}, level={self.user_profile['level']}")
            else:
                logging.warning(f"No settings found for user {self.user.id}")
                
            return True
                
        except Exception as e:
            logging.error(f"Error loading user profile from database: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return False

    def save_profile(self):
        """Save user profile to database and file"""
        if self.user:
            try:
                # Save achievements one by one
                for achievement in self.achievements:
                    self.user.save_achievement(achievement)
                    
                # Save badges one by one
                for badge in self.badges:
                    self.user.save_badge(badge)
                    
                # Save profile data to user settings
                profile_settings = {
                    'profile_points': self.user_profile['points'],
                    'profile_level': self.user_profile['level'],
                    'profile_experience': self.user_profile['experience'],
                    'daily_streak': self.user_profile['streaks']['daily_login'],
                    'pomodoro_streak': self.user_profile['streaks']['pomodoro_sessions']
                }
                
                # Save last_session_date and last_check_in_date if they exist
                if self.user_profile.get('last_session_date'):
                    if isinstance(self.user_profile['last_session_date'], datetime):
                        profile_settings['last_session_date'] = self.user_profile['last_session_date'].isoformat()
                    else:
                        profile_settings['last_session_date'] = self.user_profile['last_session_date']
                        
                if self.user_profile.get('last_check_in_date'):
                    profile_settings['last_check_in_date'] = self.user_profile['last_check_in_date']
                        
                # Update user settings
                success = self.user.update_settings(profile_settings)
                
                if success:
                    logging.info(f"User profile saved to database for user {self.user.id}")
                    return True
                else:
                    logging.error(f"Failed to save user profile settings for user {self.user.id}")
                    return False
                    
            except Exception as e:
                logging.error(f"Error saving user profile to database: {str(e)}")
                return False
        else:
            logging.warning("No user provided for save_profile")
            return False
    
    def _save_profile_to_file(self):
        """
        Fallback method to save profile to file 
        This is kept for backward compatibility but actually doesn't save anything
        as we're using the database instead
        """
        logging.info("Using database storage only, file saving is disabled")
        return True
            
    def add_points(self, amount, reason=""):
        """Add points to user profile and update level"""
        self.user_profile['points'] += amount
        self.user_profile['experience'] += amount
        
        # Check if user has leveled up
        current_level = self.user_profile['level']
        new_level = current_level
        
        # Find the appropriate level based on experience
        current_xp = self.user_profile['experience']
        
        # Get the XP threshold for the next level
        if current_level < len(self.level_thresholds):
            next_level_threshold = self.level_thresholds[current_level]
            # If XP meets or exceeds the threshold for next level, level up
            if current_xp >= next_level_threshold:
                new_level = current_level + 1
        
        # Standard level calculation as fallback
        for level, threshold in enumerate(self.level_thresholds, 1):
            if current_xp >= threshold:
                new_level = level
        
        # If level has increased, update and return the new level
        if new_level > current_level:
            self.user_profile['level'] = new_level
            self.check_level_badges()
            return {'points_added': amount, 'new_level': new_level, 'old_level': current_level}
        
        return {'points_added': amount}
        
    def check_session_achievements(self, session_stats):
        """Check achievements based on session statistics"""
        newly_completed = []
        
        # Check for first session achievement
        if not self._is_achievement_completed('first_session'):
            newly_completed.append(self._complete_achievement('first_session'))
            
        # Check for 30-minute focus with < 3 distractions
        session_duration = session_stats.get('session_duration_minutes', 0)
        distraction_events = session_stats.get('total_distraction_events', 0)
        
        if session_duration >= 30 and distraction_events < 3 and not self._is_achievement_completed('focus_30m'):
            newly_completed.append(self._complete_achievement('focus_30m'))
            
        # Check for no drowsiness
        drowsy_events = session_stats.get('total_drowsy_events', 0)
        if drowsy_events == 0 and session_duration >= 15 and not self._is_achievement_completed('no_drowsy_session'):
            newly_completed.append(self._complete_achievement('no_drowsy_session'))
        
        return newly_completed
        
    def check_pomodoro_achievements(self, completed_sessions):
        """Check achievements related to Pomodoro sessions"""
        newly_completed = []
        
        # Update the pomodoro streak
        self.user_profile['streaks']['pomodoro_sessions'] = completed_sessions
        
        # Check for pomodoro achievements
        if completed_sessions >= 5 and not self._is_achievement_completed('pomodoro_5'):
            newly_completed.append(self._complete_achievement('pomodoro_5'))
            
        if completed_sessions >= 20 and not self._is_achievement_completed('pomodoro_20'):
            newly_completed.append(self._complete_achievement('pomodoro_20'))
            
        # Check for pomodoro badges
        for badge in self.badges:
            if 'pomodoro_required' in badge and not badge['unlocked']:
                if completed_sessions >= badge['pomodoro_required']:
                    badge['unlocked'] = True
                    newly_completed.append({
                        'type': 'badge',
                        'id': badge['id'],
                        'name': badge['name'],
                        'description': badge['description']
                    })
        
        return newly_completed
        
    def check_streak_achievements(self):
        """Check achievements related to streaks"""
        newly_completed = []
        streak_days = self.user_profile['streaks']['daily_login']
        
        if streak_days >= 3 and not self._is_achievement_completed('streak_3'):
            newly_completed.append(self._complete_achievement('streak_3'))
            
        return newly_completed
    
    def check_daily_login(self):
        """Check if this is a new day and update streaks accordingly"""
        today = datetime.now().date()
        
        # First prioritize last_check_in_date over last_session_date for streak continuity
        last_check_in = None
        if self.user_profile.get('last_check_in_date'):
            try:
                # Handle string ISO format dates
                if isinstance(self.user_profile['last_check_in_date'], str):
                    last_check_in = datetime.fromisoformat(self.user_profile['last_check_in_date']).date()
                else:
                    last_check_in = self.user_profile['last_check_in_date'].date()
            except (ValueError, TypeError, AttributeError) as e:
                logging.error(f"Error parsing last_check_in_date: {e}")
                last_check_in = None
        
        # Fallback to last_session_date if no check-in date
        last_session = None
        if not last_check_in and self.user_profile.get('last_session_date'):
            try:
                if isinstance(self.user_profile['last_session_date'], str):
                    last_session = datetime.fromisoformat(self.user_profile['last_session_date']).date()
                else:
                    last_session = self.user_profile['last_session_date'].date()
            except (ValueError, TypeError, AttributeError) as e:
                logging.error(f"Error parsing last_session_date: {e}")
                last_session = None
        
        # Use the most recent date between check-in and session
        last_date = last_check_in if last_check_in else last_session
        
        result = {'new_day': False, 'streak_continued': False, 'streak_reset': False}
        
        if not last_date:
            # First time ever logging in
            self.user_profile['last_check_in_date'] = datetime.now().isoformat()
            self.user_profile['streaks']['daily_login'] = 1
            result['new_day'] = True
            self.add_points(self.point_rules['daily_login'], "First login")
            logging.info("First time check-in, streak set to 1")
            
        elif last_date < today:
            # It's a new day
            result['new_day'] = True
            yesterday = today - timedelta(days=1)
            
            if last_date == yesterday:
                # Consecutive day (streak continues)
                # Increment the streak instead of resetting it
                current_streak = self.user_profile['streaks']['daily_login']
                self.user_profile['streaks']['daily_login'] += 1
                new_streak = self.user_profile['streaks']['daily_login']
                
                result['streak_continued'] = True
                logging.info(f"Streak continued: {current_streak} -> {new_streak}")
                
                # Award points for daily login + streak bonus
                streak_bonus = self.point_rules['streak_bonus'] * self.user_profile['streaks']['daily_login']
                self.add_points(self.point_rules['daily_login'] + streak_bonus, 
                            f"Daily login + streak bonus (day {self.user_profile['streaks']['daily_login']})")
            else:
                # Streak broken - only if it's been more than one day since last check-in
                logging.info(f"Streak reset: Last check-in {last_date}, today {today}")
                self.user_profile['streaks']['daily_login'] = 1
                result['streak_reset'] = True
                
                # Award points just for daily login
                self.add_points(self.point_rules['daily_login'], "Daily login (streak reset)")
            
            # Update the last check-in date to today
            self.user_profile['last_check_in_date'] = datetime.now().isoformat()
            
        return result
    
    def calculate_session_points(self, session_stats):
        """Calculate points earned in a session based on focus metrics"""
        points = 0
        details = []
        
        # Points for focused time
        duration_minutes = session_stats.get('session_duration_minutes', 0)
        focused_points = duration_minutes * self.point_rules['minute_focused']
        points += focused_points
        details.append({
            'reason': 'Focused time',
            'points': focused_points,
            'explanation': f"{duration_minutes} minutes × {self.point_rules['minute_focused']} points"
        })
        
        # Penalties for drowsy events
        drowsy_events = session_stats.get('total_drowsy_events', 0)
        if drowsy_events > 0:
            drowsy_penalty = drowsy_events * self.point_rules['drowsy_penalty']
            points += drowsy_penalty  # This will be negative
            details.append({
                'reason': 'Drowsiness penalty',
                'points': drowsy_penalty,
                'explanation': f"{drowsy_events} events × {self.point_rules['drowsy_penalty']} points"
            })
        
        # Penalties for distraction events
        distraction_events = session_stats.get('total_distraction_events', 0)
        if distraction_events > 0:
            distraction_penalty = distraction_events * self.point_rules['distraction_penalty']
            points += distraction_penalty  # This will be negative
            details.append({
                'reason': 'Distraction penalty',
                'points': distraction_penalty,
                'explanation': f"{distraction_events} events × {self.point_rules['distraction_penalty']} points"
            })
            
        # Bonus for completed pomodoro sessions
        pomodoro_sessions = session_stats.get('completed_pomodoro_sessions', 0)
        if pomodoro_sessions > 0:
            pomodoro_points = pomodoro_sessions * self.point_rules['pomodoro_complete']
            points += pomodoro_points
            details.append({
                'reason': 'Completed Pomodoro sessions',
                'points': pomodoro_points,
                'explanation': f"{pomodoro_sessions} sessions × {self.point_rules['pomodoro_complete']} points"
            })
        
        # Ensure points don't go negative for a session
        if points < 0:
            points = 0
            details.append({
                'reason': 'Minimum points floor',
                'points': 0,
                'explanation': 'Session points cannot go below zero'
            })
            
        # Add the points
        point_result = self.add_points(points, "Session completion")
        
        # Return the detailed breakdown
        result = {
            'total_points': points,
            'details': details,
            'level_up': 'new_level' in point_result,
            'new_level': point_result.get('new_level'),
            'current_points': self.user_profile['points'],
            'current_level': self.user_profile['level']
        }
        
        return result
    
    def check_level_badges(self):
        """Check if any level-based badges should be unlocked"""
        newly_unlocked = []
        current_level = self.user_profile['level']
        
        for badge in self.badges:
            if 'level_required' in badge and not badge['unlocked']:
                if current_level >= badge['level_required']:
                    badge['unlocked'] = True
                    
                    # Save badge immediately to database if user exists
                    if self.user:
                        self.user.save_badge(badge)
                    
                    newly_unlocked.append({
                        'type': 'badge',
                        'id': badge['id'],
                        'name': badge['name'],
                        'description': badge['description']
                    })
                        
        return newly_unlocked
    
    def get_gamification_status(self):
        """Get the current gamification status"""
        # Calculate XP needed for next level
        current_level = self.user_profile['level']
        current_xp = self.user_profile['experience']
        
        # If at max defined level, show 100% progress
        if current_level >= len(self.level_thresholds):
            next_level_xp = current_xp
            xp_progress = 100
        else:
            current_level_xp = self.level_thresholds[current_level - 1] if current_level > 0 else 0
            next_level_xp = self.level_thresholds[current_level]
            xp_needed = next_level_xp - current_level_xp
            
            # Calculate progress percentage but cap at 99.9% - level should increment at 100%
            # This prevents showing 100% without level advancement
            xp_progress = min(99.9, ((current_xp - current_level_xp) / xp_needed) * 100)
            
        # Count completed achievements and unlocked badges
        completed_achievements = sum(1 for a in self.achievements if a['completed'])
        unlocked_badges = sum(1 for b in self.badges if b['unlocked'])
        
        return {
            'level': current_level,
            'points': self.user_profile['points'],
            'experience': current_xp,
            'next_level_at': next_level_xp,
            'xp_progress': xp_progress,
            'daily_streak': self.user_profile['streaks']['daily_login'],
            'pomodoro_streak': self.user_profile['streaks']['pomodoro_sessions'],
            'achievements': {
                'total': len(self.achievements),
                'completed': completed_achievements
            },
            'badges': {
                'total': len(self.badges),
                'unlocked': unlocked_badges
            },
            'achievement_list': self.achievements,
            'badge_list': self.badges
        }
    
    def _is_achievement_completed(self, achievement_id):
        """Check if a specific achievement is completed"""
        for achievement in self.achievements:
            if achievement['id'] == achievement_id:
                return achievement['completed']
        return False
    
    def _complete_achievement(self, achievement_id):
        """Mark an achievement as completed and award points"""
        for achievement in self.achievements:
            if achievement['id'] == achievement_id and not achievement['completed']:
                achievement['completed'] = True
                self.add_points(achievement['points'], f"Achievement: {achievement['name']}")
                
                # Save achievement immediately to database if user exists
                if self.user:
                    self.user.save_achievement(achievement)
                
                return {
                    'type': 'achievement',
                    'id': achievement_id,
                    'name': achievement['name'],
                    'description': achievement['description'],
                    'points': achievement['points']
                }
        return None