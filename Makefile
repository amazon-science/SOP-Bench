.PHONY: help install install-dev test test-cov lint format clean build publish

help:
	@echo "SOP-Bench Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install package"
	@echo "  make install-dev      Install with dev dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run tests"
	@echo "  make test-cov         Run tests with coverage"
	@echo "  make test-fast        Run tests in parallel"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run all linters"
	@echo "  make format           Format code with black and isort"
	@echo "  make type-check       Run mypy type checking"
	@echo ""
	@echo "Build & Publish:"
	@echo "  make build            Build package"
	@echo "  make publish-test     Publish to TestPyPI"
	@echo "  make publish          Publish to PyPI"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove build artifacts"
	@echo "  make clean-all        Remove all generated files"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=amazon_sop_bench --cov-report=html --cov-report=term
	@echo "Coverage report: htmlcov/index.html"

test-fast:
	pytest tests/ -v -n auto

lint:
	@echo "Running black..."
	black --check src/ tests/
	@echo "Running isort..."
	isort --check-only src/ tests/
	@echo "Running ruff..."
	ruff check src/ tests/
	@echo "All linters passed!"

format:
	black src/ tests/
	isort src/ tests/
	@echo "Code formatted!"

type-check:
	mypy src/ --ignore-missing-imports

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

clean-all: clean
	rm -rf results/
	rm -rf *_traces/
	rm -f *.log

build: clean
	python -m build

publish-test: build
	twine check dist/*
	twine upload --repository testpypi dist/*

publish: build
	twine check dist/*
	twine upload dist/*

# Development shortcuts
dev: install-dev
	@echo "Development environment ready!"

check: lint test
	@echo "All checks passed!"

ci: lint test-cov
	@echo "CI checks complete!"
