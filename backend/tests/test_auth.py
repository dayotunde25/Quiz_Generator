"""
Authentication Tests
"""
import pytest
from app.models.user import User


class TestAuth:
    """Test authentication endpoints"""
    
    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post('/api/auth/register', json={
            'email': 'newuser@example.com',
            'password': 'Password123!',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'access_token' in data
        assert 'user' in data
        assert data['user']['email'] == 'newuser@example.com'
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post('/api/auth/register', json={
            'email': 'invalid-email',
            'password': 'Password123!',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Invalid email format' in data['message']
    
    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        response = client.post('/api/auth/register', json={
            'email': 'newuser@example.com',
            'password': 'weak',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Password must be at least 8 characters' in data['message']
    
    def test_register_duplicate_email(self, client, user):
        """Test registration with existing email"""
        response = client.post('/api/auth/register', json={
            'email': user.email,
            'password': 'Password123!',
            'first_name': 'New',
            'last_name': 'User'
        })
        
        assert response.status_code == 409
        data = response.get_json()
        assert 'Email already registered' in data['message']
    
    def test_login_success(self, client, user):
        """Test successful login"""
        response = client.post('/api/auth/login', json={
            'email': user.email,
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'access_token' in data
        assert 'user' in data
        assert data['user']['email'] == user.email
    
    def test_login_invalid_credentials(self, client, user):
        """Test login with invalid credentials"""
        response = client.post('/api/auth/login', json={
            'email': user.email,
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'Invalid email or password' in data['message']
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert 'Invalid email or password' in data['message']
    
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info"""
        response = client.get('/api/auth/me', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'user' in data
        assert data['user']['email'] == 'test@example.com'
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without auth"""
        response = client.get('/api/auth/me')
        
        assert response.status_code == 401
    
    def test_logout(self, client, auth_headers):
        """Test logout"""
        response = client.post('/api/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'Successfully logged out' in data['message']
    
    def test_forgot_password(self, client, user):
        """Test forgot password request"""
        response = client.post('/api/auth/forgot-password', json={
            'email': user.email
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'password reset link has been sent' in data['message']
    
    def test_forgot_password_nonexistent_email(self, client):
        """Test forgot password with nonexistent email"""
        response = client.post('/api/auth/forgot-password', json={
            'email': 'nonexistent@example.com'
        })
        
        # Should still return success to prevent email enumeration
        assert response.status_code == 200
