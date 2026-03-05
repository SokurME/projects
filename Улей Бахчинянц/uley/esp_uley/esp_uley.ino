#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ArduinoJson.h>

// ========== НАСТРОЙКИ ТОЧКИ ДОСТУПА ==========
const char* ssid = "SmartHive_AP";
const char* password = "12345678";

// ========== ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ==========
ESP8266WebServer server(80);

// Данные с датчиков
struct SensorData {
  float temperature = 0;
  float humidity = 0;
  int gas = 0;
  int sound = 0;
  float weight = 0;
  bool alert = false;
  String lastUpdate = "Нет данных";
} sensorData;

// HTML страница
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
    .chart-container {
      background: white;
      border-radius: 10px;
      padding: 20px;
      margin-top: 30px;
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
        <h3>⚠️ Уровень газа</h3>
        <div class="value"><span id="gasValue">%GAS%</span> <span class="unit">ед.</span></div>
        <div id="gasStatus">Порог: %GASTHRESHOLD%</div>
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
      <button onclick="toggleChart()">📊 Показать график</button>
      <button onclick="location.reload()">📱 Полное обновление</button>
    </div>
    
    <div class="chart-container" id="chartContainer" style="display:none;">
      <h3>📈 История показаний (последние 10 замеров)</h3>
      <canvas id="dataChart" width="400" height="200"></canvas>
    </div>
    
    <div style="background: white; border-radius: 10px; padding: 20px; margin-top: 30px;">
      <h3>📋 Последние данные в JSON</h3>
      <pre id="jsonData" style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow: auto;"></pre>
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
      document.getElementById('gasValue').textContent = data.gas;
      document.getElementById('soundValue').textContent = data.sound;
      document.getElementById('weightValue').textContent = data.weight.toFixed(2);
      document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
      
      const alertCard = document.getElementById('alertCard');
      const alertValue = document.getElementById('alertValue');
      const statusBar = document.getElementById('statusBar');
      const statusText = document.getElementById('statusText');
      
      if (data.alert) {
        alertCard.className = 'card alert';
        alertValue.innerHTML = '🚨 АКТИВНА<br><small>Превышен газ!</small>';
        statusBar.className = 'status-bar alert';
        statusText.textContent = 'СТАТУС: ТРЕВОГА! Превышен уровень газа';
      } else if (data.gas > 200) {
        alertCard.className = 'card warning';
        alertValue.innerHTML = '⚠️ ВНИМАНИЕ<br><small>Газ повышен</small>';
        statusBar.className = 'status-bar warning';
        statusText.textContent = 'СТАТУС: Внимание. Уровень газа повышен';
      } else {
        alertCard.className = 'card normal';
        alertValue.innerHTML = '✅ НОРМА<br><small>Все показания в норме</small>';
        statusBar.className = 'status-bar normal';
        statusText.textContent = 'СТАТУС: Норма. Все системы работают';
      }
      
      document.getElementById('tempCard').className = 
        data.temperature > 35 ? 'card warning' : 'card';
      document.getElementById('humCard').className = 
        data.humidity > 80 ? 'card warning' : 'card';
      document.getElementById('gasCard').className = 
        data.gas > 250 ? 'card warning' : 'card';
        
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
            {
              label: 'Температура',
              data: dataHistory.temperature,
              borderColor: '#ff6b6b',
              backgroundColor: 'rgba(255, 107, 107, 0.1)',
              yAxisID: 'y'
            },
            {
              label: 'Влажность',
              data: dataHistory.humidity,
              borderColor: '#3498db',
              backgroundColor: 'rgba(52, 152, 219, 0.1)',
              yAxisID: 'y'
            },
            {
              label: 'Газ',
              data: dataHistory.gas,
              borderColor: '#ff9f43',
              backgroundColor: 'rgba(255, 159, 67, 0.1)',
              yAxisID: 'y1'
            }
          ]
        },
        options: {
          responsive: true,
          interaction: {
            mode: 'index',
            intersect: false
          },
          scales: {
            y: {
              type: 'linear',
              display: true,
              position: 'left',
              title: {
                display: true,
                text: 'Температура/Влажность'
              }
            },
            y1: {
              type: 'linear',
              display: true,
              position: 'right',
              title: {
                display: true,
                text: 'Газ'
              },
              grid: {
                drawOnChartArea: false
              }
            }
          }
        }
      });
    }
    
    setInterval(refreshData, 2000);
    
    window.onload = function() {
      refreshData();
      document.getElementById('gasStatus').textContent = 'Порог тревоги: 300 ед.';
    };
  </script>
  
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</body>
</html>
)rawliteral";

// ========== ФУНКЦИИ ДЛЯ ПАРСИНГА ДАННЫХ ==========
void parseSensorData(String data) {
  // Формат: T:25.5,H:60,G:245,M:512,W:12.34,A:0
  
  // Температура
  int tempStart = data.indexOf("T:");
  int tempEnd = data.indexOf(",H:");
  if (tempStart != -1 && tempEnd != -1) {
    sensorData.temperature = data.substring(tempStart + 2, tempEnd).toFloat();
  }
  
  // Влажность
  int humStart = data.indexOf(",H:");
  int humEnd = data.indexOf(",G:");
  if (humStart != -1 && humEnd != -1) {
    sensorData.humidity = data.substring(humStart + 3, humEnd).toFloat();
  }
  
  // Газ
  int gasStart = data.indexOf(",G:");
  int gasEnd = data.indexOf(",M:");
  if (gasStart != -1 && gasEnd != -1) {
    sensorData.gas = data.substring(gasStart + 3, gasEnd).toInt();
  }
  
  // Звук
  int soundStart = data.indexOf(",M:");
  int soundEnd = data.indexOf(",W:");
  if (soundStart != -1 && soundEnd != -1) {
    sensorData.sound = data.substring(soundStart + 3, soundEnd).toInt();
  }
  
  // Вес
  int weightStart = data.indexOf(",W:");
  int weightEnd = data.indexOf(",A:");
  if (weightStart != -1 && weightEnd != -1) {
    sensorData.weight = data.substring(weightStart + 3, weightEnd).toFloat();
  }
  
  // Тревога
  int alertStart = data.indexOf(",A:");
  if (alertStart != -1) {
    String alertStr = data.substring(alertStart + 3);
    alertStr.trim();
    sensorData.alert = (alertStr == "1");
  }
  
  // Время обновления
  sensorData.lastUpdate = String(millis() / 1000) + " сек. назад";
}

// ========== ВЕБ-СЕРВЕР ==========
void handleRoot() {
  String html = String(index_html);
  
  html.replace("%TEMPERATURE%", String(sensorData.temperature, 1));
  html.replace("%HUMIDITY%", String(sensorData.humidity, 1));
  html.replace("%GAS%", String(sensorData.gas));
  html.replace("%SOUND%", String(sensorData.sound));
  html.replace("%WEIGHT%", String(sensorData.weight, 2));
  html.replace("%ALERT%", sensorData.alert ? "АКТИВНА" : "НЕТ");
  html.replace("%LASTUPDATE%", sensorData.lastUpdate);
  html.replace("%IPADDRESS%", WiFi.softAPIP().toString());
  html.replace("%GASTHRESHOLD%", "300 ед.");
  
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
  doc["gasThreshold"] = 300;
  
  String response;
  serializeJson(doc, response);
  
  server.send(200, "application/json", response);
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
  Serial.begin(9600);  // Для связи с Arduino
  
  // Создаем точку доступа для ESP8266
  Serial.println("Создание точки доступа...");
  WiFi.softAP(ssid, password);
  
  Serial.print("IP адрес точки доступа: ");
  Serial.println(WiFi.softAPIP());
  
  // Настройка веб-сервера
  server.on("/", handleRoot);
  server.on("/data", handleData);
  server.onNotFound(handleNotFound);
  
  server.begin();
  Serial.println("HTTP сервер запущен");
  
  // Инициализация данных
  sensorData.temperature = 0;
  sensorData.humidity = 0;
  sensorData.gas = 0;
  sensorData.sound = 0;
  sensorData.weight = 0;
  sensorData.alert = false;
  sensorData.lastUpdate = "Ожидание данных...";
}

// ========== LOOP ==========
void loop() {
  server.handleClient();
  
  // Чтение данных с Arduino через Serial (USB/GPIO)
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    data.trim();
    
    if (data.length() > 5) {
      Serial.print("Получено: ");
      Serial.println(data);
      
      parseSensorData(data);
      
      Serial.printf("Температура: %.1f°C, Влажность: %.1f%%, Газ: %d, Звук: %d, Вес: %.2fкг, Тревога: %s\n",
                   sensorData.temperature, sensorData.humidity, sensorData.gas,
                   sensorData.sound, sensorData.weight, sensorData.alert ? "ДА" : "нет");
    }
  }
}
