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

import serial

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
    parser.add_argument(
        "--baud",
        type=int,
        default=115200,
        help="Baud rate (default: 115200)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="Serial timeout in seconds (default: 1.0)",
    )

    args = parser.parse_args()

    print(f"Opening serial port {args.tty} at {args.baud} baud...")

    try:
        # Open the serial port
        ser = serial.Serial(args.tty, args.baud, timeout=args.timeout)
        print(f"Connected to {args.tty}")

        # Create PN5180 reader instance
        with PN5180(ser) as reader:
            print("PN5180 reader initialized")

            # Call the reset function
            print("Calling reset function...")
            reader.reset()
            print("Reset completed successfully")

            print("\nExample completed successfully!")

        return 0

    except serial.SerialException as e:
        print(f"Error: Could not open serial port {args.tty}: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
