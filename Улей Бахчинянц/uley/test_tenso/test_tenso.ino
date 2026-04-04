#include "MQ135.h"

#define GAS_PIN A0

MQ135 gasSensor = MQ135(GAS_PIN);  // Используем значения по умолчанию

void setup() {
  Serial.begin(9600);
  Serial.println("MQ135 тест (библиотека с ATMOCO2=415.58)");
  delay(2000);
}

void loop() {
  float ppm = gasSensor.getPPM();
  Serial.print("CO2: ");
  Serial.print(ppm);
  Serial.println(" ppm");
  delay(2000);
}
