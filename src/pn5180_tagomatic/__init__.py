# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""PN5180-tagomatic: USB based RFID reader with Python interface."""

from .pn5180 import PN5180, MifareKeyType, RegisterOperation

__version__ = "0.1.0"
__all__ = ["PN5180", "MifareKeyType", "RegisterOperation", "__version__"]
