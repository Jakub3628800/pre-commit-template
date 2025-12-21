This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Setup and Installation
```bash
make install          # Install package, dependencies, and pre-commit hooks
source .venv/bin/activate  # Activate virtual environment
```

### Testing
```bash
make test            # Run pytest tests and pre-commit hooks
make coverage        # Generate coverage report (outputs to htmlcov/index.html)
```

### Linting and Formatting
```bash
make run-precommit   # Run all pre-commit hooks on all files
uv run ruff check    # Run ruff linter
uv run ruff format   # Run ruff formatter
```

### Other Commands
```bash
make clean          # Clean build artifacts and virtual environment
make build          # Build package
```

## Architecture Overview

This is a Python CLI tool that auto-generates `.pre-commit-config.yaml` files by detecting technologies in repositories:

- **Discovery** (`pre_commit_template/discover.py`): Scans repository to detect technologies via file extensions and content patterns
- **Config** (`pre_commit_template/config.py`): Pydantic configuration model for pre-commit options
- **Hook Templates** (`pre_commit_template/hook_templates/`): Jinja2 templates for generating YAML configs
- **CLI Interface** (`pre_commit_template/main.py`): Main entry point using argparse and rich for output formatting

## Key Implementation Details

- Uses uv for package management and virtual environments
- Supports Python 3.11+ with setuptools build system
- Technologies detected: Python, JavaScript, TypeScript, Go, Docker, GitHub Actions, YAML, JSON, TOML, XML
- Hook templates use Jinja2 for flexible config generation
- Rich console output with progress indication and colored text

## Entry Point

The CLI command `pre-commit-template` is registered in pyproject.toml, pointing to `pre_commit_template.main:main`.
