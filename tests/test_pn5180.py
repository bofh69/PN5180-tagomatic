# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Tests for the PN5180 class."""

from unittest.mock import MagicMock, Mock, patch

from pn5180_tagomatic import PN5180


@patch("pn5180_tagomatic.pn5180.Interface")
def test_pn5180_init(mock_interface_class: Mock) -> None:
    """Test PN5180 initialization."""
    tty = "/dev/ttyACM0"
    reader = PN5180(tty)
    assert reader is not None
    mock_interface_class.assert_called_once_with(tty)


@patch("pn5180_tagomatic.pn5180.Interface")
def test_pn5180_reset(mock_interface_class: Mock) -> None:
    """Test PN5180 reset method."""
    tty = "/dev/ttyACM0"
    mock_interface = MagicMock()
    mock_interface_class.return_value = mock_interface

    reader = PN5180(tty)
    reader.reset()

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
