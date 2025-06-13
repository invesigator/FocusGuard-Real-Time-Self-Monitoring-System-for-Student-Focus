# utils/analytics_manager.py
import json
import logging
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

class AnalyticsManager:
    """Manages analytics tracking for the gamification system"""
    
    def __init__(self, save_dir="analytics"):
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        
        # Initialize analytics storage
        self.reset_tracking()
        
        # Maintain daily point history for time-based analysis
        self.point_history = []
        
        # Load existing analytics data if available
        self.load_analytics()
    
    def reset_tracking(self):
        """Reset daily tracking metrics"""
        self.daily_tracking = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'points_earned': 0,
            'achievements_unlocked': 0,
            'badges_earned': 0,
            'focus_minutes': 0,
            'drowsy_events': 0,
            'distraction_events': 0,
            'pomodoro_sessions': 0,
            'level_ups': 0,
            'session_count': 0
        }
    
    def load_analytics(self):
        """Load analytics data from file if it exists"""
        analytics_path = self.save_dir / "gamification_analytics.json"
        
        if analytics_path.exists():
            try:
                with open(analytics_path, 'r') as f:
                    data = json.load(f)
                    self.point_history = data.get('point_history', [])
                    
                    # Check if we need to reset daily tracking (new day)
                    last_date = self.daily_tracking['date']
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    
                    if last_date != current_date:
                        # Save yesterday's tracking to history
                        if self.daily_tracking['points_earned'] > 0:
                            self.point_history.append(self.daily_tracking)
                        
                        # Reset for today
                        self.reset_tracking()
                    else:
                        # Continue today's tracking
                        self.daily_tracking = data.get('daily_tracking', self.daily_tracking)
                    
                    logging.info("Analytics data loaded successfully")
            except Exception as e:
                logging.error(f"Error loading analytics data: {str(e)}")
    
    def save_analytics(self):
        """Save analytics data to file"""
        analytics_path = self.save_dir / "gamification_analytics.json"
        
        try:
            data = {
                'daily_tracking': self.daily_tracking,
                'point_history': self.point_history
            }
            
            with open(analytics_path, 'w') as f:
                json.dump(data, f, indent=4)
                
            logging.info("Analytics data saved successfully")
            return True
        except Exception as e:
            logging.error(f"Error saving analytics data: {str(e)}")
            return False
    
    # Update the track_session method to ensure session stats are properly recorded
    def track_session(self, session_stats, points_earned):
        """Track metrics from a completed session"""
        # Update focus minutes
        session_duration = session_stats.get('session_duration_minutes', 0)
        self.daily_tracking['focus_minutes'] += session_duration
        
        # Update event counts
        self.daily_tracking['drowsy_events'] += session_stats.get('total_drowsy_events', 0)
        self.daily_tracking['distraction_events'] += session_stats.get('total_distraction_events', 0)
        self.daily_tracking['pomodoro_sessions'] += session_stats.get('completed_pomodoro_sessions', 0)
        
        # Update points earned
        self.daily_tracking['points_earned'] += points_earned
        
        # Increment session count
        self.daily_tracking['session_count'] += 1
        
        # Update achievement manager if available
        detector = self._get_detector_for_current_user()
        if detector and detector.achievement_manager:
            # Update total focus minutes
            total_focus_minutes = detector.achievement_manager.user_profile.get('total_focus_minutes', 0)
            detector.achievement_manager.user_profile['total_focus_minutes'] = total_focus_minutes + session_duration
            
            # Update total sessions
            total_sessions = detector.achievement_manager.user_profile.get('total_sessions', 0)
            detector.achievement_manager.user_profile['total_sessions'] = total_sessions + 1
            
            # Save the updated profile
            detector.achievement_manager.save_profile()
        
        # Save analytics
        self.save_analytics()

    # Add this helper method to get the detector for the current user
    def _get_detector_for_current_user(self):
        """Get the detector for the current user (if available)"""
        try:
            from flask_login import current_user
            from app import get_detector_for_user
            
            if current_user and current_user.is_authenticated:
                return get_detector_for_user(current_user.id)
        except Exception as e:
            logging.error(f"Error getting detector for current user: {str(e)}")
        
        return None
    
    def track_achievement(self, achievement_count=1):
        """Track achievement unlocks"""
        self.daily_tracking['achievements_unlocked'] += achievement_count
        self.save_analytics()
    
    def track_badge(self, badge_count=1):
        """Track badge earnings"""
        self.daily_tracking['badges_earned'] += badge_count
        self.save_analytics()
    
    def track_level_up(self):
        """Track level ups"""
        self.daily_tracking['level_ups'] += 1
        self.save_analytics()
    
    def get_point_history(self, days=30):
        """Get point history for the specified number of days"""
        # Start with today's data
        history = [self.daily_tracking]
        
        # Add historical data (most recent first)
        history.extend(self.point_history[:days-1])
        
        # Ensure we don't exceed the requested number of days
        history = history[:days]
        
        return history
    
    def get_leaderboard_data(self, limit=10):
        """
        Get leaderboard data for all users
        
        Args:
            limit: Maximum number of users to return, None for all users
            
        Returns:
            list: List of user data for leaderboard
        """
        DB_PATH = 'database/focusguard.db'
        
        try:
            # Connect to the database
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get all active users with their gamification data
            # Exclude admin user by adding "WHERE username != 'admin'"
            cursor.execute('''
                SELECT u.id, u.username, u.full_name, 
                    s.profile_points, s.profile_level, s.daily_streak, s.pomodoro_streak
                FROM users u
                JOIN user_settings s ON u.id = s.user_id
                WHERE u.is_active = 1 AND u.username != 'admin'
                ORDER BY s.profile_points DESC
                LIMIT ?
            ''', (limit if limit else -1,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Process the result
            result = []
            for row in rows:
                # Check if this is the current user
                is_current_user = False
                if hasattr(self, 'current_user_id') and self.current_user_id == row['id']:
                    is_current_user = True
                
                # Format user data for leaderboard
                user_data = {
                    'id': row['id'],
                    'name': row['full_name'],
                    'username': row['username'],
                    'points': row['profile_points'] or 0,
                    'level': row['profile_level'] or 1,
                    'daily_streak': row['daily_streak'] or 0,
                    'pomodoro_streak': row['pomodoro_streak'] or 0,
                    'is_current_user': is_current_user
                }
                
                result.append(user_data)
                
            return result
            
        except Exception as e:
            logging.error(f"Error getting leaderboard data: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return []
    
    
    def get_analytics_summary(self):
        """Get a summary of user analytics"""
        # Calculate engagement metrics
        total_sessions = sum(day.get('session_count', 0) for day in self.point_history) + self.daily_tracking['session_count']
        total_focus_minutes = sum(day.get('focus_minutes', 0) for day in self.point_history) + self.daily_tracking['focus_minutes']
        total_pomodoros = sum(day.get('pomodoro_sessions', 0) for day in self.point_history) + self.daily_tracking['pomodoro_sessions']
        
        # Calculate daily averages
        active_days = len(self.point_history) + 1  # +1 for today
        avg_focus_minutes = total_focus_minutes / max(1, active_days)
        avg_pomodoros = total_pomodoros / max(1, active_days)
        
        # Calculate achievement progress
        total_achievements = sum(day.get('achievements_unlocked', 0) for day in self.point_history) + self.daily_tracking['achievements_unlocked']
        total_badges = sum(day.get('badges_earned', 0) for day in self.point_history) + self.daily_tracking['badges_earned']
        
        # Get point trend
        point_trend = self.get_point_trend()
        
        # Check if we have gamification data
        detector = self._get_detector_for_current_user()
        gamification_data = {}
        if detector and detector.achievement_manager:
            gamification_data = {
                'level': detector.achievement_manager.user_profile.get('level', 1),
                'points': detector.achievement_manager.user_profile.get('points', 0),
                'daily_streak': detector.achievement_manager.user_profile.get('streaks', {}).get('daily_login', 0),
                'pomodoro_streak': detector.achievement_manager.user_profile.get('streaks', {}).get('pomodoro_sessions', 0),
                'total_focus_minutes': detector.achievement_manager.user_profile.get('total_focus_minutes', total_focus_minutes),
                'total_sessions': detector.achievement_manager.user_profile.get('total_sessions', total_sessions)
            }
        
        return {
            'engagement': {
                'total_sessions': total_sessions,
                'total_focus_minutes': total_focus_minutes,
                'total_pomodoros': total_pomodoros,
                'active_days': active_days,
                'avg_daily_focus': round(avg_focus_minutes, 1),
                'avg_daily_pomodoros': round(avg_pomodoros, 1)
            },
            'achievements': {
                'total_achievements': total_achievements,
                'total_badges': total_badges
            },
            'point_trend': point_trend,
            **gamification_data  # Include gamification data
        }
    
    def get_point_trend(self, days=7):
        """Get point earning trend for the last N days"""
        # Start with today
        trend = [{
            'date': self.daily_tracking['date'],
            'points': self.daily_tracking['points_earned']
        }]
        
        # Add historical data
        for day in self.point_history[:days-1]:
            trend.append({
                'date': day['date'],
                'points': day['points_earned']
            })
        
        # Ensure we don't exceed the requested number of days
        trend = trend[:days]
        
        # Sort by date (oldest first)
        trend.sort(key=lambda x: x['date'])
        
        return trend
    
    def export_analytics_to_csv(self):
        """Export analytics data to CSV for further analysis"""
        try:
            # Combine current day with history
            all_data = [self.daily_tracking] + self.point_history
            
            # Convert to DataFrame
            df = pd.DataFrame(all_data)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.save_dir / f"gamification_analytics_{timestamp}.csv"
            
            # Save to CSV
            df.to_csv(filename, index=False)
            
            logging.info(f"Analytics exported to {filename}")
            return filename
        except Exception as e:
            logging.error(f"Error exporting analytics: {str(e)}")
            return None