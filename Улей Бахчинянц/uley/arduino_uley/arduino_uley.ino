// ========== НАСТРОЙКИ ПРОЕКТА ==========
#define TIME_INTERVAL 1000        // Интервал опроса датчиков (мс)
#define GAS_THRESHOLD_PPM 2000    // Порог срабатывания датчика газа (ppm CO2)
#define SERVO_DURATION 700       // Время вращения сервы (мс) - время открытия/закрытия
#define DEBUG 0                   // 1 - включить отладку, 0 - выключить
#define SMOOTHING_WINDOW 10       // Размер окна скользящего среднего

// Для сервопривода ПОСТОЯННОГО ВРАЩЕНИЯ
#define SERVO_STOP 90
#define SERVO_OPEN 0              // Вперед - открыть крышку
#define SERVO_CLOSE 180           // Назад - закрыть крышку

// ========== ОПРЕДЕЛЕНИЕ ПИНОВ ==========
#define DHT_PIN 2                
#define GAS_PIN A0               
#define MIC_PIN A1               
#define BUZZER_PIN 3             
#define HX711_DOUT 4
#define HX711_SCK 5
#define SERVO_PIN 9

// ========== КАЛИБРОВКА ТЕНЗОДАТЧИКА ==========
const float CALIBRATION_FACTOR = 45.0;  // Калибровочный коэффициент (вес в граммах)

// ========== БИБЛИОТЕКИ ==========
#include <DHT.h>
#include <HX711.h>
#include <Servo.h>
#include "MQ135.h"

// ========== ОБЪЯВЛЕНИЕ ОБЪЕКТОВ ==========
DHT dht(DHT_PIN, DHT11);
HX711 scale;
Servo servo;
MQ135 gasSensor = MQ135(GAS_PIN);

// ========== ОПТИМИЗИРОВАННЫЙ КЛАСС ДЛЯ СКОЛЬЗЯЩЕГО СРЕДНЕГО ==========
class MovingAverage {
private:
  int16_t buffer[SMOOTHING_WINDOW];
  uint8_t index;
  uint8_t count;
  int32_t sum;
  
public:
  MovingAverage() : index(0), count(0), sum(0) {
    memset(buffer, 0, sizeof(buffer));
  }
  
  int16_t addValue(int16_t value) {
    if (count < SMOOTHING_WINDOW) {
      buffer[count] = value;
      sum += value;
      count++;
      return sum / count;
    } else {
      sum -= buffer[index];
      buffer[index] = value;
      sum += value;
      index = (index + 1) % SMOOTHING_WINDOW;
      return sum / SMOOTHING_WINDOW;
    }
  }
  
  void reset() {
    index = 0;
    count = 0;
    sum = 0;
    memset(buffer, 0, sizeof(buffer));
  }
  
  void forceValue(int16_t value) {
    for (int i = 0; i < SMOOTHING_WINDOW; i++) {
      buffer[i] = value;
    }
    sum = value * SMOOTHING_WINDOW;
    count = SMOOTHING_WINDOW;
    index = 0;
  }
};

// ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
// Объекты для скользящего среднего
MovingAverage tempAvg;
MovingAverage humAvg;
MovingAverage gasAvg;
MovingAverage micAvg;
MovingAverage weightAvg;

// Сырые данные
int16_t rawTemperature = 0;
int16_t rawHumidity = 0;
int16_t rawGasPPM = 0;
int16_t rawMicValue = 0;
int32_t rawWeight = 0;  // Изменено на int32_t для хранения веса в граммах

// Усреднённые данные
int16_t temperature = 0;
int16_t humidity = 0;
int16_t gasPPM = 0;
int16_t micValue = 0;
int32_t weight = 0;  // Вес в граммах (целое число)

// Состояния системы
bool lidOpen = false;           // Крышка открыта (газ превышен)
bool servoMoving = false;       // Серво в движении
bool demoMode = false;          // Демо-режим
unsigned long servoStartTime = 0;
unsigned long demoStartTime = 0;

// Демо-режим
int16_t savedGasPPM = 0;
int16_t savedRawGasPPM = 0;
bool savedLidOpen = false;

// ========== ПРОТОТИПЫ ФУНКЦИЙ ==========
void readSensors();
void applySmoothing();
void checkGasAndControlLid();
void sendDataToESP();
void calibrateScale();
void resetFilters();
void moveLid(int direction);
void stopLid();

// ========== SETUP ==========
void setup() {
  Serial.begin(9600);
  
  dht.begin();
  scale.begin(HX711_DOUT, HX711_SCK);
  scale.set_scale(CALIBRATION_FACTOR);
  scale.tare();
  delay(100);
  
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(MIC_PIN, INPUT);
  
  servo.attach(SERVO_PIN);
  delay(100);
  servo.write(SERVO_STOP);
  delay(500);
  
  delay(2000);
  
  #if DEBUG == 1
  Serial.println(F("System initialized"));
  Serial.println(F("Logic: Open lid on gas > 2000ppm, close lid when gas normal"));
  #endif
}

// ========== LOOP ==========
void loop() {
  static unsigned long lastUpdate = 0;
  
  if (millis() - lastUpdate >= TIME_INTERVAL) {
    lastUpdate = millis();
    
    readSensors();
    applySmoothing();
    checkGasAndControlLid();
    sendDataToESP();
  }
  
  // Остановка серво после завершения движения
  if (servoMoving && (millis() - servoStartTime >= SERVO_DURATION)) {
    stopLid();
  }
  
  // Завершение демо-режима
  if (demoMode && (millis() - demoStartTime >= 5000)) {
    #if DEBUG == 1
    Serial.println(F("=== EXITING DEMO MODE ==="));
    #endif
    
    demoMode = false;
    
    // Восстанавливаем реальные значения
    gasAvg.reset();
    rawGasPPM = savedRawGasPPM;
    
    for (int i = 0; i < SMOOTHING_WINDOW; i++) {
      gasPPM = gasAvg.addValue(rawGasPPM);
    }
    
    #if DEBUG == 1
    Serial.print(F("Real gas value: "));
    Serial.println(gasPPM);
    #endif
    
    // Если реальный газ в норме и крышка открыта - закрываем
    if (gasPPM <= GAS_THRESHOLD_PPM && lidOpen) {
      #if DEBUG == 1
      Serial.println(F("Gas normal, closing lid..."));
      #endif
      
      if (servoMoving) {
        servo.write(SERVO_STOP);
        delay(15);
        servoMoving = false;
      }
      
      moveLid(SERVO_CLOSE);
      lidOpen = false;
    }
    
    Serial.println("DEMO_END");
  }
  
  // Обработка команд
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    if (cmd == "DEMO_ALERT") {
      if (!demoMode) {
        demoMode = true;
        demoStartTime = millis();
        
        savedGasPPM = gasPPM;
        savedRawGasPPM = rawGasPPM;
        savedLidOpen = lidOpen;
        
        #if DEBUG == 1
        Serial.println(F("=== DEMO MODE START ==="));
        #endif
        
        // Симулируем превышение газа
        gasAvg.forceValue(2500);
        gasPPM = 2500;
        rawGasPPM = 2500;
        
        // Если крышка закрыта - открываем
        if (!lidOpen) {
          #if DEBUG == 1
          Serial.println(F("DEMO: Opening lid..."));
          #endif
          
          if (servoMoving) {
            servo.write(SERVO_STOP);
            delay(15);
            servoMoving = false;
          }
          
          moveLid(SERVO_OPEN);
          lidOpen = true;
          
          // Звуковой сигнал
          for (int i = 0; i < 3; i++) {
            digitalWrite(BUZZER_PIN, HIGH);
            delay(100);
            digitalWrite(BUZZER_PIN, LOW);
            delay(100);
          }
        }
        
        Serial.println("DEMO_START");
      }
    }
    
    else if (cmd == "CALIBRATE") {
      calibrateScale();
    }
    
    else if (cmd == "RESET_FILTERS") {
      resetFilters();
      Serial.println(F("FILTERS_RESET"));
    }
    
    else if (cmd == "TARE") {
      scale.tare();
      Serial.println(F("TARE_OK"));
    }
  }
}

// ========== УПРАВЛЕНИЕ КРЫШКОЙ ПО СОСТОЯНИЮ ГАЗА ==========
void checkGasAndControlLid() {
  static bool previousGasState = false;
  
  if (demoMode) return;
  
  bool currentGasState = (gasPPM > GAS_THRESHOLD_PPM);
  
  // Только при изменении состояния
  if (currentGasState != previousGasState) {
    if (currentGasState) {
      // Газ превышен - открываем крышку
      #if DEBUG == 1
      Serial.print(F("GAS EXCEEDED! CO2: "));
      Serial.print(gasPPM);
      Serial.println(F(" ppm - Opening lid"));
      #endif
      
      if (!lidOpen) {
        moveLid(SERVO_OPEN);
        lidOpen = true;
        
        // Звуковой сигнал тревоги
        for (int i = 0; i < 3; i++) {
          digitalWrite(BUZZER_PIN, HIGH);
          delay(100);
          digitalWrite(BUZZER_PIN, LOW);
          delay(100);
        }
      }
    } else {
      // Газ в норме - закрываем крышку
      #if DEBUG == 1
      Serial.print(F("Gas normal. CO2: "));
      Serial.print(gasPPM);
      Serial.println(F(" ppm - Closing lid"));
      #endif
      
      if (lidOpen) {
        moveLid(SERVO_CLOSE);
        lidOpen = false;
      }
    }
    
    previousGasState = currentGasState;
  }
}

// ========== ДВИЖЕНИЕ КРЫШКИ ==========
void moveLid(int direction) {
  // Останавливаем текущее движение
  if (servoMoving) {
    servo.write(SERVO_STOP);
    delay(15);
    servoMoving = false;
    delay(50);
  }
  
  // Запускаем движение
  servo.write(direction);
  delay(15);
  servoMoving = true;
  servoStartTime = millis();
  
  #if DEBUG == 1
  Serial.print(F("Lid moving: "));
  Serial.println(direction == SERVO_OPEN ? "OPEN" : "CLOSE");
  #endif
}

// ========== ОСТАНОВКА ДВИЖЕНИЯ ==========
void stopLid() {
  if (servoMoving) {
    servo.write(SERVO_STOP);
    delay(15);
    servoMoving = false;
    
    #if DEBUG == 1
    Serial.println(F("Lid stopped"));
    #endif
  }
}

// ========== ЧТЕНИЕ ДАТЧИКОВ ==========
void readSensors() {
  float t = dht.readTemperature();
  float h = dht.readHumidity();
  
  if (!isnan(t) && !isnan(h) && t > -50 && t < 100 && h >= 0 && h <= 100) {
    rawTemperature = (int16_t)(t * 10.0);
    rawHumidity = (int16_t)(h * 10.0);
    
    if (!demoMode) {
      rawGasPPM = (int16_t)gasSensor.getCorrectedPPM(t, h);
    }
  } else {
    rawTemperature = -990;
    rawHumidity = -990;
    if (!demoMode) {
      rawGasPPM = (int16_t)gasSensor.getPPM();
    }
  }
  
  rawMicValue = analogRead(MIC_PIN);
  
  // Чтение веса (в граммах)
  if (scale.is_ready()) {
    float w = scale.get_units(5);  // Вес в граммах
    if (w < 0 && w > -5) w = 0;
    rawWeight = (int32_t)(w);  // Сохраняем вес в граммах (целое число)
  } else {
    rawWeight = weight;
  }
  
  if (!demoMode && (rawGasPPM < 300 || rawGasPPM > 5000)) {
    static unsigned long lastWarning = 0;
    if (millis() - lastWarning > 10000) {
      #if DEBUG == 1
      Serial.print(F("Warning: unrealistic gas value: "));
      Serial.println(rawGasPPM);
      #endif
      lastWarning = millis();
    }
    rawGasPPM = 400;
  }
  
  #if DEBUG == 1
  static unsigned long lastDebugPrint = 0;
  if (millis() - lastDebugPrint > 10000) {
    Serial.println(F("--- Raw Data ---"));
    Serial.print(F("Temp: ")); Serial.print(rawTemperature / 10.0);
    Serial.print(F(" | Hum: ")); Serial.print(rawHumidity / 10.0);
    Serial.print(F(" | Gas: ")); Serial.print(rawGasPPM);
    Serial.print(F(" | Lid: ")); Serial.print(lidOpen ? "OPEN" : "CLOSED");
    Serial.print(F(" | Weight: ")); Serial.print(rawWeight / 1000.0, 3);
    Serial.println(F(" kg"));
    lastDebugPrint = millis();
  }
  #endif
}

// ========== ПРИМЕНЕНИЕ СКОЛЬЗЯЩЕГО СРЕДНЕГО ==========
void applySmoothing() {
  if (rawTemperature > -500) {
    temperature = tempAvg.addValue(rawTemperature);
  } else {
    temperature = -990;
  }
  
  if (rawHumidity > -500) {
    humidity = humAvg.addValue(rawHumidity);
  } else {
    humidity = -990;
  }
  
  if (!demoMode) {
    gasPPM = gasAvg.addValue(rawGasPPM);
  }
  
  micValue = micAvg.addValue(rawMicValue);
  weight = weightAvg.addValue(rawWeight);  // Вес в граммах
  
  #if DEBUG == 1
  static unsigned long lastDebugPrintAvg = 0;
  if (millis() - lastDebugPrintAvg > 10000) {
    Serial.println(F("--- Smoothed Data ---"));
    Serial.print(F("Temp: ")); Serial.print(temperature / 10.0, 1);
    Serial.print(F(" | Hum: ")); Serial.print(humidity / 10.0, 1);
    Serial.print(F(" | Gas: ")); Serial.print(gasPPM);
    Serial.print(F(" | Weight: ")); Serial.print(weight / 1000.0, 3);
    Serial.print(F(" | Lid: ")); Serial.println(lidOpen ? "OPEN" : "CLOSED");
    lastDebugPrintAvg = millis();
  }
  #endif
}

// ========== ОТПРАВКА ДАННЫХ ==========
void sendDataToESP() {
  Serial.print(F("T:"));
  if (temperature == -990) {
    Serial.print(F("0.0"));
  } else {
    Serial.print(temperature / 10.0, 1);
  }
  
  Serial.print(F(",H:"));
  if (humidity == -990) {
    Serial.print(F("0.0"));
  } else {
    Serial.print(humidity / 10.0, 1);
  }
  
  Serial.print(F(",G:"));
  Serial.print(gasPPM);
  
  Serial.print(F(",M:"));
  Serial.print(micValue);
  
  Serial.print(F(",W:"));
  // Отправляем вес в КИЛОГРАММАХ с 3 знаками после запятой
  Serial.print(weight / 1000.0, 3);
  
  Serial.print(F(",L:"));
  Serial.print(lidOpen ? "1" : "0");
  
  Serial.println();
}

// ========== КАЛИБРОВКА ==========
void calibrateScale() {
  Serial.println(F("=== КАЛИБРОВКА ТЕНЗОДАТЧИКА ==="));
  Serial.println(F("1. Уберите весь вес"));
  delay(3000);
  
  scale.tare();
  Serial.println(F("Тара сброшена"));
  
  Serial.println(F("2. Положите груз 450 грамм"));
  delay(5000);
  
  float reading = scale.get_units(10);
  float knownWeight = 450.0;  // Вес эталона в граммах
  
  if (reading != 0) {
    float newFactor = reading / knownWeight;
    Serial.print(F("Новый коэффициент: "));
    Serial.println(newFactor, 4);
    Serial.println(F("Обновите CALIBRATION_FACTOR:"));
    Serial.print(F("const float CALIBRATION_FACTOR = "));
    Serial.print(newFactor, 4);
    Serial.println(F(";"));
    
    scale.set_scale(newFactor);
    Serial.print(F("Проверка: "));
    Serial.print(scale.get_units(10), 2);
    Serial.println(F(" грамм"));
  }
  
  Serial.println(F("=== КАЛИБРОВКА ЗАВЕРШЕНА ==="));
}

// ========== СБРОС ФИЛЬТРОВ ==========
void resetFilters() {
  tempAvg.reset();
  humAvg.reset();
  gasAvg.reset();
  micAvg.reset();
  weightAvg.reset();
  
  #if DEBUG == 1
  Serial.println(F("Filters reset"));
  #endif
}
