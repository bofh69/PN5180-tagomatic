# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the PN5180 class."""

from unittest.mock import MagicMock, Mock, patch

from pn5180_tagomatic import PN5180


@patch("pn5180_tagomatic.pn5180.Interface")
def test_pn5180_init(mock_interface_class: Mock) -> None:
    """Test PN5180 initialization."""
    mock_serial = Mock()
    reader = PN5180(mock_serial)
    assert reader is not None
    mock_interface_class.assert_called_once_with(mock_serial)


@patch("pn5180_tagomatic.pn5180.Interface")
def test_pn5180_reset(mock_interface_class: Mock) -> None:
    """Test PN5180 reset method."""
    mock_serial = Mock()
    mock_interface = MagicMock()
    mock_interface_class.return_value = mock_interface

    reader = PN5180(mock_serial)
    reader.reset()

    mock_interface.reset.assert_called_once()


@patch("pn5180_tagomatic.pn5180.Interface")
def test_pn5180_close(mock_interface_class: Mock) -> None:
    """Test PN5180 close method."""
    mock_serial = Mock()
    mock_serial.is_open = True

    reader = PN5180(mock_serial)
    reader.close()

    mock_serial.close.assert_called_once()


@patch("pn5180_tagomatic.pn5180.Interface")
def test_pn5180_context_manager(mock_interface_class: Mock) -> None:
    """Test PN5180 context manager."""
    mock_serial = Mock()
    mock_serial.is_open = True

    with PN5180(mock_serial) as reader:
        assert reader is not None

    mock_serial.close.assert_called_once()
