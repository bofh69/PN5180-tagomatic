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

    def __init__(
        self, command: int, error_code: int, response_data: bytes
    ) -> None:
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


class MemoryWriteError(Exception):
    """Exception raised when memory_write returns an error response from card."""

    def __init__(
        self, offset: int, error_code: int, response_data: bytes
    ) -> None:
        """Initialize MemoryWriteError.

        Args:
            offset: The offset that was written to.
            error_code: The error code from the tag's error response.
            response_data: The full error response data from the tag.
        """
        self.offset = offset
        self.error_code = error_code
        self.response_data = response_data
        super().__init__(
            f"MemoryWrite command failed at offset {offset} "
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


class TxProtocol(IntEnum):
    """TX Protocol configuration number"""

    ISO_14443_A_106 = 0x00
    ISO_14443_A_212 = 0x01
    ISO_14443_A_424 = 0x02
    ISO_14443_A_848 = 0x03

    ISO_14443_B_106 = 0x04
    ISO_14443_B_212 = 0x05
    ISO_14443_B_424 = 0x06
    ISO_14443_B_848 = 0x07

    NFC_PI_106 = 0x00
    NFC_PI_212 = 0x08
    NFC_PI_424 = 0x09

    FELICA_212 = 0x08
    FELICA_424 = 0x09

    NFC_ACTIVE_INITIATOR_106 = 0x0A
    NFC_ACTIVE_INITIATOR_212 = 0x0B
    NFC_ACTIVE_INITIATOR_424 = 0x0C

    ISO_15693_ASK100_26 = 0x0D
    ISO_15693_ASK10_26 = 0x0E

    ISO_18003M3_MANCH_424_4 = 0x0F
    ISO_18003M3_MANCH_424_2 = 0x10
    ISO_18003M3_MANCH_848_4 = 0x11
    ISO_18003M3_MANCH_848_2 = 0x12
    ISO_18003M3_MANCH_424_4_106 = 0x13

    ISO_14443_A_PICC_212 = 0x14
    ISO_14443_A_PICC_424 = 0x15
    ISO_14443_A_PICC_848 = 0x16

    NFC_PASSIVE_TARGET_212 = 0x17
    NFC_PASSIVE_TARGET_424 = 0x18

    NFC_ACTIVE_TARGET_106 = 0x19
    NFC_ACTIVE_TARGET_212 = 0x1A
    NFC_ACTIVE_TARGET_424 = 0x1B
    GTM = 0x1C


class RxProtocol(IntEnum):
    """RX Protocol configuration number"""

    ISO_14443_A_106 = 0x80
    ISO_14443_A_212 = 0x81
    ISO_14443_A_424 = 0x82
    ISO_14443_A_848 = 0x83

    ISO_14443_B_106 = 0x84
    ISO_14443_B_212 = 0x85
    ISO_14443_B_424 = 0x86
    ISO_14443_B_848 = 0x87

    NFC_PI_106 = 0x80
    NFC_PI_212 = 0x88
    NFC_PI_424 = 0x89

    FELICA_212 = 0x88
    FELICA_424 = 0x89

    NFC_ACTIVE_INITIATOR_106 = 0x8A
    NFC_ACTIVE_INITIATOR_212 = 0x8B
    NFC_ACTIVE_INITIATOR_424 = 0x8C

    ISO_15693_26 = 0x8D
    ISO_15693_53 = 0x8E

    ISO_18003M3_MANCH_424_4 = 0x8F
    ISO_18003M3_MANCH_424_2 = 0x90
    ISO_18003M3_MANCH_848_4 = 0x91
    ISO_18003M3_MANCH_848_2 = 0x92

    ISO_14443_A_PICC_106 = 0x93
    ISO_14443_A_PICC_212 = 0x94
    ISO_14443_A_PICC_424 = 0x95
    ISO_14443_A_PICC_848 = 0x96

    NFC_PASSIVE_TARGET_212 = 0x97
    NFC_PASSIVE_TARGET_424 = 0x98

    ISO_14443_A_106_II = 0x99
    ISO_14443_A_212_II = 0x9A
    ISO_14443_A_424_II = 0x9B

    GTM = 0x9C


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
    HLTA = 0x50  # HALT
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
