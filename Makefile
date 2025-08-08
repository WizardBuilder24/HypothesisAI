.PHONY: help install dev test build deploy clean
help:
@echo "Available commands:"
@echo "  make install    - Install all dependencies"
@echo "  make dev        - Start development environment"
@echo "  make test       - Run all tests"
@echo "  make build      - Build Docker images"
@echo "  make deploy     - Deploy to production"
@echo "  make clean      - Clean up generated files"
install:
cd backend && pip install -r requirements.txt
cd frontend && npm install
dev:
docker-compose -f .docker/docker-compose.dev.yml up -d
@echo "Starting backend..."
cd backend && uvicorn app.main:app --reload &
@echo "Starting frontend..."
cd frontend && npm start &
@echo "Development environment started!"
test:
cd backend && pytest
cd frontend && npm test
build:
docker-compose -f .docker/docker-compose.yml build
deploy:
./scripts/deploy.sh
clean:
find . -type d -name "pycache" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
rm -rf backend/.pytest_cache
rm -rf frontend/node_modules
rm -rf frontend/build
rm -rf backend/htmlcov
rm -rf .coverage
