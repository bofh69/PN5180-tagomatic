#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Example program demonstrating PN5180 reader usage.

This example program opens a serial connection to the PN5180 reader
device and demonstrates basic operations including resetting the device.

Usage:
    python examples/basic_example.py /dev/ttyACM0
    python examples/basic_example.py COM3
"""

import argparse
import sys

from pn5180_tagomatic import PN5180


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

            data = reader.ll.read_eeprom(0x12, 2)
            print("Read from EEPROM")
            print(f"Firmware version: {data[1]}.{data[0]}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
