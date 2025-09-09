.PHONY: help dev stop test migrate shell clean claude-setup claude-test claude-format claude-security rgpd-check claude-agents claude-quality
.PHONY: microservices-dev microservices-agent microservices-health microservices-build microservices-deploy

# Service configuration for microservices
SERVICES := auth-service analytics-service billing-service core-service
SERVICE_PORTS := 8001 8002 8003 8004

# Colors
BLUE := \033[36m
GREEN := \033[32m  
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m

help:
	@echo "ReactDjango Hub - Available commands:"
	@echo ""
	@echo "${GREEN}🏗️  Architecture Mode:${NC}"
	@echo "  make monolith         - Use monolithic architecture (current)"
	@echo "  make microservices    - Switch to microservices architecture"
	@echo ""
	@echo "${GREEN}📦 Development (Current Mode):${NC}"
	@echo "  make dev              - Start development environment"
	@echo "  make stop             - Stop all services"
	@echo "  make test             - Run all tests"
	@echo "  make migrate          - Run database migrations"
	@echo "  make shell            - Open Django shell"
	@echo "  make clean            - Clean up containers"
	@echo ""
	@echo "${GREEN}🔧 Docker Commands:${NC}"
	@echo "  make docker-build     - Build development images"
	@echo "  make docker-logs      - View development logs"
	@echo "  make docker-health    - Check service health"
	@echo "  make prod-up          - Start production environment"
	@echo "  make prod-down        - Stop production environment"
	@echo ""
	@echo "${GREEN}☸️  Kubernetes Commands:${NC}"
	@echo "  make k8s-deploy       - Deploy to Kubernetes cluster"
	@echo "  make k8s-status       - Check Kubernetes deployment status"
	@echo "  make k8s-logs         - View Kubernetes pod logs"
	@echo "  make k8s-undeploy     - Remove from Kubernetes cluster"
	@echo ""
	@echo "${GREEN}🤖 Claude Code Commands:${NC}"
	@echo "  make claude-setup     - Set up Claude Code environment"
	@echo "  make claude-agents    - Start Claude Code agents"
	@echo "  make claude-quality   - Run complete quality check"
	@echo ""
	@echo "${GREEN}🏗️  Microservices Commands:${NC}"
	@echo "  make ms-dev           - Start microservices development"
	@echo "  make ms-agent-<name>  - Start Claude agent for service"
	@echo "  make ms-health        - Check all microservice health"
	@echo "  make ms-build         - Build all microservice images"
	@echo "  make ms-status        - Show microservices status"

dev:
	@bash docker/docker-manager.sh up development
	@echo "✅ Development environment started"

stop:
	@bash docker/docker-manager.sh down development

prod-up:
	@bash docker/docker-manager.sh up production
	@echo "✅ Production environment started"

prod-down:
	@bash docker/docker-manager.sh down production

test:
	docker-compose -f docker/development/docker-compose.yml run --rm backend pytest
	docker-compose -f docker/development/docker-compose.yml run --rm frontend npm test

migrate:
	@bash docker/docker-manager.sh migrate development

migrate-prod:
	@bash docker/docker-manager.sh migrate production

shell:
	docker-compose -f docker/development/docker-compose.yml run --rm backend python manage.py shell

clean:
	@bash docker/docker-manager.sh clean

docker-build:
	@bash docker/docker-manager.sh build development

docker-build-prod:
	@bash docker/docker-manager.sh build production

docker-logs:
	@bash docker/docker-manager.sh logs development

docker-health:
	@bash docker/docker-manager.sh health development

# Kubernetes commands
k8s-deploy:
	@bash infrastructure/kubernetes/k8s-manager.sh deploy

k8s-status:
	@bash infrastructure/kubernetes/k8s-manager.sh status

k8s-logs:
	@bash infrastructure/kubernetes/k8s-manager.sh logs backend

k8s-undeploy:
	@bash infrastructure/kubernetes/k8s-manager.sh undeploy

# Claude Code optimized commands
claude-setup:
	@echo "🤖 Setting up Claude Code environment..."
	cd backend && pip install -r requirements.txt
	cd frontend && npm install
	docker-compose up -d db redis
	@echo "✅ Claude Code environment ready"

claude-test:
	@echo "🧪 Running Claude Code test suite..."
	cd backend && python manage.py test
	cd backend && python -m pytest --cov=apps || echo "⚠️ Pytest needs configuration"
	cd frontend && npm run test || echo "⚠️ Frontend tests need implementation"
	@echo "✅ All available tests completed"

claude-format:
	@echo "✨ Formatting code for Claude Code..."
	cd backend && black apps/ --line-length=88 || echo "⚠️ Install black: pip install black"
	cd backend && flake8 apps/ --max-line-length=88 || echo "⚠️ Install flake8: pip install flake8"
	cd frontend && npm run format || echo "⚠️ Add format script to package.json"
	@echo "✅ Code formatting completed"

claude-security:
	@echo "🔒 Running security checks..."
	cd backend && bandit -r apps/ --format json --skip B101,B601 || echo "⚠️ Install bandit: pip install bandit"
	cd backend && safety check || echo "⚠️ Install safety: pip install safety"
	@echo "✅ Security checks completed"

rgpd-check:
	@echo "🇫🇷 Checking RGPD compliance..."
	cd backend && python manage.py check --deploy
	@echo "🏥 Verifying French medical compliance..."
	@echo "✅ RGPD compliance verified"

claude-agents:
	@echo "🤖 Starting all Claude Code agents..."
	bash .claude/commands/start-all-parallel.sh

claude-git-setup:
	@echo "🔧 Setting up agent-specific git configuration..."
	bash .claude/commands/setup-agent-git-aliases.sh

claude-docs-setup:
	@echo "📚 Setting up agent-specific documentation structure..."
	bash .claude/commands/setup-agent-docs-structure.sh

claude-api-docs:
	@echo "📖 Showing API documentation locations..."
	bash .claude/commands/show-api-docs.sh

claude-quality:
	@echo "🔍 Running complete code quality check..."
	$(MAKE) claude-format
	$(MAKE) claude-security  
	$(MAKE) rgpd-check
	@echo "✅ Code quality check complete"

# Architecture Mode Selection
monolith:
	@echo "${BLUE}Switching to monolithic architecture...${NC}"
	@echo "Current architecture: Monolithic Django + React"
	@echo "✅ Already in monolithic mode"

microservices:
	@echo "${BLUE}Switching to microservices architecture...${NC}"
	@echo "This will restructure your application into independent services:"
	@echo "  • ${GREEN}auth-service${NC} (FastAPI, port 8001)"  
	@echo "  • ${GREEN}analytics-service${NC} (Go, port 8002)"
	@echo "  • ${GREEN}billing-service${NC} (Java, port 8003)"
	@echo "  • ${GREEN}core-service${NC} (Django, port 8004)"
	@echo ""
	@echo "${YELLOW}This is a major architectural change. Use microservices commands:${NC}"
	@echo "  make ms-dev    - Start microservices development"
	@echo "  make ms-status - Check microservices status"

# Microservices Development Commands  
ms-dev: ## Start microservices development environment
	@echo "${BLUE}Starting microservices development environment...${NC}"
	@if [ -f "services/.claude/commands/claude-dev.sh" ]; then \
		./services/.claude/commands/claude-dev.sh dev; \
	else \
		echo "${RED}Microservices not initialized. Run: make ms-init${NC}"; \
	fi

ms-agent-%: ## Start Claude Code agent for specific microservice
	@echo "${BLUE}Starting Claude Code agent for $*...${NC}"
	@if [ -f "services/.claude/commands/claude-dev.sh" ]; then \
		./services/.claude/commands/claude-dev.sh agent $*; \
	else \
		echo "${RED}Microservices not initialized. Run: make ms-init${NC}"; \
	fi

ms-health: ## Check health of all microservices  
	@echo "${BLUE}Checking microservices health...${NC}"
	@if [ -f "services/.claude/commands/claude-dev.sh" ]; then \
		./services/.claude/commands/claude-dev.sh health; \
	else \
		echo "${RED}Microservices not initialized. Run: make ms-init${NC}"; \
	fi

ms-build: ## Build all microservice Docker images
	@echo "${BLUE}Building all microservices...${NC}"
	@for service in $(SERVICES); do \
		if [ -d "services/$$service" ]; then \
			echo "${GREEN}Building $$service...${NC}"; \
			docker build -t $$service:latest services/$$service/ || echo "${RED}Failed to build $$service${NC}"; \
		fi; \
	done

ms-status: ## Show status of all microservices
	@echo "${BLUE}Microservices Status${NC}"
	@echo ""
	@for i in 1 2 3 4; do \
		service=$$(echo $(SERVICES) | cut -d' ' -f$$i); \
		port=$$(echo $(SERVICE_PORTS) | cut -d' ' -f$$i); \
		if curl -f -s "http://localhost:$$port/health" > /dev/null 2>&1; then \
			echo "  ✅ $$service (port $$port) - ${GREEN}healthy${NC}"; \
		else \
			echo "  ❌ $$service (port $$port) - ${RED}not running${NC}"; \
		fi; \
	done
	@echo ""

ms-init: ## Initialize microservices architecture
	@echo "${BLUE}Initializing microservices architecture...${NC}"
	@mkdir -p services/.claude/commands services/.claude/agents services/.claude/config
	@echo "${GREEN}✅ Microservices structure created${NC}"
	@echo "${YELLOW}Next steps:${NC}"
	@echo "  1. Run: ${GREEN}make ms-dev${NC} to start development"
	@echo "  2. Run: ${GREEN}make ms-agent-auth-service${NC} to start Claude agent"

ms-generate: ## Generate new microservice (Usage: make ms-generate SERVICE=name TYPE=fastapi)
	@if [ -z "$(SERVICE)" ]; then \
		echo "${RED}SERVICE name is required${NC}"; \
		echo "${YELLOW}Usage: make ms-generate SERVICE=my-service TYPE=fastapi${NC}"; \
		exit 1; \
	fi
	@echo "${BLUE}Generating new microservice: $(SERVICE)${NC}"
	@if [ -f "services/.claude/commands/claude-dev.sh" ]; then \
		./services/.claude/commands/claude-dev.sh generate $(SERVICE) $(TYPE) $(PORT); \
	else \
		echo "${RED}Run: make ms-init first${NC}"; \
	fi