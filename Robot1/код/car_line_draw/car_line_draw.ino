#include <Servo.h>
#include <IRremote.hpp>

#define DEBUG_MODE 1 // режим отладки
// ===== ПИНЫ УПРАВЛЕНИЯ =====
#define ENA 5   // PWM (Timer0)
#define IN1 7   // Мотор A
#define IN2 8

#define ENB 6   // PWM (Timer0)
#define IN3 2   // Мотор B (зеркально)
#define IN4 4

#define SensorPIN A0 // фоторезистор
#define ServoPIN 9 // сервопривод
#define IR_PIN 11 // ИК датчик

// ============Настройки =========
#define READ_COUNT 30 // Количество измерений для усреднения
#define SERVO_UP 180 // сервопривод верхнее положение
#define SERVO_DOWN 0 // сервопривод нижнее положение

// ===== КОЭФФИЦИЕНТЫ =====
float kMotorA = 1.0;    // Мотор A "сильный"
float kMotorB = 0.85;   // Мотор B "слабый"
uint16_t moveTime = 1000/14; // Время движения в мс на один зубец

unsigned long startTime;
bool motorsRunning = false;
bool lineDetected = false;    // Флаг обнаружения линии
bool endTask = false; // флаг окончания задачи
byte baseSpeed;  // максимальная скорость моторов
int sensorValue = 0; // датчик
byte state = 1; // состояние
uint8_t motorSpeedA = 0;
uint8_t motorSpeedB = 0;

// Переменные для хранения значений
uint16_t lightLevel = 0;    // Уровень светлого
uint16_t darkLevel = 0;     // Уровень темного
uint16_t threshold = 735;     // Уставка срабатывания
// Состояния системы
enum SystemState {
  NORMAL_MODE,
  SET_LIGHT_LEVEL,
  SET_DARK_LEVEL
};

enum SystemTask {
  TASK_NONE,
  TASK_1,
  TASK_2,
  TASK_3,
  TASK_4,
  TASK_5,
  TASK_6,
  TEST_SERVO_UP,
  TEST_SERVO_DOWN,
  TEST_MOVE_F,
  TEST_MOVE_B,
  TEST_STOP,
  TEST_DARK,
  TEST_LIGHT
};
SystemState currentState = NORMAL_MODE;
SystemTask currentTask = TASK_NONE;

// Массив для измерений
uint16_t readings[READ_COUNT];
uint16_t code = 0; // ИК код

Servo myservo;

// ===== Прототипы функций ===========
void motorsForward(uint8_t speedA, uint8_t speedB) ;
void motorsBackward(uint8_t speedA, uint8_t speedB);
void motorsStop();
void motorsBrake(); 



void setup() {
  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  
  pinMode(ENB, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  motorsStop();
  IrReceiver.begin(IR_PIN);
  pinMode(SensorPIN, INPUT);
  pinMode(LED_BUILTIN, OUTPUT); 
  digitalWrite(LED_BUILTIN, LOW);
  Serial.begin(9600);
  myservo.attach(ServoPIN);  // подключаем серво
  myservo.write(SERVO_UP);   // поворот вверх
  delay(500);
  // Задание базовой скорости
  baseSpeed = 250;
  
  motorSpeedA = baseSpeed * kMotorA;
  motorSpeedB = baseSpeed * kMotorB;

  // ограничиваем максимум 250
  if(motorSpeedA > 250) motorSpeedA = 250;
  if(motorSpeedB > 250) motorSpeedB = 250;
  
   #if DEBUG_MODE
    Serial.print(F("baseSpeed: "));
    Serial.println(baseSpeed);
    Serial.print(F("motorSpeedA: "));
    Serial.println(motorSpeedA);
    Serial.print(F("motorSpeedB: "));
    Serial.println(motorSpeedB);
   #endif

state = 1;
    
}

void loop() {

/* ==== ИК кнопки ====*/

  if (IrReceiver.decode()) {
    if (!(IrReceiver.decodedIRData.flags & IRDATA_FLAGS_IS_REPEAT)) {
      uint16_t code = IrReceiver.decodedIRData.command;
      
      // определения кнопки
      switch (code) {
        case 0x19:
          #if DEBUG_MODE
          Serial.println(F("Кнопка 0"));
          #endif
          break;
        case 0x45:
          #if DEBUG_MODE
          Serial.println(F("Кнопка 1"));
          #endif
          currentTask = TASK_1;
          break;
        case 0x46:
          #if DEBUG_MODE
          Serial.println(F("Кнопка 2"));
          #endif
          currentTask = TASK_2;
          break;
        case 0x47:
          #if DEBUG_MODE
          Serial.println(F("Кнопка 3"));
          #endif
          currentTask = TASK_3;
          break;
        case 0x44:
          #if DEBUG_MODE
          Serial.println(F("Кнопка 4"));
          #endif
          currentTask = TASK_4;
          break;
        case 0x40:
          #if DEBUG_MODE
          Serial.println(F("Кнопка 5"));
          #endif
          currentTask = TASK_5;
          break;
        case 0x43:
          #if DEBUG_MODE
          Serial.println(F("Кнопка 6"));
          #endif
          currentTask = TASK_6;
          break;
        case 0x07:
          #if DEBUG_MODE
          Serial.println(F("Кнопка 7"));
          #endif
          break;
        case 0x15:
          #if DEBUG_MODE
          Serial.println(F("Кнопка 8"));
          #endif
          break;
        case 0x09:
          #if DEBUG_MODE
          Serial.println(F("Кнопка 9"));
          #endif
          break;
        case 0x18:
          #if DEBUG_MODE
          Serial.println(F("Кнопка up"));
          #endif
          currentTask = TEST_MOVE_F;
          break;
        case 0x52:
          #if DEBUG_MODE
          Serial.println(F("down"));
          #endif
          currentTask = TEST_MOVE_B;
          break;
        case 0x08:
          #if DEBUG_MODE
          Serial.println(F("left"));
          #endif
          currentTask = TEST_SERVO_DOWN;
          break;
        case 0x5A:
          #if DEBUG_MODE
          Serial.println(F("right"));
          #endif
          currentTask = TEST_SERVO_UP;
          break;  
        case 0x1C:
          #if DEBUG_MODE
          Serial.println(F("ok"));
          #endif
          currentTask = TEST_STOP;
          break; 
        case 0x16:
          #if DEBUG_MODE
          Serial.println(F("*"));
          #endif
          currentTask = TEST_LIGHT;
          break;
        case 0xD:
          #if DEBUG_MODE
          Serial.println(F("#"));
          #endif
          currentTask = TEST_DARK;
          break;          
        default:
          #if DEBUG_MODE
          Serial.print(F("Неизвестный код: 0x"));
          Serial.println(code, HEX);
          #endif
          break;
      }
    }
    
    IrReceiver.resume();
  }

/* ========== Основной автомат ========== */

switch (currentTask) {

        case TASK_1:

/* === Задача 1 ======= */
      switch (state) {
        case 1:
      // пуск мотора
      if (!motorsRunning) {
        motorsForward(motorSpeedA, motorSpeedB);
        motorsRunning = true;
        }
      state = 2;
      break;

        case 2:
        // пересечение линии
       sensorValue = analogRead(SensorPIN);
          #if DEBUG_MODE
           Serial.print("Sensor: ");
           Serial.println(sensorValue);
          #endif
        // Проверяем пересечение черной линии
          if (sensorValue < threshold && !lineDetected) {
              lineDetected = true;
            digitalWrite(LED_BUILTIN, HIGH);
        }
       // Проверяем выход из черной линии
        if (sensorValue > threshold && lineDetected) {
            lineDetected = false;
            digitalWrite(LED_BUILTIN, LOW);
            startTime = millis();
            state = 3;
           }
        break;

      case 3:
    // проехали 10 зубцов и опустили маркер
      if (motorsRunning && millis() - startTime >= moveTime*10) {
          motorsStop();
          motorsRunning = false;
          state = 4;
          myservo.write(SERVO_DOWN);   // опустили маркер
        #if DEBUG_MODE
          Serial.println(F("Motors stopped"));
          Serial.print(F("Time: ")); Serial.println(moveTime);
        #endif
        }
      break;

      case 4:
        // пуск мотора
      if (!motorsRunning) {
        motorsForward(motorSpeedA, motorSpeedB);
        motorsRunning = true;
        }
      state = 5;
      startTime = millis(); // запомнили время
      break;

      case 5: // последний
      // проехали 15 зубцов и подняли маркер
      if (motorsRunning && millis() - startTime >= moveTime*15) {
          motorsStop();
          motorsRunning = false;
          state = 1; // для следующих задач
          myservo.write(SERVO_UP);   // подняли маркер
        #if DEBUG_MODE
          Serial.println(F("Motors stopped"));
          Serial.print(F("Time: ")); Serial.println(moveTime);
        #endif
        endTask = true; // Закончили задание полностью!
        }

      break;
  
}
/* ========Конец задачи =========*/
             
          if (endTask) {
            currentTask = TASK_NONE;
            endTask = false;
          } // окончание задачи
          
        break;

        case TASK_2:
          #if DEBUG_MODE
          Serial.println(F("Task 2"));
          #endif
          currentTask = TASK_NONE;
        break;

        case TASK_3:
          #if DEBUG_MODE
          Serial.println(F("Task 3"));
          #endif
          currentTask = TASK_NONE;
        break;
        
        case TASK_4:
          #if DEBUG_MODE
          Serial.println(F("Task 4"));
          #endif
          currentTask = TASK_NONE;
        break;

        case TASK_5:
          #if DEBUG_MODE
          Serial.println(F("Task 5"));
          #endif
          currentTask = TASK_NONE;
        break;    

        case TASK_6:
          #if DEBUG_MODE
          Serial.println(F("Task 6"));
          #endif
          currentTask = TASK_NONE;
        break;            
        
        case TEST_SERVO_UP:
          #if DEBUG_MODE
          Serial.println(F("Test servo Up"));
          #endif
          myservo.write(SERVO_UP);
          currentTask = TASK_NONE;
        break;  

        case TEST_SERVO_DOWN:
          #if DEBUG_MODE
          Serial.println(F("Test servo Down"));
          #endif
          myservo.write(SERVO_DOWN);
          currentTask = TASK_NONE;
        break; 

        case TEST_MOVE_F:
          #if DEBUG_MODE
          Serial.println(F("Test move forward"));
          #endif
          if (motorsRunning) {
            motorsStop();
          }
          motorsForward(motorSpeedA, motorSpeedB);
          motorsRunning = true;
          currentTask = TASK_NONE;
        break; 

        case TEST_MOVE_B:
          #if DEBUG_MODE
          Serial.println(F("Test move backward"));
          #endif
          if (motorsRunning) {
            motorsStop();
          }
          motorsBackward(motorSpeedA, motorSpeedB);
          motorsRunning = true;
          currentTask = TASK_NONE;
        break; 

         case TEST_STOP:
          #if DEBUG_MODE
          Serial.println(F("Test stop"));
          #endif
          motorsStop();
          motorsRunning = false;
          currentTask = TASK_NONE;
        break; 

          case TEST_LIGHT:
          #if DEBUG_MODE
          Serial.println(F("Test Light"));
          #endif
          if (currentState == SET_DARK_LEVEL) {
            calibrateLightLevel();
            calculateThreshold();
            currentState = NORMAL_MODE;
          }
          else {
           calibrateLightLevel();
          }
          
          currentTask = TASK_NONE;
        break;    

          case TEST_DARK:
          #if DEBUG_MODE
          Serial.println(F("Test Dark"));
          #endif
          if (currentState == SET_LIGHT_LEVEL) {
            calibrateDarkLevel();
            calculateThreshold();
            currentState = NORMAL_MODE;
          }
          else {
           calibrateDarkLevel();
          }
          
          currentTask = TASK_NONE;
        break; 
        
}






}

// ===== ФУНКЦИИ =====
void motorsForward(uint8_t speedA, uint8_t speedB) {
  // Motor A
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, speedA);

  // Motor B
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
  analogWrite(ENB, speedB);
}

void motorsBackward(uint8_t speedA, uint8_t speedB) {
  // Motor A
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  analogWrite(ENA, speedA);

  // Motor B
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
  analogWrite(ENB, speedB);
}

void motorsStop() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

void motorsBrake() {
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, HIGH);
}


// Функция для мигания светодиодом
void blinkLED(int count, int delayTime) {
  for (int i = 0; i < count; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(delayTime);
    digitalWrite(LED_BUILTIN, LOW);
    if (i < count - 1) {
      delay(delayTime);
    }
  }
}

// Калибровка светлого уровня
void calibrateLightLevel() {
    #if DEBUG_MODE
      Serial.println(F("Setup Light Level"));
    #endif  
  // Считывание и усреднение значений
  int sum = 0;
  for (int i = 0; i < READ_COUNT; i++) {
    readings[i] = analogRead(SensorPIN);
    sum += readings[i];
    delay(50); // Небольшая задержка между измерениями
    // Индикация процесса (мигаем каждые 5 измерений)
    if (i % 5 == 0) {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(50);
      digitalWrite(LED_BUILTIN, LOW);
    }
  }
  
  lightLevel = sum / READ_COUNT;
   #if DEBUG_MODE
   Serial.print(F("Light Level: "));
   Serial.println(lightLevel);
   #endif
  currentState =  SET_LIGHT_LEVEL;
}

// Калибровка темного уровня
void calibrateDarkLevel() {
  #if DEBUG_MODE
   Serial.println("Dark level: ");
  #endif
    
  // Считывание и усреднение значений
  int sum = 0;
  for (int i = 0; i < READ_COUNT; i++) {
    readings[i] = analogRead(SensorPIN);
    sum += readings[i];
    delay(50);
    
    // Индикация процесса
    if (i % 5 == 0) {
      digitalWrite(LED_BUILTIN, HIGH);
      delay(20);
      digitalWrite(LED_BUILTIN, LOW);
    }
  }
  
  darkLevel = sum / READ_COUNT;
  #if DEBUG_MODE
   Serial.print("darkLevel: ");
   Serial.println(darkLevel);
  #endif
  currentState = SET_DARK_LEVEL;
}

// Расчет уставки
void calculateThreshold() {
  threshold = (lightLevel + darkLevel) / 2;
  #if DEBUG_MODE
  Serial.print(F("Threshold: "));
  Serial.println(threshold);
  #endif
  }
