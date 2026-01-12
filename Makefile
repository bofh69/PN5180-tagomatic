# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
BLACK := $(VENV)/bin/black
MYPY := $(VENV)/bin/mypy
MKDOCS := $(VENV)/bin/mkdocs

.PHONY: help
help:
	@echo "PN5180-tagomatic development targets:"
	@echo "  make venv         - Create virtual environment"
	@echo "  make install      - Install package and dependencies"
	@echo "  make install-dev  - Install package with dev dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting checks"
	@echo "  make format       - Format code with black"
	@echo "  make type-check   - Run type checking with mypy"
	@echo "  make docs-serve   - Serve documentation locally"
	@echo "  make docs-build   - Build documentation"
	@echo "  make clean        - Remove virtual environment and build artifacts"

$(VENV)/bin/activate:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

.PHONY: venv
venv: $(VENV)/bin/activate

# Install package with regular dependencies
$(VENV)/.timestamp: $(VENV)/bin/activate pyproject.toml
	$(PIP) install -e .
	touch $@

.PHONY:  install
install: $(VENV)/.timestamp

# Install package with development dependencies
$(VENV)/.timestamp-dev: $(VENV)/bin/activate pyproject.toml
	$(PIP) install -e ".[dev]"
	touch $@

$(VENV)/.timestamp-docs: $(VENV)/bin/activate pyproject.toml
	$(PIP) install -e ".[docs]"
	touch $@

.PHONY: install-dev
install-dev: $(VENV)/.timestamp-dev

.PHONY: test
test: install-dev
	$(PYTEST)

.PHONY: lint
lint: install-dev
	$(RUFF) check src/ tests/

.PHONY: format
format: install-dev
	$(BLACK) -l79 src/ tests/
	clang-format-15 -i sketch/*/*.ino

.PHONY: type-check
type-check: install-dev
	$(MYPY) src/

.PHONY: docs-serve
docs-serve: $(VENV)/.timestamp-docs
	$(MKDOCS) serve

.PHONY: docs-build
docs-build: $(VENV)/.timestamp-docs
	$(MKDOCS) build

.PHONY: clean
clean:
	rm -rf $(VENV)
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf site/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
