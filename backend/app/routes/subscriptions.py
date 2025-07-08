"""
Subscription Routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.user import User
from app.models.subscription import Subscription
from app.utils.decorators import validate_json

subscriptions_bp = Blueprint('subscriptions', __name__)


@subscriptions_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """Get available subscription plans"""
    from app.config import BaseConfig
    
    return jsonify({
        'plans': BaseConfig.SUBSCRIPTION_PLANS
    }), 200


@subscriptions_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_subscription():
    """Get current user's subscription"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    subscription = Subscription.get_active_subscription(current_user_id)
    
    return jsonify({
        'user_subscription': {
            'plan': user.subscription_plan,
            'status': user.subscription_status,
            'expires_at': user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            'quiz_count_current_month': user.quiz_count_current_month,
            'can_create_quiz': user.can_create_quiz(),
            'subscription_active': user.is_subscription_active()
        },
        'subscription': subscription.to_dict() if subscription else None
    }), 200


@subscriptions_bp.route('/usage', methods=['GET'])
@jwt_required()
def get_usage_stats():
    """Get user's usage statistics"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    # Get quiz count for current month
    from datetime import datetime, timezone
    from app.models.quiz import Quiz
    
    current_month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    quiz_count_this_month = Quiz.query.filter(
        Quiz.user_id == current_user_id,
        Quiz.created_at >= current_month_start
    ).count()
    
    # Get total stats
    total_quizzes = Quiz.query.filter_by(user_id=current_user_id).count()
    published_quizzes = Quiz.query.filter_by(user_id=current_user_id, status='published').count()
    
    from app.models.file import File
    total_files = File.query.filter_by(user_id=current_user_id).count()
    
    return jsonify({
        'usage': {
            'quiz_count_current_month': quiz_count_this_month,
            'quiz_limit': 5 if user.subscription_plan == 'free' else -1,
            'total_quizzes': total_quizzes,
            'published_quizzes': published_quizzes,
            'total_files': total_files,
            'plan': user.subscription_plan,
            'can_create_quiz': user.can_create_quiz()
        }
    }), 200


@subscriptions_bp.route('/create-checkout-session', methods=['POST'])
@jwt_required()
@validate_json(['plan'])
def create_checkout_session():
    """Create Stripe checkout session for subscription"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    data = request.get_json()
    plan = data['plan']
    
    from app.config import BaseConfig
    if plan not in BaseConfig.SUBSCRIPTION_PLANS:
        return jsonify({'message': 'Invalid subscription plan'}), 400
    
    if plan == 'free':
        return jsonify({'message': 'Cannot create checkout for free plan'}), 400
    
    # TODO: Implement Stripe checkout session creation
    # This would integrate with Stripe API to create a checkout session
    
    return jsonify({
        'message': 'Stripe integration not implemented yet',
        'checkout_url': '#'
    }), 501


@subscriptions_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription():
    """Cancel current subscription"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if user.subscription_plan == 'free':
        return jsonify({'message': 'Cannot cancel free plan'}), 400
    
    subscription = Subscription.get_active_subscription(current_user_id)
    
    if not subscription:
        return jsonify({'message': 'No active subscription found'}), 404
    
    # Cancel subscription (at period end)
    subscription.cancel(at_period_end=True)
    
    return jsonify({
        'message': 'Subscription will be canceled at the end of the current period',
        'subscription': subscription.to_dict()
    }), 200


@subscriptions_bp.route('/reactivate', methods=['POST'])
@jwt_required()
def reactivate_subscription():
    """Reactivate a canceled subscription"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    subscription = Subscription.query.filter_by(
        user_id=current_user_id
    ).order_by(Subscription.created_at.desc()).first()
    
    if not subscription:
        return jsonify({'message': 'No subscription found'}), 404
    
    if not subscription.cancel_at_period_end:
        return jsonify({'message': 'Subscription is not canceled'}), 400
    
    # Reactivate subscription
    subscription.reactivate()
    
    return jsonify({
        'message': 'Subscription reactivated successfully',
        'subscription': subscription.to_dict()
    }), 200


@subscriptions_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    # TODO: Implement Stripe webhook handling
    # This would handle events like:
    # - invoice.payment_succeeded
    # - customer.subscription.updated
    # - customer.subscription.deleted
    
    return jsonify({'message': 'Webhook received'}), 200
