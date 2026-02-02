# pre-commit-template

Automatically detects technologies in your repository and generates an appropriate `.pre-commit-config.yaml` file with relevant hooks.

**Written in Rust** for blazing-fast performance, distributed as a Python package.

## Quick Start

### Using uv (Recommended)

```bash
# Install from GitHub
uv tool install git+https://github.com/Jakub3628800/pre-commit-template

# Or from PyPI (after release)
uv tool install pre-commit-template
```

### Using pip

```bash
pip install pre-commit-template
```

### Running

```bash
# Auto-detect and generate config
pre-commit-template

# Interactive mode with customization prompts
pre-commit-template -i
```

The generator will:
1. Scan your repository for technologies (Python, JavaScript, Go, Docker, etc.)
2. Generate a `.pre-commit-config.yaml` file with appropriate hooks
3. Install and run pre-commit hooks automatically

## After Generation

```bash
# Install pre-commit hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## Development

### Prerequisites

- Rust (install via [rustup](https://rustup.rs/))
- Python 3.8+ (for maturin)

### Build Commands

```bash
cargo build         # Build debug
cargo test          # Run tests
cargo run           # Run locally
maturin build       # Build Python wheel
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
