def create_test_users():
    """Create test users with various levels, achievements, and points for the leaderboard"""
    from models.user import User
    import random
    from datetime import datetime, timedelta
    import logging
    from utils.achievement_manager import AchievementManager
    
    # All test users with predefined achievements and levels
    test_users = [
        {
            "username": "alexjohnson",
            "email": "alex@example.com",
            "full_name": "Alex Johnson",
            "password": "AlexPass123!",
            "level": 3,
            "points": 750,
            "achievements": ["first_session", "focus_30m", "no_drowsy_session"],
            "badges": ["focus_novice"],
            "daily_streak": 5,
            "pomodoro_streak": 8,
            "total_focus_minutes": 300
        },
        {
            "username": "samsmith",
            "email": "sam@example.com", 
            "full_name": "Sam Smith",
            "password": "SamPass456!",
            "level": 7, 
            "points": 1800,
            "achievements": ["first_session", "focus_30m", "pomodoro_5", "streak_3"],
            "badges": ["focus_novice"],
            "daily_streak": 12,
            "pomodoro_streak": 15,
            "total_focus_minutes": 850
        },
        {
            "username": "taylorb",
            "email": "taylor@example.com",
            "full_name": "Taylor Brown",
            "password": "TaylorPass789!",
            "level": 12,
            "points": 3200,
            "achievements": ["first_session", "focus_30m", "pomodoro_5", "pomodoro_20", "no_drowsy_session", "streak_3"],
            "badges": ["focus_novice", "focus_intermediate"],
            "daily_streak": 24,
            "pomodoro_streak": 42,
            "total_focus_minutes": 1700
        },
        {
            "username": "morgan",
            "email": "morgan@example.com",
            "full_name": "Morgan Wilson",
            "password": "MorganPass321!",
            "level": 20,
            "points": 5500,
            "achievements": ["first_session", "focus_30m", "pomodoro_5", "pomodoro_20", "no_drowsy_session", "streak_3"],
            "badges": ["focus_novice", "focus_intermediate", "focus_master", "productivity_champion"],
            "daily_streak": 30,
            "pomodoro_streak": 60,
            "total_focus_minutes": 3000
        },
        {
            "username": "casey",
            "email": "casey@example.com",
            "full_name": "Casey Miller",
            "password": "CaseyPass654!",
            "level": 15,
            "points": 4100,
            "achievements": ["first_session", "focus_30m", "pomodoro_5", "pomodoro_20", "streak_3"],
            "badges": ["focus_novice", "focus_intermediate", "focus_master"],
            "daily_streak": 18,
            "pomodoro_streak": 35,
            "total_focus_minutes": 2200
        },
        {
            "username": "jordan",
            "email": "jordan@example.com",
            "full_name": "Jordan Lee",
            "password": "JordanPass987!",
            "level": 10,
            "points": 2500,
            "achievements": ["first_session", "focus_30m", "pomodoro_5", "streak_3"],
            "badges": ["focus_novice", "focus_intermediate"],
            "daily_streak": 15,
            "pomodoro_streak": 20,
            "total_focus_minutes": 1200
        },
        {
            "username": "riley",
            "email": "riley@example.com",
            "full_name": "Riley Taylor",
            "password": "RileyPass135!",
            "level": 5,
            "points": 1200,
            "achievements": ["first_session", "focus_30m"],
            "badges": ["focus_novice"],
            "daily_streak": 7,
            "pomodoro_streak": 10,
            "total_focus_minutes": 600
        },
        {
            "username": "student1",
            "email": "student1@example.com",
            "full_name": "Student One",
            "password": "Student1Pass!",
            "level": 2,
            "points": 500,
            "achievements": ["first_session"],
            "badges": [],
            "daily_streak": 3,
            "pomodoro_streak": 4,
            "total_focus_minutes": 150
        },
        {
            "username": "student2",
            "email": "student2@example.com",
            "full_name": "Student Two",
            "password": "Student2Pass!",
            "level": 8,
            "points": 2000,
            "achievements": ["first_session", "focus_30m", "pomodoro_5", "no_drowsy_session"],
            "badges": ["focus_novice"],
            "daily_streak": 14,
            "pomodoro_streak": 18,
            "total_focus_minutes": 950
        },
        {
            "username": "student3",
            "email": "student3@example.com",
            "full_name": "Student Three",
            "password": "Student3Pass!",
            "level": 17,
            "points": 4400,
            "achievements": ["first_session", "focus_30m", "pomodoro_5", "pomodoro_20", "no_drowsy_session", "streak_3"],
            "badges": ["focus_novice", "focus_intermediate", "focus_master"],
            "daily_streak": 25,
            "pomodoro_streak": 50,
            "total_focus_minutes": 2500
        }
    ]
    
    # List to track all created users
    created_users = []
    
    # Create all users
    for user_data in test_users:
        user = User.get_by_username(user_data["username"])
        if not user:
            user = User.create(
                username=user_data["username"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                password=user_data["password"]
            )
            
        if user:
            created_users.append(user)
            
            # Update user settings with predefined level and points
            # Calculate points from sessions
            sessions = create_sample_sessions(user, user_data)
            total_points = sum(session.get('points_earned', 0) for session in sessions)
            
            # Make sure we have a reasonable minimum based on level
            min_points = user_data["level"] * 300
            if total_points < min_points:
                total_points = min_points
            
            # IMPORTANT: Set last_check_in_date to YESTERDAY to allow streak to increment today
            yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
            
            user.update_settings({
                'profile_level': user_data["level"],
                'profile_points': total_points,
                'profile_experience': total_points,
                'daily_streak': user_data["daily_streak"],
                'pomodoro_streak': user_data["pomodoro_streak"],
                'last_check_in_date': yesterday,  # Set to yesterday
                'last_session_date': yesterday,   # Also set to yesterday
                'total_focus_minutes': user_data["total_focus_minutes"],
                'total_sessions': user_data["level"] + random.randint(3, 7)
            })
            
            # Initialize achievement manager for the user
            achievement_manager = AchievementManager(user.id)
            
            # Load default achievements and badges
            all_achievements = achievement_manager.achievements
            all_badges = achievement_manager.badges
            
            # Set completed achievements
            for achievement in all_achievements:
                if achievement['id'] in user_data["achievements"]:
                    achievement['completed'] = True
                    
                # Save the achievement
                user.save_achievement(achievement)
            
            # Set unlocked badges
            for badge in all_badges:
                if badge['id'] in user_data["badges"]:
                    badge['unlocked'] = True
                    
                # Save the badge
                user.save_badge(badge)
            
            logging.info(f"Created/updated user {user_data['username']} with streak {user_data['daily_streak']}")
    
    logging.info(f"Created/updated {len(created_users)} test users with varying achievements and stats")
    return created_users


def create_sample_sessions(user, user_data):
    """Create sample session history for a user based on their level and achievements"""
    from datetime import datetime, timedelta
    import random
    
    # Determine number of sessions based on level
    num_sessions = user_data["level"] + random.randint(3, 7)
    sessions = []
    
    for i in range(num_sessions):
        # Session time within the last 30 days
        days_ago = random.randint(0, 30)
        start_time = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
        duration = random.randint(25, 120)  # 25-120 minutes
        end_time = start_time + timedelta(minutes=duration)
        
        # Generate metrics based on user level
        # Higher level users should have better metrics
        level_factor = min(1.0, user_data["level"] / 20.0)  # 0.0 to 1.0 based on level
        
        drowsy_events = max(0, int(random.randint(0, 10) * (1.0 - level_factor)))
        yawn_events = max(0, int(random.randint(0, 8) * (1.0 - level_factor)))
        distraction_events = max(0, int(random.randint(0, 15) * (1.0 - level_factor)))
        
        # For users with 'pomodoro_5' or 'pomodoro_20' achievements, ensure they have enough pomodoros
        if 'pomodoro_20' in user_data["achievements"]:
            pomodoros = random.randint(3, 6)  # High pomodoro sessions
        elif 'pomodoro_5' in user_data["achievements"]:
            pomodoros = random.randint(1, 4)  # Medium pomodoro sessions
        else:
            pomodoros = random.randint(0, 2)  # Low pomodoro sessions
        
        # Special case for the last session if they have 'no_drowsy_session' achievement
        if i == num_sessions - 1 and 'no_drowsy_session' in user_data["achievements"]:
            drowsy_events = 0
        
        # Calculate points (similar to how the app calculates it)
        session_points = duration * 2  # 2 points per minute
        session_points -= drowsy_events * 10  # -10 points per drowsy event
        session_points -= distraction_events * 5  # -5 points per distraction
        session_points += pomodoros * 50  # +50 points per pomodoro
        session_points = max(0, session_points)  # Ensure non-negative
        
        # Save session
        session_data = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_minutes': duration,
            'drowsy_events': drowsy_events,
            'yawn_events': yawn_events,
            'distraction_events': distraction_events,
            'completed_pomodoros': pomodoros,
            'points_earned': session_points
        }
        
        # Save to database
        session_id = user.save_session(session_data)
        
        # Add to in-memory list for points calculation
        sessions.append(session_data)
    
    return sessions