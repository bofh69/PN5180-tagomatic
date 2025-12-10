# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""PN5180 RFID reader class using SimpleRPC protocol."""

from typing import Any

from serial import Serial

try:
    from simple_rpc import Interface  # type: ignore[import-untyped]
except ImportError as e:
    raise ImportError(
        "The 'arduino-simple-rpc' package is required. "
        "Install it with: pip install arduino-simple-rpc"
    ) from e


class PN5180:
    """PN5180 RFID reader interface.

    This class provides a Python interface to the PN5180 RFID reader
    running on a Raspberry Pi Pico via USB serial communication using
    the SimpleRPC protocol.

    Args:
        serial: An open pySerial Serial object connected to the device.

    Example:
        >>> import serial
        >>> from pn5180_tagomatic import PN5180
        >>> ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
        >>> reader = PN5180(ser)
        >>> reader.reset()
    """

    def __init__(self, serial: Serial) -> None:
        """Initialize the PN5180 reader.

        Args:
            serial: An open pySerial Serial object connected to the device.
        """
        self._serial = serial
        self._interface = Interface(serial)

    def reset(self) -> None:
        """Reset the PN5180 NFC frontend.

        This method calls the reset function on the Arduino device,
        which performs a hardware reset of the PN5180 module.
        """
        self._interface.reset()

    def close(self) -> None:
        """Close the serial connection."""
        if self._serial and self._serial.is_open:
            self._serial.close()

    def __enter__(self) -> "PN5180":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
