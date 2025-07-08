"""
AI Routes for Question Generation
"""
import time
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.user import User
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.file import File
from app.utils.decorators import validate_json, require_feature
from app.ai.question_generator import QuestionGenerator

ai_bp = Blueprint('ai', __name__)
question_generator = QuestionGenerator()


@ai_bp.route('/generate-questions', methods=['POST'])
@jwt_required()
@validate_json(['text', 'num_questions'])
def generate_questions():
    """Generate questions from text using AI"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    data = request.get_json()
    text = data['text']
    num_questions = min(data['num_questions'], 50)  # Limit to 50 questions
    question_types = data.get('question_types', ['multiple_choice', 'true_false'])
    difficulty_level = data.get('difficulty_level', 'medium')
    
    if len(text.strip()) < 100:
        return jsonify({'message': 'Text must be at least 100 characters long'}), 400
    
    try:
        start_time = time.time()
        
        # Generate questions
        generated_questions = question_generator.generate_questions(
            text=text,
            num_questions=num_questions,
            question_types=question_types,
            difficulty_level=difficulty_level
        )
        
        generation_time = time.time() - start_time
        
        # Convert to dict format
        questions_data = []
        for q in generated_questions:
            question_dict = {
                'question_text': q.question_text,
                'question_type': q.question_type,
                'options': q.options,
                'correct_answer': q.correct_answer,
                'explanation': q.explanation,
                'difficulty_level': q.difficulty_level,
                'topic': q.topic,
                'keywords': q.keywords,
                'confidence_score': q.confidence_score,
                'source_sentence': q.source_sentence,
                'bloom_taxonomy_level': q.bloom_taxonomy_level
            }
            questions_data.append(question_dict)
        
        return jsonify({
            'questions': questions_data,
            'generation_time': generation_time,
            'ai_model_used': 'transformers + spacy',
            'total_generated': len(questions_data)
        }), 200
    
    except Exception as e:
        return jsonify({
            'message': 'Question generation failed',
            'error': str(e)
        }), 500


@ai_bp.route('/generate-quiz', methods=['POST'])
@jwt_required()
@validate_json(['title', 'source_text', 'num_questions'])
def generate_quiz():
    """Generate a complete quiz with questions"""
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
    
    try:
        start_time = time.time()
        
        # Create quiz
        quiz = Quiz(
            title=data['title'],
            description=data.get('description'),
            source_text=data['source_text'],
            source_file_id=data.get('source_file_id'),
            difficulty_level=data.get('difficulty_level', 'medium'),
            total_questions=data['num_questions'],
            user_id=current_user_id
        )
        
        question_types = data.get('question_types', ['multiple_choice', 'true_false'])
        quiz.set_question_types_list(question_types)
        
        db.session.add(quiz)
        db.session.commit()
        
        # Generate questions
        generated_questions = question_generator.generate_questions(
            text=data['source_text'],
            num_questions=data['num_questions'],
            question_types=question_types,
            difficulty_level=data.get('difficulty_level', 'medium')
        )
        
        # Save questions to database
        for i, q in enumerate(generated_questions):
            question = Question(
                question_text=q.question_text,
                question_type=q.question_type,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
                difficulty_level=q.difficulty_level,
                topic=q.topic,
                bloom_taxonomy_level=q.bloom_taxonomy_level,
                confidence_score=q.confidence_score,
                source_sentence=q.source_sentence,
                order_index=i + 1,
                quiz_id=quiz.id
            )
            
            if q.options:
                question.set_options_list(q.options)
            
            if q.keywords:
                question.set_keywords_list(q.keywords)
            
            db.session.add(question)
        
        generation_time = time.time() - start_time
        
        # Update quiz metadata
        quiz.ai_model_used = 'transformers + spacy'
        quiz.generation_time = generation_time
        quiz.set_generation_parameters({
            'question_types': question_types,
            'difficulty_level': data.get('difficulty_level', 'medium'),
            'source_length': len(data['source_text'])
        })
        
        db.session.commit()
        
        # Increment user's quiz count
        user.increment_quiz_count()
        
        return jsonify({
            'message': 'Quiz generated successfully',
            'quiz': quiz.to_dict(include_questions=True),
            'generation_time': generation_time,
            'questions_generated': len(generated_questions)
        }), 201
    
    except Exception as e:
        # Rollback on error
        db.session.rollback()
        return jsonify({
            'message': 'Quiz generation failed',
            'error': str(e)
        }), 500


@ai_bp.route('/generate-from-file', methods=['POST'])
@jwt_required()
@validate_json(['file_id', 'title', 'num_questions'])
def generate_quiz_from_file():
    """Generate quiz from uploaded file"""
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
    file_id = data['file_id']
    
    # Get file
    file = File.query.filter_by(id=file_id, user_id=current_user_id).first()
    
    if not file:
        return jsonify({'message': 'File not found'}), 404
    
    if not file.extracted_text:
        return jsonify({'message': 'File text not extracted yet'}), 400
    
    if file.extraction_status != 'success':
        return jsonify({'message': 'File text extraction failed'}), 400
    
    # Use the file's extracted text
    data['source_text'] = file.extracted_text
    data['source_file_id'] = file_id
    
    # Call the generate_quiz function
    return generate_quiz()


@ai_bp.route('/extract-concepts', methods=['POST'])
@jwt_required()
@validate_json(['text'])
def extract_concepts():
    """Extract key concepts from text"""
    data = request.get_json()
    text = data['text']
    
    if len(text.strip()) < 50:
        return jsonify({'message': 'Text must be at least 50 characters long'}), 400
    
    try:
        concepts = question_generator.extract_key_concepts(text)
        
        return jsonify({
            'concepts': concepts[:20],  # Limit to top 20 concepts
            'total_found': len(concepts)
        }), 200
    
    except Exception as e:
        return jsonify({
            'message': 'Concept extraction failed',
            'error': str(e)
        }), 500


@ai_bp.route('/question-types', methods=['GET'])
def get_question_types():
    """Get available question types for AI generation"""
    return jsonify({
        'question_types': [
            {
                'value': 'multiple_choice',
                'label': 'Multiple Choice',
                'description': 'Questions with 4 answer options',
                'supported': True
            },
            {
                'value': 'true_false',
                'label': 'True/False',
                'description': 'Questions with true or false answers',
                'supported': True
            },
            {
                'value': 'short_answer',
                'label': 'Short Answer',
                'description': 'Questions requiring brief written responses',
                'supported': True
            },
            {
                'value': 'essay',
                'label': 'Essay',
                'description': 'Questions requiring detailed written responses',
                'supported': False  # Not implemented yet
            }
        ]
    }), 200
