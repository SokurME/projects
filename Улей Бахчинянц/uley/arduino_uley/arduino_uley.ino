// ========== НАСТРОЙКИ ПРОЕКТА ==========
#define TIME_INTERVAL 1000        // Интервал опроса датчиков (мс)
#define GAS_THRESHOLD 300         // Порог срабатывания датчика газа
#define SERVO_ANGLE 90            // Угол поворота сервы при тревоге
#define SERVO_DELAY 5000          // Время удержания сервы в положении (мс)

// ========== ОПРЕДЕЛЕНИЕ ПИНОВ ==========
// Датчики
#define DHT_PIN 2                // DHT11
#define GAS_PIN A0               // MQ датчик газа
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

// ========== ОБЪЯВЛЕНИЕ ОБЪЕКТОВ ==========
DHT dht(DHT_PIN, DHT11);
HX711 scale;
Servo servo;

// ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
float temperature = 0;
float humidity = 0;
int gasValue = 0;
int micValue = 0;
float weight = 0;
bool gasAlert = false;
unsigned long lastServoMove = 0;

// Калибровка тензодатчика
const float CALIBRATION_FACTOR = -96650.0; // Подобрать индивидуально

void setup() {
  Serial.begin(9600);
  
  // Инициализация датчиков
  dht.begin();
  scale.begin(HX711_DOUT, HX711_SCK);
  servo.attach(SERVO_PIN);
  
  // Настройка пинов
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(GAS_PIN, INPUT);
  pinMode(MIC_PIN, INPUT);
  
  // Калибровка тензодатчика
  scale.set_scale(CALIBRATION_FACTOR);
  scale.tare(); // Сброс на ноль
  
  // Исходное положение сервы
  servo.write(0);
  
  delay(2000);
  Serial.println("System initialized");
}

void loop() {
  static unsigned long lastUpdate = 0;
  
  // Опрос датчиков с заданным интервалом
  if (millis() - lastUpdate >= TIME_INTERVAL) {
    lastUpdate = millis();
    
    readSensors();
    processGasAlert();
    sendDataToESP();
    
    // Автовозврат сервы через заданное время
    if (gasAlert && (millis() - lastServoMove >= SERVO_DELAY)) {
      servo.write(0);
      gasAlert = false;
    }
  }
}

// ========== ЧТЕНИЕ ДАННЫХ С ДАТЧИКОВ ==========
void readSensors() {
  // DHT11
  temperature = dht.readTemperature();
  humidity = dht.readHumidity();
  
  // Датчик газа MQ
  gasValue = analogRead(GAS_PIN);
  
  // Микрофон MAX9814
  micValue = analogRead(MIC_PIN);
  
  // Тензодатчик
  if (scale.is_ready()) {
    weight = scale.get_units(5); // Усреднение 5 измерений
  }
  
  // Проверка ошибок DHT
  if (isnan(temperature) || isnan(humidity)) {
    temperature = -99;
    humidity = -99;
  }
}

// ========== ОБРАБОТКА ПРЕВЫШЕНИЯ ГАЗА ==========
void processGasAlert() {
  if (gasValue > GAS_THRESHOLD && !gasAlert) {
    gasAlert = true;
    servo.write(SERVO_ANGLE);
    lastServoMove = millis();
    
    // Сигнал тревоги
    digitalWrite(BUZZER_PIN, HIGH);
    delay(200);
    digitalWrite(BUZZER_PIN, LOW);
    
    Serial.print("GAS ALERT! Value: ");
    Serial.println(gasValue);
  }
}

// ========== ПЕРЕДАЧА ДАННЫХ НА ESP ==========
void sendDataToESP() {
  // Формат: T:25.5,H:60,G:245,M:512,W:12.34,A:0
  
  Serial.print("T:");
  Serial.print(temperature, 1);
  
  Serial.print(",H:");
  Serial.print(humidity, 1);
  
  Serial.print(",G:");
  Serial.print(gasValue);
  
  Serial.print(",M:");
  Serial.print(micValue);
  
  Serial.print(",W:");
  Serial.print(weight, 2);
  
  Serial.print(",A:");
  Serial.print(gasAlert ? "1" : "0");
  
  Serial.println(); // Конец строки
}

// ========== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ==========
void calibrateScale() {
  // Функция для калибровки тензодатчика
  Serial.println("Calibrating scale...");
  Serial.println("Remove all weight from scale");
  delay(3000);
  
  scale.tare();
  Serial.println("Tare done");
  
  Serial.println("Place known weight on scale");
  delay(5000);
  
  float reading = scale.get_units(10);
  float factor = reading / 1000.0; // Для веса 1000г
  
  Serial.print("Calibration factor: ");
  Serial.println(factor);
}
