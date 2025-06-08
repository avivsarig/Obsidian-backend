.PHONY: help install install-dev run test check docker-dev docker-prod infra-plan infra-apply infra-destroy infra-validate clean setup-local-vault infra-dev-plan infra-dev-apply infra-dev-destroy docker-logs docker-clean test-deploy-script

help:
	@echo "Available targets:"
	@echo ""
	@echo "Development:"
	@echo "  install         - Install production dependencies"
	@echo "  install-dev     - Install development dependencies + pre-commit"
	@echo "  run             - Run FastAPI application locally"
	@echo "  test            - Run pytest with coverage"
	@echo "  check           - Run all pre-commit checks"
	@echo "  setup-local-vault - Create a test vault for local development"
	@echo "  test-deploy-script - Test the deployment script locally"
	@echo ""
	@echo "Docker:"
	@echo "  docker-dev      - Run development environment with Docker Compose"
	@echo "  docker-prod     - Run production environment with Docker Compose"
	@echo "  docker-logs     - Show docker logs for debugging"
	@echo "  docker-clean    - Clean up docker containers and images"
	@echo ""
	@echo "Infrastructure:"
	@echo "  infra-validate  - Validate Terraform configuration"
	@echo "  infra-plan      - Plan production infrastructure changes"
	@echo "  infra-apply     - Apply production infrastructure"
	@echo "  infra-destroy   - Destroy production infrastructure"
	@echo "  infra-dev-plan  - Plan development infrastructure changes"
	@echo "  infra-dev-apply - Apply development infrastructure"
	@echo "  infra-dev-destroy - Destroy development infrastructure"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean           - Clean up temporary files and caches"

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
	@echo "Starting development environment..."
	docker-compose up --build

docker-prod:
	@echo "Starting production environment..."
	docker-compose -f docker-compose.prod.yml up --build -d

docker-logs:
	docker-compose logs -f

docker-clean:
	@echo "Cleaning up Docker resources..."
	docker-compose down --remove-orphans || true
	docker-compose -f docker-compose.prod.yml down --remove-orphans || true
	docker system prune -f

# Infrastructure validation
infra-validate:
	@echo "Validating Terraform configuration..."
	cd infrastructure/terraform/modules/networking && tofu validate && cd -
	cd infrastructure/terraform/modules/compute && tofu validate && cd -
	cd infrastructure/terraform/environments/prod && tofu validate && cd -
	@if [ -d "infrastructure/terraform/environments/dev" ]; then \
		cd infrastructure/terraform/environments/dev && tofu validate && cd -; \
	fi
	@echo "All infrastructure files validated successfully!"

# Production infrastructure targets
infra-plan:
	@echo "Planning production infrastructure..."
	cd infrastructure/terraform/environments/prod && tofu plan && cd -

infra-apply:
	@echo "Applying production infrastructure..."
	cd infrastructure/terraform/environments/prod && tofu apply && cd -

infra-destroy:
	@echo "Destroying production infrastructure..."
	cd infrastructure/terraform/environments/prod && tofu destroy && cd -

# Development infrastructure targets
infra-dev-plan:
	@echo "Planning development infrastructure..."
	@if [ -d "infrastructure/terraform/environments/dev" ]; then \
		cd infrastructure/terraform/environments/dev && tofu plan && cd -; \
	else \
		echo "Development environment not configured yet"; \
	fi

infra-dev-apply:
	@echo "Applying development infrastructure..."
	@if [ -d "infrastructure/terraform/environments/dev" ]; then \
		cd infrastructure/terraform/environments/dev && tofu apply && cd -; \
	else \
		echo "Development environment not configured yet"; \
	fi

infra-dev-destroy:
	@echo "Destroying development infrastructure..."
	@if [ -d "infrastructure/terraform/environments/dev" ]; then \
		cd infrastructure/terraform/environments/dev && tofu destroy && cd -; \
	else \
		echo "Development environment not configured yet"; \
	fi

# Cleanup
clean:
	@echo "Cleaning up temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.tfplan" -delete 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true
