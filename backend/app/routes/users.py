"""
User Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.user import User
from app.utils.decorators import validate_json

users_bp = Blueprint('users', __name__)


@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({
        'user': user.to_dict(include_sensitive=True)
    }), 200


@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
@validate_json()
def update_profile():
    """Update user profile"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    allowed_fields = ['first_name', 'last_name', 'school_name', 'subject_areas', 'bio']
    for field in allowed_fields:
        if field in data:
            setattr(user, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully',
        'user': user.to_dict()
    }), 200


@users_bp.route('/change-password', methods=['POST'])
@jwt_required()
@validate_json(['current_password', 'new_password'])
def change_password():
    """Change user password"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    data = request.get_json()
    current_password = data['current_password']
    new_password = data['new_password']
    
    # Verify current password
    if not user.check_password(current_password):
        return jsonify({'message': 'Current password is incorrect'}), 400
    
    # Validate new password strength
    if len(new_password) < 8:
        return jsonify({'message': 'New password must be at least 8 characters long'}), 400
    
    # Update password
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200


@users_bp.route('/delete-account', methods=['DELETE'])
@jwt_required()
@validate_json(['password'])
def delete_account():
    """Delete user account"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    data = request.get_json()
    password = data['password']
    
    # Verify password
    if not user.check_password(password):
        return jsonify({'message': 'Password is incorrect'}), 400
    
    # Delete user and all related data (cascade delete)
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'Account deleted successfully'}), 200
