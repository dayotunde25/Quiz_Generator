"""
Question Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.quiz import Quiz
from app.models.question import Question
from app.utils.decorators import validate_json, check_quiz_ownership

questions_bp = Blueprint('questions', __name__)


@questions_bp.route('/quiz/<int:quiz_id>/questions', methods=['GET'])
@jwt_required()
@check_quiz_ownership
def get_quiz_questions(quiz_id):
    """Get questions for a quiz"""
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404
    
    questions = Question.query.filter_by(quiz_id=quiz_id, is_active=True)\
                            .order_by(Question.order_index)\
                            .all()
    
    return jsonify({
        'questions': [q.to_dict() for q in questions]
    }), 200


@questions_bp.route('/quiz/<int:quiz_id>/questions', methods=['POST'])
@jwt_required()
@check_quiz_ownership
@validate_json(['question_text', 'question_type', 'correct_answer'])
def create_question(quiz_id):
    """Create a new question for a quiz"""
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404
    
    data = request.get_json()
    
    # Get the next order index
    max_order = db.session.query(db.func.max(Question.order_index))\
                         .filter_by(quiz_id=quiz_id)\
                         .scalar() or 0
    
    question = Question(
        question_text=data['question_text'],
        question_type=data['question_type'],
        correct_answer=data['correct_answer'],
        explanation=data.get('explanation'),
        difficulty_level=data.get('difficulty_level', 'medium'),
        topic=data.get('topic'),
        bloom_taxonomy_level=data.get('bloom_taxonomy_level'),
        order_index=max_order + 1,
        quiz_id=quiz_id
    )
    
    if 'options' in data and data['question_type'] == 'multiple_choice':
        question.set_options_list(data['options'])
    
    if 'keywords' in data:
        question.set_keywords_list(data['keywords'])
    
    db.session.add(question)
    db.session.commit()
    
    return jsonify({
        'message': 'Question created successfully',
        'question': question.to_dict()
    }), 201


@questions_bp.route('/<int:question_id>', methods=['GET'])
@jwt_required()
def get_question(question_id):
    """Get a specific question"""
    question = Question.query.get(question_id)
    
    if not question:
        return jsonify({'message': 'Question not found'}), 404
    
    # Check if user owns the quiz
    current_user_id = get_jwt_identity()
    if question.quiz.user_id != current_user_id:
        return jsonify({'message': 'You do not own this question'}), 403
    
    return jsonify({
        'question': question.to_dict()
    }), 200


@questions_bp.route('/<int:question_id>', methods=['PUT'])
@jwt_required()
@validate_json()
def update_question(question_id):
    """Update a question"""
    question = Question.query.get(question_id)
    
    if not question:
        return jsonify({'message': 'Question not found'}), 404
    
    # Check if user owns the quiz
    current_user_id = get_jwt_identity()
    if question.quiz.user_id != current_user_id:
        return jsonify({'message': 'You do not own this question'}), 403
    
    data = request.get_json()
    
    # Update allowed fields
    allowed_fields = [
        'question_text', 'correct_answer', 'explanation', 
        'difficulty_level', 'topic', 'bloom_taxonomy_level', 
        'order_index', 'is_active'
    ]
    
    for field in allowed_fields:
        if field in data:
            setattr(question, field, data[field])
    
    if 'options' in data and question.question_type == 'multiple_choice':
        question.set_options_list(data['options'])
    
    if 'keywords' in data:
        question.set_keywords_list(data['keywords'])
    
    db.session.commit()
    
    return jsonify({
        'message': 'Question updated successfully',
        'question': question.to_dict()
    }), 200


@questions_bp.route('/<int:question_id>', methods=['DELETE'])
@jwt_required()
def delete_question(question_id):
    """Delete a question"""
    question = Question.query.get(question_id)
    
    if not question:
        return jsonify({'message': 'Question not found'}), 404
    
    # Check if user owns the quiz
    current_user_id = get_jwt_identity()
    if question.quiz.user_id != current_user_id:
        return jsonify({'message': 'You do not own this question'}), 403
    
    db.session.delete(question)
    db.session.commit()
    
    return jsonify({'message': 'Question deleted successfully'}), 200


@questions_bp.route('/quiz/<int:quiz_id>/reorder', methods=['POST'])
@jwt_required()
@check_quiz_ownership
@validate_json(['question_orders'])
def reorder_questions(quiz_id):
    """Reorder questions in a quiz"""
    quiz = Quiz.query.get(quiz_id)
    
    if not quiz:
        return jsonify({'message': 'Quiz not found'}), 404
    
    data = request.get_json()
    question_orders = data['question_orders']  # List of {id, order_index}
    
    # Update order indices
    for item in question_orders:
        question = Question.query.get(item['id'])
        if question and question.quiz_id == quiz_id:
            question.order_index = item['order_index']
    
    db.session.commit()
    
    return jsonify({'message': 'Questions reordered successfully'}), 200


@questions_bp.route('/types', methods=['GET'])
def get_question_types():
    """Get available question types"""
    return jsonify({
        'question_types': Question.get_question_types()
    }), 200


@questions_bp.route('/difficulty-levels', methods=['GET'])
def get_difficulty_levels():
    """Get available difficulty levels"""
    return jsonify({
        'difficulty_levels': Question.get_difficulty_levels()
    }), 200
