# ReactDjango Hub - Local Development Makefile
# Provides easy commands for managing all microservices

.PHONY: help start stop restart build status health logs services test clean shell

# Default target
help: ## Show this help message
	@echo "ReactDjango Hub - Local Development Commands"
	@echo "============================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

start: ## Start all microservices
	@./scripts/dev-stack.sh start

stop: ## Stop all microservices  
	@./scripts/dev-stack.sh stop

restart: ## Restart all microservices
	@./scripts/dev-stack.sh restart

build: ## Build all service images
	@./scripts/dev-stack.sh build

status: ## Show service status
	@./scripts/dev-stack.sh status

health: ## Check service health
	@./scripts/dev-stack.sh health

logs: ## Show logs for all services
	@./scripts/dev-stack.sh logs

logs-service: ## Show logs for specific service (usage: make logs-service SERVICE=backend)
	@./scripts/dev-stack.sh logs $(SERVICE)

services: ## Show available services and URLs
	@./scripts/dev-stack.sh services

test: ## Run tests in all services
	@./scripts/dev-stack.sh test

clean: ## Remove all containers and volumes
	@./scripts/dev-stack.sh clean

# Service-specific shell access
shell-identity: ## Open shell in identity service
	@./scripts/dev-stack.sh shell identity-service

shell-communication: ## Open shell in communication service
	@./scripts/dev-stack.sh shell communication-service

shell-content: ## Open shell in content service
	@./scripts/dev-stack.sh shell content-service

shell-workflow: ## Open shell in workflow intelligence service
	@./scripts/dev-stack.sh shell workflow-intelligence-service

shell-backend: ## Open shell in backend service
	@./scripts/dev-stack.sh shell backend

shell-frontend: ## Open shell in frontend service
	@./scripts/dev-stack.sh shell frontend

# Quick development commands
dev: ## Start development stack and show services
	@make start
	@echo ""
	@make services

quick-test: ## Quick health check and basic tests
	@make health
	@echo ""
	@./scripts/dev-stack.sh test

# Database management
db-migrate: ## Run Django migrations
	@docker-compose -f docker-compose.local.yml exec backend python manage.py makemigrations
	@docker-compose -f docker-compose.local.yml exec backend python manage.py migrate

db-shell: ## Open Django database shell
	@docker-compose -f docker-compose.local.yml exec backend python manage.py dbshell

# Development utilities
format: ## Format code in all services
	@echo "Formatting Python code..."
	@docker-compose -f docker-compose.local.yml exec identity-service black . || true
	@docker-compose -f docker-compose.local.yml exec communication-service black . || true
	@docker-compose -f docker-compose.local.yml exec content-service black . || true
	@docker-compose -f docker-compose.local.yml exec workflow-intelligence-service black . || true
	@docker-compose -f docker-compose.local.yml exec backend black . || true
	@echo "Formatting JavaScript/TypeScript code..."
	@docker-compose -f docker-compose.local.yml exec frontend npm run format || true

lint: ## Run linting in all services
	@echo "Linting Python code..."
	@docker-compose -f docker-compose.local.yml exec identity-service flake8 . || true
	@docker-compose -f docker-compose.local.yml exec communication-service flake8 . || true
	@docker-compose -f docker-compose.local.yml exec content-service flake8 . || true
	@docker-compose -f docker-compose.local.yml exec workflow-intelligence-service flake8 . || true
	@docker-compose -f docker-compose.local.yml exec backend flake8 . || true
	@echo "Linting JavaScript/TypeScript code..."
	@docker-compose -f docker-compose.local.yml exec frontend npm run lint || true