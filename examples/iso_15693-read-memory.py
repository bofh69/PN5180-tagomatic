#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

"""Example program demonstrating PN5180 ISO 15693 operations.

This example program finds the UID of ISO-15693 cards

Usage:
    examples/iso_15693-read-memory.py /dev/ttyACM0
    examples/iso_15693-read-memory.py COM3
"""

import argparse
import sys

from pn5180_tagomatic import PN5180
from pn5180_tagomatic.constants import (
    RxProtocol,
    TxProtocol,
)


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
            with reader.start_session(
                TxProtocol.ISO_15693_ASK100_26,
                RxProtocol.ISO_15693_26,
            ) as session:
                print("Performing ISO 15693 inventory...")

                # Perform inventory
                uids = session.iso15693_inventory(afi=0x00)

                # Display results
                if uids:
                    print(f"\nFound {len(uids)} tag(s):")
                    for i, uid in enumerate(uids, 1):
                        print(f"  {i}. {uid}")

                    card = session.connect_iso15693(uids[0])

                    try:
                        for offset in range(0, 512, 16):
                            chunk = card.read_memory(offset, 16)
                            ascii_values = "".join(
                                chr(byte) if 32 <= byte <= 126 else "."
                                for byte in chunk
                            )
                            print(
                                f"({offset:03x}): {chunk.hex(' ')} {ascii_values}"
                            )
                    except TimeoutError:
                        # Done
                        pass
                else:
                    print("\nNo tags found")

        return 0

    except Exception as e:  #  pylint: disable=broad-exception-caught
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
