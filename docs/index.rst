.. SPDX-FileCopyrightText: 2026 PN5180-tagomatic contributors
.. SPDX-License-Identifier: GPL-3.0-or-later

PN5180-tagomatic Documentation
==============================

Welcome to PN5180-tagomatic's documentation!

PN5180-tagomatic is a USB-based RFID reader that provides a Python interface 
for reading NFC/RFID tags using the PN5180 NFC Frontend module and a 
Raspberry Pi Pico (Zero).

Features
--------

- Python library for easy integration
- Uses USB serial communication to the reader
- Cross-platform support (Linux, Windows, macOS)
- Finds and selects single ISO/IEC 14443 cards
- Uses NFC FORUM commands to read/write 14443-A cards' memories
- Can authenticate against Mifare classic cards to read their memories
- Finds ISO/IEC 15693 cards, uses 15693-3 commands to read/write their memories

Installation
------------

Install from PyPI:

.. code-block:: bash

   pip install pn5180-tagomatic

Install from source:

.. code-block:: bash

   git clone https://github.com/bofh69/PN5180-tagomatic.git
   cd PN5180-tagomatic
   pip install -e .

Quick Start
-----------

.. code-block:: python

   from pn5180_tagomatic import PN5180

   # Create reader instance and use it
   with PN5180("/dev/ttyACM0") as reader:
       versions = reader.ll.read_eeprom(0x10, 6)
       with reader.start_session(0x00, 0x80) as session:
           card = session.connect_one_iso14443a()
           print(f"Reading from card {card.uid.hex(':')}")
           if len(card.uid) == 4:
               memory = card.read_mifare_memory()
           else:
               memory = card.read_memory()

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
