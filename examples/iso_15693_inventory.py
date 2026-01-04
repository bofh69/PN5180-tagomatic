#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Example program demonstrating PN5180 reader usage.

This example program implements the 4.2 example in
https://www.nxp.com/docs/en/application-note/AN12650.pdf

Usage:
    examples/iso_15693_inventory.py /dev/ttyACM0
    examples/iso_15693_inventory.py COM3
"""

import argparse
import sys

from pn5180_tagomatic import PN5180, Registers


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
            # ISO 15693
            reader.load_rf_config(0x0D, 0x8D)

            # Line 2:
            reader.rf_on()

            # Line 3:
            # Clear all IRQs
            reader.write_register(Registers.IRQ_CLEAR, 0x000FFFFF)

            # Extra: Configure IRQ ENABLE register, turn on RX_IRQ_EN
            # reader.write_register_or_mask(Registers.IRQ_ENABLE, 1)

            # Line 4:
            # Set Idle state
            reader.write_register_and_mask(Registers.SYSTEM_CONFIG, 0xFFFFFFF8)

            # Line 5:
            # Initiates Transceiver state
            reader.write_register_or_mask(Registers.SYSTEM_CONFIG, 0x00000003)

            # Line 6:
            # ISO 15693 cmd
            # 16 slots
            # Mask Length 0
            reader.send_data(0, [0x06, 0x01, 0x00])

            # Line 7
            for slotCounter in range(16):
                # Line 8:
                # Wait for reception
                status = reader.read_register(Registers.RX_STATUS)
                if status:
                    # print(f"RX_STATUS: {status:x}")
                    how_many_bytes = status & 511
                    if how_many_bytes > 0:
                        # Line 9:
                        data = reader.read_data(how_many_bytes)
                        if data[0] & 1 == 0:
                            print("Read UID:")
                            print(data[10:1:-1].hex(":"))
                        else:
                            print("Got error: ")
                            print(data)

                # Line 11:
                # Clear bit 7, 8 and 11 - only send EOF for next command
                reader.write_register_and_mask(Registers.TX_CONFIG, 0xFFFFFB3F)

                # Line 12:
                # Set state to Idle
                reader.write_register_and_mask(Registers.SYSTEM_CONFIG, 0xFFFFFFF8)

                # Line 13:
                # Set state to TRANSCEIVE
                reader.write_register_or_mask(Registers.SYSTEM_CONFIG, 0x00000003)

                # Line 14:
                reader.write_register(Registers.IRQ_CLEAR, 0x000FFFFF)

                # Line 15:
                # Send EOF (because of TX_CONFIG
                reader.send_data(0, [])

            # Line 16:
            reader.rf_off()

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
