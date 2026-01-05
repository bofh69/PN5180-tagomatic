# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""PN5180 RFID reader class using SimpleRPC protocol."""

from __future__ import annotations

from enum import IntEnum
from typing import Any, cast

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


class Registers(IntEnum):
    """PN5180 register addresses."""

    SYSTEM_CONFIG = 0
    IRQ_ENABLE = 1
    IRQ_STATUS = 2
    IRQ_CLEAR = 3
    TRANSCEIVER_CONFIG = 4
    PADCONFIG = 5
    PADOUT = 7
    TIMER0_STATUS = 8
    TIMER1_STATUS = 9
    TIMER2_STATUS = 10
    TIMER0_RELOAD = 11
    TIMER1_RELOAD = 12
    TIMER2_RELOAD = 13
    TIMER0_CONFIG = 14
    TIMER1_CONFIG = 15
    TIMER2_CONFIG = 16
    RX_WAIT_CONFIG = 17
    CRC_RX_CONFIG = 18
    RX_STATUS = 19
    TX_UNDERSHOOT_CONFIG = 20
    TX_OVERSHOOT_CONFIG = 21
    TX_DATA_MOD = 22
    TX_WAIT_CONFIG = 23
    TX_CONFIG = 24
    CRC_TX_CONFIG = 25
    SIGPRO_CONFIG = 26
    SIGPRO_CM_CONFIG = 27
    SIGPRO_RM_CONFIG = 28
    RF_STATUS = 29
    AGC_CONFIG = 30
    AGC_VALUE = 31
    RF_CONTROL_TX = 32
    RF_CONTROL_TX_CLK = 33
    RF_CONTROL_RX = 34
    LD_CONTROL = 35
    SYSTEM_STATUS = 36
    TEMP_CONTROL = 37
    CECK_CARD_RESULT = 38
    DPC_CONFIG = 39
    EMD_CONTROL = 40
    ANT_CONTROL = 41


class ISO14443ACommand(IntEnum):
    """ISO 14443-A protocol command bytes."""

    ANTICOLLISION_CL1 = 0x93  # Anticollision/Select Cascade Level 1
    ANTICOLLISION_CL2 = 0x95  # Anticollision/Select Cascade Level 2
    ANTICOLLISION_CL3 = 0x97  # Anticollision/Select Cascade Level 3
    ANTICOLLISION = 0x20  # Anticollision command parameter
    READ = 0x30  # Read command
    REQA = 0x26  # Request A
    SELECT = 0x70  # Select command parameter
    WRITE = 0xA2  # Read command
    WUPA = 0x52  # Wake Up A


class ISO15693Command(IntEnum):
    """ISO 15693 protocol command bytes."""

    INVENTORY = 0x01  # Inventory command


class ISO14443ACard:
    """Represents a connected ISO 14443-A card.

    This class provides methods to interact with a card that has been
    successfully connected via the ISO 14443-A anticollision protocol.
    """

    def __init__(self, reader: PN5180Helper, uid: bytes) -> None:
        """Initialize ISO14443ACard.

        Args:
            reader: The PN5180 reader instance.
            uid: The card's UID.
        """
        self._reader = reader
        self._uid = uid

    @property
    def uid(self) -> bytes:
        """Get the card's UID."""
        return self._uid

    def read_memory(self, start_page: int = 0, num_pages: int = 255) -> bytes:
        """Read memory from a non-MIFARE Classic ISO 14443-A card.

        This method reads memory pages from ISO 14443-A cards like NTAG
        that don't require authentication.

        Args:
            start_page: Starting page number (default: 0).
            num_pages: Number of pages to read (default: 255).

        Returns:
            All read memory as a single bytes object.

        Raises:
            PN5180Error: If communication with the card fails.
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

    def write_memory(self, page: int, data: int) -> None:
        """Write memory to a non-MIFARE Classic ISO 14443-A card.

        This method writes memory pages from ISO 14443-A cards like NTAG
        that don't require authentication.

        Args:
            page: Starting page number (default: 0).
            data: 32-bit data to write to that page

        Raises:
            PN5180Error: If communication with the card fails.
        """
        self._reader.turn_on_crc()

        # Send READ command
        self._reader.send_data(
            0,
            bytes(
                [
                    ISO14443ACommand.WRITE,
                    page,
                    data & 255,
                    (data >> 8) & 255,
                    (data >> 16) & 255,
                    data >> 24,
                ]
            ),
        )

        # TODO Check ACK status...

    def read_mifare_memory(
        self,
        key_a: bytes | None = None,
        key_b: bytes | None = None,
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
        """
        if len(self._uid) != 4:
            raise ValueError(
                "read_mifare_memory requires a 4-byte UID (MIFARE Classic)"
            )

        DEFAULT_KEY = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
        if key_a is None:
            key_a = DEFAULT_KEY
        if key_b is None:
            key_b = DEFAULT_KEY

        if len(key_a) != 6:
            raise ValueError("key_a must be exactly 6 bytes")
        if len(key_b) != 6:
            raise ValueError("key_b must be exactly 6 bytes")

        self._reader.turn_on_crc()

        # Convert UID to 32-bit integer for authentication
        mifare_uid = (
            self._uid[3] << 24
            | self._uid[2] << 16
            | self._uid[1] << 8
            | self._uid[0]
        )

        memory_parts = []
        end_page = min(start_page + num_pages, 255)
        for page in range(start_page, end_page, 4):
            # Try KEY A
            retval_a = self._reader.mifare_authenticate(
                key_a, MifareKeyType.KEY_A, page, mifare_uid
            )
            if retval_a == 2:  # timeout
                break

            # Try KEY B if KEY A failed
            if retval_a != 0:
                retval_b = self._reader.mifare_authenticate(
                    key_b, MifareKeyType.KEY_B, page, mifare_uid
                )
                if retval_b == 2:  # timeout
                    break
                if retval_b != 0:
                    # Both keys failed, stop reading
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


class PN5180RFSession:
    """Manages RF communication session.

    This class handles the lifecycle of an RF communication session,
    ensuring that the RF field is turned off when the session ends.
    """

    def __init__(self, reader: PN5180Helper) -> None:
        """Initialize PN5180RFSession.

        Args:
            reader: The PN5180 reader instance.
        """
        self._reader = reader
        self._active = True

    def connect_iso14443a(self) -> ISO14443ACard:
        """Connect to an ISO 14443-A card.

        This method performs the ISO 14443-A anticollision protocol to
        retrieve the card's UID and returns a card object.

        Returns:
            ISO14443ACard object representing the connected card.

        Raises:
            PN5180Error: If communication with the card fails.
            ValueError: If the card's response is invalid.
            TimeoutError: If no card responds.
        """
        if not self._active:
            raise RuntimeError("Communication session is no longer active")

        uid = self._get_iso14443a_uid()
        return ISO14443ACard(self._reader, uid)

    def _get_iso14443a_uid(self) -> bytes:
        """Get the UID of an ISO 14443-A card using anticollision protocol.

        Returns:
            The card's UID as bytes.

        Raises:
            PN5180Error: If communication with the card fails.
            ValueError: If the card's response is invalid.
            TimeoutError: If no card responds.
        """
        self._reader.turn_off_crc()

        # Clear all IRQs
        self._reader.write_register(Registers.IRQ_CLEAR, 0x000FFFFF)

        # Configure IRQ ENABLE register, turn on RX_IRQ_EN
        self._reader.write_register_or_mask(Registers.IRQ_ENABLE, 1)

        self._reader.change_mode_to_transceiver()

        # Send WUPA command (0x52)
        self._reader.send_data(7, bytes([ISO14443ACommand.WUPA]))

        # Wait for reception
        self._reader.wait_for_irq(1000)

        # Read ATQA response
        rx_status = self._reader.read_register(Registers.RX_STATUS)
        data_len = rx_status & 511

        if data_len < 1:
            raise TimeoutError("No card answered to WUPA command")

        data = self._reader.read_data(data_len)
        uid_len = data[0] // 64

        uid = []
        cascade_tag = -1

        for cl in range(uid_len + 1):
            # 0 == 4 bytes, 1 == 7 bytes, 2 == 10 bytes

            # Send Anticollision CL X
            if cl == 0:
                data = self._reader.send_and_receive(
                    0,
                    bytes(
                        [
                            ISO14443ACommand.ANTICOLLISION_CL1,
                            ISO14443ACommand.ANTICOLLISION,
                        ]
                    ),
                )
            elif cl == 1:
                data = self._reader.send_and_receive(
                    0,
                    bytes(
                        [
                            ISO14443ACommand.ANTICOLLISION_CL2,
                            ISO14443ACommand.ANTICOLLISION,
                        ]
                    ),
                )
            elif cl == 2:
                data = self._reader.send_and_receive(
                    0,
                    bytes(
                        [
                            ISO14443ACommand.ANTICOLLISION_CL3,
                            ISO14443ACommand.ANTICOLLISION,
                        ]
                    ),
                )

            if len(data) < 5:
                raise ValueError(
                    f"Incomplete UID response received, data_len={len(data)}"
                )

            # Verify BCC (Block Check Character)
            bcc = data[0] ^ data[1] ^ data[2] ^ data[3]
            if bcc != data[4]:
                raise ValueError("Invalid BCC in UID response")

            # Verify cascade tag
            if 0 < cl < uid_len and data[0] != cascade_tag:
                raise ValueError("Wrong cascade tag in UID response")

            # Build UID
            if uid_len == cl:
                uid.append(data[0])
            elif cl == 0:
                cascade_tag = data[0]
            uid.append(data[1])
            uid.append(data[2])
            uid.append(data[3])

            # Send SELECT command
            self._reader.turn_on_crc()
            if cl == 0:
                _ = self._reader.send_and_receive(
                    0,
                    bytes(
                        [
                            ISO14443ACommand.ANTICOLLISION_CL1,
                            ISO14443ACommand.SELECT,
                        ]
                    )
                    + data,
                )
            elif cl == 1:
                _ = self._reader.send_and_receive(
                    0,
                    bytes(
                        [
                            ISO14443ACommand.ANTICOLLISION_CL2,
                            ISO14443ACommand.SELECT,
                        ]
                    )
                    + data,
                )
            elif cl == 2:
                _ = self._reader.send_and_receive(
                    0,
                    bytes(
                        [
                            ISO14443ACommand.ANTICOLLISION_CL3,
                            ISO14443ACommand.SELECT,
                        ]
                    )
                    + data,
                )

            # Read SAK (Select Acknowledge) - already received
            self._reader.turn_off_crc()

        return bytes(uid)

    def iso15693_inventory(
        self, slots: int = 16, mask_length: int = 0
    ) -> list[bytes]:
        """Perform ISO 15693 inventory to find tags.

        This method implements the ISO 15693 inventory protocol to discover
        tags in the RF field. It uses 16 slots by default for anticollision.

        Args:
            slots: Number of slots for anticollision (default: 16).
                Must be 16 for mask_length 0.
            mask_length: Length of mask (default: 0).

        Returns:
            List of UIDs found (bytes objects).

        Raises:
            PN5180Error: If communication fails.

        Example:
            >>> with reader.start_session(0x0D, 0x8D) as session:
            ...     uids = session.iso15693_inventory()
            ...     for uid in uids:
            ...         print(f"Found UID: {uid.hex(':')}")
        """
        if not self._active:
            raise RuntimeError("Communication session is no longer active")

        uids = []

        # Clear all IRQs
        self._reader.write_register(Registers.IRQ_CLEAR, 0x000FFFFF)

        # Set to transceiver mode
        self._reader.change_mode_to_transceiver()

        # Send ISO 15693 Inventory command
        # Format: [Flags, Command, Mask Length]
        # 0x06 = Inventory flag (1 slot mode bit not set for 16 slots)
        # 0x01 = Inventory command
        self._reader.send_data(
            0,
            bytes(
                [
                    0x06,
                    ISO15693Command.INVENTORY,
                    mask_length,
                ]
            ),
        )

        # Loop through all slots
        for _ in range(slots):
            # Read response if available
            rx_status = self._reader.read_register(Registers.RX_STATUS)
            if rx_status:
                how_many_bytes = rx_status & 511
                if how_many_bytes > 0:
                    data = self._reader.read_data(how_many_bytes)
                    # Check if no error flag (bit 0 clear)
                    if len(data) > 0 and (data[0] & 1) == 0:
                        # UID is in bytes 10:1:-1 (reversed)
                        if len(data) >= 10:
                            uid = bytes(data[9:1:-1])
                            uids.append(uid)

            # Prepare for next slot
            # Clear bit 7, 8 and 11 - only send EOF for next command
            self._reader.write_register_and_mask(
                Registers.TX_CONFIG, 0xFFFFFB3F
            )

            # Set state to TRANSCEIVE
            self._reader.change_mode_to_transceiver()

            # # Clear IRQs
            # self._reader.write_register(Registers.IRQ_CLEAR, 0x000FFFFF)

            # Send EOF
            self._reader.send_data(0, b"")

        return uids

    def close(self) -> None:
        """Close the communication session and turn off RF field."""
        if self._active:
            self._reader.rf_off()
            self._active = False

    def __enter__(self) -> PN5180RFSession:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()

    def __del__(self) -> None:
        """Cleanup when object is destroyed."""
        self.close()


class PN5180Proxy:
    """Low-level PN5180 RFID reader interface.

    This class provides direct access to the PN5180 RFID reader's RPC methods
    via the SimpleRPC protocol. It contains only the low-level methods that
    directly communicate with the hardware.

    Args:
        tty: The tty device path to communicate via.

    Example:
        >>> from pn5180_tagomatic import PN5180Proxy
        >>> reader = PN5180Proxy("/dev/ttyACM0")
        >>> reader.reset()
    """

    def __init__(self, tty: str) -> None:
        """Initialize the PN5180 low-level reader.

        Args:
            tty: The tty device path to communicate via.
        """
        self._interface = Interface(tty)

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
        result = cast(
            int, self._interface.write_register_and_mask(addr, value)
        )
        if result < 0:
            raise PN5180Error("write_register_and_mask", result)

    def write_register_multiple(
        self, elements: list[tuple[int, int, int]]
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
        result = cast(tuple[int, int], self._interface.read_register(addr))
        if result[0] < 0:
            raise PN5180Error("read_register", result[0])
        return result[1]

    def read_register_multiple(self, addrs: list[int]) -> list[int]:
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
            tuple[int, list[int]],
            self._interface.read_register_multiple(addrs),
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

    def switch_mode(self, mode: int, params: list[int]) -> None:
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
        self._validate_uint8(
            select_command_final_bits, "select_command_final_bits"
        )
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
        result = cast(
            int, self._interface.epc_retrieve_inventory_result_size()
        )
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
        result = cast(
            int, self._interface.load_rf_config(tx_config, rx_config)
        )
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
        if self._interface:
            self._interface.close()

    def __enter__(self) -> PN5180Proxy:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()


class PN5180Helper(PN5180Proxy):
    """Helper methods for PN5180.

    This class extends PN5180Proxy with convenience methods that build on
    the low-level RPC methods but are not direct RPC wrappers.
    """

    def turn_off_crc(self) -> None:
        """Turn off CRC for TX and RX.

        Disables CRC calculation and verification for transmission and reception.
        """
        # Turn off CRC for TX
        self.write_register_and_mask(Registers.CRC_TX_CONFIG, 0xFFFFFFFE)
        # Turn off CRC for RX
        self.write_register_and_mask(Registers.CRC_RX_CONFIG, 0xFFFFFFFE)

    def turn_on_crc(self) -> None:
        """Turn on CRC for TX and RX.

        Enables CRC calculation and verification for transmission and reception.
        """
        # Turn on CRC for TX
        self.write_register_or_mask(Registers.CRC_TX_CONFIG, 0x00000001)
        # Turn on CRC for RX
        self.write_register_or_mask(Registers.CRC_RX_CONFIG, 0x00000001)

    def change_mode_to_transceiver(self) -> None:
        """Change PN5180 mode to transceiver.

        Sets the device to Idle state first, then initiates Transceiver state.
        """
        # Set Idle state
        self.write_register_and_mask(Registers.SYSTEM_CONFIG, 0xFFFFFFF8)
        # Initiates Transceiver state
        self.write_register_or_mask(Registers.SYSTEM_CONFIG, 0x00000003)

    def send_and_receive(self, bits: int, data: bytes) -> bytes:
        """Send data and receive response.

        This is a common pattern that sends data, checks RX_STATUS register,
        and reads the response if available.

        Args:
            bits: Number of valid bits in final byte (byte: 0-255).
            data: Up to 260 bytes to send.

        Returns:
            Received data as bytes. Empty bytes() if no data was received.

        Raises:
            PN5180Error: If communication fails.
        """
        self.send_data(bits, data)
        rx_status = self.read_register(Registers.RX_STATUS)
        data_len = rx_status & 511

        if data_len == 0:
            return b""

        return self.read_data(data_len)


class PN5180:
    """High-level PN5180 RFID reader interface.

    This class provides a convenient, high-level API for common RFID operations.
    For direct hardware access, use the `ll` (low-level) attribute.

    Args:
        tty: The tty device path to communicate via.

    Attributes:
        ll: Low-level PN5180 interface for direct hardware access.

    Example:
        >>> from pn5180_tagomatic import PN5180
        >>> with PN5180("/dev/ttyACM0") as reader:
        ...     # High-level API (recommended)
        ...     with reader.start_session(0x00, 0x80) as comm:
        ...         card = comm.connect_iso14443a()
        ...         memory = card.read_memory()
        ...
        ...     # Low-level access if needed
        ...     reader.ll.write_register(addr, value)
    """

    def __init__(self, tty: str) -> None:
        """Initialize the PN5180 reader.

        Args:
            tty: The tty device path to communicate via.
        """
        self.ll = PN5180Helper(tty)

    def start_session(self, tx_config: int, rx_config: int) -> PN5180RFSession:
        """Start an RF communication session.

        This method loads the RF configuration and turns on the RF field,
        then returns a PN5180RFSession object that manages the session.
        The RF field will be automatically turned off when the session ends.

        Args:
            tx_config: TX configuration index (byte: 0-255, see table 32).
            rx_config: RX configuration index (byte: 0-255, see table 32).

        Returns:
            PN5180RFSession object for managing the session.

        Raises:
            PN5180Error: If the operation fails.

        Example:
            >>> reader = PN5180("/dev/ttyACM0")
            >>> with reader.start_session(0x00, 0x80) as comm:
            ...     card = comm.connect_iso14443a()
            ...     uid = card.uid
            ...     memory = card.read_memory()
        """
        self.ll.load_rf_config(tx_config, rx_config)
        self.ll.rf_on()
        return PN5180RFSession(self.ll)

    def close(self) -> None:
        """Close the serial connection."""
        self.ll.close()

    def __enter__(self) -> PN5180:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
