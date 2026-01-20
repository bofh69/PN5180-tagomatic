<!--
SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->

# PN5180 Tagomatic
A USB connected RFID Reader/Writer with a python interface.

---

A PN5180 card is connected to a Raspberry Pi Pico Zero via SPI.
The Pico Zero runs an arduino firmware which exposes a SimpleRPC
interface which this python module uses via USB to communicate
with RFID tags.

## Features

- Python library for easy integration.
- Uses USB serial communication to the reader.
- Cross-platform support (Linux, Windows, macOS).
- Finds and selects ISO/IEC 14443A and ISO/IEC 15693 cards.
- Can read/write the cards' memories.
- Can authenticate against Mifare classic cards to read their memories.
- Supports multiple cards within the field.

## API Documentation

See [API Reference](reference.md).

## Installation

### Python Package

Install from PyPI:

```bash
pip install pn5180-tagomatic
```

### Building the hardware

See
[here](https://github.com/bofh69/pn5180-tagomatic/tree/main/sketch/README.md)
for instructions on the hardware and the firmware.

## Usage

```python
from pn5180_tagomatic import PN5180, RxProtocol, TxProtocol

# Create reader instance and use it
with PN5180("/dev/ttyACM0") as reader:
    versions = reader.ll.read_eeprom(0x10, 6)
    with reader.start_session(
        TxProtocol.ISO_14443_A_106, RxProtocol.ISO_14443_A_106
    ) as session:
        card = session.connect_one_iso14443a()
        print(f"Reading from card {card.id}")
        memory = card.read_memory()
```

## License

This project is licensed under the GNU General Public License v3.0 or later (GPL-3.0-or-later).

## Contributing

Contributions are welcome!

## Acknowledgments

This project uses FastLED by Daniel Garcia et al.

SimpleRPC by Jeroen F.J. Laros, Chris Flesher et al is also used.
