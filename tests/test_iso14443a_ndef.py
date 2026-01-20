# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for ISO14443a card NDEF functionality."""

from unittest.mock import MagicMock

import pytest

from pn5180_tagomatic.cards import Iso14443AUniqueId
from pn5180_tagomatic.iso14443a import ISO14443ACard


def test_iso14443a_decode_cc_valid():
    """Test decode_cc with valid capability container."""
    mock_comm = MagicMock()
    uid = Iso14443AUniqueId(bytes([0x01, 0x02, 0x03, 0x04]), bytes([0x08]))
    card = ISO14443ACard(mock_comm, uid)
    
    # Valid CC: magic byte 0xE1, version 1.0, memory size 12*4=48 bytes, read/write access
    cc = bytes([0xE1, 0x10, 0x0C, 0x00])
    
    result = card.decode_cc(cc)
    
    assert result is not None
    major, minor, mlen, is_readonly = result
    assert major == 1
    assert minor == 0
    assert mlen == 48  # 12 * 4
    assert is_readonly is False


def test_iso14443a_decode_cc_readonly():
    """Test decode_cc with readonly access."""
    mock_comm = MagicMock()
    uid = Iso14443AUniqueId(bytes([0x01, 0x02, 0x03, 0x04]), bytes([0x08]))
    card = ISO14443ACard(mock_comm, uid)
    
    # CC with readonly flag (cc[3] & 0xF0 == 0xF0)
    cc = bytes([0xE1, 0x10, 0x0C, 0xF0])
    
    result = card.decode_cc(cc)
    
    assert result is not None
    major, minor, mlen, is_readonly = result
    assert major == 1
    assert minor == 0
    assert mlen == 48
    assert is_readonly is True


def test_iso14443a_decode_cc_partial_readonly():
    """Test decode_cc with partial readonly bits set."""
    mock_comm = MagicMock()
    uid = Iso14443AUniqueId(bytes([0x01, 0x02, 0x03, 0x04]), bytes([0x08]))
    card = ISO14443ACard(mock_comm, uid)
    
    # CC with some readonly bits but not all (0xF0)
    cc = bytes([0xE1, 0x10, 0x0C, 0xE0])
    
    result = card.decode_cc(cc)
    
    assert result is not None
    major, minor, mlen, is_readonly = result
    assert is_readonly is False  # Not all bits set


def test_iso14443a_decode_cc_invalid_magic():
    """Test decode_cc with invalid magic byte."""
    mock_comm = MagicMock()
    uid = Iso14443AUniqueId(bytes([0x01, 0x02, 0x03, 0x04]), bytes([0x08]))
    card = ISO14443ACard(mock_comm, uid)
    
    # Invalid magic byte (should be 0xE1)
    cc = bytes([0xE2, 0x10, 0x0C, 0x00])
    
    result = card.decode_cc(cc)
    
    assert result is None


def test_iso14443a_decode_cc_short_input():
    """Test decode_cc with input too short."""
    mock_comm = MagicMock()
    uid = Iso14443AUniqueId(bytes([0x01, 0x02, 0x03, 0x04]), bytes([0x08]))
    card = ISO14443ACard(mock_comm, uid)
    
    # Too short (only 3 bytes, should be at least 4)
    cc = bytes([0xE1, 0x10, 0x0C])
    
    with pytest.raises(ValueError):
        card.decode_cc(cc)


def test_iso14443a_get_ndef_simple_tlv():
    """Test get_ndef with a simple NDEF TLV structure."""
    mock_comm = MagicMock()
    uid = Iso14443AUniqueId(bytes([0x01, 0x02, 0x03, 0x04]), bytes([0x08]))
    card = ISO14443ACard(mock_comm, uid)
    
    # Memory layout for ISO14443a:
    # Bytes 0-11: Not used (12 bytes before CC)
    # Bytes 12-15: CC (0xE1, version 1.0, 48 bytes, read/write)
    # Bytes 16-17: NDEF TLV (Type=0x03, Length=10)
    # Bytes 18-27: NDEF message content
    memory = bytearray([0x00] * 12)  # First 12 bytes
    memory.extend([
        0xE1, 0x10, 0x0C, 0x00,  # CC at offset 12
        0x03, 0x0A,              # NDEF TLV at offset 16
        0xD1, 0x01, 0x06, 0x54, 0x02, 0x65, 0x6E, 0x68, 0x69, 0x00  # NDEF message
    ])
    # Pad to 48 bytes to match CC
    memory.extend([0x00] * (48 - len(memory)))
    
    result = card.get_ndef(memory)
    
    assert result is not None
    pos, ndef_bytes = result
    assert pos == 18
    assert len(ndef_bytes) == 10
    assert ndef_bytes == bytes([0xD1, 0x01, 0x06, 0x54, 0x02, 0x65, 0x6E, 0x68, 0x69, 0x00])


def test_iso14443a_get_ndef_long_length():
    """Test get_ndef with 3-byte length encoding (length >= 255)."""
    mock_comm = MagicMock()
    uid = Iso14443AUniqueId(bytes([0x01, 0x02, 0x03, 0x04]), bytes([0x08]))
    card = ISO14443ACard(mock_comm, uid)
    
    # Memory with 3-byte length encoding
    memory = bytearray([0x00] * 12)  # First 12 bytes
    memory.extend([
        0xE1, 0x10, 0xFF, 0x00,  # CC: 255*4=1020 bytes
        0x03, 0xFF, 0x01, 0x00,  # NDEF TLV: Type=0x03, Length=0xFF (3-byte), value=256
    ])
    # Add 256 bytes of NDEF data
    memory.extend([0xBB] * 256)
    # Pad to 1020 bytes to match CC
    memory.extend([0x00] * (1020 - len(memory)))
    
    result = card.get_ndef(memory)
    
    assert result is not None
    pos, ndef_bytes = result
    assert pos == 20
    assert len(ndef_bytes) == 256
    assert all(b == 0xBB for b in ndef_bytes)


def test_iso14443a_get_ndef_with_null_tlvs():
    """Test get_ndef with NULL TLVs before NDEF."""
    mock_comm = MagicMock()
    uid = Iso14443AUniqueId(bytes([0x01, 0x02, 0x03, 0x04]), bytes([0x08]))
    card = ISO14443ACard(mock_comm, uid)
    
    # Memory with NULL TLVs (0x00) before NDEF
    memory = bytearray([0x00] * 12)
    memory.extend([
        0xE1, 0x10, 0x0C, 0x00,  # CC
        0x00, 0x00,              # NULL TLVs
        0x03, 0x05,              # NDEF TLV
        0x48, 0x65, 0x6C, 0x6C, 0x6F  # "Hello"
    ])
    # Pad to 48 bytes to match CC
    memory.extend([0x00] * (48 - len(memory)))
    
    result = card.get_ndef(memory)
    
    assert result is not None
    pos, ndef_bytes = result
    assert pos == 20
    assert ndef_bytes == bytes([0x48, 0x65, 0x6C, 0x6C, 0x6F])


def test_iso14443a_get_ndef_terminator_tlv():
    """Test get_ndef returns None when encountering terminator TLV before NDEF."""
    mock_comm = MagicMock()
    uid = Iso14443AUniqueId(bytes([0x01, 0x02, 0x03, 0x04]), bytes([0x08]))
    card = ISO14443ACard(mock_comm, uid)
    
    # Memory with terminator TLV (0xFE) before NDEF
    memory = bytearray([0x00] * 12)
    memory.extend([
        0xE1, 0x10, 0x0C, 0x00,  # CC
        0xFE,                    # Terminator TLV
        0x03, 0x05,              # NDEF TLV (won't be reached)
        0x48, 0x65, 0x6C, 0x6C, 0x6F
    ])
    # Pad to 48 bytes to match CC
    memory.extend([0x00] * (48 - len(memory)))
    
    result = card.get_ndef(memory)
    
    assert result is None


def test_iso14443a_get_ndef_invalid_cc():
    """Test get_ndef returns None with invalid CC."""
    mock_comm = MagicMock()
    uid = Iso14443AUniqueId(bytes([0x01, 0x02, 0x03, 0x04]), bytes([0x08]))
    card = ISO14443ACard(mock_comm, uid)
    
    # Invalid CC (wrong magic byte)
    memory = bytearray([0x00] * 12)
    memory.extend([
        0xE2, 0x10, 0x0C, 0x00,  # Invalid CC
        0x03, 0x05,
        0x48, 0x65, 0x6C, 0x6C, 0x6F
    ])
    # Pad to 48 bytes (using the CC value as if it were valid)
    memory.extend([0x00] * (48 - len(memory)))
    
    result = card.get_ndef(memory)
    
    assert result is None


def test_iso14443a_get_ndef_unsupported_version():
    """Test get_ndef returns None with unsupported major version."""
    mock_comm = MagicMock()
    uid = Iso14443AUniqueId(bytes([0x01, 0x02, 0x03, 0x04]), bytes([0x08]))
    card = ISO14443ACard(mock_comm, uid)
    
    # Major version > 1 (unsupported for ISO14443a)
    memory = bytearray([0x00] * 12)
    memory.extend([
        0xE1, 0x20, 0x0C, 0x00,  # CC with major version 2
        0x03, 0x05,
        0x48, 0x65, 0x6C, 0x6C, 0x6F
    ])
    # Pad to 48 bytes to match CC
    memory.extend([0x00] * (48 - len(memory)))
    
    result = card.get_ndef(memory)
    
    assert result is None


def test_iso14443a_get_ndef_memory_too_small():
    """Test get_ndef returns None when memory is smaller than CC indicates."""
    mock_comm = MagicMock()
    uid = Iso14443AUniqueId(bytes([0x01, 0x02, 0x03, 0x04]), bytes([0x08]))
    card = ISO14443ACard(mock_comm, uid)
    
    # CC indicates 1020 bytes but memory is only 28 bytes
    memory = bytearray([0x00] * 12)
    memory.extend([
        0xE1, 0x10, 0xFF, 0x00,  # CC: 255*4=1020 bytes
        0x03, 0x05,
        0x48, 0x65, 0x6C, 0x6C, 0x6F
    ])
    
    result = card.get_ndef(memory)
    
    assert result is None


def test_iso14443a_get_ndef_field_exceeds_memory():
    """Test get_ndef returns None when NDEF field exceeds memory length."""
    mock_comm = MagicMock()
    uid = Iso14443AUniqueId(bytes([0x01, 0x02, 0x03, 0x04]), bytes([0x08]))
    card = ISO14443ACard(mock_comm, uid)
    
    # NDEF field length exceeds available memory
    memory = bytearray([0x00] * 12)
    memory.extend([
        0xE1, 0x10, 0x0C, 0x00,  # CC: 48 bytes
        0x03, 0x64,              # NDEF TLV: Length=100 (exceeds limit)
        0x48, 0x65, 0x6C, 0x6C, 0x6F
    ])
    # Pad to 48 bytes to match CC
    memory.extend([0x00] * (48 - len(memory)))
    
    result = card.get_ndef(memory)
    
    assert result is None
