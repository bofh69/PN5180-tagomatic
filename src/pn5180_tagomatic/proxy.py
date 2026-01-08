# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Low-level PN5180 proxy and helper classes."""

from __future__ import annotations

from typing import Any, cast

try:
    from simple_rpc import Interface  # type: ignore[import-untyped]
except ImportError as e:
    raise ImportError(
        "The 'arduino-simple-rpc' package is required. "
        "Install it with: pip install arduino-simple-rpc"
    ) from e

from .constants import (
    ISO15693Error,
    MifareKeyType,
    PN5180Error,
    RegisterOperation,
    Registers,
    SwitchMode,
    TimeslotBehavior,
)

MAX_TIMEOUT = 200  # Maximum time to wait for response


class PN5180Proxy:  # pylint: disable=too-many-public-methods
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

    # pylint: disable=no-member

    def reset(self) -> None:
        """Reset the PN5180 NFC frontend.

        This method calls the reset function on the Arduino device,
        which performs a hardware reset of the PN5180 module.
        """
        self._interface.reset()

    def test_it(self) -> int:
        """Run a basic self-test on the PN5180 NFC frontend.

        This method invokes the underlying Arduino ``test_it`` RPC to verify
        communication with the PN5180 and perform a simple hardware check.

        Returns:
            int: Status code from the Arduino implementation:
                * ``0`` indicates success.
                * A negative value indicates a failure, with the exact
                  meaning determined by the Arduino firmware.

        Raises:
            Exception: Any communication or transport-related exception
                raised by the underlying :class:`simple_rpc.Interface`.
        """
        return cast(int, self._interface.test_it())

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
        result = cast(
            int,
            self._interface.write_register(addr, value),
        )
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
        result = cast(
            int,
            self._interface.write_register_or_mask(addr, value),
        )
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
            int,
            self._interface.write_register_and_mask(addr, value),
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
            int,
            self._interface.epc_retrieve_inventory_result_size(),
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
            int,
            self._interface.load_rf_config(tx_config, rx_config),
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
        return cast(
            bool,
            self._interface.wait_for_irq(timeout_ms),
        )

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

    def turn_off_rx_crc(self) -> None:
        """Turn off CRC for RX.

        Disables CRC verification for reception.
        """
        # Turn off CRC for RX
        self.write_register_and_mask(Registers.CRC_RX_CONFIG, 0xFFFFFFFE)

    def turn_off_tx_crc(self) -> None:
        """Turn off CRC for TX.

        Disables CRC calculation for transmission.
        """
        # Turn off CRC for TX
        self.write_register_and_mask(Registers.CRC_TX_CONFIG, 0xFFFFFFFE)

    def turn_off_crc(self) -> None:
        """Turn off CRC for TX and RX. Sets RX_BIT_ALIGN to 0

        Disables CRC calculation and verification for transmission and reception.
        """
        self.set_rx_crc_and_first_bit(False, 0)
        self.turn_off_tx_crc()

    def turn_on_rx_crc(self) -> None:
        """Turn on CRC for RX.

        Enables CRC verification for reception.
        """
        # Turn on CRC for RX
        self.write_register_or_mask(Registers.CRC_RX_CONFIG, 0x00000001)

    def turn_on_tx_crc(self) -> None:
        """Turn on CRC for TX.

        Enables CRC calculation for transmission.
        """
        # Turn on CRC for TX
        self.write_register_or_mask(Registers.CRC_TX_CONFIG, 0x00000001)

    def set_rx_crc_and_first_bit(self, on: bool, bit_start: int = 0) -> None:
        """Set RX_CRC_ENABLE and RX_BIT_ALIGN fields

        Enables/disables CRC calculation for transmissions,
        sets the RX_BIT_ALIGN field as needed for the first
        received bits.
        """
        self.write_register_and_mask(Registers.CRC_RX_CONFIG, 0xFFFFFE3E)
        flags = bit_start << 6
        if on:
            flags |= 1
        self.write_register_or_mask(Registers.CRC_RX_CONFIG, flags)

    def turn_on_crc(self) -> None:
        """Turn on CRC for TX and RX. Sets RX_BIT_ALIGN to 0

        Enables CRC calculation and verification for transmission and reception.
        """
        self.set_rx_crc_and_first_bit(True, 0)
        self.turn_on_tx_crc()

    def change_mode_to_transceiver(self) -> None:
        """Change PN5180 mode to transceiver.

        Sets the device to Idle state first, then initiates Transceiver state.
        """
        # Set Idle state
        self.write_register_and_mask(Registers.SYSTEM_CONFIG, 0xFFFFFFF8)
        # Initiates Transceiver state
        self.write_register_or_mask(Registers.SYSTEM_CONFIG, 0x00000003)

    def clear_rx_irq(self) -> None:
        """Clear RX IRQ in IRQ_STATUS register."""
        self.write_register(Registers.IRQ_CLEAR, 1)

    def enable_only_rx_irq(self) -> None:
        """Enable only RX IRQ in IRQ_ENABLE register."""
        self.write_register(Registers.IRQ_ENABLE, 1)

    def disable_all_irqs(self) -> None:
        """Disable all IRQs in IRQ_ENABLE register."""
        self.write_register(Registers.IRQ_ENABLE, 0)

    def get_rx_data_len(self) -> int:
        """Read the RX_STATUS register and get the length bits."""
        # TODO Verify other bits?
        rx_status = self.read_register(Registers.RX_STATUS)
        data_len = rx_status & 511
        return data_len

    def read_received_data(self) -> bytes:
        """Returns received data, empty bytes, if none."""
        data_len = self.get_rx_data_len()
        if data_len == 0:
            return b""
        return self.read_data(data_len)

    def send_and_receive(self, bits: int, data: bytes) -> bytes:
        """Send data and receive response.

        Args:
            bits: Number of valid bits in final byte (byte: 0-255).
            data: Up to 260 bytes to send.

        Returns:
            Received data as bytes. Empty bytes() if no data was received.

        Raises:
            PN5180Error: If communication fails.
        """
        self.clear_rx_irq()
        self.enable_only_rx_irq()

        self.send_data(bits, data)

        if not self.wait_for_irq(MAX_TIMEOUT):
            raise TimeoutError(f"No answer for {data[0]:x} request.")

        self.disable_all_irqs()
        self.clear_rx_irq()

        return self.read_received_data()

    def send_15693_request(
        self,  # pylint: disable=too-many-arguments
        command: int,
        parameters: bytes,
        is_inventory: bool = False,
        slow_rate: bool = False,
        dual_sub_carrier: bool = False,
        protocol_extension: bool = False,
        to_selected: bool = False,
        option_flag: bool = False,
        uid: bytes | None = None,
    ) -> None:
        """Send ISO/IEC 15693 Request

        Args:
            command: The command's 8-bit value.
            parameters: Up to 250 bytes to send.
            is_inventory: Only set for the INVENTORY command.
            slow_rate: Use low data rate.
            dual_sub_carrier: Use dual sub-carrier
            protocol_extension: Sets that bit in flags.
            to_selected: Sets Select flag bit in flags.
            option_flag: Sets that bit in flags.
            uid: Sets the UID flag bit and includes the uid after command.

        Raises:
            PN5180Error: If communication fails.
        """

        self._validate_uint8(command, "command")
        flags = 0
        if dual_sub_carrier:
            flags |= 1
        if not slow_rate:
            flags |= 2
        if is_inventory:
            flags |= 4
        if protocol_extension:
            flags |= 8
        if to_selected:
            if uid:
                raise ValueError("Can't combine UID with to_selected")
            flags |= 16
        if uid:
            flags |= 32
        if option_flag:
            flags |= 64

        frame = bytes([flags, command])
        if uid:
            frame += uid[::-1]
        frame += parameters

        # print(f"Sending frame {frame.hex(' ')}")

        self.send_data(0, frame)

    def send_and_receive_15693(
        self,  # pylint: disable=too-many-arguments
        command: int,
        parameters: bytes,
        is_inventory: bool = False,
        slow_rate: bool = False,
        dual_sub_carrier: bool = False,
        protocol_extension: bool = False,
        to_selected: bool = False,
        option_flag: bool = False,
        uid: bytes | None = None,
    ) -> bytes:
        """Send ISO/IEC 15693 Request

        Args:
            command: The command's 8-bit value.
            parameters: Up to 250 bytes to send.
            is_inventory: Only set for the INVENTORY command.
            slow_rate: Use low data rate.
            dual_sub_carrier: Use dual sub-carrier
            protocol_extension: Sets that bit in flags.
            to_selected: Sets Select flag bit in flags.
            option_flag: Sets that bit in flags.
            uid: Sets the UID flag bit and includes the uid after command.

        Returns:
            Received data as bytes. Empty bytes() if no data was received.

        Raises:
            ISO15693Error: If the tag returns an error response.
            TimeoutError: If no response is received within timeout.
            PN5180Error: If communication with the PN5180 fails.
        """
        self.clear_rx_irq()
        self.enable_only_rx_irq()

        self.send_15693_request(
            command,
            parameters,
            is_inventory=is_inventory,
            slow_rate=slow_rate,
            dual_sub_carrier=dual_sub_carrier,
            protocol_extension=protocol_extension,
            to_selected=to_selected,
            option_flag=option_flag,
            uid=uid,
        )
        if not self.wait_for_irq(MAX_TIMEOUT):
            raise TimeoutError(f"No answer for 0x{command:02x} request.")

        self.disable_all_irqs()
        self.clear_rx_irq()

        data = self.read_received_data()

        if len(data) and data[0] & 1:
            error_code = 0xFF
            if len(data) >= 2:
                error_code = data[1]
            raise ISO15693Error(
                command=command,
                error_code=error_code,
                response_data=data,
            )
        return data

    def send_and_wait_for_ack(self, bits: int, data: bytes) -> bytes:
        """Send a request and wait for an ACK/NACK response.

        Args:
            bits: Number of valid bits in the data to send.
            data: Payload bytes to transmit.

        Returns:
            The raw response bytes received from the PN5180.

        Raises:
            TimeoutError: If no response is received within the configured timeout.
        """
        self.turn_on_tx_crc()
        self.turn_off_rx_crc()
        self.change_mode_to_transceiver()

        self.clear_rx_irq()
        self.enable_only_rx_irq()

        self.send_data(bits, data)

        if not self.wait_for_irq(MAX_TIMEOUT):
            raise TimeoutError(f"No answer for 0x{data[0]:02x} request.")

        self.clear_rx_irq()
        self.disable_all_irqs()

        data = self.read_received_data()
        return data
