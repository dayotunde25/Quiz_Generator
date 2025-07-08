# Deployment Guide

This guide covers deploying the AI-Powered Quiz Generator to production environments.

## Prerequisites

- Docker and Docker Compose
- Domain name with SSL certificate
- PostgreSQL database (managed service recommended)
- Redis instance (managed service recommended)
- Email service (SendGrid, AWS SES, etc.)
- Stripe account for payments
- OpenAI API key (optional)

## Environment Setup

### Backend Environment Variables

Create a production `.env` file in the `backend` directory:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=0
SECRET_KEY=your-super-secret-production-key
JWT_SECRET_KEY=your-jwt-secret-production-key

# Database
DATABASE_URL=postgresql://user:password@host:port/database
SQLALCHEMY_TRACK_MODIFICATIONS=False

# Redis
REDIS_URL=redis://host:port/0

# Celery
CELERY_BROKER_URL=redis://host:port/0
CELERY_RESULT_BACKEND=redis://host:port/0

# Email
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=your-sendgrid-api-key
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# AI/NLP
OPENAI_API_KEY=your-openai-api-key
HUGGINGFACE_API_KEY=your-huggingface-api-key

# Stripe
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# File Upload
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=/app/uploads
ALLOWED_EXTENSIONS=txt,pdf,docx

# Security
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Monitoring
SENTRY_DSN=your-sentry-dsn

# CORS
CORS_ORIGINS=https://yourdomain.com
```

### Frontend Environment Variables

Create a production `.env` file in the `frontend` directory:

```bash
VITE_API_URL=https://api.yourdomain.com
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
VITE_APP_NAME=Quiz Maker
VITE_APP_VERSION=1.0.0
```

## Docker Production Setup

### 1. Create Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - static_files:/var/www/static
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

  # Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - FLASK_ENV=production
    volumes:
      - ./backend/.env:/app/.env
      - uploads:/app/uploads
      - static_files:/app/static
    depends_on:
      - redis
    restart: unless-stopped

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    volumes:
      - static_files:/app/dist
    restart: unless-stopped

  # Redis Cache
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # Celery Worker
  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.celery worker --loglevel=info
    volumes:
      - ./backend/.env:/app/.env
      - uploads:/app/uploads
    depends_on:
      - redis
    restart: unless-stopped

  # Celery Beat
  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A app.celery beat --loglevel=info
    volumes:
      - ./backend/.env:/app/.env
    depends_on:
      - redis
    restart: unless-stopped

volumes:
  redis_data:
  uploads:
  static_files:
```

### 2. Create Production Dockerfiles

**Backend Dockerfile.prod:**

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy project
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

**Frontend Dockerfile.prod:**

```dockerfile
FROM node:18-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 3. Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:5000;
    }

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Frontend
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # File uploads
        client_max_body_size 16M;
    }
}
```

## Database Setup

### 1. Create Production Database

```sql
CREATE DATABASE quiz_maker_prod;
CREATE USER quiz_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE quiz_maker_prod TO quiz_user;
```

### 2. Run Migrations

```bash
docker-compose -f docker-compose.prod.yml run --rm backend flask db upgrade
```

### 3. Create Admin User

```bash
docker-compose -f docker-compose.prod.yml run --rm backend flask create-admin
```

## Deployment Steps

### 1. Clone Repository

```bash
git clone <repository-url>
cd quiz-maker
```

### 2. Set Up Environment

```bash
# Copy and configure environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit the files with production values
nano backend/.env
nano frontend/.env
```

### 3. Build and Deploy

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
docker-compose -f docker-compose.prod.yml run --rm backend flask db upgrade

# Create admin user
docker-compose -f docker-compose.prod.yml run --rm backend flask create-admin
```

### 4. Set Up SSL Certificate

Use Let's Encrypt with Certbot:

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Set up auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring and Maintenance

### 1. Health Checks

Create health check endpoints and monitor them:

```bash
# Check backend health
curl https://api.yourdomain.com/api/health

# Check frontend
curl https://yourdomain.com
```

### 2. Log Monitoring

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 3. Database Backups

Set up automated database backups:

```bash
#!/bin/bash
# backup.sh
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 4. Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run any new migrations
docker-compose -f docker-compose.prod.yml run --rm backend flask db upgrade
```

## Security Considerations

1. **Environment Variables**: Never commit production secrets to version control
2. **Database Security**: Use strong passwords and restrict access
3. **SSL/TLS**: Always use HTTPS in production
4. **File Uploads**: Validate and scan uploaded files
5. **Rate Limiting**: Implement rate limiting for API endpoints
6. **CORS**: Configure CORS properly for your domain
7. **Updates**: Keep dependencies and base images updated

## Performance Optimization

1. **Database**: Use connection pooling and optimize queries
2. **Caching**: Implement Redis caching for frequently accessed data
3. **CDN**: Use a CDN for static assets
4. **Compression**: Enable gzip compression in Nginx
5. **Monitoring**: Set up application performance monitoring

## Troubleshooting

### Common Issues

1. **Database Connection**: Check DATABASE_URL and network connectivity
2. **File Permissions**: Ensure proper file permissions for uploads
3. **Memory Issues**: Monitor memory usage and adjust container limits
4. **SSL Certificate**: Verify certificate installation and renewal

### Useful Commands

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend

# View resource usage
docker stats

# Clean up unused resources
docker system prune
```
