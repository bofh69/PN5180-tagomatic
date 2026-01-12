# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""ISO 14443-A card implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .constants import ISO14443ACommand, MemoryWriteError, MifareKeyType

if TYPE_CHECKING:
    from .proxy import PN5180Helper


class ISO14443ACard:
    """Represents a connected ISO 14443-A card.

    This class provides methods to interact with a card that has been
    successfully connected via the ISO 14443-A anticollision protocol.
    """

    def __init__(self, reader: PN5180Helper, uid: bytes, sak: bytes) -> None:
        """Initialize ISO14443ACard.

        Args:
            reader: The PN5180 reader instance.
            uid: The card's UID.
        """
        self._reader = reader
        self._uid = uid
        self._sak = sak

    @property
    def uid(self) -> bytes:
        """Get the card's UID."""
        return self._uid

    @property
    def sak(self) -> bytes:
        """Get the card's SAK response."""
        return self._sak

    def read_memory(self, start_page: int = 0, num_pages: int = 255) -> bytes:
        """Read memory from a non-MIFARE Classic ISO 14443-A card.

        This method reads memory pages from ISO 14443-A cards like NTAG
        that don't require authentication.

        Args:
            start_page: Starting page number (default: 0).
            num_pages: Number of pages to read (default: 255).

        Returns:
            All read memory as a single bytes object.

        Raises:
            PN5180Error: If communication with the card fails.
            TimeoutError: If card does not respond.
        """
        self._reader.turn_on_crc()

        memory_parts = []
        end_page = min(start_page + num_pages, 255)
        for page in range(start_page, end_page, 4):
            # Send READ command
            memory_content = self._reader.send_and_receive(
                0, bytes([ISO14443ACommand.READ, page])
            )

            if len(memory_content) < 1:
                # No more data available
                break

            memory_parts.append(memory_content)

        return b"".join(memory_parts)

    def write_memory(self, page: int, data: int) -> None:
        """Write memory to a non-MIFARE Classic ISO 14443-A card.

        This method writes memory pages from ISO 14443-A cards like NTAG
        that don't require authentication.

        Args:
            page: Starting page number (default: 0).
            data: 32-bit data to write to that page

        Raises:
            PN5180Error: If communication with the card fails.
            TimeoutError: If card does not respond.
            MemoryWriteError: If memory write fails.
        """

        response = self._reader.send_and_wait_for_ack(
            0,
            bytes(
                [
                    ISO14443ACommand.WRITE,
                    page,
                    data & 255,
                    (data >> 8) & 255,
                    (data >> 16) & 255,
                    data >> 24,
                ]
            ),
        )

        if len(response) == 0:
            raise MemoryWriteError(
                error_code=0xFF,
                response_data=b"",
            )

        if (response[0] & 0xF) != 0xA:
            raise MemoryWriteError(
                error_code=response[0],
                response_data=response,
            )

    def read_mifare_memory(
        self,
        key_a: bytes | None = None,
        key_b: bytes | None = None,
        start_page: int = 0,
        num_pages: int = 255,
    ) -> bytes:
        """Read memory from a MIFARE Classic card.

        This method reads memory from MIFARE Classic cards that require
        authentication. It tries authentication with both KEY_A and KEY_B.

        Args:
            key_a: 6-byte KEY_A (default: all 0xFF).
            key_b: 6-byte KEY_B (default: all 0xFF).
            start_page: Starting page number (default: 0).
            num_pages: Number of pages to read (default: 255).

        Returns:
            All read memory as a single bytes object.

        Raises:
            PN5180Error: If communication with the card fails.
            ValueError: If UID is not 4 bytes (not MIFARE Classic).
            TimeoutError: If card does not respond.
        """
        if len(self._uid) != 4:
            raise ValueError(
                "read_mifare_memory requires a 4-byte UID (MIFARE Classic)"
            )

        DEFAULT_KEY = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
        if key_a is None:
            key_a = DEFAULT_KEY
        if key_b is None:
            key_b = DEFAULT_KEY

        if len(key_a) != 6:
            raise ValueError("key_a must be exactly 6 bytes")
        if len(key_b) != 6:
            raise ValueError("key_b must be exactly 6 bytes")

        self._reader.turn_on_crc()

        # Convert UID to 32-bit integer for authentication
        mifare_uid = (
            self._uid[3] << 24
            | self._uid[2] << 16
            | self._uid[1] << 8
            | self._uid[0]
        )

        memory_parts = []
        end_page = min(start_page + num_pages, 255)
        for page in range(start_page, end_page, 4):
            # Try KEY A
            retval_a = self._reader.mifare_authenticate(
                key_a, MifareKeyType.KEY_A, page, mifare_uid
            )
            if retval_a == 2:  # timeout
                break

            # Try KEY B if KEY A failed
            if retval_a != 0:
                retval_b = self._reader.mifare_authenticate(
                    key_b, MifareKeyType.KEY_B, page, mifare_uid
                )
                if retval_b == 2:  # timeout
                    break
                if retval_b != 0:
                    # Both keys failed, stop reading
                    break

            # Send READ command
            memory_content = self._reader.send_and_receive(
                0, bytes([ISO14443ACommand.READ, page])
            )

            if len(memory_content) < 1:
                # No more data available
                break

            memory_parts.append(memory_content)

        return b"".join(memory_parts)
