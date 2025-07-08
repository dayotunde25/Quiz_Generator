"""
Authentication Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timezone, timedelta
import secrets
import re

from app import db, redis_client, limiter
from app.models.user import User
from app.models.subscription import Subscription
from app.utils.decorators import validate_json

auth_bp = Blueprint('auth', __name__)


def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def is_strong_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    return True, "Password is strong"


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
@validate_json(['email', 'password', 'first_name', 'last_name'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate input
    email = data['email'].lower().strip()
    password = data['password']
    first_name = data['first_name'].strip()
    last_name = data['last_name'].strip()
    
    # Validate email format
    if not is_valid_email(email):
        return jsonify({'message': 'Invalid email format'}), 400
    
    # Validate password strength
    is_strong, message = is_strong_password(password)
    if not is_strong:
        return jsonify({'message': message}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 409
    
    # Create new user
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        role=data.get('role', 'teacher'),
        school_name=data.get('school_name'),
        subject_areas=data.get('subject_areas')
    )
    user.set_password(password)
    
    # Generate verification token
    user.verification_token = secrets.token_urlsafe(32)
    
    db.session.add(user)
    db.session.commit()
    
    # Create free subscription
    Subscription.create_free_subscription(user.id)
    
    # TODO: Send verification email
    
    # Create tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 201


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
@validate_json(['email', 'password'])
def login():
    """Login user"""
    data = request.get_json()
    
    email = data['email'].lower().strip()
    password = data['password']
    
    # Find user
    user = User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'message': 'Account is deactivated'}), 401
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.session.commit()
    
    # Create tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify({'message': 'User not found or inactive'}), 404
    
    access_token = create_access_token(identity=current_user_id)
    
    return jsonify({
        'access_token': access_token
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (revoke token)"""
    jti = get_jwt()['jti']
    
    # Add token to blacklist
    redis_client.set(f"revoked_token:{jti}", "true", ex=timedelta(hours=1))
    
    return jsonify({'message': 'Successfully logged out'}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({
        'user': user.to_dict(include_sensitive=True)
    }), 200


@auth_bp.route('/forgot-password', methods=['POST'])
@limiter.limit("3 per minute")
@validate_json(['email'])
def forgot_password():
    """Request password reset"""
    data = request.get_json()
    email = data['email'].lower().strip()
    
    user = User.query.filter_by(email=email).first()
    
    if user:
        # Generate reset token
        user.reset_token = secrets.token_urlsafe(32)
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.commit()
        
        # TODO: Send password reset email
    
    # Always return success to prevent email enumeration
    return jsonify({
        'message': 'If the email exists, a password reset link has been sent'
    }), 200


@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit("5 per minute")
@validate_json(['token', 'password'])
def reset_password():
    """Reset password with token"""
    data = request.get_json()
    token = data['token']
    password = data['password']
    
    # Validate password strength
    is_strong, message = is_strong_password(password)
    if not is_strong:
        return jsonify({'message': message}), 400
    
    # Find user by reset token
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.now(timezone.utc):
        return jsonify({'message': 'Invalid or expired reset token'}), 400
    
    # Update password
    user.set_password(password)
    user.reset_token = None
    user.reset_token_expires = None
    db.session.commit()
    
    return jsonify({'message': 'Password reset successfully'}), 200


@auth_bp.route('/verify-email', methods=['POST'])
@validate_json(['token'])
def verify_email():
    """Verify email address"""
    data = request.get_json()
    token = data['token']
    
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        return jsonify({'message': 'Invalid verification token'}), 400
    
    user.is_verified = True
    user.verification_token = None
    db.session.commit()
    
    return jsonify({'message': 'Email verified successfully'}), 200


@auth_bp.route('/resend-verification', methods=['POST'])
@limiter.limit("3 per minute")
@validate_json(['email'])
def resend_verification():
    """Resend email verification"""
    data = request.get_json()
    email = data['email'].lower().strip()
    
    user = User.query.filter_by(email=email).first()
    
    if user and not user.is_verified:
        # Generate new verification token
        user.verification_token = secrets.token_urlsafe(32)
        db.session.commit()
        
        # TODO: Send verification email
    
    return jsonify({
        'message': 'If the email exists and is unverified, a verification link has been sent'
    }), 200
