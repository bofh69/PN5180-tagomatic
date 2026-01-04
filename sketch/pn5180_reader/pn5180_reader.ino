// SPDX-FileCopyrightText: 2025 PN5180-tagomatic contributors
// SPDX-License-Identifier: GPL-3.0-or-later

/*
 * PN5180 RFID Reader for Raspberry Pi Pico
 *
 * Dependencies:
 * - FastLED (3.10.3)
 * - SimpleRPC (3.2.0)
 *
 * This sketch implements a USB-based RFID reader interface.
 * It communicates with the host computer over USB serial using the
 * SimpleRPC protocol.
 *
 * The code is based on https://www.nxp.com/docs/en/data-sheet/PN5180A0XX-C1-C2.pdf
 */

#include <Arduino.h>
#include <SPI.h>
#define FASTLED_INTERNAL 1
#include <FastLED.h>
#include <simpleRPC.h>

// SPI commands for PN5180:
static const uint8_t PN5180_WRITE_REGISTER = 0x00;
static const uint8_t PN5180_WRITE_REGISTER_OR_MASK = 0x01;
static const uint8_t PN5180_WRITE_REGISTER_AND_MASK = 0x02;
static const uint8_t PN5180_WRITE_REGISTER_MULTIPLE = 0x03;
static const uint8_t PN5180_READ_REGISTER = 0x04;
static const uint8_t PN5180_READ_REGISTER_MULTIPLE = 0x05;
static const uint8_t PN5180_WRITE_EEPROM = 0x06;
static const uint8_t PN5180_READ_EEPROM = 0x07;
static const uint8_t PN5180_WRITE_TX_DATA = 0x08;
static const uint8_t PN5180_SEND_DATA = 0x09;
static const uint8_t PN5180_READ_DATA = 0x0A;
static const uint8_t PN5180_SWITCH_MODE = 0x0B;
static const uint8_t PN5180_MIFARE_AUTHENTICATE = 0x0C;
static const uint8_t PN5180_EPC_INVENTORY = 0x0D;
static const uint8_t PN5180_EPC_RESUME_INVENTORY = 0x0E;
static const uint8_t PN5180_EPC_RETRIEVE_INVENTORY_RESULT_SIZE = 0x0F;
static const uint8_t PN5180_LOAD_RF_CONFIG = 0x11;
static const uint8_t PN5180_UPDATE_RF_CONFIG = 0x12;
static const uint8_t PN5180_RETRIEVE_RF_CONFIG_SIZE = 0x13;
static const uint8_t PN5180_RETRIEVE_RF_CONFIG = 0x14;
static const uint8_t PN5180_RF_ON = 0x16;
static const uint8_t PN5180_RF_OFF = 0x17;
static const uint8_t PN5180_CONFIGURE_TESTBUS_DIGITAL = 0x18;
static const uint8_t PN5180_CONFIGURE_TESTBUS_ANALOG = 0x19;

// Pin definitions for Raspberry Pi Pico Zero
static const unsigned long PN5180_MISO = 0u;
static const unsigned long PN5180_MOSI = 3u;
static const unsigned long PN5180_SCK = 2u;
static const unsigned long PN5180_NSS = 1u;  // SPI, negative chip select
static const unsigned long PN5180_BUSY = 4u;
static const unsigned long PN5180_RST = 7u;  // Reset
static const unsigned long PN5180_IRQ = 6u;

static const unsigned long LED_DATA_PIN = 16;

// Colors:
static const CRGB WEAK_RED = 0x010000;
static const CRGB RED = 0x100000;
static const CRGB GREEN = 0x000800;
static const CRGB BLUE = 0x000008;

static CRGB led_value = WEAK_RED;

static arduino::MbedSPI PN_SPI(PN5180_MISO, PN5180_MOSI, PN5180_SCK);
static const SPISettings PN_SPI_SETTINGS(125000, MSBFIRST, SPI_MODE0);

static void set_color(CRGB color) {
  led_value = color;
  FastLED.show();
}

static void log(const char msg[]) {
  Serial.println(msg);
}

static bool wait_busy_is(PinStatus value, const unsigned long timeout = 800) {
  auto start = millis();
  while ((millis() - start) <= timeout) {
    if (digitalRead(PN5180_BUSY) == value) {
      return true;
    }
  }
  return digitalRead(PN5180_BUSY) == value;
}

static int send_spi_data(const uint8_t* data, size_t data_len) {
  uint8_t buffer[256];
  if (data_len > sizeof(buffer)) {
    log("data_len too large");
    return -1;
  }
  memcpy(buffer, data, data_len);

  if (!wait_busy_is(LOW)) {
    log("First busy check failed");
    return -2;
  }

  digitalWrite(PN5180_NSS, LOW);
  delay(5);

  PN_SPI.beginTransaction(PN_SPI_SETTINGS);
  PN_SPI.transfer(buffer, data_len);

  int retval = 0;
  if (!wait_busy_is(HIGH)) {
    log("Second busy check failed");
    retval = -3;
  }

  PN_SPI.endTransaction();
  digitalWrite(PN5180_NSS, HIGH);

  if (!retval && !wait_busy_is(LOW)) {
    log("Third busy check failed");
    retval = -4;
  }

  return retval;
}

static int recv_spi_data(uint8_t* buffer, size_t buffer_len) {
  memset(buffer, 0xff, buffer_len);

  if (!wait_busy_is(LOW)) {
    log("First busy check failed");
    return -1;
  }

  digitalWrite(PN5180_NSS, LOW);
  delay(5);

  PN_SPI.beginTransaction(PN_SPI_SETTINGS);
  PN_SPI.transfer(buffer, buffer_len);

  int retval = 0;
  if (!wait_busy_is(HIGH)) {
    log("Second busy check failed");
    retval = -2;
  }

  PN_SPI.endTransaction();
  digitalWrite(PN5180_NSS, HIGH);

  if (!retval && !wait_busy_is(LOW)) {
    log("Third busy check failed");
    retval = -3;
  }

  return retval;
}

//////////////////////////////////////////////
// Functions available to the RPC interface //
//////////////////////////////////////////////

/**
 * Reset the PN5180 NFC frontend.
 *
 * Performs a hardware reset of the PN5180 module by toggling the reset pin.
 */
static void reset() {
  digitalWrite(PN5180_RST, LOW);
  delay(10);
  digitalWrite(PN5180_RST, HIGH);
  delay(50);
}

/**
 * Write register to the PN5180 NFC frontend.
 * Returns 0 at success.
 */
static int write_register(uint8_t addr, uint32_t value) {
  uint8_t cmd[] = {PN5180_WRITE_REGISTER, addr, value, value >> 8, value >> 16, value >> 24};
  auto retval = send_spi_data(cmd, sizeof(cmd));
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }
  return 0;
}

/**
 * Write register OR mask to the PN5180 NFC frontend.
 * Returns 0 at success.
 */
static int write_register_or_mask(uint8_t addr, uint32_t value) {
  uint8_t cmd[] = {
      PN5180_WRITE_REGISTER_OR_MASK, addr, value, value >> 8, value >> 16, value >> 24};
  auto retval = send_spi_data(cmd, sizeof(cmd));
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }
  return 0;
}

/**
 * Write register AND mask to the PN5180 NFC frontend.
 * Returns 0 at success.
 */
static int write_register_and_mask(uint8_t addr, uint32_t value) {
  uint8_t cmd[] = {
      PN5180_WRITE_REGISTER_AND_MASK, addr, value, value >> 8, value >> 16, value >> 24};
  auto retval = send_spi_data(cmd, sizeof(cmd));
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }
  return 0;
}

/**
 * Write multiple registers to the PN5180 NFC frontend.
 * The argument is a Vector of up to 42 elements.
 * Each element is (address, operation, value/mask)).
 * Operation is:
 *  1 - Write Register
 *  2 - Write Register OR mask
 *  3 - Write Register AND mask
 *
 * Returns 0 at success.
 */
static int write_register_multiple(Vector<Object<uint8_t, uint8_t, uint32_t>>& elements) {
  if (elements.size > 42) {
    log("Too many elements");
    return -1;
  }

  uint8_t buffer[211];
  buffer[0] = PN5180_WRITE_REGISTER_MULTIPLE;
  for (size_t i{0}; i < elements.size; ++i) {
    // Address:
    buffer[1 + i * 6] = get<0>(elements[i]);

    // Operation:
    buffer[2 + i * 6] = get<1>(elements[i]);

    // Value/mask:
    buffer[3 + i * 6] = get<2>(elements[i]);
    buffer[4 + i * 6] = get<2>(elements[i]) >> 8;
    buffer[5 + i * 6] = get<2>(elements[i]) >> 16;
    buffer[6 + i * 6] = get<2>(elements[i]) >> 24;
  }

  auto retval = send_spi_data(buffer, 1 + 6 * elements.size);
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }
  return 0;
}

/**
 * Read register from the PN5180 NFC frontend.
 */
static Object<int, uint32_t> read_register(uint8_t addr) {
  uint8_t cmd[] = {PN5180_READ_REGISTER, addr};
  auto retval = send_spi_data(cmd, sizeof(cmd));
  Object<int, uint32_t> result;
  if (retval) {
    log("Failed to send cmd");
    get<0>(result) = retval;
    return result;
  }
  get<0>(result) = 0;
  uint32_t reg_value;
  retval = recv_spi_data((uint8_t*)(&reg_value), 4);
  if (retval) {
    log("Failed to recv data");
    get<0>(result) = retval;
  }
  get<1>(result) = reg_value;
  return result;
}

/**
 * Read multiple registers from the PN5180 NFC frontend.
 * Reads from up to 18 addresses.
 * Returns an Object of <returnval, Vector<values>>.
 * Returnval is 0 when everything went well.
 */
static Object<int, Vector<uint32_t>> read_register_multiple(Vector<uint8_t>& addrs) {
  Object<int, Vector<uint32_t>> result;

  if (addrs.size > 18) {
    log("Too many addresses");
    get<0>(result) = -1;
    return result;
  }

  uint8_t buffer[211];
  buffer[0] = PN5180_READ_REGISTER_MULTIPLE;
  for (size_t i{0}; i < addrs.size; ++i) {
    // Address:
    buffer[1 + i] = addrs[i];
  }

  auto retval = send_spi_data(buffer, addrs.size + 1);
  if (retval) {
    log("Failed to send cmd");
    get<0>(result) = retval;
    return result;
  }
  retval = recv_spi_data(buffer, 4 * addrs.size);
  if (retval) {
    log("Failed to recv data");
    get<0>(result) = retval;
    return result;
  }
  for (int i = 0; i < addrs.size; ++i) {
    get<1>(result)[i] = buffer[i * 4 + 0] | (buffer[i * 4 + 1] << 8) | (buffer[i * 4 + 2] << 16) |
                        (buffer[i * 4 + 3] << 24);
  }
  return result;
}

/**
 * Write from address in EEPROM to the PN5180 NFC frontend.
 *
 * Negative return numbers are errors.
 */
static int16_t write_eeprom(uint8_t addr, Vector<uint8_t>& values) {
  uint8_t buffer[256];
  if (values.size > 255) {
    log("Too much data to write");
    return -1;
  }

  buffer[0] = PN5180_WRITE_EEPROM;

  for (size_t i = 0; i < values.size; ++i) {
    buffer[1 + i] = values[i];
  }

  auto retval = send_spi_data(buffer, 1 + values.size);
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }
  return 0;
}

/**
 * Read address in EEPROM from the PN5180 NFC frontend.

 * Negative numbers are errors.
 */
static Object<int, Vector<uint8_t>> read_eeprom(uint8_t addr, uint8_t len) {
  Object<int, Vector<uint8_t>> result;

  uint8_t cmd[] = {PN5180_READ_EEPROM, addr, len};
  auto retval = send_spi_data(cmd, sizeof(cmd));
  if (retval) {
    log("Failed to send cmd");
    get<0>(result) = retval;
    return result;
  }
  uint8_t response[255];
  retval = recv_spi_data(response, len);
  get<0>(result) = 0;
  if (retval) {
    log("Failed to recv data");
    get<0>(result) = retval;
  }
  for (size_t i = 0; i < len; ++i) {
    get<1>(result)[i] = response[i];
  }
  return result;
}

/**
 * Write data to TX buffer and send it on the PN5180 NFC frontend.
 *
 * Negative return numbers are errors.
 */
static int16_t write_tx_data(Vector<uint8_t>& values) {
  uint8_t buffer[261];
  if (values.size > 260) {
    log("Too much data to write");
    return -1;
  }

  buffer[0] = PN5180_WRITE_TX_DATA;

  for (size_t i = 0; i < values.size; ++i) {
    buffer[1 + i] = values[i];
  }

  auto retval = send_spi_data(buffer, 1 + values.size);
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }
  return 0;
}

/**
 * Write data to TX buffer and send it on the PN5180 NFC frontend.
 *
 * Bits are how many bits are valid in the final byte.
 *
 * Negative return numbers are errors.
 */
static int16_t send_data(uint8_t bits, Vector<uint8_t>& values) {
  uint8_t buffer[262];
  if (values.size > 260) {
    log("Too much data to write");
    return -1;
  }

  buffer[0] = PN5180_SEND_DATA;
  buffer[1] = bits;

  for (size_t i = 0; i < values.size; ++i) {
    buffer[2 + i] = values[i];
  }

  auto retval = send_spi_data(buffer, 2 + values.size);
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }
  return 0;
}

/**
 * Read data from RX buffer from the PN5180 NFC frontend.

 * Negative numbers are errors.
 */
static Object<int, Vector<uint8_t>> read_data(uint16_t len) {
  uint8_t response[508];
  Object<int, Vector<uint8_t>> result;

  if (len > sizeof(response)) {
    log("len too large");
    get<0>(result) = -1;
    return result;
  }

  uint8_t cmd[] = {PN5180_READ_DATA, 0x00};
  auto retval = send_spi_data(cmd, sizeof(cmd));
  if (retval) {
    log("Failed to send cmd");
    get<0>(result) = retval;
    return result;
  }

  retval = recv_spi_data(response, len);
  get<0>(result) = 0;
  if (retval) {
    log("Failed to recv data");
    get<0>(result) = retval;
  }
  for (size_t i = 0; i < len; ++i) {
    get<1>(result)[i] = response[i];
  }
  return result;
}

/**
 * Switch mode on PN5180.
 *
 * Mode is:
 *  0 - Standby, params is then:
 *     1 byte for wake-up control
 *     2 bytes for wake-up counter value.
 *  1 - LPCD, params is then:
 *     2 bytes for wake-up counter value.
 *  2 - Autocoll, param is then:
 *     2 bytes for wake-up counter value.
 *     1 byte for RF Technologies
 *     1 byte for autocoll mode.
 * Returns 0 on success.
 */
static int switch_mode(uint8_t mode, Vector<uint8_t>& params) {
  uint8_t buffer[1 + 1 + 4];
  if (params.size > 4) {
    log("Too many params");
    return -1;
  }
  buffer[0] = PN5180_SWITCH_MODE;
  buffer[1] = mode;

  for (size_t i = 0; i < params.size; ++i) {
    buffer[2 + i] = params[i];
  }

  auto retval = send_spi_data(buffer, 2 + params.size);
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }
  return 0;
}

/**
 * Authenticate to mifare card at the PN5180 NFC frontend.
 *
 * key_type is 0x60 for Key type A.
 * key_type is 0x61 for Key type B.
 * Returns negative numbers at failures, otherwise mifare authenticate value.
 * 0 is authenticated.
 * 1 is permission denied.
 * 2 is timeout waiting for card response.
 */
static int16_t mifare_authenticate(uint8_t key[6], uint8_t key_type, uint8_t block_addr,
                                   uint32_t uid) {
  uint8_t cmd[] = {
      PN5180_MIFARE_AUTHENTICATE,
      key[0],
      key[1],
      key[2],
      key[3],
      key[4],
      key[5],
      key_type,
      block_addr,
      uid,
      uid >> 8,
      uid >> 16,
      uid >> 24,
  };
  auto retval = send_spi_data(cmd, sizeof(cmd));
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }
  uint8_t result;
  retval = recv_spi_data(&result, sizeof(result));
  if (retval) {
    log("Failed to recv cmd");
    return retval;
  }
  return result;
}

/**
 * Perform EPC inventory on the PN5180 NFC frontend.
 *
 * Returns negative numbers at failures.
 */
static int16_t epc_inventory(Vector<uint8_t>& select_command, uint8_t select_command_final_bits,
                             uint8_t begin_round[3], uint8_t timeslot_behavior) {
  if (select_command.size > 39) {
    log("Too large select_command");
    return -1;
  }

  uint8_t buffer[47];

  buffer[0] = PN5180_EPC_INVENTORY;
  size_t pos = 1;
  buffer[pos++] = select_command.size;

  if (select_command.size) {
    buffer[pos++] = select_command_final_bits;
    for (size_t i = 0; i < select_command.size; ++i) {
      buffer[pos++] = select_command[i];
    }
  }
  buffer[pos++] = begin_round[0];
  buffer[pos++] = begin_round[1];
  buffer[pos++] = begin_round[2];
  buffer[pos++] = timeslot_behavior;

  auto retval = send_spi_data(buffer, pos);
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }
  return 0;
}

/**
 * Continue EPC inventory on the PN5180 NFC frontend.
 *
 * Returns negative numbers at failures.
 */
static int16_t epc_resume_inventory() {
  uint8_t cmd[] = {
      PN5180_EPC_RESUME_INVENTORY,
      0,
  };

  auto retval = send_spi_data(cmd, sizeof(cmd));
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }
  return 0;
}

/**
 * Get inventory result size from the PN5180 NFC frontend.
 *
 * Returns negative numbers at failures.
 */
static int32_t epc_retrieve_inventory_result_size() {
  uint8_t cmd[] = {
      PN5180_EPC_RETRIEVE_INVENTORY_RESULT_SIZE,
      0,
  };

  auto retval = send_spi_data(cmd, sizeof(cmd));
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }

  uint16_t result;
  retval = recv_spi_data((uint8_t*)&result, sizeof(result));
  if (retval) {
    log("Failed to recv cmd");
    return retval;
  }

  return result;
}

// TODO: Make an inventory command that implements the whole algorithm

/**
 * Loads RF config from eeprom on the PN5180 NFC frontend.
 *
 * See table 32 for valid values for tx_config/rx_config.
 *
 * Returns negative numbers at failures.
 */
static int16_t load_rf_config(uint8_t tx_config, uint8_t rx_config) {
  uint8_t cmd[] = {
      PN5180_LOAD_RF_CONFIG,
      tx_config,
      rx_config,
  };

  auto retval = send_spi_data(cmd, sizeof(cmd));
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }

  return 0;
}

// TODO: PN5180_UPDATE_RF_CONFIG
// TODO: PN5180_RETRIEVE_RF_CONFIG_SIZE
// TODO: PN5180_RETRIEVE_RF_CONFIG

/**
 * Turn on RF field on the PN5180 NFC frontend.
 *
 * Flags:
 * Bit0 == 1: disable collision avoidance according to ISO/IEC 18092
 * Bit1 == 1: Use Active Communication mode according to ISO/IEC 18092
 *
 * Returns negative numbers at failures.
 */
static int16_t rf_on(uint8_t flags) {
  uint8_t cmd[] = {
      PN5180_RF_ON,
      flags,
  };

  auto retval = send_spi_data(cmd, sizeof(cmd));
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }

  return 0;
}

/**
 * Turn off RF field on the PN5180 NFC frontend.
 *
 * Returns negative numbers at failures.
 */
static int16_t rf_off() {
  uint8_t cmd[] = {
      PN5180_RF_OFF,
      0,
  };

  auto retval = send_spi_data(cmd, sizeof(cmd));
  if (retval) {
    log("Failed to send cmd");
    return retval;
  }

  return 0;
}

// TODO: PN5180_CONFIGURE_TESTBUS_DIGITAL
// TODO: PN5180_CONFIGURE_TESTBUS_ANALOG

/**
 * Returns true if IRQ is set.
 */
static bool is_irq_set() {
  return digitalRead(PN5180_IRQ);
}

/**
 * Waits upto timeout milliseconds until the IRQ is set.
 * Returns IRQ status.
 */
static bool wait_for_irq(unsigned long timeout) {
  auto start = millis();
  while ((millis() - start) <= timeout) {
    if (is_irq_set()) {
      return true;
    }
    yield();
  }

  return is_irq_set();
}

/////////////////////////
// End of RPC commands //
/////////////////////////

void setup() {
  FastLED.addLeds<NEOPIXEL, LED_DATA_PIN>(&led_value, 1);
  FastLED.show();

  // Initialize USB serial communication
  Serial.begin(115200);

  while (!Serial) {
    ;  // Wait for serial port to connect
  }

  set_color(BLUE);

  // Initialize pins
  pinMode(PN5180_NSS, OUTPUT);
  digitalWrite(PN5180_NSS, HIGH);
  pinMode(PN5180_BUSY, INPUT);
  pinMode(PN5180_RST, OUTPUT);
  digitalWrite(PN5180_RST, HIGH);

  // Reset PN5180
  reset();

  // Initialize SPI
  PN_SPI.begin();
}

void loop() {
  // Handle SimpleRPC communication
  // clang-format off
  interface(Serial,
    reset, "reset: Reset the PN5180 NFC frontend.",
    write_register, "write_register: Write to a PN5180 register. @addr: register address. @value: 32 bit value to write. @return: < 0 at failure.",
    write_register_or_mask, "write_register_or_mask: Write to a PN5180 register OR the old value.",
    write_register_and_mask, "write_register_and_mask: Write to a PN5180 register AND the old value.",
    write_register_multiple, "write_register_multiple: Write to a PN5180 register.",
    read_register, "read_register: Read from a PN5180 register.",
    read_register_multiple, "read_register_multiple: Read from a PN5180 register.",
    write_eeprom, "write_eeprom: Write to the EEPROM.",
    read_eeprom, "read_eeprom: Read from the EEPROM.",
    write_tx_data, "write_tx_data: Write to tx buffer.",
    send_data, "send_data: Write to TX buffer and send it.",
    read_data, "read_data: Read from RX buffer.",
    switch_mode, "switch_mode: Switch mode",
    mifare_authenticate, "mifare_authenticate: Authenticate to mifare card.",
    epc_inventory, "epc_inventory: Start EPC inventory algorithm.",
    epc_resume_inventory, "epc_resume_inventory: Continue EPC inventory algorithm.",
    epc_retrieve_inventory_result_size, "epc_retrieve_inventory_result_size: Get result size from EPC algorithm.",
    load_rf_config, "load_rf_config: Load RF config settings for RX/TX",
    rf_on, "rf_on: Turn on RF field. @flags: bit0 turns off collision avoidance for ISO/IEC 18092. bit1 use Active Communication mode. @return: < 0 at errors.",
    rf_off, "rf_off: Turn off RF field.",
    is_irq_set, "is_irq_set: Is the IRQ pin set.",
    wait_for_irq, "wait_for_irq: Wait up to a timeout value for the IRQ to be set. @timeout: time in ms to wait. @return: true, if IRQ is set.");
  // clang-format on
  set_color(led_value == RED ? GREEN : RED);
}
