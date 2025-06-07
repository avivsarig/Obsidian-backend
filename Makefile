.PHONY: help install install-dev run test check docker-dev docker-prod infra-plan infra-apply infra-destroy clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies + pre-commit"
	@echo "  run          - Run FastAPI application locally"
	@echo "  test         - Run pytest with coverage"
	@echo "  check        - Run all pre-commit checks"
	@echo "  docker-dev   - Run development environment with Docker Compose"
	@echo "  docker-prod  - Run production environment with Docker Compose"
	@echo "  infra-plan   - Plan Terraform infrastructure changes"
	@echo "  infra-apply  - Apply Terraform infrastructure"
	@echo "  infra-destroy- Destroy Terraform infrastructure"
	@echo "  clean        - Clean up temporary files and caches"

# Installation targets
install:
	pip install -r requirements.txt

install-dev: install
	pip install -r requirements-dev.txt
	pre-commit install

# Development targets
run:
	python -m app.src.main

test:
	pytest app/tests/ --cov=app/src --cov-report=term-missing

check:
	pre-commit run --all-files

# Docker targets
docker-dev:
	docker-compose up --build

docker-prod:
	docker-compose -f docker-compose.prod.yml up --build -d

# Infrastructure targets
infra-plan:
	cd infrastructure/terraform/environments/prod && tofu plan && cd -

infra-apply:
	cd infrastructure/terraform/environments/prod && tofu apply && cd -

infra-destroy:
	cd infrastructure/terraform/environments/prod && tofu destroy && cd -

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
