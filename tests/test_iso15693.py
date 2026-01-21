# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for ISO15693 card functionality."""

from unittest.mock import MagicMock

import pytest

from pn5180_tagomatic.iso15693 import ISO15693Card


@pytest.fixture
def iso15693_card():
    """Create an ISO15693 card instance for testing."""
    mock_comm = MagicMock()
    return ISO15693Card(
        mock_comm, bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08])
    )


def test_iso15693_decode_cc_valid(iso15693_card):
    """Test decode_cc with valid capability container."""
    # Valid CC:
    # * magic byte 0xE1
    # * version 1.0
    # * memory size (7+1)*8=64 bytes
    # * read/write access
    cc = bytes([0xE1, 0x10, 0x07, 0x00])

    result = iso15693_card.decode_cc(cc)

    assert result is not None
    major, minor, mlen, is_readonly = result
    assert major == 1
    assert minor == 0
    assert mlen == 64  # (7 + 1) * 8
    assert is_readonly is False


def test_iso15693_decode_cc_readonly(iso15693_card):
    """Test decode_cc with readonly access."""
    # CC with readonly bit set (bit 0 of cc[3])
    cc = bytes([0xE1, 0x10, 0x0F, 0x01])

    result = iso15693_card.decode_cc(cc)

    assert result is not None
    major, minor, mlen, is_readonly = result
    assert major == 1
    assert minor == 0
    assert mlen == 128  # (15 + 1) * 8
    assert is_readonly is True


def test_iso15693_decode_cc_invalid_magic(iso15693_card):
    """Test decode_cc with invalid magic byte."""
    # Invalid magic byte (should be 0xE1)
    cc = bytes([0xE2, 0x10, 0x07, 0x00])

    result = iso15693_card.decode_cc(cc)

    assert result is None


def test_iso15693_decode_cc_short_input(iso15693_card):
    """Test decode_cc with input too short."""
    # Too short (only 3 bytes, should be at least 4)
    cc = bytes([0xE1, 0x10, 0x07])

    with pytest.raises(ValueError):
        iso15693_card.decode_cc(cc)


def test_iso15693_get_ndef_simple_tlv(iso15693_card):
    """Test get_ndef with a simple NDEF TLV structure."""
    # Memory layout:
    # Bytes 0-3: CC (0xE1, version 1.0, 64 bytes, read/write)
    # Bytes 4-5: NDEF TLV (Type=0x03, Length=10)
    # Bytes 6-15: NDEF message content
    memory = bytearray(
        [
            0xE1,
            0x10,
            0x07,
            0x00,  # CC
            0x03,
            0x0A,  # NDEF TLV: Type=0x03, Length=10
            0xD1,
            0x01,
            0x06,
            0x54,
            0x02,
            0x65,
            0x6E,
            0x68,
            0x69,
            0x00,  # NDEF message
        ]
    )
    # Pad to 64 bytes to match CC
    memory.extend([0x00] * (64 - len(memory)))

    result = iso15693_card.get_ndef(memory)

    assert result is not None
    pos, ndef_bytes = result
    assert pos == 6
    assert len(ndef_bytes) == 10
    assert ndef_bytes == bytes(
        [0xD1, 0x01, 0x06, 0x54, 0x02, 0x65, 0x6E, 0x68, 0x69, 0x00]
    )


def test_iso15693_get_ndef_long_length(iso15693_card):
    """Test get_ndef with 3-byte length encoding (length >= 255)."""
    # Memory with 3-byte length encoding
    # CC allows up to 2048 bytes
    memory = bytearray(
        [
            0xE1,
            0x10,
            0xFF,
            0x00,  # CC: 256*8=2048 bytes
            0x03,
            0xFF,
            0x01,
            0x00,  # NDEF TLV: Type=0x03, Length=0xFF (3-byte), length value=256
        ]
    )
    # Add 256 bytes of NDEF data
    memory.extend([0xAA] * 256)
    # Pad to 2048 bytes to match CC
    memory.extend([0x00] * (2048 - len(memory)))

    result = iso15693_card.get_ndef(memory)

    assert result is not None
    pos, ndef_bytes = result
    assert pos == 8
    assert len(ndef_bytes) == 256
    assert all(b == 0xAA for b in ndef_bytes)


def test_iso15693_get_ndef_with_null_tlvs(iso15693_card):
    """Test get_ndef with NULL TLVs before NDEF."""
    # Memory with NULL TLVs (0x00) before NDEF
    memory = bytearray(
        [
            0xE1,
            0x10,
            0x07,
            0x00,  # CC
            0x00,
            0x00,  # NULL TLVs
            0x03,
            0x05,  # NDEF TLV
            0x48,
            0x65,
            0x6C,
            0x6C,
            0x6F,  # "Hello"
        ]
    )
    # Pad to 64 bytes to match CC
    memory.extend([0x00] * (64 - len(memory)))

    result = iso15693_card.get_ndef(memory)

    assert result is not None
    pos, ndef_bytes = result
    assert pos == 8
    assert ndef_bytes == bytes([0x48, 0x65, 0x6C, 0x6C, 0x6F])


def test_iso15693_get_ndef_terminator_tlv(iso15693_card):
    """Test get_ndef returns None when encountering terminator TLV before NDEF."""
    # Memory with terminator TLV (0xFE) before NDEF
    memory = bytearray(
        [
            0xE1,
            0x10,
            0x07,
            0x00,  # CC
            0xFE,  # Terminator TLV
            0x03,
            0x05,  # NDEF TLV (won't be reached)
            0x48,
            0x65,
            0x6C,
            0x6C,
            0x6F,
        ]
    )

    result = iso15693_card.get_ndef(memory)

    assert result is None


def test_iso15693_get_ndef_invalid_cc(iso15693_card):
    """Test get_ndef returns None with invalid CC."""
    # Invalid CC (wrong magic byte)
    memory = bytearray(
        [
            0xE2,
            0x10,
            0x07,
            0x00,  # Invalid CC
            0x03,
            0x05,
            0x48,
            0x65,
            0x6C,
            0x6C,
            0x6F,
        ]
    )

    result = iso15693_card.get_ndef(memory)

    assert result is None


def test_iso15693_get_ndef_unsupported_version(iso15693_card):
    """Test get_ndef returns None with unsupported major version."""
    # Major version > 4 (unsupported)
    memory = bytearray(
        [
            0xE1,
            0x50,
            0x07,
            0x00,  # CC with major version 5
            0x03,
            0x05,
            0x48,
            0x65,
            0x6C,
            0x6C,
            0x6F,
        ]
    )

    result = iso15693_card.get_ndef(memory)

    assert result is None


def test_iso15693_get_ndef_memory_too_small(iso15693_card):
    """Test get_ndef returns None when memory is smaller than CC indicates."""
    # CC indicates 2048 bytes but memory is only 16 bytes
    memory = bytearray(
        [
            0xE1,
            0x10,
            0xFF,
            0x00,  # CC: 256*8=2048 bytes
            0x03,
            0x05,
            0x48,
            0x65,
            0x6C,
            0x6C,
            0x6F,
        ]
    )

    result = iso15693_card.get_ndef(memory)

    assert result is None


def test_iso15693_get_ndef_field_exceeds_memory(iso15693_card):
    """Test get_ndef returns None when NDEF field exceeds memory length."""
    # NDEF field length exceeds available memory
    memory = bytearray(
        [
            0xE1,
            0x10,
            0x07,
            0x00,  # CC: 64 bytes
            0x03,
            0x64,  # NDEF TLV: Length=100 (exceeds 64 byte limit)
            0x48,
            0x65,
            0x6C,
            0x6C,
            0x6F,
        ]
    )

    result = iso15693_card.get_ndef(memory)

    assert result is None
