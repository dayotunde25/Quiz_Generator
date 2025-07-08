"""
Test Configuration
"""
import pytest
import tempfile
import os
from app import create_app, db
from app.models.user import User
from app.models.subscription import Subscription


@pytest.fixture
def app():
    """Create application for testing"""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def user(app):
    """Create test user"""
    with app.app_context():
        user = User(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            role='teacher',
            is_verified=True
        )
        user.set_password('password123')
        
        db.session.add(user)
        db.session.commit()
        
        # Create subscription
        Subscription.create_free_subscription(user.id)
        
        return user


@pytest.fixture
def admin_user(app):
    """Create test admin user"""
    with app.app_context():
        user = User(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            role='school_admin',
            is_verified=True,
            subscription_plan='school'
        )
        user.set_password('admin123')
        
        db.session.add(user)
        db.session.commit()
        
        return user


@pytest.fixture
def auth_headers(client, user):
    """Get authentication headers for test user"""
    response = client.post('/api/auth/login', json={
        'email': user.email,
        'password': 'password123'
    })
    
    data = response.get_json()
    token = data['access_token']
    
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def admin_auth_headers(client, admin_user):
    """Get authentication headers for admin user"""
    response = client.post('/api/auth/login', json={
        'email': admin_user.email,
        'password': 'admin123'
    })
    
    data = response.get_json()
    token = data['access_token']
    
    return {'Authorization': f'Bearer {token}'}
