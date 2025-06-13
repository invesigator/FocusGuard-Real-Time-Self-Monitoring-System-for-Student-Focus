from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
auth_bp = Blueprint('auth', __name__)

# Helper Functions
def is_valid_email(email):
    """Validate email format"""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def is_valid_username(username):
    """Validate username format (alphanumeric, underscore, 3-20 chars)"""
    username_regex = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(username_regex, username) is not None

def is_strong_password(password):
    """Check if password meets security requirements"""
    # At least 8 characters, contains a digit, an uppercase, a lowercase, and a special character
    if len(password) < 8:
        return False
    
    has_digit = any(char.isdigit() for char in password)
    has_upper = any(char.isupper() for char in password)
    has_lower = any(char.islower() for char in password)
    has_special = any(not char.isalnum() for char in password)
    
    return has_digit and has_upper and has_lower and has_special

# Routes
@auth_bp.route('/login')
def login_page():
    """Render login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')

@auth_bp.route('/register')
def register_page():
    """Render registration page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/api/auth/login', methods=['POST'])
def login_api():
    """API endpoint for login"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400
    
    username_or_email = data.get('username', '').strip()
    password = data.get('password', '')
    remember = data.get('remember', False)
    
    if not username_or_email or not password:
        return jsonify({'success': False, 'message': 'Username/email and password are required'}), 400
    
    # Check if input is email or username
    is_email = '@' in username_or_email
    
    # Get user by email or username
    user = User.get_by_email(username_or_email) if is_email else User.get_by_username(username_or_email)
    
    if not user:
        logger.warning(f"Login attempt failed: User {username_or_email} not found")
        return jsonify({'success': False, 'message': 'Invalid username/email or password'}), 401
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt for inactive account: {username_or_email}")
        return jsonify({'success': False, 'message': 'Account is inactive. Please contact support.'}), 401
    
    # Verify password
    if not user.check_password(password):
        logger.warning(f"Login attempt failed: Incorrect password for {username_or_email}")
        return jsonify({'success': False, 'message': 'Invalid username/email or password'}), 401
    
    # Login successful
    login_user(user, remember=remember)
    user.update_last_login()
    
    logger.info(f"User {user.username} logged in successfully")
    
    return jsonify({
        'success': True, 
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name
        }
    }), 200

@auth_bp.route('/api/auth/register', methods=['POST'])
def register_api():
    """API endpoint for user registration"""
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'}), 400
    
    # Extract registration data
    full_name = data.get('fullName', '').strip()
    email = data.get('email', '').strip().lower()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    # Validate input
    if not full_name or not email or not username or not password:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400
    
    if not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400
    
    if not is_valid_username(username):
        return jsonify({'success': False, 'message': 'Username must be 3-20 characters containing only letters, numbers, and underscores'}), 400
    
    if not is_strong_password(password):
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters long and include uppercase, lowercase, digit, and special character'}), 400
    
    # Check if email or username already exists
    if User.get_by_email(email):
        return jsonify({'success': False, 'message': 'Email already registered'}), 400
    
    if User.get_by_username(username):
        return jsonify({'success': False, 'message': 'Username already taken'}), 400
    
    # Create new user
    user = User.create(username=username, email=email, full_name=full_name, password=password)
    
    if not user:
        logger.error(f"Failed to create user: {username}, {email}")
        return jsonify({'success': False, 'message': 'Registration failed. Please try again.'}), 500
    
    logger.info(f"User registered successfully: {username}, {email}")
    
    return jsonify({
        'success': True, 
        'message': 'Registration successful',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name
        }
    }), 201

@auth_bp.route('/api/auth/check-username', methods=['POST'])
def check_username():
    """Check if username is available"""
    data = request.get_json()
    
    if not data or 'username' not in data:
        return jsonify({'available': False, 'message': 'Invalid request'}), 400
    
    username = data['username'].strip()
    
    if not is_valid_username(username):
        return jsonify({'available': False, 'message': 'Invalid username format'}), 400
    
    user = User.get_by_username(username)
    
    return jsonify({
        'available': user is None,
        'message': 'Username available' if user is None else 'Username already taken'
    })

@auth_bp.route('/api/auth/check-email', methods=['POST'])
def check_email():
    """Check if email is available"""
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({'available': False, 'message': 'Invalid request'}), 400
    
    email = data['email'].strip().lower()
    
    if not is_valid_email(email):
        return jsonify({'available': False, 'message': 'Invalid email format'}), 400
    
    user = User.get_by_email(email)
    
    return jsonify({
        'available': user is None,
        'message': 'Email available' if user is None else 'Email already registered'
    })

@auth_bp.route('/forgot-password')
def forgot_password_page():
    """Render forgot password page"""
    return render_template('forgot_password.html')

@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password_api():
    """API endpoint for password reset request"""
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({'success': False, 'message': 'Invalid request'}), 400
    
    email = data['email'].strip().lower()
    
    if not is_valid_email(email):
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400
    
    user = User.get_by_email(email)
    
    if not user:
        # Don't reveal that the email doesn't exist for security reasons
        return jsonify({'success': True, 'message': 'If your email is registered, you will receive password reset instructions shortly.'}), 200
    
    # TODO: Implement actual password reset functionality
    # For now, just return a success message
    
    return jsonify({'success': True, 'message': 'If your email is registered, you will receive password reset instructions shortly.'}), 200