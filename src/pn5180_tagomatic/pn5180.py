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


class PN5180Error(Exception):
    """Exception raised when a PN5180 operation fails."""

    def __init__(self, operation: str, error_code: int) -> None:
        """Initialize PN5180Error.

        Args:
            operation: Name of the operation that failed.
            error_code: The error code returned by the operation.
        """
        self.operation = operation
        self.error_code = error_code
        super().__init__(f"{operation} failed with error code {error_code}")


class MifareKeyType(IntEnum):
    """Mifare authentication key types."""

    KEY_A = 0x60
    KEY_B = 0x61


class RegisterOperation(IntEnum):
    """Register write operations for write_register_multiple."""

    SET = 1
    OR = 2
    AND = 3


class SwitchMode(IntEnum):
    """PN5180 operating modes."""

    STANDBY = 0
    LPCD = 1
    AUTOCOLL = 2


class TimeslotBehavior(IntEnum):
    """EPC inventory timeslot behavior options."""

    MAX_TIMESLOTS = 0  # Response contains max. number of time slots
    SINGLE_TIMESLOT = 1  # Response contains only one timeslot
    SINGLE_WITH_HANDLE = 2  # Single timeslot with card handle if valid


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

    def write_register(self, addr: int, value: int) -> None:
        """Write to a PN5180 register.

        Args:
            addr: Register address (byte: 0-255).
            value: 32-bit value to write (0-2^32-1).

        Raises:
            PN5180Error: If the operation fails.
        """
        self._validate_uint8(addr, "addr")
        self._validate_uint32(value, "value")
        result = cast(int, self._interface.write_register(addr, value))
        if result < 0:
            raise PN5180Error("write_register", result)

    def write_register_or_mask(self, addr: int, value: int) -> None:
        """Write to a PN5180 register OR the old value.

        Args:
            addr: Register address (byte: 0-255).
            value: 32-bit mask to OR (0-2^32-1).

        Raises:
            PN5180Error: If the operation fails.
        """
        self._validate_uint8(addr, "addr")
        self._validate_uint32(value, "value")
        result = cast(int, self._interface.write_register_or_mask(addr, value))
        if result < 0:
            raise PN5180Error("write_register_or_mask", result)

    def write_register_and_mask(self, addr: int, value: int) -> None:
        """Write to a PN5180 register AND the old value.

        Args:
            addr: Register address (byte: 0-255).
            value: 32-bit mask to AND (0-2^32-1).

        Raises:
            PN5180Error: If the operation fails.
        """
        self._validate_uint8(addr, "addr")
        self._validate_uint32(value, "value")
        result = cast(int, self._interface.write_register_and_mask(addr, value))
        if result < 0:
            raise PN5180Error("write_register_and_mask", result)

    def write_register_multiple(
        self, elements: List[Tuple[int, int, int]]
    ) -> None:
        """Write to multiple PN5180 registers.

        Args:
            elements: List of (address, op, value/mask) tuples.
                     address: byte (0-255)
                     op: RegisterOperation (1=SET, 2=OR, 3=AND)
                     value/mask: 32-bit value (0-2^32-1)

        Raises:
            PN5180Error: If the operation fails.
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
        result = cast(int, self._interface.write_register_multiple(elements))
        if result < 0:
            raise PN5180Error("write_register_multiple", result)

    def read_register(self, addr: int) -> int:
        """Read from a PN5180 register.

        Args:
            addr: Register address (byte: 0-255).

        Returns:
            32-bit register value.

        Raises:
            PN5180Error: If the operation fails.
        """
        self._validate_uint8(addr, "addr")
        result = cast(Tuple[int, int], self._interface.read_register(addr))
        if result[0] < 0:
            raise PN5180Error("read_register", result[0])
        return result[1]

    def read_register_multiple(self, addrs: List[int]) -> List[int]:
        """Read from multiple PN5180 registers.

        Args:
            addrs: List of up to 18 register addresses (each byte: 0-255).

        Returns:
            List of 32-bit register values.

        Raises:
            PN5180Error: If the operation fails.
        """
        if len(addrs) > 18:
            raise ValueError("addrs must contain at most 18 addresses")
        for i, addr in enumerate(addrs):
            self._validate_uint8(addr, f"addrs[{i}]")
        result = cast(
            Tuple[int, List[int]], self._interface.read_register_multiple(addrs)
        )
        if result[0] < 0:
            raise PN5180Error("read_register_multiple", result[0])
        return result[1]

    def write_eeprom(self, addr: int, values: bytes) -> None:
        """Write to the EEPROM.

        Args:
            addr: EEPROM address (byte: 0-255).
            values: Up to 255 bytes to write.

        Raises:
            PN5180Error: If the operation fails.
        """
        self._validate_uint8(addr, "addr")
        if len(values) > 255:
            raise ValueError("values must be at most 255 bytes")
        result = cast(int, self._interface.write_eeprom(addr, list(values)))
        if result < 0:
            raise PN5180Error("write_eeprom", result)

    def read_eeprom(self, addr: int, length: int) -> bytes:
        """Read from the EEPROM.

        Args:
            addr: EEPROM address (byte: 0-255).
            length: Number of bytes to read (byte: 0-255).

        Returns:
            Bytes read from EEPROM.

        Raises:
            PN5180Error: If the operation fails.
        """
        self._validate_uint8(addr, "addr")
        self._validate_uint8(length, "length")
        result = self._interface.read_eeprom(addr, length)
        if result[0] < 0:
            raise PN5180Error("read_eeprom", result[0])
        return bytes(result[1])

    def write_tx_data(self, values: bytes) -> None:
        """Write to tx buffer.

        Args:
            values: Up to 260 bytes to write.

        Raises:
            PN5180Error: If the operation fails.
        """
        if len(values) > 260:
            raise ValueError("values must be at most 260 bytes")
        result = cast(int, self._interface.write_tx_data(list(values)))
        if result < 0:
            raise PN5180Error("write_tx_data", result)

    def send_data(self, bits: int, values: bytes) -> None:
        """Write to TX buffer and send it.

        Args:
            bits: Number of valid bits in final byte (byte: 0-255).
            values: Up to 260 bytes to send.

        Raises:
            PN5180Error: If the operation fails.
        """
        self._validate_uint8(bits, "bits")
        if len(values) > 260:
            raise ValueError("values must be at most 260 bytes")
        result = cast(int, self._interface.send_data(bits, list(values)))
        if result < 0:
            raise PN5180Error("send_data", result)

    def read_data(self, length: int) -> bytes:
        """Read from RX buffer.

        Args:
            length: Number of bytes to read (max 508, 16-bit value: 0-65535).

        Returns:
            Bytes read from RX buffer.

        Raises:
            PN5180Error: If the operation fails.
        """
        self._validate_uint16(length, "length")
        if length > 508:
            raise ValueError("length must be at most 508")
        result = self._interface.read_data(length)
        if result[0] < 0:
            raise PN5180Error("read_data", result[0])
        return bytes(result[1])

    def switch_mode(self, mode: int, params: List[int]) -> None:
        """Switch mode.

        Args:
            mode: Operating mode (SwitchMode.STANDBY, LPCD, or AUTOCOLL).
            params: List of mode-specific parameters (each byte: 0-255).

        Raises:
            PN5180Error: If the operation fails.
        """
        if mode not in (
            SwitchMode.STANDBY,
            SwitchMode.LPCD,
            SwitchMode.AUTOCOLL,
        ):
            raise ValueError(
                f"mode must be SwitchMode.STANDBY (0), LPCD (1), "
                f"or AUTOCOLL (2), got {mode}"
            )
        for i, param in enumerate(params):
            self._validate_uint8(param, f"params[{i}]")
        result = cast(int, self._interface.switch_mode(mode, params))
        if result < 0:
            raise PN5180Error("switch_mode", result)

    def mifare_authenticate(
        self, key: bytes, key_type: int, block_addr: int, uid: int
    ) -> int:
        """Authenticate to mifare card.

        Args:
            key: 6 byte key.
            key_type: MifareKeyType.KEY_A (0x60) or MifareKeyType.KEY_B (0x61).
            block_addr: Block address (byte: 0-255).
            uid: 32-bit card UID (0-2^32-1).

        Returns:
            Authentication result: 0=authenticated, 1=permission denied, 2=timeout.

        Raises:
            PN5180Error: If the operation fails with error < 0.
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
        result = cast(
            int,
            self._interface.mifare_authenticate(
                list(key), key_type, block_addr, uid
            ),
        )
        if result < 0:
            raise PN5180Error("mifare_authenticate", result)
        return result

    def epc_inventory(
        self,
        select_command: bytes,
        select_command_final_bits: int,
        begin_round: bytes,
        timeslot_behavior: int,
    ) -> None:
        """Start EPC inventory algorithm.

        Args:
            select_command: Up to 39 bytes.
            select_command_final_bits: Number of valid bits in final byte (byte: 0-255).
            begin_round: Exactly 3 bytes.
            timeslot_behavior: Timeslot behavior (TimeslotBehavior enum):
                - MAX_TIMESLOTS (0): NextSlot issued until buffer full
                - SINGLE_TIMESLOT (1): Algorithm pauses after one timeslot
                - SINGLE_WITH_HANDLE (2): Req_Rn issued if valid tag response

        Raises:
            PN5180Error: If the operation fails.
        """
        if len(select_command) > 39:
            raise ValueError("select_command must be at most 39 bytes")
        self._validate_uint8(select_command_final_bits, "select_command_final_bits")
        if len(begin_round) != 3:
            raise ValueError("begin_round must be exactly 3 bytes")
        if timeslot_behavior not in (
            TimeslotBehavior.MAX_TIMESLOTS,
            TimeslotBehavior.SINGLE_TIMESLOT,
            TimeslotBehavior.SINGLE_WITH_HANDLE,
        ):
            raise ValueError(
                f"timeslot_behavior must be TimeslotBehavior.MAX_TIMESLOTS (0), "
                f"SINGLE_TIMESLOT (1), or SINGLE_WITH_HANDLE (2), "
                f"got {timeslot_behavior}"
            )
        result = cast(
            int,
            self._interface.epc_inventory(
                list(select_command),
                select_command_final_bits,
                list(begin_round),
                timeslot_behavior,
            ),
        )
        if result < 0:
            raise PN5180Error("epc_inventory", result)

    def epc_resume_inventory(self) -> None:
        """Continue EPC inventory algorithm.

        Raises:
            PN5180Error: If the operation fails.
        """
        result = cast(int, self._interface.epc_resume_inventory())
        if result < 0:
            raise PN5180Error("epc_resume_inventory", result)

    def epc_retrieve_inventory_result_size(self) -> int:
        """Get result size from EPC algorithm.

        Returns:
            Result size in bytes.

        Raises:
            PN5180Error: If the operation fails.
        """
        result = cast(int, self._interface.epc_retrieve_inventory_result_size())
        if result < 0:
            raise PN5180Error("epc_retrieve_inventory_result_size", result)
        return result

    def load_rf_config(self, tx_config: int, rx_config: int) -> None:
        """Load RF config settings for RX/TX.

        Args:
            tx_config: TX configuration index (byte: 0-255, see table 32).
            rx_config: RX configuration index (byte: 0-255, see table 32).

        Raises:
            PN5180Error: If the operation fails.
        """
        self._validate_uint8(tx_config, "tx_config")
        self._validate_uint8(rx_config, "rx_config")
        result = cast(int, self._interface.load_rf_config(tx_config, rx_config))
        if result < 0:
            raise PN5180Error("load_rf_config", result)

    def rf_on(
        self,
        disable_collision_avoidance: bool = False,
        use_active_communication: bool = False,
    ) -> None:
        """Turn on RF field.

        Args:
            disable_collision_avoidance: Turn off collision avoidance for ISO/IEC 18092.
            use_active_communication: Use Active Communication mode.

        Raises:
            PN5180Error: If the operation fails.
        """
        flags = 0
        if disable_collision_avoidance:
            flags |= 0x01
        if use_active_communication:
            flags |= 0x02
        result = cast(int, self._interface.rf_on(flags))
        if result < 0:
            raise PN5180Error("rf_on", result)

    def rf_off(self) -> None:
        """Turn off RF field.

        Raises:
            PN5180Error: If the operation fails.
        """
        result = cast(int, self._interface.rf_off())
        if result < 0:
            raise PN5180Error("rf_off", result)

    def is_irq_set(self) -> bool:
        """Is the IRQ pin set.

        Returns:
            True if IRQ is set.
        """
        return cast(bool, self._interface.is_irq_set())

    def wait_for_irq(self, timeout_ms: int) -> bool:
        """Wait up to a timeout value for the IRQ to be set.

        Args:
            timeout_ms: Time in milliseconds to wait (16-bit value: 0-65535).

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
