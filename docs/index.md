<!--
SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->

# PN5180-tagomatic Documentation

Welcome to the documentation for **PN5180-tagomatic**, a USB-based RFID reader with a Python interface.

## Overview

PN5180-tagomatic is a USB-based RFID reader that provides a Python interface for reading NFC/RFID tags using the PN5180 NFC Frontend module and a Raspberry Pi Pico (Zero).

## Features

- **Python library** for easy integration
- **USB serial communication** to the reader
- **Cross-platform support** (Linux, Windows, macOS)
- **ISO/IEC 14443 support**: Find and select single ISO/IEC 14443 cards
- **NFC FORUM commands**: Read/write 14443-A cards' memories
- **Mifare Classic support**: Authenticate against Mifare classic cards to read their memories
- **ISO/IEC 15693 support**: Find cards and use 15693-3 commands to read/write their memories

!!! note
    Multiple cards in the RFID field is currently not fully supported, although the hardware and Arduino sketch support all commands for it.

## Quick Start

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

## Documentation Sections

- **[Getting Started](getting-started/installation.md)**: Installation and basic usage
- **[API Reference](api/index.md)**: Detailed API documentation

## License

This project is licensed under the GNU General Public License v3.0 or later (GPL-3.0-or-later).

## Contributing

Contributions are welcome! Please ensure that:

1. All code passes linting and type checking
2. Tests are added for new functionality
3. All files include proper REUSE-compliant license headers
4. Code follows the project's style guidelines

## Acknowledgments

This project uses:
- FastLED by Daniel Garcia et al.
- SimpleRPC by Jeroen F.J. Laros, Chris Flesher et al.
