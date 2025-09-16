# ReactDjango Hub - Local-First Development Makefile
# Per ADR-010: Local-first development strategy for maximum velocity

.PHONY: help setup dev stop test clean migrate lint format docs

# Default target
help: ## Show this help message
	@echo "ReactDjango Hub - Local Development Commands"
	@echo "============================================="
	@echo "Strategy: Local-first development (ADR-010)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ==================== SETUP COMMANDS ====================

setup: ## One-time setup for local development
	@echo "Setting up local development environment..."
	@./scripts/setup-local-dev.sh

setup-db: ## Create all PostgreSQL databases locally
	@echo "Creating local PostgreSQL databases..."
	@createdb identity_service_db 2>/dev/null || echo "identity_service_db already exists"
	@createdb django_backend_db 2>/dev/null || echo "django_backend_db already exists"
	@createdb communication_service_db 2>/dev/null || echo "communication_service_db already exists"
	@createdb content_service_db 2>/dev/null || echo "content_service_db already exists"
	@createdb workflow_service_db 2>/dev/null || echo "workflow_service_db already exists"
	@echo "Databases created successfully"

setup-venv: ## Create Python virtual environments for all services
	@echo "Creating Python virtual environments..."
	@cd services/identity-service && python -m venv venv
	@cd services/communication-service && python -m venv venv
	@cd services/content-service && python -m venv venv
	@cd services/workflow-intelligence-service && python -m venv venv
	@cd backend && python -m venv venv
	@echo "Virtual environments created"

install-deps: ## Install dependencies for all services
	@echo "Installing dependencies..."
	@cd services/identity-service && . venv/bin/activate && pip install -r requirements.txt
	@cd services/communication-service && . venv/bin/activate && pip install -r requirements.txt
	@cd services/content-service && . venv/bin/activate && pip install -r requirements.txt
	@cd services/workflow-intelligence-service && . venv/bin/activate && pip install -r requirements.txt
	@cd backend && . venv/bin/activate && pip install -r requirements.txt
	@cd frontend && npm install
	@echo "Dependencies installed"

# ==================== DEVELOPMENT COMMANDS ====================

dev: ## Start all services locally (main development command)
	@echo "Starting all services locally..."
	@echo "Open separate terminals and run:"
	@echo "  1. make run-identity"
	@echo "  2. make run-backend"
	@echo "  3. make run-frontend"
	@echo "  4. make run-communication (if needed)"
	@echo "  5. make run-content (if needed)"
	@echo "  6. make run-workflow (if needed)"
	@echo ""
	@echo "Services will be available at:"
	@echo "  - Identity Service: http://localhost:8001/docs"
	@echo "  - Backend (Django): http://localhost:8000/api/docs"
	@echo "  - Frontend (React): http://localhost:3000"

run-identity: ## Run identity service
	@cd services/identity-service && . venv/bin/activate && python main.py

run-backend: ## Run Django backend service
	@cd backend && . venv/bin/activate && python manage.py runserver

run-frontend: ## Run React frontend
	@cd frontend && npm run dev

run-communication: ## Run communication service
	@cd services/communication-service && . venv/bin/activate && python main.py

run-content: ## Run content service
	@cd services/content-service && . venv/bin/activate && python main.py

run-workflow: ## Run workflow intelligence service
	@cd services/workflow-intelligence-service && . venv/bin/activate && python main.py

stop: ## Stop all running services
	@echo "Stopping services..."
	@pkill -f "python main.py" || true
	@pkill -f "python manage.py runserver" || true
	@pkill -f "npm run dev" || true
	@echo "Services stopped"

# ==================== DATABASE COMMANDS ====================

migrate: ## Run all database migrations
	@echo "Running database migrations..."
	@cd backend && . venv/bin/activate && python manage.py migrate
	@cd services/identity-service && . venv/bin/activate && alembic upgrade head
	@echo "Migrations complete"

migrate-backend: ## Run Django migrations
	@cd backend && . venv/bin/activate && python manage.py makemigrations && python manage.py migrate

db-shell: ## Open PostgreSQL shell
	@psql -d django_backend_db

db-reset: ## Reset all databases (WARNING: destroys data)
	@echo "WARNING: This will destroy all data. Press Ctrl+C to cancel, or wait 5 seconds..."
	@sleep 5
	@dropdb --if-exists identity_service_db
	@dropdb --if-exists django_backend_db
	@dropdb --if-exists communication_service_db
	@dropdb --if-exists content_service_db
	@dropdb --if-exists workflow_service_db
	@make setup-db
	@make migrate
	@echo "Databases reset successfully"

# ==================== TESTING COMMANDS ====================

test: ## Run all tests
	@echo "Running all tests..."
	@make test-backend
	@make test-frontend
	@make test-identity

test-backend: ## Run Django backend tests
	@cd backend && . venv/bin/activate && python manage.py test

test-frontend: ## Run React frontend tests
	@cd frontend && npm test

test-identity: ## Run identity service tests
	@cd services/identity-service && . venv/bin/activate && pytest

test-coverage: ## Run tests with coverage
	@cd backend && . venv/bin/activate && coverage run --source='.' manage.py test && coverage report
	@cd frontend && npm test -- --coverage

# ==================== CODE QUALITY COMMANDS ====================

lint: ## Run linting for all services
	@echo "Running linters..."
	@cd backend && . venv/bin/activate && flake8 .
	@cd services/identity-service && . venv/bin/activate && flake8 .
	@cd frontend && npm run lint

format: ## Format code in all services
	@echo "Formatting code..."
	@cd backend && . venv/bin/activate && black .
	@cd services/identity-service && . venv/bin/activate && black .
	@cd frontend && npm run format

type-check: ## Run type checking
	@cd backend && . venv/bin/activate && mypy .
	@cd frontend && npm run type-check

# ==================== DOCUMENTATION COMMANDS ====================

docs: ## Generate documentation
	@echo "Generating documentation..."
	@cd docs && make html

docs-serve: ## Serve documentation locally
	@cd docs && python -m http.server 8080 --directory _build/html

# ==================== UTILITY COMMANDS ====================

clean: ## Clean up generated files and caches
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name ".DS_Store" -delete
	@echo "Cleanup complete"

health: ## Check health of all services
	@echo "Checking service health..."
	@curl -s http://localhost:8001/health || echo "Identity service not running"
	@curl -s http://localhost:8000/health || echo "Backend service not running"
	@curl -s http://localhost:3000 || echo "Frontend not running"

status: ## Show status of all services
	@echo "Service Status:"
	@echo "==============="
	@ps aux | grep -E "(python main.py|python manage.py|npm run dev)" | grep -v grep || echo "No services running"

# ==================== DOCKER COMMANDS (FUTURE USE) ====================

docker-info: ## Information about Docker strategy
	@echo "=========================================="
	@echo "Docker/Containerization Status:"
	@echo "=========================================="
	@echo "Per ADR-010: Containerization is deferred"
	@echo "for future production deployment."
	@echo ""
	@echo "Current strategy: Local-first development"
	@echo "for maximum velocity with Claude Code."
	@echo "=========================================="

# ==================== QUICK START ====================

quickstart: ## Quick start for new developers
	@echo "Quick Start Guide"
	@echo "================="
	@echo "1. Run: make setup"
	@echo "2. Run: make migrate"
	@echo "3. Open 3 terminals and run:"
	@echo "   - Terminal 1: make run-identity"
	@echo "   - Terminal 2: make run-backend"
	@echo "   - Terminal 3: make run-frontend"
	@echo ""
	@echo "That's it! Services will be running locally."

.DEFAULT_GOAL := help