// SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
// SPDX-License-Identifier: GPL-3.0-or-later

/*
 * PN5180 RFID Reader for Raspberry Pi Pico
 *
 * This sketch implements a USB-based RFID reader interface using the PN5180 NFC module.
 * It communicates with the host computer over USB serial.
 */

#include <Arduino.h>
#include <SPI.h>

// Pin definitions for Raspberry Pi Pico
#define PN5180_NSS 5   // SPI chip select
#define PN5180_BUSY 6  // Busy pin
#define PN5180_RST 7   // Reset pin

void setup() {
  // Initialize USB serial communication
  Serial.begin(115200);
  while (!Serial) {
    ;  // Wait for serial port to connect
  }

  Serial.println("PN5180-tagomatic RFID Reader");
  Serial.println("Initializing...");

  // Initialize pins
  pinMode(PN5180_NSS, OUTPUT);
  pinMode(PN5180_BUSY, INPUT);
  pinMode(PN5180_RST, OUTPUT);

  // Reset PN5180
  digitalWrite(PN5180_RST, LOW);
  delay(10);
  digitalWrite(PN5180_RST, HIGH);
  delay(10);

  // Initialize SPI
  SPI.begin();

  Serial.println("Ready");
}

void loop() {
  // Main loop - placeholder for RFID reading logic
  // TODO: Implement PN5180 communication protocol
  // TODO: Implement tag detection and reading
  // TODO: Implement USB protocol for host communication

  delay(100);
}
