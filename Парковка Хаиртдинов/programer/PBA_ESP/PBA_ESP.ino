#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <FS.h>
#include <IPAddress.h>
#include <TaskScheduler.h>

#define PIN_TRIG 14 
#define PIN_ECHO 12
// драйвер моторов
#define PinA1 5 // D1
#define PinA2 4 // D2
#define PinB1 0 // D3
#define PinB2 2 // D4 
#define MIN_DIST 4 // минимальная дистанция
#define DELAY_STOP 800

// Настройки точки доступа
const char* ssid = "ESP8266_AP";
const char* password = "12345678";

// Настройки IP-адреса
IPAddress local_IP(192, 168, 4, 1);
IPAddress gateway(192, 168, 4, 1);
IPAddress subnet(255, 255, 255, 0);

// Переменные для управления
bool forwardFlag = false;
bool backwardFlag = false;
bool stopFlag = true;
bool parkFlag = false;
bool forwardOn = false;
bool backwardOn = false;
bool stopOn = false;
bool parkOn = false;
bool taskEnd = false;
bool flagSlow = false;

const int max_speed = 70;  // максимальная скорость, значение ШИМ 60
const int lo_speed = 50; // медленная скорость 40
//int cur_speed = 60; // текущая скорость

long duration = 0; // длительность импульса
long curent_dist = 0; // расстояние в см
unsigned long time_now = 0;

// прототип функций
void distance();   //задаем прототип для определения дистанции
void show_data(); // прототип для отладочной информации
void drive_car(); // прототип для управления моторами

// Создаем объекты 
Scheduler userScheduler;   // планировщик
// Создаем веб-сервер на порту 80
ESP8266WebServer server(80);

Task taskDistance(TASK_MILLISECOND * 100 , TASK_FOREVER, &distance);   // задание для УЗ-датчика
Task taskShow(TASK_MILLISECOND * 500 , TASK_FOREVER, &show_data);   // задание для вывода отладочной информации
Task taskDrive(TASK_MILLISECOND * 100 , TASK_FOREVER, &drive_car);   // задание для управления двигателями

// HTML страница
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Car Control</title>
  <style>
    body {
      background-color: aqua;
      text-align: center;
      font-family: Arial, sans-serif;
    }
    img {
      width: 300px;
      margin-top: 20px;
    }
    button {
      display: block;
      margin: 20px auto;
      padding: 30px 60px;
      font-size: 40px;
      cursor: pointer;
    }
    h1 {
      font-size: 50px;
      margin-top: 20px;
    }
    #status {
      margin-top: 20px;
      font-size: 30px;
      color: green;
    }
  </style>
</head>
<body>
  <h1>Управление машиной</h1>
  <img src="/car.jpg" alt="Car">
  <div>
    <button onclick="sendRequest('forward')">Вперед</button>
    <button onclick="sendRequest('backward')">Назад</button>
    <button onclick="sendRequest('stop')">Стоп</button>
    <button onclick="sendRequest('park')">Парковка</button>
  </div>
  <div id="status"></div>
  <script>
    function sendRequest(action) {
      fetch('/' + action)
        .then(response => response.text())
        .then(text => {
          document.getElementById('status').textContent = text;
        })
        .catch(error => {
          document.getElementById('status').textContent = 'Ошибка: ' + error;
        });
    }
  </script>
</body>
</html>
)rawliteral";

void handleRoot() {
  server.send_P(200, "text/html", index_html);
}

void handleImage() {
  File file = SPIFFS.open("/car.jpg", "r");
  if (!file) {
    server.send(404, "text/plain", "Image not found");
    return;
  }
  server.streamFile(file, "image/jpeg");
  file.close();
}

void handleForward() {
  forwardFlag = true;
  backwardFlag = false;
  stopFlag = false;
  parkFlag = false;
  server.send(200, "text/plain", "Команда 'Вперед' выполнена");
}

void handleBackward() {
  forwardFlag = false;
  backwardFlag = true;
  stopFlag = false;
  parkFlag = false;
  server.send(200, "text/plain", "Команда 'Назад' выполнена");
}

void handleStop() {
  forwardFlag = false;
  backwardFlag = false;
  stopFlag = true;
  parkFlag = false;
  server.send(200, "text/plain", "Команда 'Стоп' выполнена");
}

void handlePark() {
  forwardFlag = false;
  backwardFlag = false;
  stopFlag = false;
  parkFlag = true;
  server.send(200, "text/plain", "Команда 'Парковка' выполнена");
}

void handleStatus() {
  String json = "{";
  json += "\"forwardFlag\": " + String(forwardFlag ? "true" : "false") + ",";
  json += "\"backwardFlag\": " + String(backwardFlag ? "true" : "false") + ",";
  json += "\"stopFlag\": " + String(stopFlag ? "true" : "false") + ",";
  json += "\"parkFlag\": " + String(parkFlag ? "true" : "false") + ",";
  json += "\"taskEnd\": " + String(taskEnd ? "true" : "false");
  json += "}";
  server.send(200, "application/json", json);
}

void handleSetFlag() {
  if (server.hasArg("flag") && server.hasArg("value")) {
    String flag = server.arg("flag");   // Получаем имя флага
    String value = server.arg("value"); // Получаем значение флага

    if (flag == "taskEnd") {
      taskEnd = (value == "true");
    } 
    server.send(200, "text/plain; charset=utf-8", "Флаг изменен успешно");
  } else {
    server.send(400, "text/plain; charset=utf-8", "Ошибка: Отсутствуют параметры 'flag' или 'value'");
  }
}


void setup() {
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PinA1, OUTPUT); 
  pinMode(PinA2, OUTPUT);
  pinMode(PinB1, OUTPUT);
  pinMode(PinB2, OUTPUT);
  digitalWrite(PinA1, 0);
  digitalWrite(PinA2, 0);
  digitalWrite(PinB1, 0);
  digitalWrite(PinB2, 0);
  Serial.begin(115200);

  // Инициализация файловой системы
  if (!SPIFFS.begin()) {
    Serial.println("Failed to mount file system");
    return;
  }

  // Настройка точки доступа с фиксированным IP-адресом
  if (!WiFi.softAPConfig(local_IP, gateway, subnet)) {
    Serial.println("Failed to configure AP");
  }
  WiFi.softAP(ssid, password);
  Serial.println("Access Point started");
  Serial.print("IP Address: ");
  Serial.println(WiFi.softAPIP());

  // Настройка обработчиков запросов
  server.on("/", handleRoot);
  server.on("/car.jpg", handleImage);
  server.on("/forward", handleForward);
  server.on("/backward", handleBackward);
  server.on("/stop", handleStop);
  server.on("/park", handlePark);
  server.on("/status", handleStatus);
  server.on("/set_flag", handleSetFlag);

  // Запуск сервера
  server.begin();
  Serial.println("HTTP server started");

// добавляем задания в обработчик
userScheduler.addTask(taskDistance);
userScheduler.addTask(taskShow);
userScheduler.addTask(taskDrive);


// запускаем задания
taskDistance.enable();
taskShow.enable();
taskDrive.enable();
}

void loop() {
  server.handleClient();
  userScheduler.execute();    //запуск планировщика заданий

  
}

void distance(){
  // датчик расстояния
  // Создаем короткий импульс длительностью 5 микросекунд.
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(5);
  digitalWrite(PIN_TRIG, HIGH);
  // Установим высокий уровень сигнала
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  //  Определяем задержку сигнала
  duration = pulseIn(PIN_ECHO, HIGH);
  // Преобразуем время задержки в расстояние
  if (duration > 0) 
      curent_dist = (duration / 2) / 29.1;
}

void show_data(){
// Вывод текущих состояний для отладки
  Serial.print("Forward: ");
  Serial.print(forwardFlag);
  Serial.print(" | Backward: ");
  Serial.print(backwardFlag);
  Serial.print(" | Stop: ");
  Serial.print(stopFlag);
  Serial.print(" | Park: ");
  Serial.print(parkFlag);
  Serial.print(" | Dist: ");
  Serial.println(curent_dist);
  
}

void drive_car(){
  // управление моторами
if (forwardFlag && !forwardOn) {
   stop_drive();
   move_forward(max_speed);
   forwardOn = true;
   backwardOn = false;
   stopOn = false;
   parkOn = false;
   Serial.println("Forward on! ");
}

if (backwardFlag && !backwardOn){
   stop_drive();
   move_backward(max_speed);
   forwardOn = false;
   backwardOn = true;
   stopOn = false;
   parkOn = false;
   Serial.println("backward on! ");  
}
if (stopFlag && !stopOn){
   stop_drive();
   stopOn = true;
   backwardOn = false;
   forwardOn = false;
   parkOn = false;
   Serial.println("stop on! ");
}

if (parkFlag && !parkOn){
   stop_drive();
   move_forward(max_speed);
   parkOn = true;
   stopOn = false;
   backwardOn = false;
   forwardOn = false;
   Serial.println("park on! ");
}

if (parkOn){
// автопарковка
  if (curent_dist > 10 && curent_dist < 30) {
    move_forward(lo_speed);
  }
  if (curent_dist <= MIN_DIST && !flagSlow) {
    flagSlow = true;
    time_now = millis();
  }

  if (flagSlow && ((millis()- time_now) > DELAY_STOP)) {
    parkOn = false;
    parkFlag = false;
    taskEnd = true;
    stopFlag = true;
    flagSlow = false;
    stop_drive();
  }
  
}
  
}

void move_backward(int speed) // Назад.
{
  analogWrite(PinA1, 0);
  analogWrite(PinA2, speed);
  analogWrite(PinB1, 0);
  analogWrite(PinB2, speed);
}
void move_forward(int speed) // Вперед ...
{
  analogWrite(PinA1, speed);
  analogWrite(PinA2, 0);
  analogWrite(PinB1, speed);
  analogWrite(PinB2, 0);
}
void move_left(int speed) // В левую сторону
{
  analogWrite(PinA1, speed);
  analogWrite(PinA2, 0);
  analogWrite(PinB1, 0);
  analogWrite(PinB2, speed);
}
void move_right(int speed) //В правую сторону
{
  analogWrite(PinA1, 0);
  analogWrite(PinA2, speed);
  analogWrite(PinB1, speed);
  analogWrite(PinB2, 0);
}
void stop_drive() //Стоп
{
  analogWrite(PinA1, 0);
  analogWrite(PinA2, 0);
  analogWrite(PinB1, 0);
  analogWrite(PinB2, 0);
  delay (1000);
}
