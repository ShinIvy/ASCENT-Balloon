#include <Arduino_MKRENV.h>
#include <SPI.h>
#include <SD.h>
#include <LoRa.h>
#include <SparkFun_u-blox_GNSS_Arduino_Library.h>
#include "LSM6DS3.h"
#include "Wire.h"
#include "telecom.h"

SFE_UBLOX_GNSS myGNSS;

// Availability of different subsystems
bool shieldOk;
bool gpsOk;
bool accOk;
bool sdOk;
bool loraOk;

// Variable initialization
float temperature; //Temperature Sensor in °C
float humidity; //Humidity Sensor in %
float pressure; //Pressure Sensor in kPa
float illuminance; //Illuminance Sensor in lx
float aX, aY, aZ; //Accelerometer in g
float gX, gY, gZ; //Gyroscope in ????
unsigned long nowMillis = 0;
unsigned long prevTelemetryLoopMillis = 0; // Timestamp of previous telemetry loop run

String telemetryFileName = "data.txt"; // Path to CSV-formatted telemetry file
File telemetryFile;

//Variable telecom
telecomQueue queue; // Queue to hold outgoing telecom packets
String rxLogFileName = "rx.log"; // Path to received packets log file

// Variables pour la gestion du temps
unsigned long previousGPSTime = 0;
const unsigned long gpsInterval = 500; // Intervalle GPS (500 ms)

// Variables globales pour les données GPS
float latitude = 0;
float longitude = 0;
float speed = 0;
int timeUNIX = 0;

//Call function because we define main before all function
void acc_gyro();
void env();
void motor();
void monitor();
void SDcard();
void telecom();
void gps();

//Create a instance of class LSM6DS3
LSM6DS3 lsm6ds3(I2C_MODE, 0x6A); //I2C device address 0x6A

//Create class for SD Card
File file;

void setup() {
  Serial.begin(9600);
  // Wait max 10s for serial connection to open
  unsigned long serialMillis = millis();
  while (!Serial && millis() - serialMillis < 10000);

  if (!ENV.begin()) { //MKR ENV Shield
    Serial.println("Failed to initialize MKR ENV shield!");
    shieldOk = false;
  } else {
    Serial.println("Successfully initialized MKR ENV shield.");
    shieldOk = true;
  }

  Serial.println("Initialisation du GPS...");
  Wire.begin();
  if (!myGNSS.begin(Wire, 0x42)) {  // Adresse I2C du module SAM-M8Q
    Serial.println("Échec de l'initialisation du module GNSS!");
    gpsOk = false;
  } else {
    myGNSS.setI2COutput(COM_TYPE_UBX);  // Active uniquement les messages UBX
    // Configuration du modèle dynamique en Airborne 4G
    if (myGNSS.setDynamicModel(DYN_MODEL_AIRBORNE4g)) {
      Serial.println("Modèle dynamique réglé sur Airborne <4G>.");
    } else {
      Serial.println("Échec du réglage du modèle dynamique.");
    }
    Serial.println("Module GNSS initialisé avec succès.");
    gpsOk = true;
  }

  if (lsm6ds3.begin() != 0) {  //Accelerometer and Gyroscope
    Serial.println("Accelerometer / gyroscope device error");
    accOk = false;
  } else {
    Serial.println("Accelerometer / gyroscope device OK!");
    accOk = true;
  }

  if (!SD.begin()) {  //SD Card
    Serial.println("Failed to initialize SD card!");
    sdOk = false;
  } else {
    // Create a file on the SD Card
    file = SD.open(telemetryFileName, FILE_WRITE);
    if (!file) {
      Serial.println("Failed to create file!");
      sdOk = false;
    }
    file.close();
    Serial.println("Successfully initialized SD card.");
    sdOk = true;
  }

  Serial.print("Starting LoRa...");
  if (!LoRa.begin(868E6)) {
    Serial.println("failed!");
    rxLogFileName = ""; // Skips logging received telemetry to SD card
    loraOk = false;
  } else {
    Serial.println("done.");
    loraOk = true;
  }
}


void loop() {
  nowMillis = millis();
  // Run telemetry loop every 10s
  if (nowMillis - prevTelemetryLoopMillis >= 10000) {
    if (accOk) acc_gyro();
    if (shieldOk) env();
    if (gpsOk) gps();

    monitor();
    if (sdOk) SDcard();

    // Update loop timestamp
    prevTelemetryLoopMillis = nowMillis;
  }

  if (loraOk) telecom();
}

void telecom() {
  // Check for new received packets
  telecom_rx(rxLogFileName);

  // Transmit packets waiting in queue
  telecom_tx(&queue, TELECOM_DUTY_CYCLE_EU868);
}

//Function for accelerometer and gyroscope
void acc_gyro() {
  aX = lsm6ds3.readFloatAccelX();
  aY = lsm6ds3.readFloatAccelY();
  aZ = lsm6ds3.readFloatAccelZ();

  telecomPacket packet_aX;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_ACC_X, aX, &packet_aX);
  telecomQueue_enqueue(&queue, &packet_aX);

  telecomPacket packet_aY;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_ACC_Y, aY, &packet_aY);
  telecomQueue_enqueue(&queue, &packet_aY);

  telecomPacket packet_aZ;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_ACC_Z, aZ, &packet_aZ);
  telecomQueue_enqueue(&queue, &packet_aZ);

  gX = lsm6ds3.readFloatGyroX();
  gY = lsm6ds3.readFloatGyroY();
  gZ = lsm6ds3.readFloatGyroZ();

  telecomPacket packet_gX;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_GYRO_X, gX, &packet_gX);
  telecomQueue_enqueue(&queue, &packet_gX);

  telecomPacket packet_gY;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_GYRO_Y, gY, &packet_gY);
  telecomQueue_enqueue(&queue, &packet_gY);

  telecomPacket packet_gZ;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_GYRO_Z, gZ, &packet_gZ);
  telecomQueue_enqueue(&queue, &packet_gZ);
}

//Function for environment
void env() {
  temperature = ENV.readTemperature();
  humidity = ENV.readHumidity();
  pressure = ENV.readPressure();
  illuminance = ENV.readIlluminance();

  telecomPacket packet_temperature;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_TEMPERATURE, temperature, &packet_temperature);
  telecomQueue_enqueue(&queue, &packet_temperature);

  telecomPacket packet_humidity;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_HUMIDITY, humidity, &packet_humidity);
  telecomQueue_enqueue(&queue, &packet_humidity);

  telecomPacket packet_pressure;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_PRESSURE, pressure, &packet_pressure);
  telecomQueue_enqueue(&queue, &packet_pressure);

  telecomPacket packet_illuminance;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_ILLUMINANCE, illuminance, &packet_illuminance);
  telecomQueue_enqueue(&queue, &packet_illuminance);
}

//Function for motor
void motor() {
}

//Function for GPS
void gps() {
  latitude = myGNSS.getLatitude() / 10000000.0;
  longitude = myGNSS.getLongitude() / 10000000.0;
  speed = myGNSS.getGroundSpeed() * 100; // Conversion de mm/s en m/s
  timeUNIX  = myGNSS.getUnixEpoch();

  telecomPacket packet_lat;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_GPS_LAT, latitude, &packet_lat);
  telecomQueue_enqueue(&queue, &packet_lat);

  telecomPacket packet_lon;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_GPS_LON, longitude, &packet_lon);
  telecomQueue_enqueue(&queue, &packet_lon);

  telecomPacket packet_speed;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_GPS_SPEED, speed, &packet_speed);
  telecomQueue_enqueue(&queue, &packet_speed);

  telecomPacket packet_time;
  telecomPacket_init_float(nowMillis / 1000, TELECOM_PACKET_SOURCE_ASCENT, TELECOM_PACKET_TYPE_GPS_TIME, timeUNIX, &packet_time);
  telecomQueue_enqueue(&queue, &packet_time);
}

//Function to save on SD card
void SDcard() {
  file = SD.open(telemetryFileName, FILE_WRITE);
  if (file) {
    file.print(nowMillis);
    file.print(",");

    file.print(temperature);
    file.print(",");

    file.print(humidity);
    file.print(",");

    file.print(pressure);
    file.print(",");

    file.print(illuminance);
    file.print(",");

    file.print(aX);
    file.print(",");

    file.print(aY);
    file.print(",");

    file.print(aZ);
    file.print(",");

    file.print(gX);
    file.print(",");

    file.print(gY);
    file.print(",");

    file.print(gZ);

    //GPS
    file.print(latitude, 7);
    file.print(",");

    file.print(longitude, 7);
    file.print(",");

    file.print(speed, 4);
    file.print(",");

    file.print(timeUNIX);
    file.println();

    file.close();
  } else {
    Serial.println("Error opening file for writing");
  }
}

void monitor() {
  Serial.print("Temperature = ");
  Serial.print(temperature);
  Serial.println(" °C");

  Serial.print("Humidity    = ");
  Serial.print(humidity);
  Serial.println(" %");

  Serial.print("Pressure    = ");
  Serial.print(pressure);
  Serial.println(" kPa");

  Serial.print("Illuminance = ");
  Serial.print(illuminance);
  Serial.println(" lx");

  Serial.print("aX = ");
  Serial.print(aX);
  Serial.print("    aY = ");
  Serial.print(aY);
  Serial.print("    aZ = ");
  Serial.println(aZ);

  Serial.print("gX = ");
  Serial.print(gX);
  Serial.print("    gY = ");
  Serial.print(gY);
  Serial.print("    gZ = ");
  Serial.println(gZ);

  //GPS
  Serial.print("GPS latitude = ");
  Serial.println(latitude, 7);
  Serial.print("GPS longitude = ");
  Serial.println(longitude);
  Serial.print("GPS speed = ");
  Serial.println(speed);
  Serial.print("GPS time (UNIX) = ");
  Serial.println(timeUNIX);
}
