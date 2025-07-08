"""
Custom Decorators
"""
from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.models.user import User


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Authentication required'}), 401
    return decorated_function


def require_role(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                current_user_id = get_jwt_identity()
                user = User.query.get(current_user_id)
                
                if not user or user.role != role:
                    return jsonify({'message': 'Insufficient permissions'}), 403
                
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'message': 'Authentication required'}), 401
        return decorated_function
    return decorator


def require_subscription(plan_level='free'):
    """Decorator to require specific subscription level"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                current_user_id = get_jwt_identity()
                user = User.query.get(current_user_id)
                
                if not user:
                    return jsonify({'message': 'User not found'}), 404
                
                if not user.is_subscription_active():
                    return jsonify({'message': 'Active subscription required'}), 403
                
                # Check subscription level hierarchy
                plan_hierarchy = {'free': 0, 'premium': 1, 'school': 2}
                user_level = plan_hierarchy.get(user.subscription_plan, 0)
                required_level = plan_hierarchy.get(plan_level, 0)
                
                if user_level < required_level:
                    return jsonify({
                        'message': f'{plan_level.title()} subscription required',
                        'current_plan': user.subscription_plan,
                        'required_plan': plan_level
                    }), 403
                
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'message': 'Authentication required'}), 401
        return decorated_function
    return decorator


def require_feature(feature_name):
    """Decorator to require specific feature access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request()
                current_user_id = get_jwt_identity()
                user = User.query.get(current_user_id)
                
                if not user:
                    return jsonify({'message': 'User not found'}), 404
                
                if not user.has_feature(feature_name):
                    return jsonify({
                        'message': f'Feature "{feature_name}" not available in your plan',
                        'current_plan': user.subscription_plan
                    }), 403
                
                return f(*args, **kwargs)
            except Exception as e:
                return jsonify({'message': 'Authentication required'}), 401
        return decorated_function
    return decorator


def validate_json(required_fields=None):
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'message': 'Request must be JSON'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'message': 'No JSON data provided'}), 400
            
            if required_fields:
                missing_fields = []
                for field in required_fields:
                    if field not in data or data[field] is None:
                        missing_fields.append(field)
                
                if missing_fields:
                    return jsonify({
                        'message': 'Missing required fields',
                        'missing_fields': missing_fields
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_quiz_ownership(f):
    """Decorator to check if user owns the quiz"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            # Get quiz_id from URL parameters
            quiz_id = kwargs.get('quiz_id') or request.view_args.get('quiz_id')
            if not quiz_id:
                return jsonify({'message': 'Quiz ID required'}), 400
            
            from app.models.quiz import Quiz
            quiz = Quiz.query.get(quiz_id)
            if not quiz:
                return jsonify({'message': 'Quiz not found'}), 404
            
            if quiz.user_id != current_user_id:
                return jsonify({'message': 'You do not own this quiz'}), 403
            
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Authentication required'}), 401
    return decorated_function


def check_file_ownership(f):
    """Decorator to check if user owns the file"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            # Get file_id from URL parameters
            file_id = kwargs.get('file_id') or request.view_args.get('file_id')
            if not file_id:
                return jsonify({'message': 'File ID required'}), 400
            
            from app.models.file import File
            file = File.query.get(file_id)
            if not file:
                return jsonify({'message': 'File not found'}), 404
            
            if file.user_id != current_user_id:
                return jsonify({'message': 'You do not own this file'}), 403
            
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Authentication required'}), 401
    return decorated_function
