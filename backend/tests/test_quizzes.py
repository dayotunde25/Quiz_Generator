"""
Quiz Tests
"""
import pytest
from app import db
from app.models.quiz import Quiz
from app.models.question import Question


class TestQuizzes:
    """Test quiz endpoints"""
    
    def test_create_quiz(self, client, auth_headers):
        """Test creating a new quiz"""
        response = client.post('/api/quizzes', 
            headers=auth_headers,
            json={
                'title': 'Test Quiz',
                'description': 'A test quiz',
                'source_text': 'This is test content for the quiz.',
                'difficulty_level': 'medium',
                'total_questions': 5
            }
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert 'quiz' in data
        assert data['quiz']['title'] == 'Test Quiz'
        assert data['quiz']['status'] == 'draft'
    
    def test_create_quiz_unauthorized(self, client):
        """Test creating quiz without authentication"""
        response = client.post('/api/quizzes', json={
            'title': 'Test Quiz'
        })
        
        assert response.status_code == 401
    
    def test_get_quizzes(self, client, auth_headers, user):
        """Test getting user's quizzes"""
        # Create a test quiz
        quiz = Quiz(
            title='Test Quiz',
            description='Test description',
            user_id=user.id
        )
        db.session.add(quiz)
        db.session.commit()
        
        response = client.get('/api/quizzes', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'quizzes' in data
        assert len(data['quizzes']) == 1
        assert data['quizzes'][0]['title'] == 'Test Quiz'
    
    def test_get_quiz_by_id(self, client, auth_headers, user):
        """Test getting a specific quiz"""
        quiz = Quiz(
            title='Test Quiz',
            description='Test description',
            user_id=user.id
        )
        db.session.add(quiz)
        db.session.commit()
        
        response = client.get(f'/api/quizzes/{quiz.id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'quiz' in data
        assert data['quiz']['title'] == 'Test Quiz'
    
    def test_get_quiz_not_found(self, client, auth_headers):
        """Test getting nonexistent quiz"""
        response = client.get('/api/quizzes/999', headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_get_quiz_not_owned(self, client, auth_headers, admin_user):
        """Test getting quiz not owned by user"""
        quiz = Quiz(
            title='Admin Quiz',
            description='Admin description',
            user_id=admin_user.id
        )
        db.session.add(quiz)
        db.session.commit()
        
        response = client.get(f'/api/quizzes/{quiz.id}', headers=auth_headers)
        
        assert response.status_code == 403
    
    def test_update_quiz(self, client, auth_headers, user):
        """Test updating a quiz"""
        quiz = Quiz(
            title='Original Title',
            description='Original description',
            user_id=user.id
        )
        db.session.add(quiz)
        db.session.commit()
        
        response = client.put(f'/api/quizzes/{quiz.id}',
            headers=auth_headers,
            json={
                'title': 'Updated Title',
                'description': 'Updated description'
            }
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['quiz']['title'] == 'Updated Title'
        assert data['quiz']['description'] == 'Updated description'
    
    def test_delete_quiz(self, client, auth_headers, user):
        """Test deleting a quiz"""
        quiz = Quiz(
            title='Test Quiz',
            description='Test description',
            user_id=user.id
        )
        db.session.add(quiz)
        db.session.commit()
        quiz_id = quiz.id
        
        response = client.delete(f'/api/quizzes/{quiz_id}', headers=auth_headers)
        
        assert response.status_code == 200
        
        # Verify quiz is deleted
        deleted_quiz = Quiz.query.get(quiz_id)
        assert deleted_quiz is None
    
    def test_publish_quiz(self, client, auth_headers, user):
        """Test publishing a quiz"""
        quiz = Quiz(
            title='Test Quiz',
            description='Test description',
            user_id=user.id
        )
        db.session.add(quiz)
        db.session.commit()
        
        # Add a question so quiz can be published
        question = Question(
            question_text='Test question?',
            question_type='multiple_choice',
            correct_answer='A',
            quiz_id=quiz.id
        )
        db.session.add(question)
        db.session.commit()
        
        response = client.post(f'/api/quizzes/{quiz.id}/publish', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['quiz']['status'] == 'published'
    
    def test_publish_quiz_without_questions(self, client, auth_headers, user):
        """Test publishing quiz without questions"""
        quiz = Quiz(
            title='Test Quiz',
            description='Test description',
            user_id=user.id
        )
        db.session.add(quiz)
        db.session.commit()
        
        response = client.post(f'/api/quizzes/{quiz.id}/publish', headers=auth_headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'Cannot publish quiz without questions' in data['message']
    
    def test_generate_share_link(self, client, auth_headers, user):
        """Test generating share link for quiz"""
        quiz = Quiz(
            title='Test Quiz',
            description='Test description',
            status='published',
            user_id=user.id
        )
        db.session.add(quiz)
        db.session.commit()
        
        response = client.post(f'/api/quizzes/{quiz.id}/share', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'share_token' in data
        assert 'share_url' in data
