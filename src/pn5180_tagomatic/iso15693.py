# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""ISO 15693 card implementation."""

from __future__ import annotations

from .cards import Card, Iso15693UniqueId, UniqueId
from .constants import ISO15693Command, MemoryWriteError
from .proxy import PN5180Error, PN5180Helper


class ISO15693Card(Card):
    """Represents a connected ISO 15693 card.

    This class provides methods to interact with a card that has been
    successfully connected via the SELECT command.
    """

    def __init__(
        self, reader: PN5180Helper, card_id: Iso15693UniqueId
    ) -> None:
        """Initialize ISO15693.

        Args:
            reader: The PN5180 reader instance.
            card_id: The card's UID
        """
        self._reader = reader
        self._card_id = card_id
        self._block_size = -1
        self._num_blocks = 32
        self._dsfid: int | None = None
        self._afi: int | None = None
        self._ic_reference: int | None = None

    @property
    def id(self) -> UniqueId:
        """Get the card's UID."""
        return self._card_id

    @property
    def dsfid(self) -> int | None:
        """Gets the DSFID value, if supported by card"""
        self._ensure_sys_info_loaded()
        return self._dsfid

    @property
    def afi(self) -> int | None:
        """Gets the AFI value, if supported by card"""
        self._ensure_sys_info_loaded()
        return self._afi

    @property
    def ic_reference(self) -> int | None:
        """Gets the IC reference value, if supported by card"""
        self._ensure_sys_info_loaded()
        return self._ic_reference

    def _ensure_sys_info_loaded(self) -> None:
        if self._block_size < 0:
            sys_info = self.get_system_information()
            self._block_size = sys_info.get("block_size", 4)
            self._num_blocks = sys_info.get("num_blocks", 256)
            self._dsfid = sys_info.get("dsfid", None)
            self._afi = sys_info.get("afi", None)
            self._ic_reference = sys_info.get("ic_reference", None)

    @property
    def memory_block_size(self) -> int:
        self._ensure_sys_info_loaded()
        return self._block_size

    @property
    def memory_number_of_blocks(self) -> int:
        """Gets the number of blocks the card contains"""
        self._ensure_sys_info_loaded()
        return self._num_blocks

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

        mlen = (cc[2] + 1) * 8

        is_readonly = bool(cc[3] & 1)

        return (major, minor, mlen, is_readonly)

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

        cc = self.decode_cc(memory)
        if cc is None:
            return None

        major, _minor, mlen, _ = cc

        if major > 4:
            return None

        if mlen > len(memory):
            return None

        pos = 4

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

    def read_memory(self, offset: int = 0, length: int | None = None) -> bytes:
        """Read memory from card.

        Args:
            offset: Starting offset, in bytes (default: 0)
            length: Number of bytes to read read (default: 128)

        Returns:
            All read memory as a single bytes object.

        Raises:
            PN5180Error: If communication with the card fails.
        """
        if offset % self.memory_block_size != 0:
            raise ValueError(
                "Offset not an even multiple of memory_block_size"
            )

        start_block = offset // self.memory_block_size

        if length is None:
            num_blocks = self._num_blocks
        else:
            if length % self.memory_block_size != 0:
                raise ValueError(
                    "length is not an even multiple of memory_block_size"
                )
            num_blocks = length // self.memory_block_size

        self._reader.turn_on_crc()
        self._reader.change_mode_to_transceiver()

        # TODO: If num_blocks * memory_block_size > 128, loop

        # TODO: If start_block > 255, use EXTENDED_READ_MULTIPLE_BLOCKS
        memory_content = self._reader.send_and_receive_15693(
            ISO15693Command.READ_MULTIPLE_BLOCKS,
            bytes([start_block, num_blocks - 1]),
        )

        if len(memory_content) > 0 and memory_content[0] & 1:
            memory_content += b"\0"
            raise PN5180Error(
                "Got error while reading memory", memory_content[1]
            )
        if len(memory_content) < 2:
            # No more data available
            return b""

        return memory_content[1:]

    def get_system_information(self) -> dict[str, int]:
        """Get System information from card.

        Returns:
            The system info as a single bytes object.

        Raises:
            PN5180Error: If communication with the card fails.
        """
        self._reader.turn_on_crc()
        self._reader.change_mode_to_transceiver()

        system_info = self._reader.send_and_receive_15693(
            ISO15693Command.GET_SYSTEM_INFORMATION,
            b"",
        )

        if len(system_info) > 0 and system_info[0] & 1:
            system_info += b"\0"
            raise PN5180Error(
                "Error getting system information", system_info[1]
            )
        if len(system_info) < 1:
            raise PN5180Error("Error getting system information, no answer", 0)

        pos = 10
        result = {}
        if system_info[1] & 1:
            result["dsfid"] = system_info[pos]
            pos += 1
        if system_info[1] & 2:
            result["afi"] = system_info[pos]
            pos += 1
        if system_info[1] & 4:
            result["num_blocks"] = system_info[pos] + 1
            pos += 1
            result["block_size"] = (system_info[pos] & 31) + 1
            pos += 1
        if system_info[1] & 8:
            result["ic_reference"] = system_info[pos]
            pos += 1

        return result

    def write_memory(self, offset: int, data: bytes) -> None:
        """Write to a card's memory

        Args:
            offset: Starting byte (default: 0).
            data: <even memory_block_size> bytes

        Raises:
            PN5180Error: If communication with the card fails.
        """
        if offset % self.memory_block_size != 0:
            raise ValueError(
                "Offset not an even multiple of memory_block_size"
            )

        if len(data) % self.memory_block_size != 0:
            raise ValueError(
                "data's length is not an even multiple of memory_block_size"
            )

        start_block = offset // self.memory_block_size

        num_blocks = len(data) // self.memory_block_size

        self._reader.turn_on_crc()
        self._reader.change_mode_to_transceiver()

        ##### This should work, but some cards are incompatible...
        # result = self._reader.send_and_receive_15693(
        #    ISO15693Command.WRITE_MULTIPLE_BLOCKS,
        #    bytes([
        #        start_block,
        #        num_blocks - 1,
        #        ]) + data)

        for block in range(num_blocks):
            result = self._reader.send_and_receive_15693(
                ISO15693Command.WRITE_SINGLE_BLOCK,
                bytes(
                    [
                        block + start_block,
                    ]
                )
                + data[
                    block
                    * self.memory_block_size : (block + 1)
                    * self.memory_block_size
                ],
            )
            if len(result) < 1 or result[0] & 1:
                result += b"\0\0"
                raise MemoryWriteError(
                    offset=block * self.memory_block_size,
                    error_code=result[1],
                    response_data=result,
                )
