# SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
# SPDX-License-Identifier: GPL-3.0-or-later

# PN5180 RFID Reader Firmware

This directory contains the Arduino sketch for the Raspberry Pi Pico firmware that interfaces with the PN5180 NFC module.

## Hardware Requirements

- Raspberry Pi Pico
- PN5180 NFC Frontend Module
- USB cable for connection to host computer

## Pin Connections

| PN5180 Pin | Raspberry Pi Pico Pin |
|------------|----------------------|
| NSS        | GP5                  |
| BUSY       | GP6                  |
| RST        | GP7                  |
| MOSI       | GP19 (SPI0 TX)       |
| MISO       | GP16 (SPI0 RX)       |
| SCK        | GP18 (SPI0 SCK)      |
| VCC        | 3.3V                 |
| GND        | GND                  |

## Building and Uploading

### Using Arduino IDE

1. Install the Arduino IDE
2. Add Raspberry Pi Pico board support:
   - Go to File > Preferences
   - Add to Additional Board Manager URLs: `https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json`
   - Go to Tools > Board > Board Manager
   - Search for "pico" and install "Raspberry Pi Pico/RP2040"
3. Select Board: Tools > Board > Raspberry Pi Pico
4. Select Port: Tools > Port > (your Pico's port)
5. Upload the sketch

### Using Arduino CLI

```bash
# Install board support
arduino-cli core install rp2040:rp2040

# Compile
arduino-cli compile --fqbn rp2040:rp2040:rpipico firmware/pn5180_reader

# Upload (replace /dev/ttyACM0 with your port)
arduino-cli upload -p /dev/ttyACM0 --fqbn rp2040:rp2040:rpipico firmware/pn5180_reader
```

## Protocol

The firmware communicates with the host computer over USB serial at 115200 baud.

(Protocol specification to be defined)
