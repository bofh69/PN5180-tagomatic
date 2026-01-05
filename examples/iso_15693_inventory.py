#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Example program demonstrating PN5180 ISO 15693 inventory.

This example program implements the 4.2 example in
https://www.nxp.com/docs/en/application-note/AN12650.pdf

Usage:
    examples/iso_15693_inventory.py /dev/ttyACM0
    examples/iso_15693_inventory.py COM3
"""

import argparse
import sys

from pn5180_tagomatic import PN5180


def main() -> int:
    """Main entry point for the example program."""
    parser = argparse.ArgumentParser(
        description="PN5180 ISO 15693 Inventory Example",
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

            # Start ISO 15693 communication session
            # 0x0D = TX config for ISO 15693
            # 0x8D = RX config for ISO 15693
            with reader.start_comm(0x0D, 0x8D) as session:
                print("Performing ISO 15693 inventory...")

                # Perform inventory
                uids = session.iso15693_inventory()

                # Display results
                if uids:
                    print(f"\nFound {len(uids)} tag(s):")
                    for i, uid in enumerate(uids, 1):
                        print(f"  {i}. UID: {uid.hex(':')}")
                else:
                    print("\nNo tags found")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
