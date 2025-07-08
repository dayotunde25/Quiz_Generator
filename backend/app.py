"""
Flask Application Entry Point
"""
import os
from app import create_app, db
from app.models import User, Quiz, Question, Subscription, File
from flask.cli import with_appcontext
import click

# Create Flask application
app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell"""
    return {
        'db': db,
        'User': User,
        'Quiz': Quiz,
        'Question': Question,
        'Subscription': Subscription,
        'File': File
    }


@app.cli.command()
@with_appcontext
def init_db():
    """Initialize the database"""
    db.create_all()
    click.echo('Database initialized.')


@app.cli.command()
@with_appcontext
def create_admin():
    """Create an admin user"""
    email = click.prompt('Admin email')
    password = click.prompt('Admin password', hide_input=True)
    first_name = click.prompt('First name')
    last_name = click.prompt('Last name')
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        click.echo('User already exists.')
        return
    
    # Create admin user
    admin = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        role='school_admin',
        is_verified=True,
        subscription_plan='school'
    )
    admin.set_password(password)
    
    db.session.add(admin)
    db.session.commit()
    
    # Create subscription
    Subscription.create_free_subscription(admin.id)
    
    click.echo(f'Admin user {email} created successfully.')


@app.cli.command()
@with_appcontext
def seed_data():
    """Seed the database with sample data"""
    # Create sample users
    teacher1 = User(
        email='teacher1@example.com',
        first_name='John',
        last_name='Smith',
        role='teacher',
        is_verified=True,
        school_name='Springfield Elementary',
        subject_areas='["Mathematics", "Science"]'
    )
    teacher1.set_password('password123')
    
    teacher2 = User(
        email='teacher2@example.com',
        first_name='Jane',
        last_name='Doe',
        role='teacher',
        is_verified=True,
        school_name='Riverside High School',
        subject_areas='["English", "Literature"]'
    )
    teacher2.set_password('password123')
    
    db.session.add(teacher1)
    db.session.add(teacher2)
    db.session.commit()
    
    # Create subscriptions
    Subscription.create_free_subscription(teacher1.id)
    Subscription.create_free_subscription(teacher2.id)
    
    # Create sample quiz
    quiz = Quiz(
        title='Introduction to Photosynthesis',
        description='A quiz covering the basics of photosynthesis in plants',
        source_text='Photosynthesis is the process by which plants convert light energy into chemical energy...',
        difficulty_level='medium',
        total_questions=5,
        user_id=teacher1.id,
        status='published'
    )
    quiz.set_question_types_list(['multiple_choice', 'true_false'])
    
    db.session.add(quiz)
    db.session.commit()
    
    # Create sample questions
    questions = [
        Question(
            question_text='What is the primary purpose of photosynthesis?',
            question_type='multiple_choice',
            correct_answer='To convert light energy into chemical energy',
            explanation='Photosynthesis converts light energy from the sun into chemical energy stored in glucose.',
            topic='Photosynthesis Basics',
            difficulty_level='easy',
            quiz_id=quiz.id,
            order_index=1
        ),
        Question(
            question_text='Photosynthesis occurs in the chloroplasts of plant cells.',
            question_type='true_false',
            correct_answer='true',
            explanation='Chloroplasts contain chlorophyll and are the site of photosynthesis.',
            topic='Plant Cell Structure',
            difficulty_level='medium',
            quiz_id=quiz.id,
            order_index=2
        )
    ]
    
    # Set options for multiple choice question
    questions[0].set_options_list([
        'To convert light energy into chemical energy',
        'To break down glucose for energy',
        'To produce oxygen as waste',
        'To absorb carbon dioxide'
    ])
    
    for question in questions:
        db.session.add(question)
    
    db.session.commit()
    
    click.echo('Sample data created successfully.')


@app.cli.command()
@with_appcontext
def reset_db():
    """Reset the database (drop and recreate all tables)"""
    if click.confirm('This will delete all data. Are you sure?'):
        db.drop_all()
        db.create_all()
        click.echo('Database reset successfully.')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
