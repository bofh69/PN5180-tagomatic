# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Common types for different cards"""

from typing import Protocol


class UniqueId(Protocol):
    """Represents a cards unique identifier.
    Subtypes contain type specific extensions.
    """

    def uid_as_bytes(self) -> bytes:
        """Returns the UID as bytes"""

    def uid_as_string(self) -> str:
        """Returns the UID as a string"""

    def __str__(self) -> str:
        """Returns a printable representation"""


class Iso14443AUniqueId(UniqueId):
    """ISO/IEC 14443A card identifiers.
    It also includes the SAK response.
    """

    def __init__(self, uid: bytes, sak: bytes):
        self._uid = uid
        self._sak = sak

    def uid_as_bytes(self) -> bytes:
        return self._uid

    def uid_as_string(self) -> str:
        return self._uid.hex(":")

    def sak_as_bytes(self) -> bytes:
        """The SAK response as bytes"""
        return self._sak

    def sak_as_string(self) -> str:
        """The SAK response as a string"""
        return self._sak.hex(":")

    def __str__(self) -> str:
        return f"UID: {self.uid_as_string()}, SAK={self.sak_as_string()}"


# Add a class for ISO-15693 UIDs too


class Iso15693UniqueId(UniqueId):
    """ISO/IEC 15693 card identifiers."""

    def __init__(self, uid: bytes) -> None:
        self._uid = uid

    def uid_as_bytes(self) -> bytes:
        return self._uid

    def uid_as_string(self) -> str:
        return self._uid.hex(":")

    def __str__(self) -> str:
        return f"UID: {self.uid_as_string()}"


class Card(Protocol):
    """Protocol for Cards"""

    @property
    def id(self) -> UniqueId:
        """Returns the card's unique id"""

    @property
    def memory_block_size(self) -> int:
        """How big the memory blocks are.
        This is the smallest unit that can be written
        and read from the card.

        Raises:
            PN5180Error: If communication with the card fails.
            TimeoutError: If card does not respond.
        """

    def read_memory(self, offset: int = 0, length: int = 128) -> bytes:
        """Read memory from the card.

        Cards normally can only read blocks of fixed sizes so
        the returned memory region may be larger than the requested length.
        At the end of the cards memory, some cards wrap around, others
        stop responding. So the returned memory may be shorter as well.

        Args:
            offset: Starting offset (default: 0).
            length: Number of bytes to read (default: 128).

        Returns:
            All read memory as a single bytes object.

        Raises:
            PN5180Error: If communication with the card fails.
            TimeoutError: If card does not respond.
        """

    def write_memory(self, offset: int, data: bytes) -> None:
        """Write memory to a card.

        Cards can only write blocks of a fixed size.
        The offset needs to start at an even such multiple
        and the data needs to be of the right length as well.

        Args:
            offset: Starting page number (default: 0).
            data: 32-bit data to write to that page

        Raises:
            PN5180Error: If communication with the card fails.
            TimeoutError: If card does not respond.
            MemoryWriteError: Other memory write failures.
        """

    def get_ndef(self, memory: bytes) -> tuple[int, bytes] | None:
        """Find the NDEF memory.

        If found, the start index in the input memory and
        its bytes are returned.

        Args:
            memory: The card's memory, starting from 0

        Returns:
            (start, ndef_bytes),
            or None if it wasn't found.
        """
