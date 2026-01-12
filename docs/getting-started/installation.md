<!--
SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Installation

## Python Package

### From PyPI

Install the latest stable version from PyPI:

```bash
pip install pn5180-tagomatic
```

### From Source

Install the development version from source:

```bash
git clone https://github.com/bofh69/PN5180-tagomatic.git
cd PN5180-tagomatic
pip install -e .
```

### Development Installation

For development with additional tools:

```bash
git clone https://github.com/bofh69/PN5180-tagomatic.git
cd PN5180-tagomatic
pip install -e ".[dev]"
# or:
make install-dev
```

## Firmware

The PN5180-tagomatic requires firmware to be uploaded to the Raspberry Pi Pico.

See [sketch/README.md](https://github.com/bofh69/PN5180-tagomatic/blob/main/sketch/README.md) in the repository for detailed instructions on building and uploading the Raspberry Pi Pico firmware.

## Requirements

- **Python**: 3.10 or higher
- **Operating Systems**: Linux, Windows, macOS
- **Hardware**: 
  - PN5180 NFC Frontend module
  - Raspberry Pi Pico (Zero)
  - USB connection

## Verifying Installation

After installation, you can verify that the package is installed correctly:

```python
import pn5180_tagomatic
print(pn5180_tagomatic.__version__)
```

## Next Steps

Once installed, proceed to the [Usage](usage.md) guide to learn how to use the library.
