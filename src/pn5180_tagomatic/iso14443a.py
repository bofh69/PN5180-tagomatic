# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""ISO 14443-A card implementation."""

from __future__ import annotations

from .cards import Card, Iso14443AUniqueId, UniqueId
from .constants import ISO14443ACommand, MemoryWriteError, MifareKeyType
from .proxy import PN5180Helper


class ISO14443ACard(Card):
    """Represents a connected ISO 14443-A card.

    This class provides methods to interact with a card that has been
    successfully connected via the ISO 14443-A anticollision protocol.
    """

    def __init__(
        self, reader: PN5180Helper, card_id: Iso14443AUniqueId
    ) -> None:
        """Initialize ISO14443ACard.

        Args:
            reader: The PN5180 reader instance.
            card_id: The card's UID + SAK
        """
        self._reader = reader
        self._card_id = card_id
        self._keys_a: dict[int, bytes] = {}
        self._keys_b: dict[int, bytes] = {}
        self._keys_a[-1] = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
        self._keys_b[-1] = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    @property
    def id(self) -> UniqueId:
        """Get the card's UniqueId."""
        return self._card_id

    @property
    def sak(self) -> bytes:
        """Get the card's SAK response."""
        return self._card_id.sak_as_bytes()

    @property
    def memory_block_size(self) -> int:
        """How big the memory blocks are"""
        # This should be calculated from card
        return 4

    def read_memory(self, offset: int = 0, length: int = 255) -> bytes:
        start_page = offset // self.memory_block_size
        num_pages = (length + 3) // self.memory_block_size

        uid = self.id.uid_as_bytes()
        if len(uid) == 4:
            return self._read_mifare_memory(start_page, num_pages)
        return self._read_unauthenticated_memory(start_page, num_pages)

    def _read_unauthenticated_memory(
        self, start_page: int = 0, num_pages: int = 255
    ) -> bytes:
        """Read memory from a non-MIFARE Classic ISO 14443-A card.

        This method reads memory pages from ISO 14443-A cards like NTAG
        that don't require authentication.

        Args:
            start_page: Starting page to read
            num_pages: How many pages to read.

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

    def write_memory(self, offset: int, data: bytes) -> None:
        """Write memory to a non-MIFARE Classic ISO 14443-A card.

        This method writes memory pages from ISO 14443-A cards like NTAG
        that don't require authentication.

        Args:
            offset: Starting page number (default: 0).
            data: data to write to the page(s).

        Raises:
            PN5180Error: If communication with the card fails.
            TimeoutError: If card does not respond.
            MemoryWriteError: If memory write fails.
            ValueError: The bytes are not of an even page length or offset not aligned.
        """

        if offset % self.memory_block_size != 0:
            raise ValueError(
                "Offset not an even multiple of memory_block_size"
            )

        if len(data) % self.memory_block_size != 0:
            raise ValueError(
                "data's length is not an even multiple of memory_block_size"
            )

        start_page = offset // self.memory_block_size

        for page in range(len(data) // self.memory_block_size):
            response = self._reader.send_and_wait_for_ack(
                0,
                bytes([ISO14443ACommand.WRITE, start_page + page])
                + data[
                    offset
                    + page * self.memory_block_size : offset
                    + (page + 1) * self.memory_block_size
                ],
            )

            if len(response) == 0:
                raise MemoryWriteError(
                    offset=offset + page * self.memory_block_size,
                    error_code=0xFF,
                    response_data=b"",
                )

            if (response[0] & 0xF) != 0xA:
                raise MemoryWriteError(
                    offset=offset + page * self.memory_block_size,
                    error_code=response[0],
                    response_data=response,
                )

    def _read_mifare_memory(
        self,
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
        uid = self.id.uid_as_bytes()
        if len(uid) != 4:
            raise ValueError(
                "This card does not have a 4-byte UID required for MIFARE Classic"
            )

        self._reader.turn_on_crc()

        # Convert UID to 32-bit integer for authentication
        mifare_uid = uid[3] << 24 | uid[2] << 16 | uid[1] << 8 | uid[0]

        memory_parts = []
        end_page = min(start_page + num_pages, 255)
        for page in range(start_page, end_page, 4):
            # Try KEY A
            key_a = (
                self._keys_a[page]
                if page in self._keys_a
                else self._keys_a.get(-1, None)
            )

            if key_a is not None:
                retval_a = self._reader.mifare_authenticate(
                    key_a, MifareKeyType.KEY_A, page, mifare_uid
                )
                if retval_a == 2:  # timeout
                    break
            else:
                retval_a = -1

            # Try KEY B if KEY A failed
            if retval_a != 0:
                key_b = (
                    self._keys_b[page]
                    if page in self._keys_b
                    else self._keys_b.get(-1, None)
                )
                if key_b is not None:
                    retval_b = self._reader.mifare_authenticate(
                        key_b, MifareKeyType.KEY_B, page, mifare_uid
                    )
                    if retval_b == 2:  # timeout
                        break
                    if retval_b != 0:
                        # Both keys failed, stop reading
                        break
                else:
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

    def authenticate_for_page(
        self, page_num: int, key_a: bytes | None, key_b: bytes | None
    ) -> None:
        """Set authenticate keys for page.

        For mifare cards, an authentication key is needed to read their pages.
        It can be different per page.
        When reading a page and they key is missing, the -1 page's keys are used.

        Args:
            page_num: what page this key should be used for, -1 for setting default key
            key_a: The new key, or None to remove the old one.
            key_b: The new key, or None to remove the old one.
        """
        if key_a is None:
            self._keys_a.pop(page_num, None)
        else:
            if len(key_a) != 6:
                raise ValueError("key_a must be exactly 6 bytes")
            self._keys_a[page_num] = bytes(key_a)

        if key_b is None:
            self._keys_b.pop(page_num, None)
        else:
            if len(key_b) != 6:
                raise ValueError("key_b must be exactly 6 bytes")
            self._keys_b[page_num] = bytes(key_b)

    def decode_cc(self, cc: bytes) -> tuple[int, int, int, bool] | None:
        """Decode the CC memory block (block 0)

        Args:
            cc(bytes): The memory from block 0.

        Returns:
            (major_version, minor_version, memory size, is readonly)
            or None if CC isn't valid.

        Raises:
            PN5180Error: If communication with the card fails.
            ValueError: If cc is less than 4 bytes.
        """
        if len(cc) < 4:
            raise ValueError("cc should be at least 4 bytes")

        if cc[0] != 0xE1:
            return None

        major = cc[1] >> 4
        minor = cc[1] & 0xF

        mlen = (cc[2]) * 4

        is_readonly = bool((cc[3] & 0xF0) == 0xF0)

        return (major, minor, mlen, is_readonly)

    def get_ndef(self, memory: bytes) -> tuple[int, bytes] | None:
        """Find the NDEF memory.

        Args:
            memory: The card's memory, starting from offset 0

        Returns:
            (start, ndef_bytes),
            or None if NDEF couldn't be found.
        """

        cc = self.decode_cc(memory[12:16])
        if cc is None:
            return None

        major, _minor, mlen, _ = cc

        if major > 1:
            return None

        if mlen > len(memory):
            return None

        pos = 16

        def read_val(memory: bytes, pos: int) -> tuple[int, int]:
            if memory[pos] < 255:
                return memory[pos], pos + 1
            else:
                return (memory[pos + 1] << 8) | memory[pos + 2], pos + 3

        while pos < mlen:
            typ, pos = read_val(memory, pos)
            if typ == 0:
                continue
            if typ == 0xFE:
                # End of TLV
                return None
            field_len, pos = read_val(memory, pos)
            if typ == 0x03:
                if pos + field_len > mlen:
                    return None
                return (pos, memory[pos : pos + field_len])
            pos += field_len

        return None
