// ========== НАСТРОЙКИ ПРОЕКТА ==========
#define TIME_INTERVAL 1000        // Интервал опроса датчиков (мс)
#define GAS_THRESHOLD_PPM 2000    // Порог срабатывания датчика газа (ppm CO2)
#define SERVO_DELAY 5000          // Время вращения сервы при тревоге (мс)
#define DEBUG 0
#define SMOOTHING_WINDOW 10       // Размер окна скользящего среднего

// Для сервопривода ПОСТОЯННОГО ВРАЩЕНИЯ:
// 90 = СТОП
// 0 = полный ход в одну сторону
// 180 = полный ход в другую сторону
#define SERVO_STOP 90
#define SERVO_FORWARD 0           // Направление для тревоги (можно поменять на 180)

// ========== ОПРЕДЕЛЕНИЕ ПИНОВ ==========
// Датчики
#define DHT_PIN 2                // DHT11
#define GAS_PIN A0               // MQ135 датчик газа (аналоговый выход)
#define MIC_PIN A1               // MAX9814
#define BUZZER_PIN 3             // Пьезопищалка (опционально)

// Тензодатчик (HX711)
#define HX711_DOUT 4
#define HX711_SCK 5

// Сервопривод
#define SERVO_PIN 9

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

// ========== КЛАСС ДЛЯ СКОЛЬЗЯЩЕГО СРЕДНЕГО ==========
class MovingAverage {
private:
  float buffer[SMOOTHING_WINDOW];
  int index;
  int count;
  float sum;
  
public:
  MovingAverage() {
    index = 0;
    count = 0;
    sum = 0;
    for (int i = 0; i < SMOOTHING_WINDOW; i++) {
      buffer[i] = 0;
    }
  }
  
  float addValue(float value) {
    if (count < SMOOTHING_WINDOW) {
      // Заполняем буфер
      buffer[count] = value;
      sum += value;
      count++;
      return sum / count;
    } else {
      // Замещаем старые значения
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
  }
};

// ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
MovingAverage tempAvg;
MovingAverage humAvg;
MovingAverage gasAvg;
MovingAverage micAvg;
MovingAverage weightAvg;

float rawTemperature = 0;
float rawHumidity = 0;
float rawGasPPM = 0;
int rawMicValue = 0;
float rawWeight = 0;

float temperature = 0;
float humidity = 0;
float gasPPM = 0;
int micValue = 0;
float weight = 0;

bool gasAlert = false;
unsigned long lastServoMove = 0;
bool servoCommandSent = false;

// Для демо-режима
bool demoMode = false;
unsigned long demoStartTime = 0;
float savedGasPPM = 0;

// Калибровка тензодатчика
const float CALIBRATION_FACTOR = -96650.0;

// ========== SETUP ==========
void setup() {
  Serial.begin(9600);
  
  dht.begin();
  scale.begin(HX711_DOUT, HX711_SCK);
  
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(MIC_PIN, INPUT);
  
  // scale.set_scale(CALIBRATION_FACTOR);
  // scale.tare();
  
  // ИНИЦИАЛИЗАЦИЯ СЕРВО ПОСТОЯННОГО ВРАЩЕНИЯ
  servo.attach(SERVO_PIN);
  delay(100);
  servo.write(SERVO_STOP);    // СТОП
  delay(500);
  
  delay(2000);
  #if DEBUG == 1
  Serial.println("========================================");
  Serial.println("System initialized");
  Serial.println("Порог тревоги: 2000 ppm CO2");
  Serial.println("Сервопривод постоянного вращения");
  Serial.println("Скользящее среднее: 10 значений");
  Serial.println("========================================");
  #endif
}

// ========== LOOP ==========
void loop() {
  static unsigned long lastUpdate = 0;
  
  // Опрос датчиков (раз в секунду)
  if (millis() - lastUpdate >= TIME_INTERVAL) {
    lastUpdate = millis();
    
    readSensors();
    applySmoothing();         // Применяем скользящее среднее
    processGasAlert();
    sendDataToESP();
  }
  
  // Остановка вращения через заданное время
  if (gasAlert && (millis() - lastServoMove >= SERVO_DELAY)) {
    servo.write(SERVO_STOP);    // СТОП
    delay(15);
    gasAlert = false;
    servoCommandSent = false;
    #if DEBUG == 1
    Serial.println("🔄 Серво остановлен (таймаут)");
    #endif
  }
  
  // Демо-режим
  if (demoMode && (millis() - demoStartTime >= 3000)) {
    demoMode = false;
    gasPPM = savedGasPPM;
    
    if (gasAlert) {
      servo.write(SERVO_STOP);
      delay(15);
      gasAlert = false;
      servoCommandSent = false;
    }
    
    Serial.println("DEMO_END");
    #if DEBUG == 1
    Serial.println("🏁 Демо-режим завершён");
    #endif
  }
  
  // Команды от ESP8266
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    if (cmd == "DEMO_ALERT") {
      if (!demoMode && !gasAlert) {
        demoMode = true;
        demoStartTime = millis();
        savedGasPPM = gasPPM;
        rawGasPPM = 2500;         // Сырое значение для демо
        applySmoothing();          // Применяем сглаживание
        processGasAlert();
        
        Serial.println("DEMO_START");
        #if DEBUG == 1
        Serial.println("🎬 Демо: CO2 = 2500 ppm");
        #endif
      }
    }
  }
}

// ========== ЧТЕНИЕ ДАННЫХ С ДАТЧИКОВ ==========
void readSensors() {
  rawTemperature = dht.readTemperature();
  rawHumidity = dht.readHumidity();
  
  if (!demoMode) {
    if (!isnan(rawTemperature) && !isnan(rawHumidity) && rawTemperature > -50 && rawHumidity >= 0 && rawHumidity <= 100) {
      rawGasPPM = gasSensor.getCorrectedPPM(rawTemperature, rawHumidity);
    } else {
      rawGasPPM = gasSensor.getPPM();
    }
  }
  
  rawMicValue = analogRead(MIC_PIN);
  
  if (scale.is_ready()) {
    rawWeight = scale.get_units(5);
  }
  
  if (isnan(rawTemperature) || isnan(rawHumidity)) {
    rawTemperature = -99;
    rawHumidity = -99;
  }
  
  if (rawGasPPM < 300 || rawGasPPM > 5000) {
    static unsigned long lastWarning = 0;
    if (millis() - lastWarning > 10000) {
       #if DEBUG == 1
      Serial.print("⚠️ Предупреждение: нереалистичное значение CO2: ");
      Serial.println(rawGasPPM);
      #endif
      lastWarning = millis();
    }
  }
}

// ========== ПРИМЕНЕНИЕ СКОЛЬЗЯЩЕГО СРЕДНЕГО ==========
void applySmoothing() {
  // Применяем фильтр только для корректных значений
  if (rawTemperature != -99 && rawTemperature > -50 && rawTemperature < 100) {
    temperature = tempAvg.addValue(rawTemperature);
  } else {
    temperature = -99;
  }
  
  if (rawHumidity != -99 && rawHumidity >= 0 && rawHumidity <= 100) {
    humidity = humAvg.addValue(rawHumidity);
  } else {
    humidity = -99;
  }
  
  if (rawGasPPM >= 300 && rawGasPPM <= 5000) {
    gasPPM = gasAvg.addValue(rawGasPPM);
  } else {
    gasPPM = gasAvg.addValue(400); // Подставляем нормальное значение для фильтра
  }
  
  micValue = (int)micAvg.addValue((float)rawMicValue);
  weight = weightAvg.addValue(rawWeight);
}

// ========== ОБРАБОТКА ПРЕВЫШЕНИЯ ГАЗА ==========
void processGasAlert() {
  if (gasPPM > GAS_THRESHOLD_PPM && !gasAlert && !servoCommandSent) {
    gasAlert = true;
    servoCommandSent = true;
    
    // ЗАПУСКАЕМ ВРАЩЕНИЕ (полный ход)
    servo.write(SERVO_FORWARD);
    delay(15);
    lastServoMove = millis();
    
    // Сигнал тревоги
    for (int i = 0; i < 3; i++) {
      digitalWrite(BUZZER_PIN, HIGH);
      delay(100);
      digitalWrite(BUZZER_PIN, LOW);
      delay(100);
    }
     #if DEBUG == 1
    Serial.print("🚨 GAS ALERT! CO2: ");
    Serial.print(gasPPM);
    Serial.println(" ppm (превышен порог 2000 ppm)");
    Serial.println("🔧 Серво начал вращение");
    #endif
  }
}

// ========== ПЕРЕДАЧА ДАННЫХ НА ESP ==========
void sendDataToESP() {
  Serial.print("T:");
  if (temperature == -99) {
    Serial.print("0.0");
  } else {
    Serial.print(temperature, 1);
  }
  
  Serial.print(",H:");
  if (humidity == -99) {
    Serial.print("0.0");
  } else {
    Serial.print(humidity, 1);
  }
  
  Serial.print(",G:");
  Serial.print(gasPPM, 1);
  
  Serial.print(",M:");
  Serial.print(micValue);
  
  Serial.print(",W:");
  Serial.print(weight, 2);
  
  Serial.print(",A:");
  Serial.print(gasAlert ? "1" : "0");
  
  Serial.println();
}

// ========== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ==========
void calibrateScale() {
   #if DEBUG == 1
  Serial.println("Calibrating scale...");
  Serial.println("Remove all weight from scale");
  #endif
  delay(3000);
  
  scale.tare();
   #if DEBUG == 1
  Serial.println("Tare done");
  
  Serial.println("Place known weight on scale");
  #endif
  delay(5000);
  
  float reading = scale.get_units(10);
  float factor = reading / 1000.0;
   #if DEBUG == 1
  Serial.print("Calibration factor: ");
  Serial.println(factor);
  #endif
}
