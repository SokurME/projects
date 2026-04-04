#include "HX711.h"

#define HX711_DOUT 4
#define HX711_SCK 5

HX711 scale;
const float KNOWN_WEIGHT = 450.0;  // Ваш эталонный вес в граммах

void setup() {
  Serial.begin(9600);
  Serial.print(F("=== КАЛИБРОВКА С ВЕСОМ "));
  Serial.print(KNOWN_WEIGHT);
  Serial.println(F(" ГРАММ ==="));
  
  scale.begin(HX711_DOUT, HX711_SCK);
  
  Serial.println(F("ШАГ 1: Уберите весь вес с датчика"));
  delay(3000);
  scale.tare();
  Serial.println(F("Обнуление выполнено"));
  
  Serial.print(F("\nШАГ 2: Положите груз "));
  Serial.print(KNOWN_WEIGHT);
  Serial.println(F(" грамма"));
  Serial.println(F("(подождите 5 секунд)"));
  delay(5000);
  
  float reading = scale.get_units(10);
  Serial.print(F("Сырое значение датчика: "));
  Serial.println(reading);
  
  float newFactor = reading / KNOWN_WEIGHT;  // Правильная формула
  Serial.println(F("\n=== РЕЗУЛЬТАТ ==="));
  Serial.print(F("Ваш калибровочный коэффициент: "));
  Serial.println(newFactor, 4);
  
  scale.set_scale(newFactor);
  Serial.print(F("Проверка: вес = "));
  Serial.print(scale.get_units(5), 2);
  Serial.println(F(" грамм"));
  
  Serial.println(F("\nСкопируйте этот коэффициент в основной код:"));
  Serial.print(F("const float CALIBRATION_FACTOR = "));
  Serial.print(newFactor, 4);
  Serial.println(F(";"));
}

void loop() {
  // Постоянное отображение веса после калибровки
  if (scale.is_ready()) {
    float weight = scale.get_units(5);
    Serial.print(F("Вес: "));
    Serial.print(weight, 2);
    Serial.println(F(" грамм"));
  }
  delay(500);
}
