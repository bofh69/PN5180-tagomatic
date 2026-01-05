# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""RF communication session management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .constants import ISO14443ACommand, ISO15693Command, Registers
from .iso14443a import ISO14443ACard
from .iso15693 import ISO15693Card

if TYPE_CHECKING:
    from .proxy import PN5180Helper


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

        self._reader.turn_on_crc()

        # Set to transceiver mode
        self._reader.change_mode_to_transceiver()

        stored_tx_config = self._reader.read_register(Registers.TX_CONFIG)

        self._reader.send_15693_request(
            ISO15693Command.INVENTORY, bytes([mask_length]), is_inventory=True
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

            # Send EOF
            self._reader.send_data(0, b"")

        self._reader.write_register(Registers.TX_CONFIG, stored_tx_config)

        return uids

    def connect_iso15693(self, uid: bytes) -> ISO15693Card:
        """Connect to an ISO 15693 card.

        This method selects an ISO 15693 card and returns
        a card object.

        Returns:
            ISO15693Card object representing the connected card.

        Raises:
            PN5180Error: If communication with the card fails.
            ValueError: If the card's response is invalid.
            TimeoutError: If no card responds.
        """
        if not self._active:
            raise RuntimeError("Communication session is no longer active")

        self._reader.turn_on_crc()
        self._reader.change_mode_to_transceiver()
        _answer = self._reader.send_and_receive_15693(
            ISO15693Command.SELECT,
            b"",
            uid=uid,
        )

        return ISO15693Card(self._reader, uid)

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
