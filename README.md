# HypothesisAI

A Multi-Agent Scientific Research Acceleration Platform.

## Features

- 🔍 Multi-database literature search
- 🧠 AI-powered knowledge synthesis
- 💡 Automated hypothesis generation
- 📊 Research pattern recognition
- 👥 Team collaboration
- 📚 Comprehensive export options

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 14+
- Redis 7+

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hypothesisai.git
cd hypothesisai

Set up the backend:

bashcd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
alembic upgrade head

Set up the frontend:

bashcd ../frontend
npm install
cp .env.example .env
# Edit .env with your configuration

Start development services:

bashcd ../.docker
docker-compose -f docker-compose.dev.yml up -d

Run the application:

bash# Terminal 1 - Backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm start

# Terminal 3 - Celery Worker
cd backend
celery -A app.core.celery_app worker --loglevel=info

# Terminal 4 - Celery Flower (optional)
cd backend
celery -A app.core.celery_app flower
Access the application at:

Frontend: http://localhost:3000
Backend API: http://localhost:8000
API Documentation: http://localhost:8000/docs
Flower (Celery monitoring): http://localhost:5555

Testing
bash# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
Docker Deployment
bashcd .docker
docker-compose up --build
Documentation

API Documentation
Architecture Guide
Deployment Guide
Development Guide
User Manual

Contributing
Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.
License
This project is licensed under the MIT License - see the LICENSE file for details.
Support
For support, email support@hypothesisai.com or join our Discord server.
