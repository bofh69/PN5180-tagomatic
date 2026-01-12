<!--
SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->

# API Reference

This section provides detailed API documentation for all public modules, classes, and functions in PN5180-tagomatic.

## Main Modules

- **[PN5180](pn5180.md)**: High-level PN5180 RFID reader interface
- **[Session](session.md)**: RF communication session management
- **[ISO 14443-A](iso14443a.md)**: ISO 14443-A card implementation
- **[ISO 15693](iso15693.md)**: ISO 15693 card implementation
- **[Proxy](proxy.md)**: Low-level PN5180 hardware interface
- **[Constants](constants.md)**: Constants, enums, and exceptions

## Quick Links

### Classes

- [`PN5180`](pn5180.md#pn5180_tagomatic.pn5180.PN5180): Main reader interface
- [`PN5180RFSession`](session.md#pn5180_tagomatic.session.PN5180RFSession): RF session manager
- [`ISO14443ACard`](iso14443a.md#pn5180_tagomatic.iso14443a.ISO14443ACard): ISO 14443-A card
- [`ISO15693Card`](iso15693.md#pn5180_tagomatic.iso15693.ISO15693Card): ISO 15693 card
- [`PN5180Helper`](proxy.md#pn5180_tagomatic.proxy.PN5180Helper): Low-level hardware interface
- [`PN5180Proxy`](proxy.md#pn5180_tagomatic.proxy.PN5180Proxy): Direct hardware proxy

### Exceptions

- [`PN5180Error`](constants.md#pn5180_tagomatic.constants.PN5180Error): General PN5180 error
- [`ISO15693Error`](constants.md#pn5180_tagomatic.constants.ISO15693Error): ISO 15693 specific error
- [`MemoryWriteError`](constants.md#pn5180_tagomatic.constants.MemoryWriteError): Memory write error

### Enums

- [`ISO14443ACommand`](constants.md#pn5180_tagomatic.constants.ISO14443ACommand): ISO 14443-A commands
- [`ISO15693Command`](constants.md#pn5180_tagomatic.constants.ISO15693Command): ISO 15693 commands
- [`MifareKeyType`](constants.md#pn5180_tagomatic.constants.MifareKeyType): Mifare key types
- [`Registers`](constants.md#pn5180_tagomatic.constants.Registers): PN5180 registers
- [`SwitchMode`](constants.md#pn5180_tagomatic.constants.SwitchMode): RF switch modes

## Usage Patterns

### Basic Usage

```python
from pn5180_tagomatic import PN5180

with PN5180("/dev/ttyACM0") as reader:
    with reader.start_session(0x00, 0x80) as session:
        card = session.connect_one_iso14443a()
        memory = card.read_memory()
```

### Low-Level Usage

```python
from pn5180_tagomatic import PN5180

with PN5180("/dev/ttyACM0") as reader:
    # Direct hardware access
    reader.ll.write_register(0x00, 0x1234)
    data = reader.ll.read_eeprom(0x10, 6)
```

## Navigation

Use the sidebar to navigate to specific module documentation. Each module page contains detailed information about its classes, functions, and usage examples.
