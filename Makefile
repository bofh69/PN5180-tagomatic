# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

.PHONY: help install install-dev clean test lint format typecheck check arduino-format arduino-build all

# Default target
help:
	@echo "PN5180-tagomatic Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  help           - Show this help message"
	@echo ""
	@echo "Python Development:"
	@echo "  install        - Install package in editable mode"
	@echo "  install-dev    - Install package with development dependencies"
	@echo "  lint           - Run Python linting with ruff"
	@echo "  format         - Format Python code with black and ruff"
	@echo "  format-check   - Check Python code formatting without modifying files"
	@echo "  typecheck      - Run type checking with mypy"
	@echo "  test           - Run Python tests with pytest"
	@echo "  check          - Run all Python quality checks (lint, format-check, typecheck)"
	@echo ""
	@echo "Arduino Development:"
	@echo "  arduino-format       - Format Arduino/C++ code with clang-format"
	@echo "  arduino-format-check - Check Arduino/C++ code formatting"
	@echo "  arduino-build        - Build Arduino sketch for Raspberry Pi Pico"
	@echo ""
	@echo "Combined:"
	@echo "  all            - Run all checks and tests"
	@echo "  clean          - Remove build artifacts and cache files"

# Python package installation
install:
	pip install -e .

install-dev:
	pip install -e .[dev]

# Python linting
lint:
	ruff check src/ tests/ examples/

lint-fix:
	ruff check --fix src/ tests/ examples/

# Python formatting
format:
	black src/ tests/ examples/
	ruff format src/ tests/ examples/

format-check:
	black --check src/ tests/ examples/
	ruff format --check src/ tests/ examples/

# Python type checking
typecheck:
	mypy src/

# Python testing
test:
	pytest -v

test-cov:
	pytest -v --cov=pn5180_tagomatic --cov-report=term-missing --cov-report=html

# Combined Python quality checks
check: lint format-check typecheck
	@echo "All Python quality checks passed!"

# Arduino/C++ formatting
arduino-format:
	find sketch -name "*.ino" -o -name "*.cpp" -o -name "*.h" | xargs clang-format -i

arduino-format-check:
	find sketch -name "*.ino" -o -name "*.cpp" -o -name "*.h" | xargs clang-format --dry-run --Werror

# Arduino build (requires Arduino CLI to be installed)
arduino-build:
	@command -v arduino-cli >/dev/null 2>&1 || { echo >&2 "arduino-cli is required but not installed. Please install it first."; exit 1; }
	arduino-cli config init || true
	arduino-cli core update-index
	arduino-cli core install arduino:mbed_rp2040 || true
	arduino-cli lib install simpleRPC || true
	arduino-cli lib install FastLED || true
	arduino-cli compile --fqbn arduino:mbed_rp2040:pico sketch/pn5180_reader

# Clean build artifacts and cache
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf src/*.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# Run all checks and tests
all: check test arduino-format-check
	@echo "All checks and tests passed!"
