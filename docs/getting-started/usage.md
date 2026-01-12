<!--
SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Usage

## Basic Usage

The main entry point for using PN5180-tagomatic is the `PN5180` class. Here's a simple example:

```python
from pn5180_tagomatic import PN5180

# Create reader instance using context manager
with PN5180("/dev/ttyACM0") as reader:
    # Access low-level interface
    versions = reader.ll.read_eeprom(0x10, 6)
    
    # Start an RF session
    with reader.start_session(0x00, 0x80) as session:
        # Connect to an ISO 14443-A card
        card = session.connect_one_iso14443a()
        print(f"Reading from card {card.uid.hex(':')}")
        
        # Read memory
        if len(card.uid) == 4:
            # Mifare Classic card
            memory = card.read_mifare_memory()
        else:
            # Other ISO 14443-A card (e.g., NTAG)
            memory = card.read_memory()
```

!!! tip
    Always use context managers (`with` statements) to ensure proper cleanup of resources.

## Device Path

On Linux, the device path is typically `/dev/ttyACM0` or `/dev/ttyUSB0`.

On Windows, it's usually `COM3`, `COM4`, etc.

On macOS, it might be `/dev/cu.usbmodem*`.

## ISO 14443-A Cards

### Reading Cards

```python
from pn5180_tagomatic import PN5180

with PN5180("/dev/ttyACM0") as reader:
    with reader.start_session(0x00, 0x80) as session:
        card = session.connect_one_iso14443a()
        
        # Read memory from page 0, up to 255 pages
        memory = card.read_memory(start_page=0, num_pages=255)
        print(f"Memory: {memory.hex()}")
```

### Writing to Cards

```python
from pn5180_tagomatic import PN5180

with PN5180("/dev/ttyACM0") as reader:
    with reader.start_session(0x00, 0x80) as session:
        card = session.connect_one_iso14443a()
        
        # Write 32-bit data to page 4
        card.write_memory(page=4, data=0x12345678)
```

### Mifare Classic Cards

```python
from pn5180_tagomatic import PN5180, MifareKeyType

with PN5180("/dev/ttyACM0") as reader:
    with reader.start_session(0x00, 0x80) as session:
        card = session.connect_one_iso14443a()
        
        # Read Mifare Classic memory with authentication
        key = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])  # Default key
        memory = card.read_mifare_memory(
            start_block=0,
            num_blocks=64,
            key=key,
            key_type=MifareKeyType.KEY_A
        )
```

## ISO 15693 Cards

### Inventory (Finding Cards)

```python
from pn5180_tagomatic import PN5180

with PN5180("/dev/ttyACM0") as reader:
    with reader.start_session(0x01, 0x81) as session:
        # Find all ISO 15693 cards in the field
        cards = session.inventory_iso15693()
        
        for card in cards:
            print(f"Found card: {card.uid.hex(':')}")
            memory = card.read_memory()
```

### Reading and Writing

```python
from pn5180_tagomatic import PN5180

with PN5180("/dev/ttyACM0") as reader:
    with reader.start_session(0x01, 0x81) as session:
        cards = session.inventory_iso15693()
        
        if cards:
            card = cards[0]
            
            # Read memory
            memory = card.read_memory(start_block=0, num_blocks=32)
            
            # Get system information
            info = card.get_system_information()
            print(f"Block size: {info.get('block_size', 'unknown')}")
            print(f"Num blocks: {info.get('num_blocks', 'unknown')}")
```

## Low-Level Access

For direct hardware control, use the `ll` (low-level) attribute:

```python
from pn5180_tagomatic import PN5180

with PN5180("/dev/ttyACM0") as reader:
    # Read EEPROM
    data = reader.ll.read_eeprom(address=0x00, length=16)
    
    # Write register
    reader.ll.write_register(address=0x00, value=0x1234)
    
    # Load RF configuration
    reader.ll.load_rf_config(tx_config=0x00, rx_config=0x80)
    
    # Turn RF field on/off
    reader.ll.rf_on()
    reader.ll.rf_off()
```

## Example Programs

Several example programs are available in the `examples/` directory of the repository:

- `basic_example.py`: Simple card reading example
- `iso_14443-get-uid.py`: Get UID from ISO 14443-A card
- `iso_14443-read-memory.py`: Read memory from ISO 14443-A card
- `iso_14443-write-memory.py`: Write memory to ISO 14443-A card
- `iso_15693-inventory.py`: Find ISO 15693 cards
- `iso_15693-update-memory.py`: Update ISO 15693 card memory

## Error Handling

The library raises various exceptions for error conditions:

```python
from pn5180_tagomatic import PN5180, PN5180Error, MemoryWriteError

try:
    with PN5180("/dev/ttyACM0") as reader:
        with reader.start_session(0x00, 0x80) as session:
            card = session.connect_one_iso14443a()
            memory = card.read_memory()
except PN5180Error as e:
    print(f"Communication error: {e}")
except TimeoutError:
    print("No card found or card did not respond")
except MemoryWriteError as e:
    print(f"Memory write failed: {e}")
```

## Next Steps

For detailed API documentation, see the [API Reference](../api/index.md).
