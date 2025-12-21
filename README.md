# pre-commit-template

Automatically detects technologies in your repository and generates an appropriate `.pre-commit-config.yaml` file with relevant hooks.

## Quick Start

### Using uv (Recommended)

```bash
uvx --from git+https://github.com/Jakub3628800/pre-commit-template pre-commit-template
```

### Using the tool directly

```bash
git clone https://github.com/Jakub3628800/pre-commit-template
cd pre-commit-template
make install
make run
```

The generator will:
1. Scan your repository for technologies (Python, JavaScript, Go, Docker, etc.)
2. Generate a `.pre-commit-config.yaml` file with appropriate hooks
3. Guide you through customization options (with `-i` flag)

## After Generation

```bash
# Install pre-commit hooks
uvx pre-commit install

# Run on all files
uvx pre-commit run --all-files
```

## Development

```bash
make install    # Install dependencies
make run        # Run the tool
make test       # Run tests
make build      # Build package
make clean      # Clean up
```

## Supported Technologies

- **Python**: Ruff (linting/formatting) + Pyrefly (type checking)
- **JavaScript/TypeScript**: Prettier + ESLint
- **Go**: golangci-lint + formatting
- **Docker**: hadolint for Dockerfile linting
- **GitHub Actions**: actionlint for workflow validation
- **File Types**: YAML, JSON, TOML, XML syntax checking

## License

MIT License
