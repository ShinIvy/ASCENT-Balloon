#ifndef TELECOM_PACKET_H
#define TELECOM_PACKET_H

typedef enum {
  TELECOM_PACKET_SOURCE_VEREST = 0,
  TELECOM_PACKET_SOURCE_ASCENT = 1
} telecomPacket_source;

typedef enum {
  TELECOM_PACKET_TYPE_TEMPERATURE = 0,
  TELECOM_PACKET_TYPE_PRESSURE = 1,
  TELECOM_PACKET_TYPE_GYRO_X = 2,
  TELECOM_PACKET_TYPE_GYRO_Y = 3,
  TELECOM_PACKET_TYPE_GYRO_Z = 4,
  TELECOM_PACKET_TYPE_ACC_X = 5,
  TELECOM_PACKET_TYPE_ACC_Y = 6,
  TELECOM_PACKET_TYPE_ACC_Z = 7,
  TELECOM_PACKET_TYPE_HUMIDITY = 8,
  TELECOM_PACKET_TYPE_GPS_TIME = 9,
  TELECOM_PACKET_TYPE_GPS_LAT = 10,
  TELECOM_PACKET_TYPE_GPS_LON = 11,
  TELECOM_PACKET_TYPE_GPS_SPEED = 12,
  TELECOM_PACKET_TYPE_ILLUMINANCE = 13,
  // ... etc
} telecomPacket_type;

typedef enum {
  TELECOM_PACKET_DATA_TYPE_UNKNOWN = -1,
  TELECOM_PACKET_DATA_TYPE_UINT32 = 0,
  TELECOM_PACKET_DATA_TYPE_FLOAT = 1
} telecomPacket_dataType;

#define TELECOM_PACKET_N_DATA_BYTES 4

typedef struct {
  uint16_t timestamp;
  telecomPacket_source source;
  telecomPacket_type type;
  uint8_t data[TELECOM_PACKET_N_DATA_BYTES];
} telecomPacket;

#define TELECOM_PACKET_N_BYTES 3 + TELECOM_PACKET_N_DATA_BYTES

int telecomPacket_init_uint32(const uint16_t timestamp, const telecomPacket_source source, const telecomPacket_type type, const uint32_t value, telecomPacket *packet);

int telecomPacket_init_float(const uint16_t timestamp, const telecomPacket_source source, const telecomPacket_type type, const float value, telecomPacket *packet);

int telecomPacket_encode(const telecomPacket *packet, uint8_t buffer[TELECOM_PACKET_N_BYTES]);

int telecomPacket_decode(const uint8_t buffer[TELECOM_PACKET_N_BYTES], telecomPacket *packet);

telecomPacket_dataType telecomPacket_typeToDataType(const telecomPacket_type type);

uint32_t telecomPacket_parse_uint32(const telecomPacket *packet);

float telecomPacket_parse_float(const telecomPacket *packet);

#endif
