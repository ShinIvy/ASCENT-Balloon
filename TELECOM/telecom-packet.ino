#include <stdlib.h>
#include "telecom-packet.h"

int telecomPacket_init_uint32(const uint16_t timestamp, const telecomPacket_source source, const telecomPacket_type type, const uint32_t value, telecomPacket *packet) {
  packet->timestamp = timestamp;
  packet->source = source;
  packet->type = type;

  memcpy(packet->data, &value, sizeof(uint32_t));

  return 0;
}

int telecomPacket_init_float(const uint16_t timestamp, const telecomPacket_source source, const telecomPacket_type type, const float value, telecomPacket *packet) {
  packet->timestamp = timestamp;
  packet->source = source;
  packet->type = type;

  memcpy(packet->data, &value, sizeof(float));

  return 0;
}

int telecomPacket_encode(const telecomPacket *packet, uint8_t buffer[TELECOM_PACKET_N_BYTES]) {
  // timestamp (2 bytes, meaning that 65535 seconds is the max): 00001111 00111100
  uint16_t timestamp = packet->timestamp;
  buffer[0] = (uint8_t)(timestamp >> 8);
  buffer[1] = (uint8_t)timestamp;

  // type (1st bit tells us which balloon (0 = tue, 1 = thu), following 7 bits signify data type, e.g. temperature): 10000001
  uint8_t source = packet->source;
  uint8_t type = packet->type;
  buffer[2] = (source << 7) | type;

  // value (4 bytes, able to contain e.g. a float value): 01000010 11001000 10010001 00000010
  buffer[3] = packet->data[0];
  buffer[4] = packet->data[1];
  buffer[5] = packet->data[2];
  buffer[6] = packet->data[3];

  return 0;
}

int telecomPacket_decode(const uint8_t buffer[TELECOM_PACKET_N_BYTES], telecomPacket *packet) {
  uint16_t timestamp = 0;
  timestamp = timestamp | buffer[0];
  timestamp = (timestamp << 8) | buffer[1];
  packet->timestamp = timestamp;

  uint8_t source = buffer[2] >> 7;
  uint8_t type = buffer[2] & 127;
  packet->source = (telecomPacket_source)source;
  packet->type = (telecomPacket_type)type;

  packet->data[0] = buffer[3];
  packet->data[1] = buffer[4];
  packet->data[2] = buffer[5];
  packet->data[3] = buffer[6];

  return 0;
}

telecomPacket_dataType telecomPacket_typeToDataType(telecomPacket_type type) {
  switch (type) {
    case TELECOM_PACKET_TYPE_GPS_TIME:
      return TELECOM_PACKET_DATA_TYPE_UINT32;
    case TELECOM_PACKET_TYPE_TEMPERATURE:
    case TELECOM_PACKET_TYPE_PRESSURE:
    case TELECOM_PACKET_TYPE_GYRO_X:
    case TELECOM_PACKET_TYPE_GYRO_Y:
    case TELECOM_PACKET_TYPE_GYRO_Z:
    case TELECOM_PACKET_TYPE_ACC_X:
    case TELECOM_PACKET_TYPE_ACC_Y:
    case TELECOM_PACKET_TYPE_ACC_Z:
    case TELECOM_PACKET_TYPE_HUMIDITY:
    case TELECOM_PACKET_TYPE_GPS_LAT:
    case TELECOM_PACKET_TYPE_GPS_LON:
    case TELECOM_PACKET_TYPE_ILLUMINANCE:
      return TELECOM_PACKET_DATA_TYPE_FLOAT;
    default:
      return TELECOM_PACKET_DATA_TYPE_UNKNOWN;
  }
}

uint32_t telecomPacket_parse_uint32(const telecomPacket *packet) {
  uint32_t value = 0;

  memcpy(&value, packet->data, sizeof(uint32_t));

  return value;
}

float telecomPacket_parse_float(const telecomPacket *packet) {
  float value = 0;

  memcpy(&value, packet->data, sizeof(float));

  return value;
}