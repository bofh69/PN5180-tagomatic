# PN5180-tagomatic

<!--
SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->

**This is a work in progress. Some things described here doesn't work yet,
and bug reports are not welcome at this time.**

USB based RFID reader with Python interface

[![Python CI](https://github.com/bofh69/PN5180-tagomatic/workflows/Python%20CI/badge.svg)](https://github.com/bofh69/PN5180-tagomatic/actions)
[![REUSE status](https://api.reuse.software/badge/git@github.com/bofh69/PN5180-tagomatic)](https://api.reuse.software/info/git@github.com/bofh69/PN5180-tagomatic)
[![PyPI version](https://badge.fury.io/py/pn5180-tagomatic.svg)](https://badge.fury.io/py/pn5180-tagomatic)

## Overview

PN5180-tagomatic is a USB-based RFID reader that provides
a Python interface for reading NFC/RFID tags using the PN5180 NFC
Frontend module and a Raspberry Pi Pico (Zero).

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

See [sketch/README.md](sketch/README.md) for instructions on building and uploading the Raspberry Pi Pico firmware.

## Usage

```python
from pn5180_tagomatic import PN5180


# Create reader instance and use it
with PN5180("/dev/ttyACM0") as reader:
    reader.reset()
    versions = reader.read_eeprom(0x10, 6)
```

### Example Program

An example program is provided in the `examples/` directory:

```bash
# Run the basic example
python examples/basic_example.py /dev/ttyACM0

# On Windows
python examples/basic_example.py COM3
```

The example demonstrates:
- Opening a serial connection to the device
- Creating a PN5180 reader instance
- Calling the reset function via SimpleRPC
- Proper resource cleanup using context managers

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
make check

# Formatting
make format

# Type checking
make type-check
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

This project uses FastLED by Daniel Garcia et al.
It also uses SimpleRPC by Jeroen F.J. Laros, Chris Flesher et al.
