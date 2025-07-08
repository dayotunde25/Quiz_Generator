-- Initialize database for Quiz Maker

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE quiz_maker_dev'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'quiz_maker_dev')\gexec

-- Create test database if it doesn't exist
SELECT 'CREATE DATABASE quiz_maker_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'quiz_maker_test')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE quiz_maker_dev TO quiz_user;
GRANT ALL PRIVILEGES ON DATABASE quiz_maker_test TO quiz_user;
