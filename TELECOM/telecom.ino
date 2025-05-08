#include "telecom.h"
#include "telecom-packet.h"

float telecom_dutyCycleBudget = 0.0;
unsigned long telecom_prevTxLoopMillis = 0;  // Timestamp of previous transmission loop run
unsigned long telecom_prevTxEndMillis = 0;   // Timestamp of previous actual transmission ending

String bytesToHex(const uint8_t bytes[], const size_t length) {
  String hexStr = "";
  for (size_t i = 0; i < length; i++) {
    if (bytes[i] < 0x10) hexStr += "0";  // Add leading zero
    hexStr += String(bytes[i], HEX);
    if (i < length - 1) hexStr += " ";
  }
  return hexStr;
}

void telecom_rx(String rxLogFilePath) {
  // Check for new LoRa transmissions
  int packetSize = LoRa.parsePacket();
  if (packetSize) {
    Serial.println("[telecom] Packet received.");

    String packetStr;
    if (packetSize == TELECOM_PACKET_N_BYTES) {
      // ASCENT telemetry format.

      uint8_t buffer[TELECOM_PACKET_N_BYTES];
      int i = 0;
      while (LoRa.available() && i < TELECOM_PACKET_N_BYTES) {
        buffer[i] = (uint8_t)LoRa.read();
        i++;
      }

      String rawPacketStr = bytesToHex(buffer, TELECOM_PACKET_N_BYTES);
      Serial.print("[telecom] Raw packet: ");
      Serial.println(rawPacketStr);

      telecomPacket packet;
      if (telecomPacket_decode(buffer, &packet) != 0) {
        Serial.println("[telecom] Failed to decode packet.");
        return;
      }

      String sourceLabel = telecomPacket_sourceToLabel(packet.source);
      String typeLabel = telecomPacket_typeToLabel(packet.type);
      telecomPacket_dataType dataType = telecomPacket_typeToDataType(packet.type);

      switch (dataType) {
        case TELECOM_PACKET_DATA_TYPE_UINT32:
          {
            uint32_t value = telecomPacket_parse_uint32(&packet);
            packetStr = String(packet.timestamp) + "," + sourceLabel + "," + typeLabel + "," + String(value);
            break;
          }
        case TELECOM_PACKET_DATA_TYPE_FLOAT:
          {
            float value = telecomPacket_parse_float(&packet);
            packetStr = String(packet.timestamp) + "," + sourceLabel + "," + typeLabel + "," + String(value);
            break;
          }
        default:
          {
            Serial.println("[telecom] Packet data type unsupported.");
            String rawValueStr = bytesToHex(packet.data, TELECOM_PACKET_N_DATA_BYTES);
            packetStr = String(packet.timestamp) + "," + sourceLabel + "," + typeLabel + "," + rawValueStr;
          }
      }
    } else {
      // Unrecognized telemetry format, treat as plain text.
      while (LoRa.available()) {
        packetStr += (char)LoRa.read();
      }
    }

    Serial.print("[telecom] Decoded packet: ");
    Serial.println(packetStr);

    if (rxLogFilePath != "") {
      File rxLogFile = SD.open(rxLogFilePath, FILE_WRITE);
      if (rxLogFile) {
        rxLogFile.println(packetStr);
        rxLogFile.close();
        Serial.println("[telecom] Packet saved to SD card.");
      } else {
        Serial.print("[telecom] Error opening ");
        Serial.println(rxLogFilePath);
      }
    }

    Serial.print("[telecom] RSSI: ");
    Serial.println(LoRa.packetRssi());
  }
}

void telecom_tx(telecomQueue *queue, float dutyCycle) {
  // Wait at least a few ms between subsequent transmission attempts
  if (millis() - telecom_prevTxEndMillis < TELECOM_TX_MIN_DELAY_MILLIS) return;

  float maxDutyCycleBudget = TELECOM_DUTY_CYCLE_WINDOW_MILLIS * dutyCycle;

  unsigned long totalActiveTxMillis = 0;

  // Transmit packet if available in queue
  telecomPacket packet;
  if (telecom_dutyCycleBudget > 0 && telecomQueue_dequeue(queue, &packet) == 0) {
    uint8_t buffer[TELECOM_PACKET_N_BYTES];
    if (telecomPacket_encode(&packet, buffer) != 0) {
      Serial.println("[telecom] Error encoding packet for transmission.");
      return;
    }

    if (!LoRa.beginPacket()) {
      Serial.println("[telecom] LoRa radio can not transmit.");
      return;
    }

    Serial.print("[telecom] Transmitting packet: ");
    for (int i = 0; i < TELECOM_PACKET_N_BYTES; i++) {
      Serial.print(buffer[i], HEX);
      Serial.print(" ");
    }
    Serial.print(" (duty cycle budget: ");
    Serial.print(100.0 * (telecom_dutyCycleBudget / maxDutyCycleBudget));
    Serial.println("%)");

    unsigned long activeTxStartMillis = millis();
    if (!LoRa.write(buffer, sizeof(buffer))) {
      Serial.println("[telecom] Failed to transmit packet.");
      return;
    }
    unsigned long activeTxMillis = millis() - activeTxStartMillis;
    totalActiveTxMillis += activeTxMillis;

    if (!LoRa.endPacket()) {
      Serial.println("[telecom] Failed to end transmitted packet.");
    }

    unsigned long weightedActiveTxMillis = activeTxMillis / dutyCycle;

    telecom_dutyCycleBudget -= weightedActiveTxMillis;
  }

  unsigned long txEndMillis = millis();
  unsigned long totalTxMillis = txEndMillis - telecom_prevTxEndMillis;
  unsigned long txIdleMillis = totalTxMillis - totalActiveTxMillis;

  telecom_dutyCycleBudget += txIdleMillis;

  // Clamp duty cycle budget within reasonable limits
  telecom_dutyCycleBudget = max(-maxDutyCycleBudget, min(maxDutyCycleBudget, telecom_dutyCycleBudget));

  telecom_prevTxEndMillis = txEndMillis;
}
