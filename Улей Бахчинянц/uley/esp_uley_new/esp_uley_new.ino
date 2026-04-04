#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ArduinoJson.h>

// ========== НАСТРОЙКИ ОТЛАДКИ ==========
#define DEBUG 0  // 1 - включить отладку, 0 - выключить

// ========== НАСТРОЙКИ ТОЧКИ ДОСТУПА ==========
const char* ssid = "SmartHive_AP";
const char* password = "12345678";

// ========== НАСТРОЙКИ ФИЛЬТРАЦИИ ==========
#define MIN_TEMP -20.0
#define MAX_TEMP 80.0
#define MIN_HUM 0.0
#define MAX_HUM 100.0
#define MIN_GAS 300.0      // Минимальное адекватное значение CO2 (ppm)
#define MAX_GAS 5000.0     // Максимальное адекватное значение CO2 (ppm)
#define MIN_SOUND 0
#define MAX_SOUND 1023
#define MIN_WEIGHT -5.0
#define MAX_WEIGHT 500000.0

// ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
ESP8266WebServer server(80);

// Данные с датчиков
struct SensorData {
  float temperature = 0;
  float humidity = 0;
  float gas = 400;        // ppm, начальное значение
  int sound = 0;
  float weight = 0;
  bool alert = false;
  String lastUpdate = "Нет данных";
} sensorData;

// ========== HTML СТРАНИЦА (с порогом 2000 ppm и обновлением 3 сек) ==========
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Умный улей - Мониторинг</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
      margin: 0;
      padding: 20px;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
    }
    .header {
      text-align: center;
      background: #2c3e50;
      color: white;
      padding: 20px;
      border-radius: 10px;
      margin-bottom: 30px;
    }
    .cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }
    .card {
      background: white;
      border-radius: 10px;
      padding: 20px;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      transition: transform 0.3s;
    }
    .card:hover {
      transform: translateY(-5px);
    }
    .card h3 {
      margin-top: 0;
      color: #2c3e50;
      border-bottom: 2px solid #3498db;
      padding-bottom: 10px;
    }
    .value {
      font-size: 2.5em;
      font-weight: bold;
      text-align: center;
      margin: 20px 0;
    }
    .unit {
      color: #7f8c8d;
      font-size: 0.8em;
    }
    .alert {
      background: #ff6b6b !important;
      color: white;
      animation: pulse 2s infinite;
    }
    .normal {
      background: #1dd1a1 !important;
      color: white;
    }
    .warning {
      background: #ff9f43 !important;
      color: white;
    }
    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.8; }
      100% { opacity: 1; }
    }
    .status-bar {
      background: white;
      border-radius: 10px;
      padding: 15px;
      margin-bottom: 20px;
      text-align: center;
      font-size: 1.2em;
    }
    .controls {
      display: flex;
      justify-content: center;
      gap: 20px;
      margin-top: 20px;
      flex-wrap: wrap;
    }
    button {
      background: #3498db;
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 5px;
      cursor: pointer;
      font-size: 1em;
      transition: background 0.3s;
    }
    button:hover {
      background: #2980b9;
    }
    .demo-btn {
      background: #e67e22;
    }
    .demo-btn:hover {
      background: #d35400;
    }
    .chart-container {
      background: white;
      border-radius: 10px;
      padding: 20px;
      margin-top: 30px;
    }
    pre {
      background: #2c3e50;
      color: #ecf0f1;
      padding: 15px;
      border-radius: 10px;
      overflow: auto;
      font-size: 0.9em;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🐝 Умный улей - Мониторинг</h1>
      <p>IP адрес: %IPADDRESS%</p>
      <p>Последнее обновление: <span id="lastUpdate">%LASTUPDATE%</span></p>
    </div>
    
    <div class="status-bar" id="statusBar">
      <span id="statusText">Статус: Норма</span>
    </div>
    
    <div class="cards">
      <div class="card" id="tempCard">
        <h3>🌡️ Температура</h3>
        <div class="value"><span id="tempValue">%TEMPERATURE%</span> <span class="unit">°C</span></div>
      </div>
      
      <div class="card" id="humCard">
        <h3>💧 Влажность</h3>
        <div class="value"><span id="humValue">%HUMIDITY%</span> <span class="unit">%</span></div>
      </div>
      
      <div class="card" id="gasCard">
        <h3>⚠️ Уровень CO₂</h3>
        <div class="value"><span id="gasValue">%GAS%</span> <span class="unit">ppm</span></div>
        <div style="font-size: 0.8em; text-align: center;">⚠️ Порог тревоги: <strong>2000 ppm</strong></div>
      </div>
      
      <div class="card" id="soundCard">
        <h3>🎤 Уровень звука</h3>
        <div class="value"><span id="soundValue">%SOUND%</span> <span class="unit">ед.</span></div>
      </div>
      
      <div class="card" id="weightCard">
        <h3>⚖️ Вес улья</h3>
        <div class="value"><span id="weightValue">%WEIGHT%</span> <span class="unit">кг</span></div>
      </div>
      
      <div class="card" id="alertCard">
        <h3>🚨 Тревога</h3>
        <div class="value" id="alertValue">%ALERT%</div>
      </div>
    </div>
    
    <div class="controls">
      <button onclick="refreshData()">🔄 Обновить данные</button>
      <button onclick="sendDemoAlert()" class="demo-btn">⚠️ ДЕМО: Превышение CO₂</button>
      <button onclick="location.reload()">📱 Полное обновление</button>
    </div>
    
    <div class="chart-container" id="chartContainer" style="display:none;">
      <h3>📈 История показаний (последние 10 замеров)</h3>
      <canvas id="dataChart" width="400" height="200"></canvas>
    </div>
    
    <div style="background: white; border-radius: 10px; padding: 20px; margin-top: 30px;">
      <h3>📋 Последние данные в JSON</h3>
      <pre id="jsonData">Загрузка...</pre>
    </div>
  </div>
  
  <script>
    let dataHistory = {
      temperature: [],
      humidity: [],
      gas: [],
      sound: [],
      weight: []
    };
    
    function updateCards(data) {
      document.getElementById('tempValue').textContent = data.temperature.toFixed(1);
      document.getElementById('humValue').textContent = data.humidity.toFixed(1);
      document.getElementById('gasValue').textContent = Math.round(data.gas);
      document.getElementById('soundValue').textContent = data.sound;
      document.getElementById('weightValue').textContent = data.weight.toFixed(2);
      document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
      
      const alertCard = document.getElementById('alertCard');
      const alertValue = document.getElementById('alertValue');
      const statusBar = document.getElementById('statusBar');
      const statusText = document.getElementById('statusText');
      
      if (data.alert) {
        alertCard.className = 'card alert';
        alertValue.innerHTML = '🚨 АКТИВНА<br><small>CO₂ > 2000 ppm!</small>';
        statusBar.className = 'status-bar alert';
        statusText.textContent = '🚨 СТАТУС: ТРЕВОГА! Превышение CO₂ > 2000 ppm';
      } else if (data.gas > 1500) {
        alertCard.className = 'card warning';
        alertValue.innerHTML = '⚠️ ВНИМАНИЕ<br><small>CO₂ повышен</small>';
        statusBar.className = 'status-bar warning';
        statusText.textContent = '⚠️ СТАТУС: Внимание. Уровень CO₂ повышен';
      } else {
        alertCard.className = 'card normal';
        alertValue.innerHTML = '✅ НОРМА<br><small>CO₂ в норме</small>';
        statusBar.className = 'status-bar normal';
        statusText.textContent = '✅ СТАТУС: Норма. Все показания в порядке';
      }
      
      // Оценка температуры
      if (data.temperature > 35) {
        document.getElementById('tempCard').className = 'card warning';
      } else {
        document.getElementById('tempCard').className = 'card';
      }
      
      // Оценка влажности
      if (data.humidity > 80) {
        document.getElementById('humCard').className = 'card warning';
      } else {
        document.getElementById('humCard').className = 'card';
      }
      
      // Оценка газа (CO₂) с порогом 2000 ppm
      if (data.gas > 2000) {
        document.getElementById('gasCard').className = 'card alert';
      } else if (data.gas > 1500) {
        document.getElementById('gasCard').className = 'card warning';
      } else {
        document.getElementById('gasCard').className = 'card';
      }
        
      addToHistory(data);
      document.getElementById('jsonData').textContent = JSON.stringify(data, null, 2);
    }
    
    function addToHistory(data) {
      const maxItems = 10;
      dataHistory.temperature.push(data.temperature);
      dataHistory.humidity.push(data.humidity);
      dataHistory.gas.push(data.gas);
      dataHistory.sound.push(data.sound);
      dataHistory.weight.push(data.weight);
      
      Object.keys(dataHistory).forEach(key => {
        if (dataHistory[key].length > maxItems) {
          dataHistory[key].shift();
        }
      });
    }
    
    function refreshData() {
      fetch('/data')
        .then(response => response.json())
        .then(data => {
          updateCards(data);
        })
        .catch(error => {
          console.error('Error fetching data:', error);
        });
    }
    
    function sendDemoAlert() {
      fetch('/demo/alert', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
          console.log('Демо-тревога:', data);
          refreshData();
        })
        .catch(error => console.error('Error:', error));
    }
    
    function toggleChart() {
      const chartContainer = document.getElementById('chartContainer');
      if (chartContainer.style.display === 'none') {
        chartContainer.style.display = 'block';
        drawChart();
      } else {
        chartContainer.style.display = 'none';
      }
    }
    
    function drawChart() {
      const ctx = document.getElementById('dataChart').getContext('2d');
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: Array.from({length: dataHistory.temperature.length}, (_, i) => i + 1),
          datasets: [
            { label: 'Температура', data: dataHistory.temperature, borderColor: '#ff6b6b', yAxisID: 'y' },
            { label: 'Влажность', data: dataHistory.humidity, borderColor: '#3498db', yAxisID: 'y' },
            { label: 'CO₂', data: dataHistory.gas, borderColor: '#ff9f43', yAxisID: 'y1' }
          ]
        },
        options: {
          responsive: true,
          scales: {
            y: { title: { display: true, text: 'Температура/Влажность' } },
            y1: { position: 'right', title: { display: true, text: 'CO₂ (ppm)' }, grid: { drawOnChartArea: false } }
          }
        }
      });
    }
    
    // ОБНОВЛЕНИЕ КАЖДЫЕ 3 СЕКУНДЫ
    setInterval(refreshData, 3000);
    
    window.onload = function() { 
      refreshData(); 
    };
  </script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</body>
</html>
)rawliteral";

// ========== ПАРСИНГ ДАННЫХ С ARDUINO (универсальный) ==========
void parseSensorData(String data) {
  float temp = sensorData.temperature;
  float hum = sensorData.humidity;
  float gas = sensorData.gas;
  int sound = sensorData.sound;
  float weight = sensorData.weight;
  bool alert = sensorData.alert;
  
  bool hasValidData = false;
  
  // Разбиваем строку на части по запятым
  int start = 0;
  int end = data.indexOf(',');
  
  // Добавляем запятую в конец для обработки последнего параметра
  String workData = data;
  if (!workData.endsWith(",")) {
    workData += ",";
  }
  
  while (end > 0) {
    String pair = workData.substring(start, end);
    pair.trim();
    
    if (pair.length() > 2 && pair.indexOf(':') > 0) {
      String key = pair.substring(0, pair.indexOf(':'));
      String value = pair.substring(pair.indexOf(':') + 1);
      
      #if DEBUG == 1
        Serial.printf("Парсим: ключ=%s, значение=%s\n", key.c_str(), value.c_str());
      #endif
      
      if (key == "T") {
        float newTemp = value.toFloat();
        if (newTemp >= MIN_TEMP && newTemp <= MAX_TEMP) {
          temp = newTemp;
          hasValidData = true;
          #if DEBUG == 1
            Serial.printf("✅ Температура принята: %.1f°C\n", temp);
          #endif
        } else {
          #if DEBUG == 1
            Serial.printf("⚠️ Температура отброшена (некорректная): %.1f°C\n", newTemp);
          #endif
        }
      }
      else if (key == "H") {
        float newHum = value.toFloat();
        if (newHum >= MIN_HUM && newHum <= MAX_HUM) {
          hum = newHum;
          hasValidData = true;
          #if DEBUG == 1
            Serial.printf("✅ Влажность принята: %.1f%%\n", hum);
          #endif
        } else {
          #if DEBUG == 1
            Serial.printf("⚠️ Влажность отброшена (некорректная): %.1f%%\n", newHum);
          #endif
        }
      }
      else if (key == "G") {
        float newGas = value.toFloat();
        if (newGas >= MIN_GAS && newGas <= MAX_GAS) {
          gas = newGas;
          hasValidData = true;
          #if DEBUG == 1
            Serial.printf("✅ Газ принят: %.1f ppm\n", gas);
          #endif
        } else {
          #if DEBUG == 1
            Serial.printf("⚠️ Газ отброшен (некорректный): %.1f ppm\n", newGas);
          #endif
        }
      }
      else if (key == "M") {
        int newSound = value.toInt();
        if (newSound >= MIN_SOUND && newSound <= MAX_SOUND) {
          sound = newSound;
          hasValidData = true;
          #if DEBUG == 1
            Serial.printf("✅ Звук принят: %d\n", sound);
          #endif
        } else {
          #if DEBUG == 1
            Serial.printf("⚠️ Звук отброшен (некорректный): %d\n", newSound);
          #endif
        }
      }
      else if (key == "W") {
        float newWeight = value.toFloat();
        if (newWeight >= MIN_WEIGHT && newWeight <= MAX_WEIGHT) {
          weight = newWeight;
          hasValidData = true;
          #if DEBUG == 1
            Serial.printf("✅ Вес принят: %.2f\n", weight);
          #endif
        } else {
          #if DEBUG == 1
            Serial.printf("⚠️ Вес отброшен (некорректный): %.2f\n", newWeight);
          #endif
        }
      }
      else if (key == "L") {
        alert = (value == "1");
        hasValidData = true;
        #if DEBUG == 1
          Serial.printf("✅ Статус тревоги принят: %d\n", alert);
        #endif
      }
    }
    
    start = end + 1;
    end = workData.indexOf(',', start);
  }
  
  // Обновляем глобальную структуру
  if (hasValidData) {
    sensorData.temperature = temp;
    sensorData.humidity = hum;
    sensorData.gas = gas;
    sensorData.sound = sound;
    sensorData.weight = weight;
    sensorData.alert = alert;
    sensorData.lastUpdate = String(millis() / 1000) + " сек. назад";
    
    #if DEBUG == 1
      Serial.printf("📊 Итоговые данные: T=%.1f H=%.1f G=%.1f M=%d W=%.2f A=%d\n",
                    temp, hum, gas, sound, weight, alert);
    #endif
  } else {
    #if DEBUG == 1
      Serial.println("❌ Нет валидных данных для обновления");
    #endif
  }
}

// ========== ОБРАБОТЧИКИ ВЕБ-СЕРВЕРА ==========
void handleRoot() {
  String html = String(index_html);
  
  html.replace("%TEMPERATURE%", String(sensorData.temperature, 1));
  html.replace("%HUMIDITY%", String(sensorData.humidity, 1));
  html.replace("%GAS%", String((int)sensorData.gas));
  html.replace("%SOUND%", String(sensorData.sound));
  html.replace("%WEIGHT%", String(sensorData.weight, 2));
  html.replace("%ALERT%", sensorData.alert ? "АКТИВНА" : "НЕТ");
  html.replace("%LASTUPDATE%", sensorData.lastUpdate);
  html.replace("%IPADDRESS%", WiFi.softAPIP().toString());
  
  server.send(200, "text/html", html);
}

void handleData() {
  StaticJsonDocument<256> doc;
  
  doc["temperature"] = sensorData.temperature;
  doc["humidity"] = sensorData.humidity;
  doc["gas"] = sensorData.gas;
  doc["sound"] = sensorData.sound;
  doc["weight"] = sensorData.weight;
  doc["alert"] = sensorData.alert;
  doc["lastUpdate"] = sensorData.lastUpdate;
  doc["threshold"] = 2000;  // Передаём порог на клиент
  
  String response;
  serializeJson(doc, response);
  server.send(200, "application/json", response);
}

void handleDemoAlert() {
  // Отправляем команду на Arduino через Serial (всегда отправляем, даже при DEBUG 0)
  Serial.println("DEMO_ALERT");
  
  StaticJsonDocument<128> response;
  response["status"] = "ok";
  response["message"] = "Демо-тревога активирована (CO₂ > 2000 ppm)";
  
  String resp;
  serializeJson(response, resp);
  server.send(200, "application/json", resp);
  
  #if DEBUG == 1
    Serial.println("📢 Демо-тревога отправлена на Arduino");
  #endif
}

void handleNotFound() {
  String message = "File Not Found\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArguments: ";
  message += server.args();
  message += "\n";
  
  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }
  
  server.send(404, "text/plain", message);
}

// ========== SETUP ==========
void setup() {
  Serial.begin(9600);
  delay(100);
  
  #if DEBUG == 1
    Serial.println("\n\n=========================================");
    Serial.println("   ESP8266 ВЕБ-СЕРВЕР для Умного улья");
    Serial.println("   Порог тревоги: 2000 ppm CO₂");
    Serial.println("   Обновление данных: каждые 3 секунды");
    Serial.println("=========================================\n");
  #endif
  
  // Создаем точку доступа
  #if DEBUG == 1
    Serial.print("Создание точки доступа ");
    Serial.print(ssid);
  #endif
  
  WiFi.softAP(ssid, password);
  
  #if DEBUG == 1
    Serial.print(" - IP адрес: ");
    Serial.println(WiFi.softAPIP());
  #endif
  
  // Настройка веб-сервера
  server.on("/", handleRoot);
  server.on("/data", handleData);
  server.on("/demo/alert", HTTP_POST, handleDemoAlert);
  server.onNotFound(handleNotFound);
  
  server.begin();
  
  #if DEBUG == 1
    Serial.println("HTTP сервер запущен");
    Serial.println("Подключитесь к Wi-Fi: SmartHive_AP (пароль: 12345678)");
    Serial.print("Откройте браузер и перейдите по адресу: http://");
    Serial.println(WiFi.softAPIP());
    Serial.println("\n=========================================\n");
  #endif
  
  // Инициализация данных
  sensorData.temperature = 0;
  sensorData.humidity = 0;
  sensorData.gas = 400;
  sensorData.sound = 0;
  sensorData.weight = 0;
  sensorData.alert = false;
  sensorData.lastUpdate = "Ожидание данных...";
}

// ========== LOOP ==========
void loop() {
  server.handleClient();
  
  // Чтение данных с Arduino через Serial
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    data.trim();
    
    if (data.length() > 5) {
      #if DEBUG == 1
        Serial.print("📨 Получено: ");
        Serial.println(data);
      #endif
      
      // Обработка демо-команд от Arduino
      if (data == "DEMO_START") {
        sensorData.alert = true;
        sensorData.gas = 2500;  // > 2000, тревога!
        #if DEBUG == 1
          Serial.println("🎬 Демо: тревога установлена (CO₂ = 2500 ppm)");
        #endif
      }
      else if (data == "DEMO_END") {
        sensorData.alert = false;
        sensorData.gas = 450;   // Норма
        #if DEBUG == 1
          Serial.println("🏁 Демо: тревога снята (CO₂ = 450 ppm)");
        #endif
      }
      else {
        // Обычные данные с датчиков
        parseSensorData(data);
      }
    }
  }
}
