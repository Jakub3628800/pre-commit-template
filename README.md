# prec-templ

Automatically detects technologies in your repository and generates an appropriate `.pre-commit-config.yaml` file with relevant hooks.

`prec-templ` is opinionated to my preferred pre-commit hook stack.
It is written in Rust and distributed as a Python package so it fits Python workflow tooling conventions (`ruff`, `pre-commit`, `uv`).

Repository: https://github.com/Jakub3628800/prec-templ
Latest release: https://github.com/Jakub3628800/prec-templ/releases/latest

## Quick Start

```bash
uv tool run --isolated --from "git+https://github.com/Jakub3628800/prec-templ@master" prec-templ --generate-only
```

## Usage

```bash
prec-templ
prec-templ --generate-only
prec-templ -i
```

`prec-templ` will:
1. Scan your repository for technologies (Python, JavaScript, Go, Docker, etc.)
2. Generate a `.pre-commit-config.yaml` file with appropriate hooks
3. Install and run pre-commit hooks automatically

## License

MIT License
