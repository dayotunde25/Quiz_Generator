"""
Subscription Model
"""
from datetime import datetime, timezone
from app import db
import json


class Subscription(db.Model):
    """Subscription model for tracking user subscriptions and payments"""
    
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Stripe integration
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    stripe_customer_id = db.Column(db.String(100))
    stripe_price_id = db.Column(db.String(100))
    
    # Subscription details
    plan_name = db.Column(db.String(50), nullable=False)  # free, premium, school
    status = db.Column(db.String(20), nullable=False)  # active, canceled, past_due, unpaid
    
    # Billing information
    current_period_start = db.Column(db.DateTime(timezone=True))
    current_period_end = db.Column(db.DateTime(timezone=True))
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    canceled_at = db.Column(db.DateTime(timezone=True))
    
    # Pricing
    amount = db.Column(db.Integer)  # Amount in cents
    currency = db.Column(db.String(3), default='usd')
    interval = db.Column(db.String(20))  # month, year
    
    # Trial information
    trial_start = db.Column(db.DateTime(timezone=True))
    trial_end = db.Column(db.DateTime(timezone=True))
    
    # Usage tracking
    usage_data = db.Column(db.Text)  # JSON data for usage tracking
    
    # Timestamps
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f'<Subscription {self.plan_name} for User {self.user_id}>'
    
    def is_active(self):
        """Check if subscription is currently active"""
        if self.status != 'active':
            return False
        
        if self.current_period_end and self.current_period_end < datetime.now(timezone.utc):
            return False
        
        return True
    
    def is_in_trial(self):
        """Check if subscription is in trial period"""
        if not self.trial_start or not self.trial_end:
            return False
        
        now = datetime.now(timezone.utc)
        return self.trial_start <= now <= self.trial_end
    
    def days_until_renewal(self):
        """Get days until next renewal"""
        if not self.current_period_end:
            return None
        
        delta = self.current_period_end - datetime.now(timezone.utc)
        return max(0, delta.days)
    
    def get_usage_data(self):
        """Get usage data as dictionary"""
        if self.usage_data:
            try:
                return json.loads(self.usage_data)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_usage_data(self, data):
        """Set usage data from dictionary"""
        self.usage_data = json.dumps(data)
    
    def update_usage(self, metric, value):
        """Update a specific usage metric"""
        usage = self.get_usage_data()
        usage[metric] = value
        self.set_usage_data(usage)
        db.session.commit()
    
    def increment_usage(self, metric, amount=1):
        """Increment a usage metric"""
        usage = self.get_usage_data()
        usage[metric] = usage.get(metric, 0) + amount
        self.set_usage_data(usage)
        db.session.commit()
    
    def cancel(self, at_period_end=True):
        """Cancel the subscription"""
        if at_period_end:
            self.cancel_at_period_end = True
        else:
            self.status = 'canceled'
            self.canceled_at = datetime.now(timezone.utc)
        
        db.session.commit()
    
    def reactivate(self):
        """Reactivate a canceled subscription"""
        self.status = 'active'
        self.cancel_at_period_end = False
        self.canceled_at = None
        db.session.commit()
    
    def to_dict(self):
        """Convert subscription to dictionary"""
        return {
            'id': self.id,
            'stripe_subscription_id': self.stripe_subscription_id,
            'plan_name': self.plan_name,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at else None,
            'amount': self.amount,
            'currency': self.currency,
            'interval': self.interval,
            'trial_start': self.trial_start.isoformat() if self.trial_start else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'is_active': self.is_active(),
            'is_in_trial': self.is_in_trial(),
            'days_until_renewal': self.days_until_renewal(),
            'usage_data': self.get_usage_data(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id
        }
    
    @staticmethod
    def get_active_subscription(user_id):
        """Get the active subscription for a user"""
        return Subscription.query.filter_by(
            user_id=user_id,
            status='active'
        ).first()
    
    @staticmethod
    def create_free_subscription(user_id):
        """Create a free subscription for a new user"""
        subscription = Subscription(
            user_id=user_id,
            plan_name='free',
            status='active',
            amount=0,
            currency='usd',
            interval='month'
        )
        db.session.add(subscription)
        db.session.commit()
        return subscription
