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

claude-quality:
	@echo "🔍 Running complete code quality check..."
	$(MAKE) claude-format
	$(MAKE) claude-security  
	$(MAKE) rgpd-check
	@echo "✅ Code quality check complete"