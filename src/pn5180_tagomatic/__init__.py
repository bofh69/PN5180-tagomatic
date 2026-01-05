# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""PN5180-tagomatic: USB based RFID reader with Python interface."""

from .pn5180 import (
    PN5180,
    ISO14443ACard,
    ISO14443ACommand,
    ISO15693Command,
    MifareKeyType,
    PN5180Error,
    PN5180Helper,
    PN5180Proxy,
    PN5180RFSession,
    RegisterOperation,
    Registers,
    SwitchMode,
    TimeslotBehavior,
)

__version__ = "0.1.0"
__all__ = [
    "ISO14443ACard",
    "ISO14443ACommand",
    "ISO15693Command",
    "MifareKeyType",
    "PN5180",
    "PN5180Error",
    "PN5180Helper",
    "PN5180Proxy",
    "PN5180RFSession",
    "RegisterOperation",
    "Registers",
    "SwitchMode",
    "TimeslotBehavior",
    "__version__",
]
