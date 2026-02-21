.PHONY: run test build clean install dev release release-test lint format

# Development
run:
	cargo run

dev:
	maturin develop

# Testing
test:
	cargo test

lint:
	cargo clippy -- -D warnings
	cargo fmt --check

format:
	cargo fmt

# Building
build:
	cargo build --release

build-wheel:
	maturin build --release

# Installation
install:
	maturin build --release
	uv tool install --force dist/*.whl

# Cleaning
clean:
	cargo clean
	rm -rf target/ dist/ *.egg-info .pytest_cache/ .mypy_cache/ .ruff_cache/

# Release
release:
	@if [ -z "$(TAG)" ]; then \
		echo "Usage: make release TAG=vX.Y.Z"; \
		exit 1; \
	fi
	gh release create "$(TAG)" --target master --title "$(TAG)" --generate-notes

release-test:
	@if [ -z "$(TAG)" ]; then \
		echo "Usage: make release-test TAG=vX.Y.Z-test.N [TARGET=branch-or-sha]"; \
		exit 1; \
	fi
	gh release create "$(TAG)" --target "$(or $(TARGET),master)" --prerelease --title "$(TAG)" --generate-notes
