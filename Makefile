.PHONY: run test build clean install dev release release-test lint format

VERSION ?= 0.2.0
TAG ?= v$(VERSION)
TARGET ?= $(shell git rev-parse --verify HEAD)

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
	gh release create "$(TAG)" --target "$(TARGET)" --title "$(TAG)" --generate-notes

release-test:
	gh release create "$(TAG)" --target "$(TARGET)" --prerelease --title "$(TAG)" --generate-notes
