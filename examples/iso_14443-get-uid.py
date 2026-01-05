#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Example program demonstrating PN5180 reader usage.

This example program detects the UID of a single card in the RF field.

Usage:
    examples/iso_14443-a-get-uid.py /dev/ttyACM0
    examples/iso_14443-a-get-uid.py COM3
"""

import argparse
import sys

from pn5180_tagomatic import PN5180


def main() -> int:
    """Main entry point for the example program."""
    parser = argparse.ArgumentParser(
        description="PN5180 RFID Reader Example - Get ISO 14443-A Card UID",
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

            # Start communication with ISO 14443-A configuration
            with reader.start_session(0x00, 0x80) as session:
                # Connect to a card
                try:
                    card = session.connect_iso14443a()
                    print(f"UID: {card.uid.hex(':')}")
                except TimeoutError as e:
                    print(f"Error: {e}")
                    return 1
                except ValueError as e:
                    print(f"Error: {e}")
                    return 1

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    sys.exit(main())
