# AI-Powered Quiz Generator for Teachers

A production-ready web application that allows teachers to generate quiz questions automatically from lesson content using advanced NLP and AI technologies.

## 🚀 Features

### Core Features
- **Smart Question Generation**: Upload documents (PDF, DOCX, TXT) or paste text to generate multiple-choice, true/false, and short-answer questions
- **AI-Powered Analysis**: Uses advanced NLP to extract key concepts and generate relevant questions
- **Difficulty Scaling**: Automatically generates questions at Easy, Medium, and Hard difficulty levels
- **Real-time Preview**: Edit and customize generated questions before finalizing
- **Export Options**: Export quizzes as PDF or Word documents with professional formatting

### User Management
- **Secure Authentication**: JWT-based authentication with password reset
- **Role-based Access**: Teacher and School Admin roles
- **Dashboard**: Manage quizzes, view history, and track usage

### Monetization (Freemium Model)
- **Free Tier**: 5 quiz generations per month
- **Premium**: Unlimited access, PDF export, analytics dashboard
- **School Plan**: Multi-user management, admin dashboard, bulk operations

## 🛠 Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for responsive design
- **React Query** for state management and API calls
- **React Hook Form** with Zod validation

### Backend
- **Flask** with Python 3.11+
- **SQLAlchemy** ORM with PostgreSQL
- **Redis** for caching and session management
- **Flask-JWT-Extended** for authentication
- **Celery** for background tasks

### AI/NLP
- **Hugging Face Transformers** for question generation
- **spaCy** for NLP preprocessing
- **OpenAI API** for enhanced question generation (optional)

### Infrastructure
- **PostgreSQL** database
- **Redis** for caching
- **Docker** for containerization
- **Stripe** for payment processing

## 📁 Project Structure

```
quiz-maker/
├── frontend/                 # React application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API services
│   │   ├── store/          # State management
│   │   └── utils/          # Utility functions
│   ├── public/
│   └── package.json
├── backend/                  # Flask API
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── routes/         # API routes
│   │   ├── services/       # Business logic
│   │   ├── utils/          # Utility functions
│   │   └── ai/             # AI/NLP modules
│   ├── migrations/         # Database migrations
│   ├── tests/              # Backend tests
│   └── requirements.txt
├── shared/                   # Shared utilities
├── docs/                    # Documentation
├── scripts/                 # Setup scripts
└── docker-compose.yml      # Development environment
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose (recommended)
- OR: Node.js 18+, Python 3.11+, PostgreSQL 14+, Redis 6+

### Easy Setup with Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd quiz-maker
   ```

2. **Run the setup script**
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

   This script will:
   - Create environment files
   - Build Docker containers
   - Set up the database
   - Optionally create an admin user and seed data

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000
   - API Documentation: http://localhost:5000/docs

### Manual Development Setup

1. **Clone and setup environment**
   ```bash
   git clone <repository-url>
   cd quiz-maker

   # Copy environment files
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

   # Download spaCy model
   python -m spacy download en_core_web_sm
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   ```

4. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb quiz_maker_dev

   # Run migrations
   cd backend
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade

   # Create admin user (optional)
   flask create-admin

   # Seed sample data (optional)
   flask seed-data
   ```

5. **Start Services**
   ```bash
   # Terminal 1: Redis
   redis-server

   # Terminal 2: Backend
   cd backend
   flask run

   # Terminal 3: Frontend
   cd frontend
   npm run dev

   # Terminal 4: Celery Worker (optional, for background tasks)
   cd backend
   celery -A app.celery worker --loglevel=info
   ```

### Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild containers
docker-compose build

# Run database migrations
docker-compose run --rm backend flask db upgrade

# Create admin user
docker-compose run --rm backend flask create-admin

# Access backend shell
docker-compose run --rm backend flask shell
```

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc`

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Production Build
```bash
# Frontend
cd frontend
npm run build

# Backend
cd backend
pip install -r requirements.txt
flask db upgrade
```

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📞 Support

For support, email support@quizmaker.com or join our Slack channel.
