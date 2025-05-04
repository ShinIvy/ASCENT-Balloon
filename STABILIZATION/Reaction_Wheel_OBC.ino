#include <SPI.h>
#include "LSM6DS3.h"
#include "Seeed_BMP280.h"
#include "Wire.h"
#include "DualTB9051FTGMotorShield.h"

//Initialisation of variables
float aX;
float aY;
float aZ;
float gX;
float gY;
float gZ;
int currentSpeed = 0;
int targetSpeed = 0;

//Create instance of classes
LSM6DS3 lsm6ds3(I2C_MODE, 0x6A);    //I2C device address 0x6A
BMP280 bmp280;
DualTB9051FTGMotorShield md;

void stopIfFault()
{
  if (md.getM1Fault())
  {
    Serial.println("M1 fault");
    while (1);
  }
}

void adjustSpeed(int targetSpeed) {
  
  if (targetSpeed > currentSpeed) {  
    for (int i = currentSpeed; i <= targetSpeed; i += 2) {
      md.setM1Speed(i);
      currentSpeed = i;
      stopIfFault();
      delay(10);
    }
  }
  else if (targetSpeed < currentSpeed) {  
    for (int i = currentSpeed; i >= targetSpeed; i -= 2) {
      md.setM1Speed(i);
      currentSpeed = i;
      stopIfFault();
      delay(10);
    }
  }
  //Serial.print("Motor speed : ");
  //Serial.println(currentSpeed);
  //Serial.println();
}

void setup() { //Initialisation
  Serial.begin(9600);
  while (!Serial);

  // Initialisation du motor shield 
  md.init();

  if (lsm6ds3.begin() != 0) { //Accéléromètre et Gyroscope
    Serial.println("Gyro error");
  } else {
    Serial.println("Gyro OK!");
  }
  if (!bmp280.init()) {
    Serial.println("Barometer error");
  } else {
    Serial.println("Barometer OK!");
  }
}

void loop() {
  // Initialisation des drivers du shield moteur 
  md.enableM1Driver();

  int rpm = 0;
  float max_rpm = 553; // A changer si pas en 12.1V : 548 rpm - 12V, 507 rpm - 11.1
  float max_pwm = 400;
  float rpm_to_pwm = max_pwm/max_rpm;
  float I_coeff = 268.7;

  float p_low = 80000;
  float p_high = 3000;

  // Lecture des données d'accélération
  aX = lsm6ds3.readFloatAccelX();
  aY = lsm6ds3.readFloatAccelY();
  aZ = lsm6ds3.readFloatAccelZ();
  // Lecture des données de gyroscope
  gX = lsm6ds3.readFloatGyroX();
  gY = lsm6ds3.readFloatGyroY();
  gZ = lsm6ds3.readFloatGyroZ() + 0.56; // Ajusté
  // Lecture de la Température
  float t = bmp280.getTemperature();
  // Lecture de la Pression
  float p1 = bmp280.getPressure();

  //Serial.print("aX = ");
  //Serial.print(aX);
  //Serial.print("g");
  //Serial.print("    aY = ");
  //Serial.print(aY);
  //Serial.print("g");
  //Serial.print("    aZ = ");
  //Serial.print(aZ);
  //Serial.println("g");
  //Serial.println();

  //Serial.print("gX = ");
  //Serial.print(gX);
  //Serial.print("°/s");
  //Serial.print("    gY = ");
  //Serial.print(gY);
  //Serial.print("°/s");
  //Serial.print("    gZ = ");
  //Serial.print(gZ);
  //Serial.println("°/s");
  //Serial.println();

  //Serial.print("Temp: ");
  //Serial.print(t);
  //Serial.println("°C");
  //Serial.println();

  //Serial.print("Pression: ");
  //Serial.print(p1);
  //Serial.println(" Pa");
  //Serial.println();

  if (p1 < p_low && p1 > p_high ) {
    if (abs(gZ) < 6) {
        if (gZ < 0) {
          gZ = -6;
        }
        else {
          gZ = 6;
        }
    }
    else {
      gZ = gZ;
    }
    rpm = round(gZ * rpm_to_pwm * I_coeff / 6);  //en pwm% : /6 pour passer de °/s en rpm
    Serial.print("rpm : ");
    Serial.println(rpm / rpm_to_pwm);
      if(abs(rpm) < max_pwm){
        targetSpeed = rpm;
      }
      else{
        targetSpeed = max_pwm;
      }
      adjustSpeed(targetSpeed);
  }
  else {
      adjustSpeed(0); 
      md.disableDrivers();
      Serial.println("Motor stopped");
      Serial.println();
  }

  delay(50);
}
