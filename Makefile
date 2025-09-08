.PHONY: help dev stop test migrate shell clean
help:
@echo "ReactDjango Hub - Available commands:"
@echo "  make dev          - Start development environment"
@echo "  make stop         - Stop all services"
@echo "  make test         - Run all tests"
@echo "  make migrate      - Run database migrations"
@echo "  make shell        - Open Django shell"
@echo "  make clean        - Clean up containers"
dev:
docker-compose up -d
@echo "✅ Development started at http://localhost:5173"
stop:
docker-compose down
test:
docker-compose run --rm backend pytest
docker-compose run --rm frontend npm test
migrate:
docker-compose run --rm backend python manage.py migrate
shell:
docker-compose run --rm backend python manage.py shell
clean:
docker-compose down -v
