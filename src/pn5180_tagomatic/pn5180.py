# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""High-level PN5180 RFID reader interface."""

from __future__ import annotations

from typing import Any

from .proxy import PN5180Helper
from .session import PN5180RFSession


class PN5180:
    """High-level PN5180 RFID reader interface.

    This class provides a convenient, high-level API for common RFID operations.
    For direct hardware access, use the `ll` (low-level) attribute.

    Args:
        tty: The tty device path to communicate via.

    Attributes:
        ll: Low-level PN5180 interface for direct hardware access.

    Example:
        >>> from pn5180_tagomatic import PN5180
        >>> with PN5180("/dev/ttyACM0") as reader:
        ...     # High-level API (recommended)
        ...     with reader.start_session(0x00, 0x80) as comm:
        ...         card = comm.connect_one_iso14443a()
        ...         memory = card.read_memory()
        ...
        ...     # Low-level access if needed
        ...     reader.ll.write_register(addr, value)
    """

    def __init__(self, tty: str) -> None:
        """Initialize the PN5180 reader.

        Args:
            tty: The tty device path to communicate via.
        """
        self.ll = PN5180Helper(tty)

    def start_session(self, tx_config: int, rx_config: int) -> PN5180RFSession:
        """Start an RF communication session.

        This method loads the RF configuration and turns on the RF field,
        then returns a PN5180RFSession object that manages the session.
        The RF field will be automatically turned off when the session ends.

        Args:
            tx_config: TX configuration index (byte: 0-255, see table 32).
            rx_config: RX configuration index (byte: 0-255, see table 32).

        Returns:
            PN5180RFSession object for managing the session.

        Raises:
            PN5180Error: If the operation fails.

        Example:
            >>> reader = PN5180("/dev/ttyACM0")
            >>> with reader.start_session(0x00, 0x80) as comm:
            ...     card = comm.connect_one_iso14443a()
            ...     uid = card.uid
            ...     memory = card.read_memory()
        """
        self.ll.load_rf_config(tx_config, rx_config)
        self.ll.rf_on()
        return PN5180RFSession(self.ll)

    def close(self) -> None:
        """Close the serial connection."""
        self.ll.close()

    def __enter__(self) -> PN5180:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
