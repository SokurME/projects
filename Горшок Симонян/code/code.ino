// Умный горшок. Полная программа с фоторезистором и реле на D4
#include <DHT.h>

// --- ПИНЫ ---
#define RELAY_PIN 2       // Реле на D2 (управление питанием УЗ датчика)
#define RELAY_D4_PIN 4    // Новое реле на D4 (включается при темноте)
#define RGB_RED_PIN 6     // Красный канал RGB
#define RGB_GREEN_PIN 7   // Зеленый канал RGB
#define RGB_BLUE_PIN 8    // Синий канал RGB
#define WATER_SENSOR_PIN A0  // Датчик воды на A0 (обратная логика: высокое = влажно)
#define PHOTORESISTOR_PIN A2 // Фоторезистор на A2 (высокое = светло)
#define PUMP_PIN 3        // Насос на D3
#define DHTPIN 5          // DHT11 на D5

// --- НАСТРОЙКИ ---
#define DELAY_BEFORE_ULTRASONIC 5000   // Через сколько включить УЗ (5 сек)
#define ULTRASONIC_ON_TIME 10000       // Время работы УЗ датчика (10 сек)
#define TOTAL_RGB_TIME 20000           // Общее время горения RGB (20 сек)
#define SOIL_DRY_THRESHOLD 400         // Порог сухой почвы (значение датчика)
#define PUMP_DELAY 5000                // Задержка перед включением насоса (5 сек)
#define PUMP_ON_TIME 5000              // Время работы насоса (5 сек)
#define GREEN_AFTER_PUMP_TIME 5000     // Зеленый свет после насоса (5 сек)

// Пороги для фоторезистора
#define DARK_THRESHOLD 600    // Ниже этого значения - темно (включаем реле D4)
#define BRIGHT_THRESHOLD 900  // Выше этого значения - ярко

#define DHTTYPE DHT11     // Тип датчика

// Объект DHT
DHT dht(DHTPIN, DHTTYPE);

void setup() {
  delay(3000); // Пауза для стабилизации системы
  Serial.begin(9600);
  
  // Инициализация пинов
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW); // Выключаем реле D2
  
  pinMode(RELAY_D4_PIN, OUTPUT);
  digitalWrite(RELAY_D4_PIN, LOW); // Выключаем реле D4
  
  pinMode(PUMP_PIN, OUTPUT);
  digitalWrite(PUMP_PIN, LOW); // Выключаем насос
  
  pinMode(RGB_RED_PIN, OUTPUT);
  pinMode(RGB_GREEN_PIN, OUTPUT);
  pinMode(RGB_BLUE_PIN, OUTPUT);
  
  // Инициализация DHT11
  dht.begin();
  
  // === ШАГ 0: Проверка освещенности ===
  int lightValue = analogRead(PHOTORESISTOR_PIN);
  Serial.print("   Значение фоторезистора: ");
  Serial.println(lightValue);
  
  if (lightValue < DARK_THRESHOLD) {
    Serial.println("   ОСВЕЩЕННОСТЬ: ТЕМНО (значение < 500)");
  } else if (lightValue > BRIGHT_THRESHOLD) {
    Serial.println("   ОСВЕЩЕННОСТЬ: ЯРКО (значение > 900)");
  } else {
    Serial.println("   ОСВЕЩЕННОСТЬ: НОРМАЛЬНО (500-900)");
  }
  delay(2000);
  
  // === ШАГ 1: Проверка влажности почвы ===
  int soilValue = analogRead(WATER_SENSOR_PIN);
  Serial.print("   Значение датчика почвы: ");
  Serial.println(soilValue);
  
  if (soilValue < SOIL_DRY_THRESHOLD) {
    // Почва сухая - включаем СИНИЙ и ждем полива
    Serial.println("   Почва СУХАЯ! Включаем синий свет.");
    Serial.println("   Поливайте растение!");
    
    analogWrite(RGB_RED_PIN, 0);
    analogWrite(RGB_GREEN_PIN, 0);
    analogWrite(RGB_BLUE_PIN, 255); // СИНИЙ
    
    // Ждем, пока почва не станет влажной
    bool isWatered = false;
    
    while (!isWatered) {
      soilValue = analogRead(WATER_SENSOR_PIN);
      
      // Выводим значение каждую секунду
      static unsigned long lastPrint = 0;
      if (millis() - lastPrint >= 1000) {
        lastPrint = millis();
        Serial.print("   Текущее значение: ");
        Serial.println(soilValue);
      }
      
      // Проверяем, достигли ли нужной влажности
      if (soilValue >= SOIL_DRY_THRESHOLD) {
        isWatered = true;
        Serial.println("   Отлично! Почва теперь влажная.");
      }
      
      delay(100);
    }
    
    delay(1000);
  } else {
    Serial.println("   Почва уже влажная. Пропускаем полив.");
  }
  
  // === ШАГ 2: Почва влажная - включаем ЗЕЛЕНЫЙ ===
  analogWrite(RGB_RED_PIN, 0);
  analogWrite(RGB_GREEN_PIN, 255); // ЗЕЛЕНЫЙ
  analogWrite(RGB_BLUE_PIN, 0);
  delay(2000);
  Serial.println("   Зеленый свет: 2 секунды - завершено");
  
  // === ШАГ 3: КРАСНЫЙ свет и включение НАСОСА ===
  analogWrite(RGB_RED_PIN, 255); // КРАСНЫЙ
  analogWrite(RGB_GREEN_PIN, 0);
  analogWrite(RGB_BLUE_PIN, 0);
  Serial.println("   Красный свет ВКЛ");
  
  delay(PUMP_DELAY);
  
  Serial.println("   Насос ВКЛЮЧЕН (на 5 секунд)");
  digitalWrite(PUMP_PIN, HIGH); // ВКЛ насос
  
  delay(PUMP_ON_TIME);
  
  digitalWrite(PUMP_PIN, LOW); // ВЫКЛ насос
  Serial.println("   Насос ВЫКЛЮЧЕН");
  
  // === ШАГ 4: ЗЕЛЕНЫЙ после насоса (5 секунд) ===
  Serial.println("\n=== ШАГ 4: Зеленый свет после насоса ===");
  analogWrite(RGB_RED_PIN, 0);
  analogWrite(RGB_GREEN_PIN, 255); // ЗЕЛЕНЫЙ
  analogWrite(RGB_BLUE_PIN, 0);
  Serial.print("   Зеленый свет на ");
  Serial.print(GREEN_AFTER_PUMP_TIME / 1000);
  Serial.println(" секунд");
  delay(GREEN_AFTER_PUMP_TIME);
  
  // === ШАГ 5: Ждем ТЕМНОТЫ и включаем реле D4 ===
  
  bool isDark = false;
  while (!isDark) {
    lightValue = analogRead(PHOTORESISTOR_PIN);
    
    static unsigned long lastPrint = 0;
    if (millis() - lastPrint >= 2000) {
      lastPrint = millis();
      Serial.print("   Текущее значение фоторезистора: ");
      Serial.println(lightValue);
    }
    
    if (lightValue < DARK_THRESHOLD) {
      isDark = true;
    }
    
    delay(100);
  }
  
  // Включаем реле D4 и оставляем включенным
  digitalWrite(RELAY_D4_PIN, HIGH); // ВКЛ реле D4 (проверьте логику!)
  Serial.println("   Реле D4 ВКЛЮЧЕНО и остается включенным");
  
  // === ШАГ 6: Основная демо-программа (желтый + УЗ) ===
 
  // Включаем желтый RGB
  analogWrite(RGB_RED_PIN, 255);
  analogWrite(RGB_GREEN_PIN, 150);
  analogWrite(RGB_BLUE_PIN, 0);
  Serial.println("   Желтый свет ВКЛ");
  
  delay(DELAY_BEFORE_ULTRASONIC);
  
  // Включаем реле D2 (ультразвук) через 5 секунд
  digitalWrite(RELAY_PIN, HIGH); // ВКЛ УЗ датчик
  Serial.println("   УЗ датчик ВКЛЮЧЕН (через 5 сек)");
  
  delay(ULTRASONIC_ON_TIME);
  
  // Выключаем реле D2 (УЗ датчик)
  digitalWrite(RELAY_PIN, LOW); // ВЫКЛ УЗ датчик
  Serial.println("   УЗ датчик ВЫКЛЮЧЕН (отработал 10 сек)");
  
  // Ждем оставшееся время для желтого света
  int remainingYellowTime = TOTAL_RGB_TIME - DELAY_BEFORE_ULTRASONIC - ULTRASONIC_ON_TIME;
  if (remainingYellowTime > 0) {
    delay(remainingYellowTime);
  }
  
  // Выключаем RGB (но реле D4 остается включенным!)
  analogWrite(RGB_RED_PIN, 0);
  analogWrite(RGB_GREEN_PIN, 0);
  analogWrite(RGB_BLUE_PIN, 0);
 }

void loop() {
  // Мониторинг всех датчиков и состояния реле D4
  static unsigned long lastSensorCheck = 0;
  
  if (millis() - lastSensorCheck >= 3000) {
    lastSensorCheck = millis();
    
    // 1. DHT11
    float humidity = dht.readHumidity();
    float temperature = dht.readTemperature();
    
    if (!isnan(humidity) && !isnan(temperature)) {
      Serial.print("Воздух: ");
      Serial.print(humidity);
      Serial.print("% влаж., ");
      Serial.print(temperature);
      Serial.print("°C | ");
    }
    
    // 2. Датчик почвы
    int soilValue = analogRead(WATER_SENSOR_PIN);
    Serial.print("Почва: ");
    Serial.print(soilValue);
    
    if (soilValue < SOIL_DRY_THRESHOLD) {
      Serial.print(" (СУХО!) | ");
    } else {
      Serial.print(" (норма) | ");
    }
    
    // 3. Фоторезистор
    int lightValue = analogRead(PHOTORESISTOR_PIN);
    Serial.print("Свет: ");
    Serial.print(lightValue);
    
    if (lightValue < DARK_THRESHOLD) {
      Serial.print(" (ТЕМНО) | ");
    } else if (lightValue > BRIGHT_THRESHOLD) {
      Serial.print(" (ЯРКО) | ");
    } else {
      Serial.print(" (норма) | ");
    }
    
    // 4. Состояние реле D4
    Serial.print("Реле D4: ");
    if (digitalRead(RELAY_D4_PIN) == HIGH) {
      Serial.println("ВКЛ");
    } else {
      Serial.println("ВЫКЛ");
    }
  }
  
  delay(100);
}
