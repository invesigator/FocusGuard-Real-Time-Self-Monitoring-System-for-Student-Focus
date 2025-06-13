from flask import Blueprint, flash, redirect, render_template, request, jsonify, current_app, url_for
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models.user import User
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile')
@login_required
def profile_page():
    """Render user profile page"""
    # Get user data
    user = User.get_by_id(current_user.id)
    if not user:
        flash('User data not found', 'error')
        return redirect(url_for('auth.login_page'))
    
    # Get session history
    sessions = user.get_session_history(limit=5)
    
    # Get the achievement manager for the user to ensure consistent points
    from app import get_detector_for_user
    detector = get_detector_for_user(current_user.id)
    
    # Get consistent points from achievement manager instead of just sessions
    if detector and detector.achievement_manager:
        # Make sure profile is loaded from database
        detector.achievement_manager.load_profile_from_db()
        
        # Get gamification status which contains the complete points
        gamification_data = detector.achievement_manager.get_gamification_status()
        total_points = gamification_data.get('points', 0)
        level = gamification_data.get('level', 1)
        next_level = level + 1
        level_progress = gamification_data.get('xp_progress', 0)
        daily_streak = gamification_data.get('daily_streak', 0)
        pomodoro_streak = gamification_data.get('pomodoro_streak', 0)
    else:
        # Fallback to the old calculation method if achievement manager not available
        total_sessions = len(user.get_session_history())
        total_focus_minutes = sum(session.get('duration_minutes', 0) for session in user.get_session_history())
        total_points = sum(session.get('points_earned', 0) for session in user.get_session_history())
        
        # Get user settings for streaks and level
        settings = user.get_settings() or {}
        level = settings.get('profile_level', 1)
        next_level = level + 1
        level_progress = min(100, settings.get('profile_experience', 0) % 300 / 3)
        daily_streak = settings.get('daily_streak', 0)
        pomodoro_streak = settings.get('pomodoro_streak', 0)
    
    # Calculate total_focus_minutes from sessions for progress bars
    total_focus_minutes = sum(session.get('duration_minutes', 0) for session in user.get_session_history())
    total_sessions = len(user.get_session_history())
    
    # Format focus time for display
    hours = total_focus_minutes // 60
    minutes = total_focus_minutes % 60
    focus_time = f"{hours}h {minutes}m"
    
    # Set progress values
    focus_progress = min(100, int((total_focus_minutes / 1200) * 100))  # 20h = 1200 minutes
    sessions_progress = min(100, int((total_sessions / 20) * 100))
    
    # Create user_stats object to pass to template
    user_stats = {
        'focus_time': focus_time,
        'total_sessions': total_sessions,
        'total_points': total_points,
        'level': level,
        'next_level': next_level,
        'focus_progress': focus_progress,
        'sessions_progress': sessions_progress,
        'level_progress': level_progress,
        'daily_streak': daily_streak,
        'pomodoro_streak': pomodoro_streak,
    }
    
    return render_template('profile.html', user=current_user, sessions=sessions, stats=user_stats)

@profile_bp.route('/api/user/profile', methods=['GET'])
@login_required
def get_profile():
    """Get user profile data"""
    user = User.get_by_id(current_user.id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Get session history stats
    sessions = user.get_session_history()
    total_sessions = len(sessions)
    total_focus_minutes = sum(session.get('duration_minutes', 0) for session in sessions)
    total_points = sum(session.get('points_earned', 0) for session in sessions)
    
    # Calculate additional stats
    completed_pomodoros = sum(session.get('completed_pomodoros', 0) for session in sessions)
    total_drowsy_events = sum(session.get('drowsy_events', 0) for session in sessions)
    total_yawn_events = sum(session.get('yawn_events', 0) for session in sessions)
    total_distraction_events = sum(session.get('distraction_events', 0) for session in sessions)
    
    # Format user data for response
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'created_at': user.created_at,
        'last_login': user.last_login,
        'stats': {
            'total_sessions': total_sessions,
            'total_focus_minutes': total_focus_minutes,
            'total_points': total_points,
            'completed_pomodoros': completed_pomodoros,
            'total_drowsy_events': total_drowsy_events,
            'total_yawn_events': total_yawn_events,
            'total_distraction_events': total_distraction_events
        }
    }
    
    return jsonify({'success': True, 'user': user_data})

@profile_bp.route('/api/user/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    # Extract data from request
    full_name = data.get('fullName', '').strip()
    current_password = data.get('currentPassword', '')
    new_password = data.get('newPassword', '')
    
    # Basic validation
    if not full_name:
        return jsonify({'success': False, 'message': 'Full name is required'}), 400
    
    if not current_password:
        return jsonify({'success': False, 'message': 'Current password is required to make changes'}), 400
    
    # Get user from database
    user = User.get_by_id(current_user.id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Verify current password
    if not user.check_password(current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 401
    
    try:
        # Update user data in database
        conn = user._get_db_connection()
        cursor = conn.cursor()
        
        # Start with base query to update full name
        query = "UPDATE users SET full_name = ?"
        params = [full_name]
        
        # Add password update if provided
        if new_password:
            password_hash = generate_password_hash(new_password)
            query += ", password_hash = ?"
            params.append(password_hash)
        
        # Add where clause
        query += " WHERE id = ?"
        params.append(user.id)
        
        # Execute update
        cursor.execute(query, params)
        conn.commit()
        
        # Update user object
        user.full_name = full_name
        
        # Close connection
        conn.close()
        
        logger.info(f"Profile updated for user {user.username}")
        
        return jsonify({
            'success': True, 
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating profile for user {user.username}: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to update profile. Please try again.'}), 500

@profile_bp.route('/api/user/sessions', methods=['GET'])
@login_required
def get_user_sessions():
    """Get user session history"""
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    
    # Get user from database
    user = User.get_by_id(current_user.id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Get session history
    sessions = user.get_session_history(limit=limit)
    
    return jsonify({
        'success': True,
        'sessions': sessions,
        'pagination': {
            'page': page,
            'limit': limit,
            'total': len(sessions)  # In a real app, you'd get the total count from DB
        }
    })


# Ensure the limit parameter is respected
@profile_bp.route('/api/user/sessions/all', methods=['GET'])
@login_required
def get_all_user_sessions():
    """Get full user session history"""
    # Get user from database
    user = User.get_by_id(current_user.id)
    
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Get all session history with a high limit
    # You can adjust this based on your needs
    max_limit = 200
    sessions = user.get_session_history(limit=max_limit)
    
    # Format session data for better display
    formatted_sessions = []
    for session in sessions:
        # Create a copy to avoid modifying the original
        session_copy = dict(session)
        
        # Format timestamps if they exist
        if 'start_time' in session_copy and session_copy['start_time']:
            if isinstance(session_copy['start_time'], str):
                # Keep as is, it's already a string
                pass
        
        formatted_sessions.append(session_copy)
    
    return jsonify({
        'success': True,
        'sessions': formatted_sessions,
        'total': len(formatted_sessions)
    })