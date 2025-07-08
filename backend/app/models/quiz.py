"""
Quiz Model
"""
from datetime import datetime, timezone
from app import db
import json


class Quiz(db.Model):
    """Quiz model for storing generated quizzes"""
    
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Content source
    source_text = db.Column(db.Text)  # Original text content
    source_file_id = db.Column(db.Integer, db.ForeignKey('files.id'))
    
    # Quiz configuration
    difficulty_level = db.Column(db.String(20), default='medium')  # easy, medium, hard
    question_types = db.Column(db.Text)  # JSON array of question types
    total_questions = db.Column(db.Integer, default=10)
    
    # AI generation metadata
    ai_model_used = db.Column(db.String(100))
    generation_time = db.Column(db.Float)  # Time taken to generate in seconds
    generation_parameters = db.Column(db.Text)  # JSON of parameters used
    
    # Status and sharing
    status = db.Column(db.String(20), default='draft')  # draft, published, archived
    is_public = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(100), unique=True)
    
    # Usage statistics
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    published_at = db.Column(db.DateTime(timezone=True))
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy='dynamic', cascade='all, delete-orphan')
    source_file = db.relationship('File', backref='quizzes')
    
    def __repr__(self):
        return f'<Quiz {self.title}>'
    
    @property
    def question_count(self):
        """Get the actual number of questions in this quiz"""
        return self.questions.count()
    
    def get_question_types_list(self):
        """Get question types as a list"""
        if self.question_types:
            try:
                return json.loads(self.question_types)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_question_types_list(self, types_list):
        """Set question types from a list"""
        self.question_types = json.dumps(types_list)
    
    def get_generation_parameters(self):
        """Get generation parameters as a dictionary"""
        if self.generation_parameters:
            try:
                return json.loads(self.generation_parameters)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_generation_parameters(self, params_dict):
        """Set generation parameters from a dictionary"""
        self.generation_parameters = json.dumps(params_dict)
    
    def publish(self):
        """Publish the quiz"""
        self.status = 'published'
        self.published_at = datetime.now(timezone.utc)
        db.session.commit()
    
    def archive(self):
        """Archive the quiz"""
        self.status = 'archived'
        db.session.commit()
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        db.session.commit()
    
    def increment_download_count(self):
        """Increment download count"""
        self.download_count += 1
        db.session.commit()
    
    def generate_share_token(self):
        """Generate a unique share token"""
        import secrets
        self.share_token = secrets.token_urlsafe(32)
        db.session.commit()
        return self.share_token
    
    def to_dict(self, include_questions=False, include_source=False):
        """Convert quiz to dictionary"""
        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'difficulty_level': self.difficulty_level,
            'question_types': self.get_question_types_list(),
            'total_questions': self.total_questions,
            'question_count': self.question_count,
            'status': self.status,
            'is_public': self.is_public,
            'share_token': self.share_token,
            'view_count': self.view_count,
            'download_count': self.download_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'user_id': self.user_id,
            'source_file_id': self.source_file_id,
            'ai_model_used': self.ai_model_used,
            'generation_time': self.generation_time
        }
        
        if include_questions:
            data['questions'] = [q.to_dict() for q in self.questions.all()]
        
        if include_source:
            data['source_text'] = self.source_text
            data['generation_parameters'] = self.get_generation_parameters()
            if self.source_file:
                data['source_file'] = self.source_file.to_dict()
        
        return data
    
    @staticmethod
    def get_by_share_token(token):
        """Get quiz by share token"""
        return Quiz.query.filter_by(share_token=token, is_public=True).first()
