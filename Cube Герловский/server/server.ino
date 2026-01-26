#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ArduinoJson.h>

// Настройки WiFi
const char* ssid = "ASUSBOOK5398";
const char* password = "79q=98T1";

// Создаем веб-сервер на порту 80
ESP8266WebServer server(80);

// Переменная для хранения случайного числа
int randomNumber = 0;

void setup() {
  // Инициализация Serial
  Serial.begin(115200);
  delay(100);
  
  Serial.println("\n\nESP8266 Random Number Server");
  Serial.println("============================\n");
  
  // Подключение к WiFi
  Serial.print("Подключение к WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWiFi подключен!");
  Serial.print("IP адрес: ");
  Serial.println(WiFi.localIP());
  
  // Инициализация генератора случайных чисел
  // Используем аналоговый шум для seed
  randomSeed(analogRead(A0));
  
  // Настройка маршрутов сервера
  server.on("/", handleRoot);           // Главная страница
  server.on("/data", handleData);       // JSON данные
  server.on("/random", handleRandom);   // Только число
  server.on("/info", handleInfo);       // Информация о сервере
  server.on("/generate", handleGenerate); // Принудительная генерация
  
  // Запуск сервера
  server.begin();
  Serial.println("HTTP сервер запущен");
  
  // Первоначальная генерация числа
  generateRandomNumber();
}

void loop() {
  // Обработка клиентских запросов
  server.handleClient();
}

// Генерация случайного числа от 1 до 10
void generateRandomNumber() {
  randomNumber = random(1, 11); // 11 не включается, поэтому 1-10
  Serial.print("Сгенерировано число: ");
  Serial.println(randomNumber);
}

// Обработка главной страницы
void handleRoot() {
  String html = "<!DOCTYPE html><html lang='ru'>";
  html += "<head><meta charset='UTF-8'>";
  html += "<meta name='viewport' content='width=device-width, initial-scale=1.0'>";
  html += "<title>ESP8266 Random Server</title>";
  html += "<style>";
  html += "body { font-family: Arial, sans-serif; text-align: center; margin: 50px; background-color: #f0f0f0; }";
  html += ".container { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); display: inline-block; }";
  html += "h1 { color: #2c3e50; }";
  html += ".number { font-size: 72px; font-weight: bold; color: #e74c3c; margin: 20px; }";
  html += ".button { background-color: #3498db; color: white; padding: 12px 24px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; margin: 10px; text-decoration: none; display: inline-block; }";
  html += ".button:hover { background-color: #2980b9; }";
  html += ".endpoints { margin-top: 30px; text-align: left; background: #f8f9fa; padding: 15px; border-radius: 5px; }";
  html += "</style></head>";
  html += "<body>";
  html += "<div class='container'>";
  html += "<h1>🌐 ESP8266 Random Server</h1>";
  html += "<p>Текущее случайное число:</p>";
  html += "<div class='number'>" + String(randomNumber) + "</div>";
  html += "<p><a class='button' href='/generate'>🎲 Сгенерировать новое</a></p>";
  html += "<div class='endpoints'>";
  html += "<h3>Доступные endpoints:</h3>";
  html += "<ul>";
  html += "<li><a href='/data'>/data</a> - JSON данные</li>";
  html += "<li><a href='/random'>/random</a> - Только число</li>";
  html += "<li><a href='/info'>/info</a> - Информация о сервере</li>";
  html += "</ul>";
  html += "</div>";
  html += "</div>";
  html += "</body></html>";
  
  server.send(200, "text/html; charset=utf-8", html);
}

// Обработка запроса JSON данных
void handleData() {
  // Генерируем новое число для каждого запроса
  generateRandomNumber();
  
  // Создаем JSON ответ
  StaticJsonDocument<200> jsonDoc;
  jsonDoc["random_number"] = randomNumber;
  jsonDoc["min"] = 1;
  jsonDoc["max"] = 10;
  jsonDoc["timestamp"] = millis();
  jsonDoc["chip_id"] = ESP.getChipId();
  
  String jsonResponse;
  serializeJson(jsonDoc, jsonResponse);
  
  // Устанавливаем заголовки CORS для доступа с других доменов
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  server.sendHeader("Access-Control-Allow-Headers", "Content-Type");
  
  server.send(200, "application/json", jsonResponse);
}

// Обработка запроса только числа
void handleRandom() {
  generateRandomNumber();
  
  // Устанавливаем заголовки CORS
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "text/plain", String(randomNumber));
}

// Обработка запроса информации
void handleInfo() {
  String info = "ESP8266 Random Number Server\n";
  info += "============================\n";
  info += "Chip ID: " + String(ESP.getChipId()) + "\n";
  info += "Flash Size: " + String(ESP.getFlashChipSize() / 1024) + " KB\n";
  info += "Free Heap: " + String(ESP.getFreeHeap()) + " bytes\n";
  info += "SSID: " + WiFi.SSID() + "\n";
  info += "IP Address: " + WiFi.localIP().toString() + "\n";
  info += "MAC Address: " + WiFi.macAddress() + "\n";
  info += "Uptime: " + String(millis() / 1000) + " seconds\n";
  
  server.sendHeader("Access-Control-Allow-Origin", "*");
  server.send(200, "text/plain", info);
}

// Обработка принудительной генерации
void handleGenerate() {
  generateRandomNumber();
  
  // Перенаправляем на главную страницу
  server.sendHeader("Location", "/");
  server.send(302, "text/plain", "Number generated. Redirecting...");
}
