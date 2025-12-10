# PN5180-tagomatic

<!--
SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->

USB based RFID reader with Python interface

[![Python CI](https://github.com/bofh69/PN5180-tagomatic/workflows/Python%20CI/badge.svg)](https://github.com/bofh69/PN5180-tagomatic/actions)
[![REUSE status](https://api.reuse.software/badge/github.com/bofh69/PN5180-tagomatic)](https://api.reuse.software/info/github.com/bofh69/PN5180-tagomatic)
[![PyPI version](https://badge.fury.io/py/pn5180-tagomatic.svg)](https://badge.fury.io/py/pn5180-tagomatic)

## Overview

PN5180-tagomatic is a USB-based RFID reader system that provides a Python interface for reading NFC/RFID tags using the PN5180 NFC Frontend module and a Raspberry Pi Pico.

## Features

- Python library for easy integration
- Raspberry Pi Pico firmware for PN5180 NFC module
- USB serial communication
- Cross-platform support (Linux, Windows, macOS)

## Installation

### Python Package

Install from PyPI:

```bash
pip install pn5180-tagomatic
```

Install from source:

```bash
git clone https://github.com/bofh69/PN5180-tagomatic.git
cd PN5180-tagomatic
pip install -e .
```

### Firmware

See [firmware/README.md](firmware/README.md) for instructions on building and uploading the Raspberry Pi Pico firmware.

## Usage

```python
import pn5180_tagomatic

# Usage examples to be added
```

## Development

### Setting up development environment

```bash
# Clone the repository
git clone https://github.com/bofh69/PN5180-tagomatic.git
cd PN5180-tagomatic

# Install development dependencies
pip install -e .[dev]
```

### Running tests

```bash
pytest
```

### Code quality checks

```bash
# Linting
ruff check src/ tests/

# Formatting
black src/ tests/
ruff format src/ tests/

# Type checking
mypy src/
```

## License

This project is licensed under the GNU General Public License v3.0 or later (GPL-3.0-or-later).

See [LICENSE](LICENSE) for the full license text.

## Contributing

Contributions are welcome! Please ensure that:

1. All code passes linting and type checking
2. Tests are added for new functionality
3. All files include proper REUSE-compliant license headers
4. Code follows the project's style guidelines

## Acknowledgments

This project uses the PN5180 NFC Frontend from NXP Semiconductors.
