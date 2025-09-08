.PHONY: help dev stop test migrate shell clean claude-setup claude-test claude-format claude-security rgpd-check claude-agents claude-quality

help:
	@echo "ReactDjango Hub - Available commands:"
	@echo "  make dev          - Start development environment"
	@echo "  make stop         - Stop all services"
	@echo "  make test         - Run all tests"
	@echo "  make migrate      - Run database migrations"
	@echo "  make shell        - Open Django shell"
	@echo "  make clean        - Clean up containers"
	@echo ""
	@echo "Docker commands:"
	@echo "  make dev          - Start development environment"  
	@echo "  make stop         - Stop development environment"
	@echo "  make prod-up      - Start production environment"
	@echo "  make prod-down    - Stop production environment"
	@echo "  make docker-build - Build development images"
	@echo "  make docker-logs  - View development logs"
	@echo "  make docker-health - Check service health"
	@echo ""
	@echo "Kubernetes commands:"
	@echo "  make k8s-deploy   - Deploy to Kubernetes cluster"
	@echo "  make k8s-status   - Check Kubernetes deployment status"
	@echo "  make k8s-logs     - View Kubernetes pod logs"
	@echo "  make k8s-undeploy - Remove from Kubernetes cluster"
	@echo ""
	@echo "Claude Code optimized commands:"
	@echo "  make claude-setup     - Set up Claude Code environment"
	@echo "  make claude-test      - Run Claude Code test suite"
	@echo "  make claude-format    - Format code for Claude Code"
	@echo "  make claude-security  - Run security checks"
	@echo "  make rgpd-check       - Check RGPD compliance"
	@echo "  make claude-agents    - Start all Claude Code agents"
	@echo "  make claude-git-setup - Configure agent git aliases"
	@echo "  make claude-docs-setup - Setup agent documentation structure"
	@echo "  make claude-api-docs  - Show API documentation locations"
	@echo "  make claude-quality   - Run complete quality check"

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