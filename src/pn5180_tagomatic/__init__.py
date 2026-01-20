# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""PN5180-tagomatic: USB connected RFID reader with Python interface."""

from .cards import (
    Card,
    Iso14443AUniqueId,
    Iso15693UniqueId,
    UniqueId,
)
from .constants import (
    ISO14443ACommand,
    ISO15693Command,
    ISO15693Error,
    MemoryWriteError,
    MifareKeyType,
    PN5180Error,
    RegisterOperation,
    Registers,
    RxProtocol,
    SwitchMode,
    TimeslotBehavior,
    TxProtocol,
)
from .iso14443a import ISO14443ACard
from .iso15693 import ISO15693Card
from .pn5180 import PN5180
from .proxy import PN5180Helper, PN5180Proxy
from .session import PN5180RFSession

__version__ = "0.1.1rc2"
__all__ = [
    "Card",
    "ISO14443ACard",
    "ISO14443ACommand",
    "Iso14443AUniqueId",
    "ISO15693Card",
    "ISO15693Command",
    "ISO15693Error",
    "Iso15693UniqueId",
    "MemoryWriteError",
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
    "UniqueId",
    "__version__",
]
