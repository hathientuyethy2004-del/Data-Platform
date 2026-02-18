# Product-based Makefile for Mobile User Analytics

.PHONY: help install dev-up dev-down run-local test lint format clean deploy-staging deploy-prod

help:
	@echo "Mobile User Analytics - Available targets:"
	@echo "  install         - Install dependencies"
	@echo "  dev-up          - Start local development environment"
	@echo "  dev-down        - Stop local development environment"
	@echo "  run-local       - Run product locally"
	@echo "  test            - Run all tests"
	@echo "  lint            - Run code linting"
	@echo "  format          - Format code"
	@echo "  clean           - Clean build artifacts"
	@echo "  deploy-staging  - Deploy to staging"
	@echo "  deploy-prod     - Deploy to production"

install:
	pip install -r requirements.txt

dev-up:
	@echo "Starting Mobile User Analytics development environment..."
	docker-compose -f ../../docker-compose.yml up -d

dev-down:
	@echo "Stopping development environment..."
	docker-compose -f ../../docker-compose.yml down

run-local:
	python -m src.ingestion.consumer

test:
	pytest src/tests/ -v --cov=src

lint:
	flake8 src/
	mypy src/

format:
	black src/
	isort src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache

deploy-staging:
	@echo "Deploying Mobile User Analytics to staging..."
	# Add deployment logic here

deploy-prod:
	@echo "Deploying Mobile User Analytics to production..."
	# Add deployment logic here
