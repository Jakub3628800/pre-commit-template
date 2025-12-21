.PHONY: run test install build clean run-precommit coverage test-all update-templates generate-config update-hooks

run:
	uv run python -m pre_commit_template

update-templates:  ## Update hook versions in templates
	uv run python scripts/update_hook_versions.py

generate-config:  ## Generate .pre-commit-config.yaml from templates
	uv run python -m pre_commit_template

update-hooks:  ## Update templates and regenerate config
	@$(MAKE) update-templates
	@$(MAKE) generate-config

test:
	uv run --extra dev pytest tests/ -v
	uv run --extra dev pre-commit run --all-files

install:
	uv run --extra dev pre-commit install
	@echo "Pre-commit hooks installed"

run-precommit:
	uv run --extra dev pre-commit run --all-files

coverage:
	uv run --extra dev pytest tests/ --cov=pre_commit_template --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

test-all:
	uv run --extra dev pytest tests/ -v
	uv run --extra dev pre-commit run --all-files
	@if command -v act >/dev/null 2>&1; then act; else echo "act not available, skipping GitHub Actions tests"; fi

build:
	uv build

clean:
	rm -rf build/ dist/ *.egg-info .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/ .venv/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.py[co]" -delete 2>/dev/null || true
