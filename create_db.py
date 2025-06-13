"""
Database initialization script for FocusGuard

This script initializes the database and creates required tables.
It also creates a default admin user if one doesn't exist.
"""
import logging
from models.user import init_db, User
from utils.achievement_manager import AchievementManager

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_admin_user():
    """
    Create an admin user if one doesn't exist with all achievements and badges unlocked
    
    Default credentials:
    - Username: admin
    - Email: admin@focusguard.com
    - Password: Admin123!
    """
    # Check if admin user already exists
    admin = User.get_by_username('admin')
    if admin:
        logger.info("Admin user already exists")
        # Ensure admin has all achievements and badges
        unlock_all_for_admin(admin.id)
        return admin
    
    # Create admin user
    admin = User.create(
        username='admin',
        email='admin@focusguard.com',
        full_name='Administrator',
        password='Admin123!'
    )
    
    if admin:
        logger.info("Admin user created successfully")
        # Set admin achievements and badges
        unlock_all_for_admin(admin.id)
    else:
        logger.error("Failed to create admin user")
    
    return admin

def unlock_all_for_admin(admin_id):
    """Set up admin privileges with high levels, points, and all achievements unlocked"""
    logger.info(f"Setting up admin privileges for user {admin_id}")
    try:
        achievement_manager = AchievementManager(admin_id)

        # Make sure profile is loaded before modifications
        achievement_manager.load_profile_from_db()

        # Set all achievements to completed
        for achievement in achievement_manager.achievements:
            achievement['completed'] = True
            # Save the achievement directly to database
            achievement_manager.user.save_achievement(achievement)
        
        # Set all badges to unlocked
        for badge in achievement_manager.badges:
            badge['unlocked'] = True
            # Save the badge directly to database
            achievement_manager.user.save_badge(badge)
        
        # Update user_profile directly - this prevents discrepancies
        achievement_manager.user_profile['points'] = 999999
        achievement_manager.user_profile['level'] = 50
        achievement_manager.user_profile['experience'] = 999999
        achievement_manager.user_profile['streaks']['daily_login'] = 365
        achievement_manager.user_profile['streaks']['pomodoro_sessions'] = 500
        
        # Set these additional values that aren't part of the standard profile
        additional_settings = {
            'total_focus_minutes': 50000,
            'total_sessions': 1000
        }
        
        # First, save the profile to update the main gamification stats
        success1 = achievement_manager.save_profile()
        
        # Then, update the additional settings
        success2 = achievement_manager.user.update_settings(additional_settings)
        
        # Log results
        if success1 and success2:
            logger.info(f"Admin privileges set up successfully for user {admin_id}")
            return True
        else:
            logger.error(f"Failed to fully set up admin privileges: profile save={success1}, settings update={success2}")
            return False
    except Exception as e:
        logger.error(f"Error setting up admin privileges: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function to set up the database"""
    logger.info("Starting database initialization")
    
    # Initialize database and create tables
    init_db()
    logger.info("Database tables created")
    
    # Create admin user with all privileges
    create_admin_user()
    
    logger.info("Database initialization completed")

if __name__ == "__main__":
    main()