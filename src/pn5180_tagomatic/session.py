# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""RF communication session management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .cards import Iso14443AUniqueId, Iso15693UniqueId
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

    def connect_one_iso14443a(self) -> ISO14443ACard:
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

        card_id = self._get_one_iso14443a_card_id()
        return ISO14443ACard(self._reader, card_id)

    def connect_iso14443a(
        self, card_id: Iso14443AUniqueId
    ) -> ISO14443ACard | None:
        """
        Select an ISO/IEC 14443A card and return an object representing it.
        """
        # Activate card first.

        # pylint: disable=too-many-return-statements

        self._reader.turn_off_crc()
        self._reader.change_mode_to_transceiver()
        atqa_data = self._send_atqa()
        if len(atqa_data) == 0:
            # No cards left in field.
            return None

        self._reader.turn_on_crc()

        uid = card_id.uid_as_bytes()
        uid_list = list(uid)
        if len(uid) == 4:
            sak = self._send_select_for_cl(0, uid_list)
            if len(sak) == 0:
                return None
        else:
            sak = self._send_select_for_part(0, uid_list[0:3])
            if len(sak) == 0:
                return None

            if len(uid) == 7:
                sak = self._send_select_for_cl(1, uid_list[3:7])
                if len(sak) == 0:
                    return None
            else:
                sak = self._send_select_for_part(1, uid_list[3:6])
                if len(sak) == 0:
                    return None

            if len(uid) == 10:
                sak = self._send_select_for_cl(2, uid_list[6:])
                if len(sak) == 0:
                    return None

        return ISO14443ACard(self._reader, card_id)

    @staticmethod
    def _is_valid_bcc(data: bytes) -> bool:
        """Verify BCC byte"""
        if len(data) != 5:
            return False
        bcc = data[0] ^ data[1] ^ data[2] ^ data[3]
        return bcc == data[4]

    def _get_coll_bit(self) -> None | int:
        """Get collision bit"""
        rx_status = self._reader.read_register(Registers.RX_STATUS)

        if rx_status & (1 << 18):
            coll_bit = (rx_status >> 19) & 63
            return coll_bit

        return None

    @staticmethod
    def _get_cmd_for_level(level: int) -> int:
        if level == 0:
            return ISO14443ACommand.ANTICOLLISION_CL1
        if level == 1:
            return ISO14443ACommand.ANTICOLLISION_CL2
        if level == 2:
            return ISO14443ACommand.ANTICOLLISION_CL3
        raise ValueError("level argument is out of range")

    def _get_one_iso14443a_card_id(self) -> Iso14443AUniqueId:
        """Get the UID of an ISO 14443-A card using anticollision protocol.

        Returns:
            The card's (UID as bytes, SAK as bytes).

        Raises:
            PN5180Error: If communication with the card fails.
            ValueError: If the card's response is invalid.
            TimeoutError: If no card responds.
        """
        card_ids = self.get_all_iso14443a_uids(
            wake_up_first=True,
            halt_when_found=False,
            max_cards=1,
        )
        if len(card_ids) == 0:
            raise TimeoutError("No card responded")
        return card_ids[0]

    @staticmethod
    def _get_nvb_and_final_bits(
        data_len: int, coll_bit: int
    ) -> tuple[int, int]:
        final_bits = coll_bit % 8
        nvb = ((data_len + 2) << 4) | final_bits
        if final_bits != 0:
            nvb -= 0x10
        return (nvb, final_bits)

    def _send_atqa(self) -> bytes:
        return self._reader.send_and_receive(7, bytes([ISO14443ACommand.WUPA]))

    def _send_select_for_cl(self, cl: int, uid: list[int]) -> bytes:
        bcc = uid[0] ^ uid[1] ^ uid[2] ^ uid[3]
        sak = bytes([uid[0], uid[1], uid[2], uid[3], bcc])
        cmd = self._get_cmd_for_level(cl)
        request = bytes([cmd, ISO14443ACommand.SELECT]) + sak
        sak = self._reader.send_and_receive(0, request)
        return sak

    def _send_select_for_part(self, cl: int, uid_part: list[int]) -> bytes:
        return self._send_select_for_cl(cl, [0x88] + uid_part)

    def get_all_iso14443a_uids(
        self,
        wake_up_first: bool = True,
        halt_when_found: bool = True,
        max_cards: int = 32,
    ) -> list[Iso14443AUniqueId]:
        """Get the UIDs of ISO 14443-A cards using anticollision protocol.

        Cards may be halted after discovery.

        If called again without "wake_up_first", cards that have previously
        been halted might not be found again. It depends on the cards' UIDs
        relative to each other.

        Args:
            wake_up_first: Send WUPA first to wake up halted cards.
            halt_when_found: Send HLTA to found cards.
            max_cards: The maximum number of cards that can be found.

        Returns:
            A list of the card's IDs.

        Raises:
            PN5180Error: If communication with the card fails.
            ValueError: If the card's response is invalid.
        """
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        card_ids: list[Iso14443AUniqueId] = []
        discovery_stack: list[tuple[int, bytes, int, list[int], bool]] = [
            (0, b"", 0, [], True),
        ]
        while len(discovery_stack) > 0:
            (cl, mask, coll_bit, uid, restart) = discovery_stack.pop()

            if restart:
                self._reader.turn_off_crc()
                self._reader.change_mode_to_transceiver()
                try:
                    cmd: int = ISO14443ACommand.REQA
                    if wake_up_first:
                        cmd = ISO14443ACommand.WUPA
                    atqa_data = self._reader.send_and_receive(7, bytes([cmd]))
                    if len(atqa_data) == 0:
                        # No longer any more cards in the field.
                        return card_ids
                    if len(uid) >= 3:
                        # This isn't tested, I don't have cards that
                        # collide in the second part only
                        self._reader.turn_on_crc()
                        sak = self._send_select_for_part(0, uid)
                        if len(sak) == 0:
                            # It no longer is in the field
                            continue

                    if len(uid) >= 6:
                        # This isn't tested, I don't have cards that
                        # collide in the third part only
                        sak = self._send_select_for_part(1, uid[4:])
                        if len(sak) == 0:
                            # It no longer is in the field
                            continue
                except TimeoutError:
                    # It no longer is in the field
                    continue
                except ValueError as e:
                    print("Got unexpected error:", e)
                    continue

            # ATQA uid length bits: 0 == 4 bytes, 1 == 7 bytes, 2 == 10 bytes

            # Send Anticollision CL X
            self._reader.set_rx_crc_and_first_bit(False, 0)
            self._reader.turn_off_tx_crc()
            cmd = self._get_cmd_for_level(cl)
            (nvb, final_bits) = self._get_nvb_and_final_bits(
                len(mask), coll_bit
            )

            try:
                self._reader.set_rx_crc_and_first_bit(False, final_bits)

                new_mask = self._reader.send_and_receive(
                    final_bits,
                    bytes([cmd, nvb]) + mask,
                )

                if len(mask) and len(new_mask):
                    # Combine new_mask and mask...
                    tmp_new_mask = bytearray(mask)
                    tmp_new_mask[-1] |= new_mask[0]
                    if len(new_mask) > 1:
                        tmp_new_mask += new_mask[1:]
                    new_mask = bytes(tmp_new_mask)
            except TimeoutError:
                # It is no longer in the field.
                continue
            except ValueError as e:
                print("Got unexpected error:", e)
                continue
            finally:
                self._reader.set_rx_crc_and_first_bit(True, 0)

            new_coll_bit = self._get_coll_bit()

            if new_coll_bit is None:
                # No collision
                if not self._is_valid_bcc(new_mask):
                    # TODO: Maybe have some maximum retry?
                    # Retry:
                    discovery_stack.append((cl, mask, coll_bit, uid, True))
                    continue

                self._reader.set_rx_crc_and_first_bit(True, 0)
                self._reader.turn_on_tx_crc()
                sak = self._send_select_for_cl(cl, list(new_mask)[0:4])
                if len(sak) == 0:
                    # TODO: Maybe have some maximum retry?
                    discovery_stack.append((cl, mask, coll_bit, uid, True))
                    continue

                # Build UID
                if sak[0] & (1 << 2) == 0:
                    uid.append(new_mask[0])
                uid.append(new_mask[1])
                uid.append(new_mask[2])
                uid.append(new_mask[3])
                if sak[0] & (1 << 2) == 0:
                    # All CL levels completed for this card
                    card_ids.append(Iso14443AUniqueId(bytes(uid), sak))
                    if halt_when_found:
                        self._reader.send_data(
                            0, bytes([ISO14443ACommand.HLTA, 0x00])
                        )
                    if len(card_ids) >= max_cards:
                        return card_ids
                else:
                    # Go to next CL
                    discovery_stack.append((cl + 1, b"", 0, uid, False))
            else:
                # There was a collision
                n_bytes = 1 + (new_coll_bit + 7) // 8
                bit = new_coll_bit % 8

                new_mask = bytearray(new_mask[:n_bytes])

                new_mask[new_coll_bit // 8] |= 1 << bit
                final_bit = (new_coll_bit + 1) % 8
                # Need to restart, another is handled next.
                discovery_stack.append(
                    (cl, bytes(new_mask[:n_bytes]), final_bit, list(uid), True)
                )

                new_mask[new_coll_bit // 8] &= 255 ^ (1 << bit)
                # No need to restart, this is handled next.
                discovery_stack.append(
                    (cl, bytes(new_mask[:n_bytes]), final_bit, uid, False)
                )
        return card_ids

    def iso15693_inventory(
        self,
        slots: int = 16,
        mask_length: int = 0,
        afi: int | None = None,
    ) -> list[Iso15693UniqueId]:
        """Perform ISO 15693 inventory to find tags.

        This method implements the ISO 15693 inventory protocol to discover
        tags in the RF field. It uses 16 slots by default for anticollision.

        Args:
            slots: Number of slots for anticollision (default: 16).
                Must be 16 for mask_length 0.
            mask_length: Length of mask (default: 0).

        Returns:
            List of UniqueIds found.

        Raises:
            PN5180Error: If communication fails.

        Example:
            >>> with reader.start_session(0x0D, 0x8D) as session:
            ...     card_ids = session.iso15693_inventory()
            ...     for card_id in card_ids:
            ...         print(f"Found UID: {card_id.uid_to_string()}")
        """
        if not self._active:
            raise RuntimeError("Communication session is no longer active")

        if slots != 16:
            raise NotImplementedError("Slots must currently be 16")

        card_ids = []

        self._reader.turn_on_crc()

        # Set to transceiver mode
        self._reader.change_mode_to_transceiver()

        stored_tx_config = self._reader.read_register(Registers.TX_CONFIG)

        # TODO Set flag according to slots
        self._reader.send_15693_request(
            ISO15693Command.INVENTORY,
            bytes([mask_length]),
            is_inventory=True,
            afi=afi,
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
                            card_ids.append(Iso15693UniqueId(uid))

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

        return card_ids

    def connect_iso15693(self, card_id: Iso15693UniqueId) -> ISO15693Card:
        """Connect to an ISO 15693 card.

        This method selects an ISO 15693 card and returns
        a card object.

        Args: card_id: An unique identifier for the card.

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
            ISO15693Command.SELECT, b"", uid=card_id
        )

        return ISO15693Card(self._reader, card_id)

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
