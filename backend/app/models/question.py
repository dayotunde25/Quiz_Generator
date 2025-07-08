"""
Question Model
"""
from datetime import datetime, timezone
from app import db
import json


class Question(db.Model):
    """Question model for storing individual quiz questions"""
    
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Question content
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # multiple_choice, true_false, short_answer, essay
    difficulty_level = db.Column(db.String(20), default='medium')  # easy, medium, hard
    
    # Answer options (for multiple choice)
    options = db.Column(db.Text)  # JSON array of options
    correct_answer = db.Column(db.Text)  # Correct answer or answer key
    explanation = db.Column(db.Text)  # Explanation for the correct answer
    
    # Question metadata
    topic = db.Column(db.String(200))  # Main topic/subject of the question
    keywords = db.Column(db.Text)  # JSON array of keywords
    bloom_taxonomy_level = db.Column(db.String(50))  # remember, understand, apply, analyze, evaluate, create
    
    # AI generation metadata
    confidence_score = db.Column(db.Float)  # AI confidence in question quality (0-1)
    source_sentence = db.Column(db.Text)  # Original sentence/paragraph from source
    
    # Question ordering and status
    order_index = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    
    # Foreign keys
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    
    def __repr__(self):
        return f'<Question {self.id}: {self.question_text[:50]}...>'
    
    def get_options_list(self):
        """Get options as a list"""
        if self.options:
            try:
                return json.loads(self.options)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_options_list(self, options_list):
        """Set options from a list"""
        self.options = json.dumps(options_list)
    
    def get_keywords_list(self):
        """Get keywords as a list"""
        if self.keywords:
            try:
                return json.loads(self.keywords)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_keywords_list(self, keywords_list):
        """Set keywords from a list"""
        self.keywords = json.dumps(keywords_list)
    
    def validate_answer(self, user_answer):
        """Validate a user's answer against the correct answer"""
        if not user_answer:
            return False
        
        user_answer = str(user_answer).strip().lower()
        correct = str(self.correct_answer).strip().lower()
        
        if self.question_type == 'multiple_choice':
            # For multiple choice, compare exact match
            return user_answer == correct
        
        elif self.question_type == 'true_false':
            # For true/false, accept various formats
            true_values = ['true', 't', 'yes', 'y', '1']
            false_values = ['false', 'f', 'no', 'n', '0']
            
            user_bool = user_answer in true_values
            correct_bool = correct in true_values
            
            return user_bool == correct_bool
        
        elif self.question_type == 'short_answer':
            # For short answer, check if key terms are present
            correct_words = set(correct.split())
            user_words = set(user_answer.split())
            
            # Calculate overlap percentage
            if not correct_words:
                return False
            
            overlap = len(correct_words.intersection(user_words))
            overlap_percentage = overlap / len(correct_words)
            
            # Consider correct if 70% of key terms are present
            return overlap_percentage >= 0.7
        
        else:
            # For essay questions, manual grading required
            return None
    
    def get_difficulty_score(self):
        """Get numeric difficulty score"""
        difficulty_map = {
            'easy': 1,
            'medium': 2,
            'hard': 3
        }
        return difficulty_map.get(self.difficulty_level, 2)
    
    def to_dict(self, include_answer=True):
        """Convert question to dictionary"""
        data = {
            'id': self.id,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'difficulty_level': self.difficulty_level,
            'topic': self.topic,
            'keywords': self.get_keywords_list(),
            'bloom_taxonomy_level': self.bloom_taxonomy_level,
            'confidence_score': self.confidence_score,
            'order_index': self.order_index,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'quiz_id': self.quiz_id
        }
        
        # Include options for multiple choice questions
        if self.question_type == 'multiple_choice':
            data['options'] = self.get_options_list()
        
        # Include answer information if requested
        if include_answer:
            data['correct_answer'] = self.correct_answer
            data['explanation'] = self.explanation
            data['source_sentence'] = self.source_sentence
        
        return data
    
    @staticmethod
    def get_question_types():
        """Get available question types"""
        return [
            {
                'value': 'multiple_choice',
                'label': 'Multiple Choice',
                'description': 'Questions with 4 answer options'
            },
            {
                'value': 'true_false',
                'label': 'True/False',
                'description': 'Questions with true or false answers'
            },
            {
                'value': 'short_answer',
                'label': 'Short Answer',
                'description': 'Questions requiring brief written responses'
            },
            {
                'value': 'essay',
                'label': 'Essay',
                'description': 'Questions requiring detailed written responses'
            }
        ]
    
    @staticmethod
    def get_difficulty_levels():
        """Get available difficulty levels"""
        return [
            {
                'value': 'easy',
                'label': 'Easy',
                'description': 'Basic recall and understanding'
            },
            {
                'value': 'medium',
                'label': 'Medium',
                'description': 'Application and analysis'
            },
            {
                'value': 'hard',
                'label': 'Hard',
                'description': 'Synthesis and evaluation'
            }
        ]
