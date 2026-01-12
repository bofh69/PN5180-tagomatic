#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Example program demonstrating PN5180 reader usage.

This example program implements the 4.1 example in
https://www.nxp.com/docs/en/application-note/AN12650.pdf

Usage:
    examples/iso_14443_reqa.py /dev/ttyACM0
    examples/iso_14443_reqa.py COM3
"""

import argparse
import sys

from pn5180_tagomatic import PN5180, Registers
from pn5180_tagomatic.constants import (
    RxProtocol,
    TxProtocol,
)


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
            reader.ll.load_rf_config(
                TxProtocol.ISO_14443_A_106, RxProtocol.ISO_14443_A_106
            )

            # Line 2:
            reader.ll.rf_on()

            # Line 3:
            # Turn off CRC for TX
            reader.ll.write_register_and_mask(
                Registers.CRC_TX_CONFIG, 0xFFFFFFFE
            )

            # Line 4:
            # Turn off CRC for RX
            reader.ll.write_register_and_mask(
                Registers.CRC_RX_CONFIG, 0xFFFFFFFE
            )

            # Line 5:
            # Clear all IRQs
            reader.ll.write_register(Registers.IRQ_CLEAR, 0x000FFFFF)

            # Extra: Configure IRQ ENABLE register, turn on RX_IRQ_EN
            reader.ll.write_register_or_mask(Registers.IRQ_ENABLE, 1)

            # Line 6:
            # Set Idle state
            reader.ll.write_register_and_mask(
                Registers.SYSTEM_CONFIG, 0xFFFFFFF8
            )

            # Line 7:
            # Initiates Transceiver state
            reader.ll.write_register_or_mask(
                Registers.SYSTEM_CONFIG, 0x00000003
            )

            # Line 8:
            # Send 0x26 (REQA command)
            reader.ll.send_data(7, [0x26])

            # Line 9:
            # Wait for reception
            irq = reader.ll.wait_for_irq(1000)
            print(f"IRQ value: {irq}")
            if irq:
                status = reader.ll.read_register(Registers.IRQ_STATUS)
                print(f"IRQ_STATUS: {status:x}")

            # Line 10:
            data = reader.ll.read_data(2)
            print("Read data:")
            # ATQA response:
            print(f"  0x{data[0]:02x} 0x{data[1]:02x}")

            # Line 11:
            reader.ll.rf_off()

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
