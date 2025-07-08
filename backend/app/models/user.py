"""
User Model
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(db.Model):
    """User model for authentication and profile management"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    
    # Role-based access control
    role = db.Column(db.String(20), nullable=False, default='teacher')  # teacher, school_admin
    
    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    
    # Subscription tracking
    subscription_plan = db.Column(db.String(20), default='free', nullable=False)
    subscription_status = db.Column(db.String(20), default='active', nullable=False)
    subscription_expires_at = db.Column(db.DateTime(timezone=True))
    stripe_customer_id = db.Column(db.String(100))
    
    # Usage tracking
    quiz_count_current_month = db.Column(db.Integer, default=0, nullable=False)
    last_quiz_reset = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Profile information
    school_name = db.Column(db.String(200))
    subject_areas = db.Column(db.Text)  # JSON string of subject areas
    bio = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    last_login = db.Column(db.DateTime(timezone=True))
    
    # Password reset
    reset_token = db.Column(db.String(100))
    reset_token_expires = db.Column(db.DateTime(timezone=True))
    
    # Email verification
    verification_token = db.Column(db.String(100))
    
    # Relationships
    quizzes = db.relationship('Quiz', backref='creator', lazy='dynamic', cascade='all, delete-orphan')
    files = db.relationship('File', backref='uploader', lazy='dynamic', cascade='all, delete-orphan')
    subscriptions = db.relationship('Subscription', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def can_create_quiz(self):
        """Check if user can create a new quiz based on their plan"""
        if self.subscription_plan == 'free':
            return self.quiz_count_current_month < 5
        return True  # Premium and school plans have unlimited quizzes
    
    def increment_quiz_count(self):
        """Increment the monthly quiz count"""
        # Reset count if it's a new month
        now = datetime.now(timezone.utc)
        if (now.year, now.month) != (self.last_quiz_reset.year, self.last_quiz_reset.month):
            self.quiz_count_current_month = 0
            self.last_quiz_reset = now
        
        self.quiz_count_current_month += 1
        db.session.commit()
    
    def has_feature(self, feature):
        """Check if user has access to a specific feature"""
        from app.config import BaseConfig
        
        plan_features = BaseConfig.SUBSCRIPTION_PLANS.get(self.subscription_plan, {}).get('features', [])
        return feature in plan_features
    
    def is_subscription_active(self):
        """Check if user's subscription is active"""
        if self.subscription_plan == 'free':
            return True
        
        if self.subscription_status != 'active':
            return False
        
        if self.subscription_expires_at and self.subscription_expires_at < datetime.now(timezone.utc):
            return False
        
        return True
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'subscription_plan': self.subscription_plan,
            'subscription_status': self.subscription_status,
            'school_name': self.school_name,
            'subject_areas': self.subject_areas,
            'bio': self.bio,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'quiz_count_current_month': self.quiz_count_current_month,
            'can_create_quiz': self.can_create_quiz(),
            'subscription_active': self.is_subscription_active()
        }
        
        if include_sensitive:
            data.update({
                'stripe_customer_id': self.stripe_customer_id,
                'subscription_expires_at': self.subscription_expires_at.isoformat() if self.subscription_expires_at else None,
            })
        
        return data
