<!--
SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Documentation

This directory contains the Sphinx documentation for PN5180-tagomatic.

## Building Documentation

To build the HTML documentation:

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build the documentation
make docs
```

The generated documentation will be available in `docs/_build/html/index.html`.

## Structure

- `conf.py` - Sphinx configuration file
- `index.rst` - Main documentation index
- `api/` - API reference documentation (auto-generated from docstrings)
- `_build/` - Generated documentation (not committed to version control)

## Documentation Style

The project uses:

- **Sphinx** for documentation generation
- **sphinx-autodoc** for extracting docstrings
- **sphinx_rtd_theme** for the Read the Docs theme
- **Google/NumPy style docstrings** in the source code
