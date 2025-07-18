.PHONY: help install install-dev setup-gcp test test-unit test-integration format lint clean deploy-prod run-dev

help: ## Show this help message
	@echo "Husqvarna 701 RAG Support System"
	@echo "=================================="
	@echo ""
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt

setup-gcp: ## Setup Google Cloud resources
	@echo "Setting up Google Cloud resources..."
	python scripts/setup/create_bigquery_resources.py
	python scripts/setup/setup_gcp_apis.py

test: ## Run all tests
	pytest tests/ -v

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

test-coverage: ## Run tests with coverage
	pytest tests/ --cov=src/husqbot --cov-report=html --cov-report=term

format: ## Format code with black and isort
	black src/ tests/ scripts/
	isort src/ tests/ scripts/

lint: ## Run linting checks
	flake8 src/ tests/ scripts/
	mypy src/

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/

run-dev: ## Run development server
	uvicorn src.husqbot.api.fastapi_app:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run production server
	uvicorn src.husqbot.api.fastapi_app:app --host 0.0.0.0 --port 8000

deploy-prod: ## Deploy to production
	@echo "Deploying to production..."
	./scripts/deployment/deploy_cloud_run.sh

docker-build: ## Build Docker image
	docker build -t husqvarna-rag .

docker-run: ## Run Docker container
	docker run -p 8000:8000 husqvarna-rag

docker-compose-up: ## Start with Docker Compose
	docker-compose up -d

docker-compose-down: ## Stop Docker Compose
	docker-compose down

setup-pre-commit: ## Setup pre-commit hooks
	pre-commit install

update-deps: ## Update dependencies
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt 