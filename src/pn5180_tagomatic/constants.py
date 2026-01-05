# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Constants and enumerations for PN5180 RFID reader."""

from enum import IntEnum


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


class ISO15693Error(Exception):
    """Exception raised when an ISO 15693 command returns an error response."""

    def __init__(self, command: int, error_code: int, response_data: bytes) -> None:
        """Initialize ISO15693Error.

        Args:
            command: The ISO 15693 command that triggered the error (8-bit value).
            error_code: The error code from the tag's error response.
            response_data: The full error response data from the tag.
        """
        self.command = command
        self.error_code = error_code
        self.response_data = response_data
        super().__init__(
            f"ISO 15693 command 0x{command:02X} failed "
            f"with error code 0x{error_code:02X}"
        )


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
    WRITE = 0xA2  # Write command
    WUPA = 0x52  # Wake Up A


class ISO15693Command(IntEnum):
    """ISO 15693 protocol command bytes."""

    GET_SYSTEM_INFORMATION = 0x2B
    GET_MULTIPLE_BLOCK_SECURITY_STATUS = 0x2C
    INVENTORY = 0x01
    LOCK_BLOCK = 0x22
    READ_SINGLE_BLOCK = 0x20
    READ_MULTIPLE_BLOCKS = 0x23
    RESET_TO_READY = 0x26
    SELECT = 0x25
    STAY_QUIET = 0x02
    WRITE_SINGLE_BLOCK = 0x21
    WRITE_MULTIPLE_BLOCKS = 0x24
