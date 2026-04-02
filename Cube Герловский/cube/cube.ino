#include <Wire.h>
#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

// ==== НАСТРОЙТЕ ЭТИ ПАРАМЕТРЫ ПОД ВАШУ СЕТЬ ====
const char* ssid = "ASUSBOOK5398";      // Имя WiFi сети
const char* password = "79q=98T1";      // Пароль WiFi сети

// IP адрес компьютера (узнайте из Python программы)
const char* serverIP = "192.168.1.62";  // ЗАМЕНИТЕ на ваш IP!
const int serverPort = 8000;             // Порт сервера

// Конфигурация MPU6050
#define MPU6050_ADDR 0x68
#define SDA_PIN 4    // GPIO4 (D2)
#define SCL_PIN 5    // GPIO5 (D1)
#define CUBE_ID 1 // ID Куба

// Текущее состояние
String currentFace = "Неизвестно";
int currentFaceNumber = 0;
unsigned long lastSendTime = 0;
const long sendInterval = 2000; // Отправлять данные каждые 2 секунды

// Функция для преобразования грани в числовой код
int faceToNumber(String face) {
  if (face == "ВЕРХНЯЯ ВВЕРХУ") return 1;    // Зеленый - Завершил
  if (face == "НИЖНЯЯ ВВЕРХУ") return 2;     // Красный - Не понимаю
  if (face == "ЛЕВАЯ ВВЕРХУ") return 3;      // Салатовый - Готов
  if (face == "ПРАВАЯ ВВЕРХУ") return 4;     // Желтый - Выполняю
  if (face == "ПЕРЕДНЯЯ ВВЕРХУ") return 5;   // Белый - Устал
  if (face == "ЗАДНЯЯ ВВЕРХУ") return 6;     // Синий - Вопрос
  return 0; // Ребро/Угол
}

void setup() {
  Serial.begin(115200);
  delay(100);
  
  // Инициализация MPU6050
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x6B); // PWR_MGMT_1
  Wire.write(0);    // Выход из сна
  Wire.endTransmission(true);
  
  Serial.println("\n\n🎲 Cube ESP Client");
  Serial.println("MPU6050 Ready");
  
  // Подключаемся к WiFi
  WiFi.begin(ssid, password);
  Serial.print("Подключение к WiFi: ");
  Serial.println(ssid);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  Serial.println();
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("✅ WiFi подключен!");
    Serial.print("IP адрес ESP: ");
    Serial.println(WiFi.localIP());
    Serial.print("MAC адрес: ");
    Serial.println(WiFi.macAddress());
  } else {
    Serial.println("❌ Не удалось подключиться к WiFi!");
    Serial.println("Проверьте имя сети и пароль");
  }
  
  Serial.println("==================================");
  Serial.println("Куб готов к работе!");
  Serial.print("Данные отправляются на сервер: ");
  Serial.print(serverIP);
  Serial.print(":");
  Serial.println(serverPort);
  Serial.println("==================================");
}

void sendDataToServer() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi не подключен");
    return;
  }
  
  WiFiClient client;
  HTTPClient http;
  
  // Формируем URL для отправки данных
  String url = "http://" + String(serverIP) + ":" + String(serverPort) + "/data";
  
  http.begin(client, url);
  http.addHeader("Content-Type", "application/json");
  
  // Формируем JSON данные
  String jsonData = "{";
  jsonData += "\"cube_id\":1,";  // ID этого куба
  jsonData += "\"face\":\"" + currentFace + "\",";
  jsonData += "\"face_number\":" + String(currentFaceNumber) + ",";
  jsonData += "\"status\":\"" + getStatusForFace(currentFaceNumber) + "\",";
  jsonData += "\"ip\":\"" + WiFi.localIP().toString() + "\",";
  jsonData += "\"mac\":\"" + WiFi.macAddress() + "\"";
  jsonData += "}";
  
  // Отправляем POST запрос
  int httpCode = http.POST(jsonData);
  
  if (httpCode > 0) {
    if (httpCode == HTTP_CODE_OK) {
      String response = http.getString();
      Serial.println("✅ Данные отправлены успешно");
    } else {
      Serial.print("⚠️ HTTP код: ");
      Serial.println(httpCode);
    }
  } else {
    Serial.print("❌ Ошибка подключения: ");
    Serial.println(http.errorToString(httpCode));
  }
  
  http.end();
}

String getStatusForFace(int faceNumber) {
  switch(faceNumber) {
    case 1: return "Завершил";
    case 2: return "Не понимаю";
    case 3: return "Готов";
    case 4: return "Выполняю";
    case 5: return "Устал";
    case 6: return "Вопрос";
    default: return "Ребро/Угол";
  }
}

void readAccelSimple(int16_t &ax, int16_t &ay, int16_t &az) {
  Wire.beginTransmission(MPU6050_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  
  Wire.requestFrom(MPU6050_ADDR, 6);
  
  // Ждем данные
  unsigned long timeout = millis() + 100;
  while (Wire.available() < 6 && millis() < timeout) {
    delay(1);
  }
  
  if (Wire.available() >= 6) {
    ax = Wire.read() << 8 | Wire.read();
    ay = Wire.read() << 8 | Wire.read();
    az = Wire.read() << 8 | Wire.read();
  } else {
    ax = ay = az = 0;
  }
}

String determineTopFace(float accX, float accY, float accZ) {
  float absX = fabs(accX);
  float absY = fabs(accY);
  float absZ = fabs(accZ);
  
  const float faceThreshold = 0.7;
  float maxVal = max(max(absX, absY), absZ);
  
  if (maxVal < faceThreshold) {
    return "Ребро/Угол";
  }
  
  if (maxVal == absX) {
    return (accX > 0) ? "ЛЕВАЯ ВВЕРХУ" : "ПРАВАЯ ВВЕРХУ";
  }
  else if (maxVal == absY) {
    return (accY > 0) ? "ПЕРЕДНЯЯ ВВЕРХУ" : "ЗАДНЯЯ ВВЕРХУ";
  }
  else {
    return (accZ > 0) ? "ВЕРХНЯЯ ВВЕРХУ" : "НИЖНЯЯ ВВЕРХУ";
  }
}

void loop() {
  // Чтение данных с MPU6050
  int16_t rawX, rawY, rawZ;
  readAccelSimple(rawX, rawY, rawZ);
  
  // Конвертируем в g
  float accX = rawX / 16384.0;
  float accY = rawY / 16384.0;
  float accZ = rawZ / 16384.0;
  
  // Определяем грань ВВЕРХУ
  currentFace = determineTopFace(accX, accY, accZ);
  currentFaceNumber = faceToNumber(currentFace);
  
  // Отправляем данные на сервер каждые sendInterval миллисекунд
  if (millis() - lastSendTime >= sendInterval) {
    lastSendTime = millis();
    
    if (WiFi.status() == WL_CONNECTED) {
      sendDataToServer();
    } else {
      Serial.println("❌ WiFi отключен, данные не отправлены");
    }
  }
  
  // Периодический вывод в Serial
  static unsigned long lastPrint = 0;
  if (millis() - lastPrint > 3000) {
    lastPrint = millis();
    
    Serial.println("==================================");
    Serial.print("Грань вверху: ");
    Serial.println(currentFace);
    Serial.print("Статус: ");
    Serial.println(getStatusForFace(currentFaceNumber));
    Serial.print("WiFi: ");
    Serial.println(WiFi.status() == WL_CONNECTED ? "Подключен" : "Отключен");
    Serial.println("==================================");
  }
  
  delay(100);
}
