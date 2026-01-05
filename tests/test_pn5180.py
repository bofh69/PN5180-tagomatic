# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the PN5180 class."""

from unittest.mock import MagicMock, Mock, call, patch

import pytest

from pn5180_tagomatic import PN5180, Registers


@patch("pn5180_tagomatic.pn5180.Interface")
def test_pn5180_init(mock_interface_class: Mock) -> None:
    """Test PN5180 initialization."""
    tty = "/dev/ttyACM0"
    reader = PN5180(tty)
    assert reader is not None
    mock_interface_class.assert_called_once_with(tty)


@patch("pn5180_tagomatic.pn5180.Interface")
def test_pn5180_reset(mock_interface_class: Mock) -> None:
    """Test PN5180 reset method via ll."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface_class.return_value = mock_interface

    reader = PN5180(tty)
    reader.ll.reset()

    mock_interface.reset.assert_called_once()


@patch("pn5180_tagomatic.pn5180.Interface")
def test_pn5180_close(mock_interface_class: Mock) -> None:
    """Test PN5180 close method."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface_class.return_value = mock_interface

    reader = PN5180(tty)
    reader.close()

    mock_interface.close.assert_called_once()


@patch("pn5180_tagomatic.pn5180.Interface")
def test_pn5180_context_manager(mock_interface_class: Mock) -> None:
    """Test PN5180 context manager."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface_class.return_value = mock_interface

    with PN5180(tty) as reader:
        assert reader is not None

    mock_interface.close.assert_called_once()


@patch("pn5180_tagomatic.pn5180.Interface")
def test_turn_off_crc(mock_interface_class: Mock) -> None:
    """Test turn_off_crc method via ll."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface.write_register_and_mask.return_value = 0
    mock_interface_class.return_value = mock_interface

    reader = PN5180(tty)
    reader.ll.turn_off_crc()

    assert mock_interface.write_register_and_mask.call_count == 2
    calls = mock_interface.write_register_and_mask.call_args_list
    assert calls[0] == call(Registers.CRC_TX_CONFIG, 0xFFFFFFFE)
    assert calls[1] == call(Registers.CRC_RX_CONFIG, 0xFFFFFFFE)


@patch("pn5180_tagomatic.pn5180.Interface")
def test_turn_on_crc(mock_interface_class: Mock) -> None:
    """Test turn_on_crc method via ll."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface.write_register_or_mask.return_value = 0
    mock_interface_class.return_value = mock_interface

    reader = PN5180(tty)
    reader.ll.turn_on_crc()

    assert mock_interface.write_register_or_mask.call_count == 2
    calls = mock_interface.write_register_or_mask.call_args_list
    assert calls[0] == call(Registers.CRC_TX_CONFIG, 0x00000001)
    assert calls[1] == call(Registers.CRC_RX_CONFIG, 0x00000001)


@patch("pn5180_tagomatic.pn5180.Interface")
def test_change_mode_to_transceiver(mock_interface_class: Mock) -> None:
    """Test change_mode_to_transceiver method via ll."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface.write_register_and_mask.return_value = 0
    mock_interface.write_register_or_mask.return_value = 0
    mock_interface_class.return_value = mock_interface

    reader = PN5180(tty)
    reader.ll.change_mode_to_transceiver()

    mock_interface.write_register_and_mask.assert_called_once_with(
        Registers.SYSTEM_CONFIG, 0xFFFFFFF8
    )
    mock_interface.write_register_or_mask.assert_called_once_with(
        Registers.SYSTEM_CONFIG, 0x00000003
    )


@patch("pn5180_tagomatic.pn5180.Interface")
def test_iso14443a_get_uid_4_bytes(mock_interface_class: Mock) -> None:
    """Test iso14443a_get_uid for 4-byte UID."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface_class.return_value = mock_interface

    # Mock register operations
    mock_interface.write_register_and_mask.return_value = 0
    mock_interface.write_register_or_mask.return_value = 0
    mock_interface.write_register.return_value = 0
    mock_interface.send_data.return_value = 0
    mock_interface.wait_for_irq.return_value = True

    # Mock ATQA response (0x0004 = 4-byte UID)
    mock_interface.read_register.side_effect = [
        (0, 0x0002),  # RX_STATUS: 2 bytes available
        (0, 0x0005),  # RX_STATUS: 5 bytes for UID
        (0, 0x0001),  # RX_STATUS: 1 byte for SAK
    ]

    mock_interface.read_data.side_effect = [
        (0, [0x00, 0x00]),  # ATQA response
        (
            0,
            [0x01, 0x02, 0x03, 0x04, 0x04],
        ),  # UID + BCC (BCC = 0x01^0x02^0x03^0x04)
        (0, [0x08]),  # SAK
    ]

    reader = PN5180(tty)
    uid = reader.iso14443a_get_uid()

    assert uid == bytes([0x01, 0x02, 0x03, 0x04])


@patch("pn5180_tagomatic.pn5180.Interface")
def test_iso14443a_get_uid_no_card(mock_interface_class: Mock) -> None:
    """Test iso14443a_get_uid when no card responds."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface_class.return_value = mock_interface

    # Mock register operations
    mock_interface.write_register_and_mask.return_value = 0
    mock_interface.write_register_or_mask.return_value = 0
    mock_interface.write_register.return_value = 0
    mock_interface.send_data.return_value = 0
    mock_interface.wait_for_irq.return_value = False

    # No data received
    mock_interface.read_register.return_value = (0, 0x0000)

    reader = PN5180(tty)
    with pytest.raises(TimeoutError):
        reader.iso14443a_get_uid()


@patch("pn5180_tagomatic.pn5180.Interface")
def test_iso14443a_get_uid_invalid_bcc(mock_interface_class: Mock) -> None:
    """Test iso14443a_get_uid with invalid BCC."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface_class.return_value = mock_interface

    # Mock register operations
    mock_interface.write_register_and_mask.return_value = 0
    mock_interface.write_register_or_mask.return_value = 0
    mock_interface.write_register.return_value = 0
    mock_interface.send_data.return_value = 0
    mock_interface.wait_for_irq.return_value = True

    mock_interface.read_register.side_effect = [
        (0, 0x0002),  # RX_STATUS: 2 bytes available
        (0, 0x0005),  # RX_STATUS: 5 bytes for UID
    ]

    mock_interface.read_data.side_effect = [
        (0, [0x00, 0x00]),  # ATQA response
        (0, [0x01, 0x02, 0x03, 0x04, 0xFF]),  # UID + invalid BCC
    ]

    reader = PN5180(tty)
    with pytest.raises(ValueError, match="Invalid BCC"):
        reader.iso14443a_get_uid()


@patch("pn5180_tagomatic.pn5180.Interface")
def test_iso14443a_read_memory_ntag(mock_interface_class: Mock) -> None:
    """Test iso14443a_read_memory for NTAG card."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface_class.return_value = mock_interface

    # Mock register operations
    mock_interface.write_register_or_mask.return_value = 0
    mock_interface.send_data.return_value = 0

    # Mock successful read of two pages
    mock_interface.read_register.side_effect = [
        (0, 0x0010),  # RX_STATUS: 16 bytes available for page 0
        (0, 0x0010),  # RX_STATUS: 16 bytes available for page 4
        (0, 0x0000),  # RX_STATUS: no more data
    ]

    mock_interface.read_data.side_effect = [
        (0, [0x01] * 16),  # Page 0 content
        (0, [0x02] * 16),  # Page 4 content
    ]

    reader = PN5180(tty)
    uid = bytes(
        [0x04, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66]
    )  # 7-byte UID (NTAG)
    memory_data = reader.iso14443a_read_memory(uid, start_page=0, max_pages=12)

    assert len(memory_data) == 2
    assert memory_data[0] == bytes([0x01] * 16)
    assert memory_data[4] == bytes([0x02] * 16)


@patch("pn5180_tagomatic.pn5180.Interface")
def test_iso14443a_read_memory_mifare(mock_interface_class: Mock) -> None:
    """Test iso14443a_read_memory for MIFARE Classic card."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface_class.return_value = mock_interface

    # Mock register operations
    mock_interface.write_register_or_mask.return_value = 0
    mock_interface.send_data.return_value = 0
    mock_interface.mifare_authenticate.return_value = 0  # Success

    # Mock successful read of one page
    mock_interface.read_register.side_effect = [
        (0, 0x0010),  # RX_STATUS: 16 bytes available for page 0
        (0, 0x0000),  # RX_STATUS: no more data
    ]

    mock_interface.read_data.side_effect = [
        (0, [0xAA] * 16),  # Page 0 content
    ]

    reader = PN5180(tty)
    uid = bytes([0x01, 0x02, 0x03, 0x04])  # 4-byte UID (MIFARE)
    memory_data = reader.iso14443a_read_memory(uid, start_page=0, max_pages=8)

    assert len(memory_data) == 1
    assert memory_data[0] == bytes([0xAA] * 16)
    # Verify authentication was called
    mock_interface.mifare_authenticate.assert_called()


@patch("pn5180_tagomatic.pn5180.Interface")
def test_start_comm(mock_interface_class: Mock) -> None:
    """Test start_comm method."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface.load_rf_config.return_value = 0
    mock_interface.rf_on.return_value = 0
    mock_interface.rf_off.return_value = 0
    mock_interface_class.return_value = mock_interface

    reader = PN5180(tty)
    comm = reader.start_comm(0x00, 0x80)

    mock_interface.load_rf_config.assert_called_once_with(0x00, 0x80)
    mock_interface.rf_on.assert_called_once()

    # Verify RF is turned off when communication is closed
    comm.close()
    mock_interface.rf_off.assert_called_once()


@patch("pn5180_tagomatic.pn5180.Interface")
def test_communication_context_manager(mock_interface_class: Mock) -> None:
    """Test PN5180RFSession context manager."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface.load_rf_config.return_value = 0
    mock_interface.rf_on.return_value = 0
    mock_interface.rf_off.return_value = 0
    mock_interface_class.return_value = mock_interface

    reader = PN5180(tty)
    with reader.start_comm(0x00, 0x80) as comm:
        assert comm is not None

    # RF should be turned off automatically
    mock_interface.rf_off.assert_called_once()


@patch("pn5180_tagomatic.pn5180.Interface")
def test_connect_iso14443a(mock_interface_class: Mock) -> None:
    """Test connecting to ISO 14443-A card."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface_class.return_value = mock_interface

    # Mock all operations
    mock_interface.load_rf_config.return_value = 0
    mock_interface.rf_on.return_value = 0
    mock_interface.rf_off.return_value = 0
    mock_interface.write_register_and_mask.return_value = 0
    mock_interface.write_register_or_mask.return_value = 0
    mock_interface.write_register.return_value = 0
    mock_interface.send_data.return_value = 0
    mock_interface.wait_for_irq.return_value = True

    # Mock ATQA response (4-byte UID)
    mock_interface.read_register.side_effect = [
        (0, 0x0002),  # RX_STATUS: 2 bytes available
        (0, 0x0005),  # RX_STATUS: 5 bytes for UID
        (0, 0x0001),  # RX_STATUS: 1 byte for SAK
    ]

    mock_interface.read_data.side_effect = [
        (0, [0x00, 0x00]),  # ATQA response
        (0, [0x01, 0x02, 0x03, 0x04, 0x04]),  # UID + BCC
        (0, [0x08]),  # SAK
    ]

    reader = PN5180(tty)
    with reader.start_comm(0x00, 0x80) as comm:
        card = comm.connect_iso14443a()
        assert card.uid == bytes([0x01, 0x02, 0x03, 0x04])


@patch("pn5180_tagomatic.pn5180.Interface")
def test_card_read_memory(mock_interface_class: Mock) -> None:
    """Test reading memory from non-MIFARE card."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface_class.return_value = mock_interface

    # Mock operations
    mock_interface.load_rf_config.return_value = 0
    mock_interface.rf_on.return_value = 0
    mock_interface.rf_off.return_value = 0
    mock_interface.write_register_and_mask.return_value = 0
    mock_interface.write_register_or_mask.return_value = 0
    mock_interface.write_register.return_value = 0
    mock_interface.send_data.return_value = 0
    mock_interface.wait_for_irq.return_value = True

    # Mock UID retrieval (4-byte UID for simplicity)
    mock_interface.read_register.side_effect = [
        (0, 0x0002),  # ATQA
        (0, 0x0005),  # UID
        (0, 0x0001),  # SAK
        (0, 0x0010),  # Memory read 1
        (0, 0x0010),  # Memory read 2
        (0, 0x0000),  # No more data
    ]

    mock_interface.read_data.side_effect = [
        (0, [0x00, 0x00]),  # ATQA (4-byte UID)
        (0, [0x01, 0x02, 0x03, 0x04, 0x04]),  # UID + BCC (4-byte)
        (0, [0x08]),  # SAK
        (0, [0xAA] * 16),  # Memory page 0
        (0, [0xBB] * 16),  # Memory page 4
    ]

    reader = PN5180(tty)
    with reader.start_comm(0x00, 0x80) as comm:
        card = comm.connect_iso14443a()
        memory = card.read_memory()
        assert len(memory) == 32  # 2 pages * 16 bytes each
        assert memory[:16] == bytes([0xAA] * 16)
        assert memory[16:32] == bytes([0xBB] * 16)


@patch("pn5180_tagomatic.pn5180.Interface")
def test_card_read_mifare_memory(mock_interface_class: Mock) -> None:
    """Test reading memory from MIFARE Classic card."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface_class.return_value = mock_interface

    # Mock operations
    mock_interface.load_rf_config.return_value = 0
    mock_interface.rf_on.return_value = 0
    mock_interface.rf_off.return_value = 0
    mock_interface.write_register_and_mask.return_value = 0
    mock_interface.write_register_or_mask.return_value = 0
    mock_interface.write_register.return_value = 0
    mock_interface.send_data.return_value = 0
    mock_interface.wait_for_irq.return_value = True
    mock_interface.mifare_authenticate.return_value = 0  # Success

    # Mock UID retrieval (4-byte UID)
    mock_interface.read_register.side_effect = [
        (0, 0x0002),  # ATQA
        (0, 0x0005),  # UID
        (0, 0x0001),  # SAK
        (0, 0x0010),  # Memory read
        (0, 0x0000),  # No more data
    ]

    mock_interface.read_data.side_effect = [
        (0, [0x00, 0x00]),  # ATQA
        (0, [0x01, 0x02, 0x03, 0x04, 0x04]),  # 4-byte UID + BCC
        (0, [0x08]),  # SAK
        (0, [0xCC] * 16),  # Memory content
    ]

    reader = PN5180(tty)
    with reader.start_comm(0x00, 0x80) as comm:
        card = comm.connect_iso14443a()
        memory = card.read_mifare_memory()
        assert len(memory) == 16
        assert memory == bytes([0xCC] * 16)
        mock_interface.mifare_authenticate.assert_called()
