# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""PN5180 RFID reader class using SimpleRPC protocol."""

from enum import IntEnum
from typing import Any, List, Tuple, cast

from serial import Serial

try:
    from simple_rpc import Interface  # type: ignore[import-untyped]
except ImportError as e:
    raise ImportError(
        "The 'arduino-simple-rpc' package is required. "
        "Install it with: pip install arduino-simple-rpc"
    ) from e


class MifareKeyType(IntEnum):
    """Mifare authentication key types."""

    KEY_A = 0x60
    KEY_B = 0x61


class RegisterOperation(IntEnum):
    """Register write operations for write_register_multiple."""

    SET = 1
    OR = 2
    AND = 3


class PN5180:
    """PN5180 RFID reader interface.

    This class provides a Python interface to the PN5180 RFID reader
    running on a Raspberry Pi Pico via USB serial communication using
    the SimpleRPC protocol.

    Args:
        serial: An open pySerial Serial object connected to the device.

    Example:
        >>> from pn5180_tagomatic import PN5180
        >>> reader = PN5180("/dev/ttyACM0")
        >>> reader.reset()
    """

    def __init__(self, serial: Serial) -> None:
        """Initialize the PN5180 reader.

        Args:
            serial: An open pySerial Serial object connected to the device.
        """
        self._serial = serial
        self._interface = Interface(serial)

    @staticmethod
    def _validate_uint8(value: int, name: str) -> None:
        """Validate that a value is a valid uint8_t (0-255)."""
        if not isinstance(value, int) or value < 0 or value > 255:
            raise ValueError(f"{name} must be between 0 and 255")

    @staticmethod
    def _validate_uint16(value: int, name: str) -> None:
        """Validate that a value is a valid uint16_t (0-65535)."""
        if not isinstance(value, int) or value < 0 or value > 65535:
            raise ValueError(f"{name} must be between 0 and 65535")

    @staticmethod
    def _validate_uint32(value: int, name: str) -> None:
        """Validate that a value is a valid uint32_t (0-2^32-1)."""
        if not isinstance(value, int) or value < 0 or value > 4294967295:
            raise ValueError(f"{name} must be between 0 and 4294967295")

    def reset(self) -> None:
        """Reset the PN5180 NFC frontend.

        This method calls the reset function on the Arduino device,
        which performs a hardware reset of the PN5180 module.
        """
        self._interface.reset()

    def write_register(self, addr: int, value: int) -> int:
        """Write to a PN5180 register.

        Args:
            addr: Register address (uint8_t: 0-255).
            value: 32 bit value to write (uint32_t: 0-2^32-1).

        Returns:
            0 at success, < 0 at failure.
        """
        self._validate_uint8(addr, "addr")
        self._validate_uint32(value, "value")
        return cast(int, self._interface.write_register(addr, value))

    def write_register_or_mask(self, addr: int, value: int) -> int:
        """Write to a PN5180 register OR the old value.

        Args:
            addr: Register address (uint8_t: 0-255).
            value: 32 bit mask to OR (uint32_t: 0-2^32-1).

        Returns:
            0 at success, < 0 at failure.
        """
        self._validate_uint8(addr, "addr")
        self._validate_uint32(value, "value")
        return cast(int, self._interface.write_register_or_mask(addr, value))

    def write_register_and_mask(self, addr: int, value: int) -> int:
        """Write to a PN5180 register AND the old value.

        Args:
            addr: Register address (uint8_t: 0-255).
            value: 32 bit mask to AND (uint32_t: 0-2^32-1).

        Returns:
            0 at success, < 0 at failure.
        """
        self._validate_uint8(addr, "addr")
        self._validate_uint32(value, "value")
        return cast(int, self._interface.write_register_and_mask(addr, value))

    def write_register_multiple(
        self, elements: List[Tuple[int, int, int]]
    ) -> int:
        """Write to multiple PN5180 registers.

        Args:
            elements: List of (address, op, value/mask) tuples.
                     address: uint8_t (0-255)
                     op: RegisterOperation (1=SET, 2=OR, 3=AND)
                     value/mask: uint32_t (0-2^32-1)

        Returns:
            0 at success, < 0 at failure.
        """
        for i, (addr, op, value) in enumerate(elements):
            self._validate_uint8(addr, f"elements[{i}].address")
            if op not in (
                RegisterOperation.SET,
                RegisterOperation.OR,
                RegisterOperation.AND,
            ):
                raise ValueError(
                    f"elements[{i}].op must be RegisterOperation.SET (1), "
                    f"OR (2), or AND (3)"
                )
            self._validate_uint32(value, f"elements[{i}].value")
        return cast(int, self._interface.write_register_multiple(elements))

    def read_register(self, addr: int) -> Tuple[int, int]:
        """Read from a PN5180 register.

        Args:
            addr: Register address (uint8_t: 0-255).

        Returns:
            Tuple with status (0 at success, < 0 at failure) and
            32 bit register value.
        """
        self._validate_uint8(addr, "addr")
        return cast(Tuple[int, int], self._interface.read_register(addr))

    def read_register_multiple(self, addrs: List[int]) -> Tuple[int, List[int]]:
        """Read from multiple PN5180 registers.

        Args:
            addrs: List of up to 18 register addresses (each uint8_t: 0-255).

        Returns:
            Tuple with status (0 at success, < 0 at failure) and
            List of 32 bit register values.
        """
        if len(addrs) > 18:
            raise ValueError("addrs must contain at most 18 addresses")
        for i, addr in enumerate(addrs):
            self._validate_uint8(addr, f"addrs[{i}]")
        return cast(
            Tuple[int, List[int]], self._interface.read_register_multiple(addrs)
        )

    def write_eeprom(self, addr: int, values: bytes) -> int:
        """Write to the EEPROM.

        Args:
            addr: EEPROM address (uint8_t: 0-255).
            values: Up to 255 bytes to write.

        Returns:
            0 at success, < 0 at failure.
        """
        self._validate_uint8(addr, "addr")
        if len(values) > 255:
            raise ValueError("values must be at most 255 bytes")
        return cast(int, self._interface.write_eeprom(addr, list(values)))

    def read_eeprom(self, addr: int, length: int) -> Tuple[int, bytes]:
        """Read from the EEPROM.

        Args:
            addr: EEPROM address (uint8_t: 0-255).
            length: Number of bytes to read (uint8_t: 0-255).

        Returns:
            Tuple with status (0 at success, < 0 at failure) and
            bytes read.
        """
        self._validate_uint8(addr, "addr")
        self._validate_uint8(length, "length")
        result = self._interface.read_eeprom(addr, length)
        return (result[0], bytes(result[1]))

    def write_tx_data(self, values: bytes) -> int:
        """Write to tx buffer.

        Args:
            values: Up to 260 bytes to write.

        Returns:
            0 at success, < 0 at failure.
        """
        if len(values) > 260:
            raise ValueError("values must be at most 260 bytes")
        return cast(int, self._interface.write_tx_data(list(values)))

    def send_data(self, bits: int, values: bytes) -> int:
        """Write to TX buffer and send it.

        Args:
            bits: Number of valid bits in final byte (uint8_t: 0-255).
            values: Up to 260 bytes to send.

        Returns:
            0 at success, < 0 at failure.
        """
        self._validate_uint8(bits, "bits")
        if len(values) > 260:
            raise ValueError("values must be at most 260 bytes")
        return cast(int, self._interface.send_data(bits, list(values)))

    def read_data(self, length: int) -> Tuple[int, bytes]:
        """Read from RX buffer.

        Args:
            length: Number of bytes to read (max 508, uint16_t: 0-65535).

        Returns:
            Tuple with status (0 at success, < 0 at failure) and
            bytes read.
        """
        self._validate_uint16(length, "length")
        if length > 508:
            raise ValueError("length must be at most 508")
        result = self._interface.read_data(length)
        return (result[0], bytes(result[1]))

    def switch_mode(self, mode: int, params: List[int]) -> int:
        """Switch mode.

        Args:
            mode: Mode to switch to (uint8_t: 0=Standby, 1=LPCD, 2=Autocoll).
            params: List of mode-specific parameters (each uint8_t: 0-255).

        Returns:
            0 at success, < 0 at failure.
        """
        self._validate_uint8(mode, "mode")
        for i, param in enumerate(params):
            self._validate_uint8(param, f"params[{i}]")
        return cast(int, self._interface.switch_mode(mode, params))

    def mifare_authenticate(
        self, key: bytes, key_type: int, block_addr: int, uid: int
    ) -> int:
        """Authenticate to mifare card.

        Args:
            key: 6 byte key.
            key_type: MifareKeyType.KEY_A (0x60) or MifareKeyType.KEY_B (0x61).
            block_addr: Block address (uint8_t: 0-255).
            uid: 32 bit card UID (uint32_t: 0-2^32-1).

        Returns:
            0=authenticated, 1=permission denied, 2=timeout, < 0 at failure.
        """
        if len(key) != 6:
            raise ValueError("key must be exactly 6 bytes")
        if key_type not in (MifareKeyType.KEY_A, MifareKeyType.KEY_B):
            raise ValueError(
                f"key_type must be MifareKeyType.KEY_A (0x60) or "
                f"MifareKeyType.KEY_B (0x61), got {key_type:#x}"
            )
        self._validate_uint8(block_addr, "block_addr")
        self._validate_uint32(uid, "uid")
        return cast(
            int,
            self._interface.mifare_authenticate(
                list(key), key_type, block_addr, uid
            ),
        )

    def epc_inventory(
        self,
        select_command: bytes,
        select_command_final_bits: int,
        begin_round: bytes,
        timeslot_behavior: int,
    ) -> int:
        """Start EPC inventory algorithm.

        Args:
            select_command: Up to 39 bytes.
            select_command_final_bits: Number of valid bits in final byte
                                       (uint8_t: 0-255).
            begin_round: Exactly 3 bytes.
            timeslot_behavior: Timeslot behavior value (uint8_t: 0-255).

        Returns:
            0 at success, < 0 at failure.
        """
        if len(select_command) > 39:
            raise ValueError("select_command must be at most 39 bytes")
        self._validate_uint8(select_command_final_bits, "select_command_final_bits")
        if len(begin_round) != 3:
            raise ValueError("begin_round must be exactly 3 bytes")
        self._validate_uint8(timeslot_behavior, "timeslot_behavior")
        return cast(
            int,
            self._interface.epc_inventory(
                list(select_command),
                select_command_final_bits,
                list(begin_round),
                timeslot_behavior,
            ),
        )

    def epc_resume_inventory(self) -> int:
        """Continue EPC inventory algorithm.

        Returns:
            0 at success, < 0 at failure.
        """
        return cast(int, self._interface.epc_resume_inventory())

    def epc_retrieve_inventory_result_size(self) -> int:
        """Get result size from EPC algorithm.

        Returns:
            Result size in bytes, < 0 at failure.
        """
        return cast(int, self._interface.epc_retrieve_inventory_result_size())

    def load_rf_config(self, tx_config: int, rx_config: int) -> int:
        """Load RF config settings for RX/TX.

        Args:
            tx_config: TX configuration index (uint8_t: 0-255, see table 32).
            rx_config: RX configuration index (uint8_t: 0-255, see table 32).

        Returns:
            0 at success, < 0 at failure.
        """
        self._validate_uint8(tx_config, "tx_config")
        self._validate_uint8(rx_config, "rx_config")
        return cast(int, self._interface.load_rf_config(tx_config, rx_config))

    def rf_on(self, flags: int) -> int:
        """Turn on RF field.

        Args:
            flags: Control flags (uint8_t: 0-255).
                  bit0 turns off collision avoidance for ISO/IEC 18092.
                  bit1 use Active Communication mode.

        Returns:
            0 at success, < 0 at failure.
        """
        self._validate_uint8(flags, "flags")
        return cast(int, self._interface.rf_on(flags))

    def rf_off(self) -> int:
        """Turn off RF field.

        Returns:
            0 at success, < 0 at failure.
        """
        return cast(int, self._interface.rf_off())

    def is_irq_set(self) -> bool:
        """Is the IRQ pin set.

        Returns:
            True if IRQ is set.
        """
        return cast(bool, self._interface.is_irq_set())

    def wait_for_irq(self, timeout_ms: int) -> bool:
        """Wait up to a timeout value for the IRQ to be set.

        Args:
            timeout_ms: Time in milliseconds to wait (uint16_t: 0-65535).

        Returns:
            True if IRQ is set.
        """
        self._validate_uint16(timeout_ms, "timeout_ms")
        return cast(bool, self._interface.wait_for_irq(timeout_ms))

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
