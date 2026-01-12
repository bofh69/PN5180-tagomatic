# PN5180-tagomatic

<!--
SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->

USB based RFID reader with Python interface

[![Python CI](https://github.com/bofh69/PN5180-tagomatic/workflows/Python%20CI/badge.svg)](https://github.com/bofh69/PN5180-tagomatic/actions)
[![REUSE status](https://api.reuse.software/badge/git@github.com/bofh69/PN5180-tagomatic)](https://api.reuse.software/info/git@github.com/bofh69/PN5180-tagomatic)
[![PyPI version](https://badge.fury.io/py/pn5180-tagomatic.svg)](https://badge.fury.io/py/pn5180-tagomatic)

## Overview

PN5180-tagomatic is a USB-based RFID reader that provides
a Python interface for reading NFC/RFID tags using the PN5180 NFC
Frontend module and a Raspberry Pi Pico (Zero).

## Features

- Python library for easy integration.
- Uses USB serial communication to the reader.
- Cross-platform support (Linux, Windows, macOS).
- Finds and selects single ISO/IEC 14443 cards.
- Uses NFC FORUM commands to read/write 14443-A cards' memories.
- Can authenticate against Mifare classic cards to read their memories.
- Finds ISO/IEC 15693 cards, uses 15693-3 commands to read/write their memories.

Multiple cards in the RFID field is currently not really supported,
the hardware and arduino sketch supports all commands for it.


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
    versions = reader.ll.read_eeprom(0x10, 6)
    with reader.start_session(0x00, 0x80) as session:
        card = session.connect_one_iso14443a()
        print(f"Reading from card {card.uid.hex(':')}")
        if len(card.uid) == 4:
            memory = card.read_mifare_memory()
        else:
            memory = card.read_memory()
```

### Example Program

A few simple example programs are in the `examples/` directory.

## Development

### Setting up development environment

```bash
# Clone the repository
git clone https://github.com/bofh69/PN5180-tagomatic.git
cd PN5180-tagomatic

# Install development dependencies
pip install -e .[dev]
# or:
make install-dev
```

### Running tests

`pytest` or `make test`

### Code quality checks

```bash
# Linting
make check

# Formatting
make format

# Type checking
make type-check
```

### Documentation

To build and view the documentation locally:

```bash
# Install documentation dependencies
pip install -e .[docs]

# Serve documentation locally (with live reload)
make docs-serve

# Build static documentation
make docs-build
```

The documentation will be available at `http://127.0.0.1:8000` when using `make docs-serve`.

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

SimpleRPC by Jeroen F.J. Laros, Chris Flesher et al is also used.
