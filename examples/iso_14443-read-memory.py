#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Example program demonstrating PN5180 reader usage.

This example program implements the 4.1 example in
https://www.nxp.com/docs/en/application-note/AN12650.pdf

Usage:
    examples/iso_14443-read-memory.py /dev/ttyACM0
    examples/iso_14443-read-memory.py COM3
"""

# WIP - This should be cleaned up and turned into proper functions
# with error handling...

import argparse
import sys

from pn5180_tagomatic import PN5180, MifareKeyType, Registers


def turn_off_crc(reader):
    # Turn off CRC for TX
    reader.write_register_and_mask(Registers.CRC_TX_CONFIG, 0xFFFFFFFE)

    # Turn off CRC for RX
    reader.write_register_and_mask(Registers.CRC_RX_CONFIG, 0xFFFFFFFE)


def turn_on_crc(reader):
    # Turn on CRC for TX
    reader.write_register_or_mask(Registers.CRC_TX_CONFIG, 0x00000001)

    # Turn on CRC for RX
    reader.write_register_or_mask(Registers.CRC_RX_CONFIG, 0x00000001)


def change_mode_to_transceiver(reader):
    # Set Idle state
    reader.write_register_and_mask(Registers.SYSTEM_CONFIG, 0xFFFFFFF8)

    # Initiates Transceiver state
    reader.write_register_or_mask(Registers.SYSTEM_CONFIG, 0x00000003)


def main() -> int:
    """Main entry point for the example program."""
    parser = argparse.ArgumentParser(
        description="PN5180 RFID Reader Example",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "tty",
        help="Serial port device (e.g., /dev/ttyACM0 or COM3)",
    )
    args = parser.parse_args()

    try:
        # Create PN5180 reader instance
        with PN5180(args.tty) as reader:
            print("PN5180 reader initialized")

            # Line 1:
            # ISO 14443-A 106
            reader.load_rf_config(0x00, 0x80)

            # Line 2:
            reader.rf_on()

            turn_off_crc(reader)

            # Line 5:
            # Clear all IRQs
            reader.write_register(Registers.IRQ_CLEAR, 0x000FFFFF)

            # Extra: Configure IRQ ENABLE register, turn on RX_IRQ_EN
            reader.write_register_or_mask(Registers.IRQ_ENABLE, 1)

            change_mode_to_transceiver(reader)

            # Line 8:
            # Send 0x26 (REQA command)
            reader.send_data(7, [0x52])

            # Line 9:
            # Wait for reception
            irq = reader.wait_for_irq(1000)
            # print(f"IRQ value: {irq}")
            # if irq:
            # status = reader.read_register(Registers.IRQ_STATUS)
            # print(f"IRQ_STATUS: {status:x}")

            rx_status = reader.read_register(Registers.RX_STATUS)
            data_len = rx_status & 511

            if data_len < 1:
                print("No card answered")
                return 0

            # Line 10:
            data = reader.read_data(data_len)
            uid_len = data[0] // 64
            uid = []
            cascade_tag = -1
            for cl in range(uid_len + 1):

                # 0 == 4 bytes
                # 1 == 7 bytes
                # 2 == 10 bytes

                # Send Anticollision CL X
                if cl == 0:
                    reader.send_data(0, [0x93, 0x20])
                elif cl == 1:
                    reader.send_data(0, [0x95, 0x20])
                elif cl == 2:
                    reader.send_data(0, [0x97, 0x20])

                rx_status = reader.read_register(Registers.RX_STATUS)
                data_len = rx_status & 511

                if data_len < 5:
                    print(f"Didn't get complete UID response, data_len=={data_len}")
                    return 0

                # Line 10:
                data = reader.read_data(data_len)

                bcc = data[0] ^ data[1] ^ data[2] ^ data[3]

                if bcc != data[4]:
                    print("Invalid BCC, aborting")
                    return 0

                if cl > 0 and cl < uid_len and data[0] != cascade_tag:
                    print("Wrong cascade tag")
                    return 0

                if uid_len == cl:
                    uid.append(data[0])
                elif cl == 0:
                    cascade_tag = data[0]
                uid.append(data[1])
                uid.append(data[2])
                uid.append(data[3])

                turn_on_crc(reader)
                # change_mode_to_transceiver(reader)
                if cl == 0:
                    reader.send_data(0, bytes([0x93, 0x70]) + data)
                elif cl == 1:
                    reader.send_data(0, bytes([0x95, 0x70]) + data)
                elif cl == 2:
                    reader.send_data(0, bytes([0x97, 0x70]) + data)

                rx_status = reader.read_register(Registers.RX_STATUS)
                data_len = rx_status & 511

                # Line 10:
                data = reader.read_data(data_len)

                print("SAK:")
                print(data)
                # more_uid = len(data) >= 1 and data[0] & 4
                # TODO: Its really the SAK that says if we should
                # continue, not the UID_LEN

                turn_off_crc(reader)

            print(f"UID: {bytes(uid).hex(':')}")

            turn_on_crc(reader)

            #            reader.send_data(0, [0x60])
            #
            #            rx_status = reader.read_register(Registers.RX_STATUS)
            #            data_len = rx_status & 511
            #
            #            if data_len < 8:
            #                print(f"Didn't get a proper GET_VERSION response, data_len=={data_len}")
            #                version_data = bytes()
            #            else:
            #                version_data = reader.read_data(data_len)
            #                print(f"Version info: {version_data.hex(' ')}")
            #                # Header 00
            #                # vendor ID: 04 == NXP
            #                # product type: 04 == NTAG
            #                # subtype: 02 == 50 pF
            #                # major product version
            #                # minor product version
            #                # Storage size (size == 1 << (x >> 1)), bit 0 says if it is exact
            #                # Protocol type: 03 (14443-3 compliant)

            is_mifare = len(uid) == 4
            mifare_uid = uid[3] << 24 | uid[2] << 16 | uid[1] << 8 | uid[0]
            for page in range(0, 255, 4):
                if is_mifare:
                    key = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
                    retvalA = reader.mifare_authenticate(
                        key, MifareKeyType.KEY_A, page, mifare_uid
                    )
                    if retvalA != 0:
                        print(
                            f"Failed to authenticate with KEY A and all 0xFF for block {page}: retval={retvalA}"
                        )
                    if retvalA == 2:
                        # timeout
                        break
                    retvalB = reader.mifare_authenticate(
                        key, MifareKeyType.KEY_B, page, mifare_uid
                    )
                    if retvalB != 0:
                        print(
                            f"Failed to authenticate with KEY B and all 0xFF for block {page}: retval={retvalB}"
                        )
                    if retvalB == 2:
                        # timeout
                        break
                    if retvalA != 0 and retvalB != 0:
                        break

                reader.send_data(0, [0x30, page])

                rx_status = reader.read_register(Registers.RX_STATUS)
                data_len = rx_status & 511

                if data_len < 1:
                    if page == 0:
                        print(
                            f"Didn't get a proper READ response, data_len=={data_len}"
                        )
                    break
                else:
                    memory_content = reader.read_data(data_len)
                    ascii_values = "".join(
                        chr(byte) if 32 <= byte <= 126 else "."
                        for byte in memory_content
                    )
                    print(f"({4*page:03x}): {memory_content.hex(' ')} {ascii_values}")

            reader.rf_off()

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise e
        # return 1


if __name__ == "__main__":
    sys.exit(main())
