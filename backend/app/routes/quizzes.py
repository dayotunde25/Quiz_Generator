"""
Quiz Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone

from app import db
from app.models.user import User
from app.models.quiz import Quiz
from app.models.question import Question
from app.utils.decorators import validate_json, check_quiz_ownership

quizzes_bp = Blueprint('quizzes', __name__)


@quizzes_bp.route('', methods=['GET'])
@jwt_required()
def get_quizzes():
    """Get user's quizzes"""
    current_user_id = get_jwt_identity()
    
    # Query parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    status = request.args.get('status')
    search = request.args.get('search')
    
    # Build query
    query = Quiz.query.filter_by(user_id=current_user_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if search:
        query = query.filter(Quiz.title.contains(search))
    
    # Order by creation date (newest first)
    query = query.order_by(Quiz.created_at.desc())
    
    # Paginate
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    quizzes = [quiz.to_dict() for quiz in pagination.items]
    
    return jsonify({
        'quizzes': quizzes,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    }), 200


@quizzes_bp.route('', methods=['POST'])
@jwt_required()
@validate_json(['title'])
def create_quiz():
    """Create a new quiz"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Check if user can create quiz
    if not user.can_create_quiz():
        return jsonify({
            'message': 'Quiz limit reached for your plan',
            'current_count': user.quiz_count_current_month,
            'limit': 5 if user.subscription_plan == 'free' else -1
        }), 403
    
    data = request.get_json()
    
    # Create quiz
    quiz = Quiz(
        title=data['title'],
        description=data.get('description'),
        source_text=data.get('source_text'),
        source_file_id=data.get('source_file_id'),
        difficulty_level=data.get('difficulty_level', 'medium'),
        total_questions=data.get('total_questions', 10),
        user_id=current_user_id
    )
    
    if 'question_types' in data:
        quiz.set_question_types_list(data['question_types'])
    
    db.session.add(quiz)
    db.session.commit()
    
    # Increment user's quiz count
    user.increment_quiz_count()
    
    return jsonify({
        'message': 'Quiz created successfully',
        'quiz': quiz.to_dict()
    }), 201


@quizzes_bp.route('/<int:quiz_id>', methods=['GET'])
@jwt_required()
@check_quiz_ownership
def get_quiz(quiz_id):
    """Get a specific quiz"""
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404
    
    return jsonify({
        'quiz': quiz.to_dict(include_questions=True, include_source=True)
    }), 200


@quizzes_bp.route('/<int:quiz_id>', methods=['PUT'])
@jwt_required()
@check_quiz_ownership
@validate_json()
def update_quiz(quiz_id):
    """Update a quiz"""
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    allowed_fields = ['title', 'description', 'difficulty_level', 'status', 'is_public']
    for field in allowed_fields:
        if field in data:
            setattr(quiz, field, data[field])
    
    if 'question_types' in data:
        quiz.set_question_types_list(data['question_types'])
    
    db.session.commit()
    
    return jsonify({
        'message': 'Quiz updated successfully',
        'quiz': quiz.to_dict()
    }), 200


@quizzes_bp.route('/<int:quiz_id>', methods=['DELETE'])
@jwt_required()
@check_quiz_ownership
def delete_quiz(quiz_id):
    """Delete a quiz"""
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404
    
    db.session.delete(quiz)
    db.session.commit()
    
    return jsonify({'message': 'Quiz deleted successfully'}), 200


@quizzes_bp.route('/<int:quiz_id>/publish', methods=['POST'])
@jwt_required()
@check_quiz_ownership
def publish_quiz(quiz_id):
    """Publish a quiz"""
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404
    
    if quiz.question_count == 0:
        return jsonify({'message': 'Cannot publish quiz without questions'}), 400
    
    quiz.publish()
    
    return jsonify({
        'message': 'Quiz published successfully',
        'quiz': quiz.to_dict()
    }), 200


@quizzes_bp.route('/<int:quiz_id>/share', methods=['POST'])
@jwt_required()
@check_quiz_ownership
def generate_share_link(quiz_id):
    """Generate a share link for a quiz"""
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404
    
    if quiz.status != 'published':
        return jsonify({'message': 'Only published quizzes can be shared'}), 400
    
    share_token = quiz.generate_share_token()
    
    return jsonify({
        'message': 'Share link generated successfully',
        'share_token': share_token,
        'share_url': f"/quiz/{share_token}"
    }), 200


@quizzes_bp.route('/shared/<share_token>', methods=['GET'])
def get_shared_quiz(share_token):
    """Get a shared quiz by token"""
    quiz = Quiz.get_by_share_token(share_token)
    
    if not quiz:
        return jsonify({'message': 'Quiz not found or not shared'}), 404
    
    # Increment view count
    quiz.increment_view_count()
    
    return jsonify({
        'quiz': quiz.to_dict(include_questions=True)
    }), 200
