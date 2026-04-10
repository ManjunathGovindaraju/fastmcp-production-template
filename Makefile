.PHONY: install dev test lint format clean

# Standardized commands for fastmcp-production-template
# Uses `uv` for fast Python package management

install:
	uv sync --all-extras

dev:
	uv run python -m src.server.main

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check src/ tests/
	uv run mypy src/ tests/ --ignore-missing-imports
	uv run bandit -r src/ -lll

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
