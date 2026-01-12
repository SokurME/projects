#include <Servo.h>
#include <LiquidCrystal.h>

// Пины
#define MOTOR_A_IN1 3   
#define MOTOR_A_IN2 5   
#define MOTOR_B_IN3 6  
#define MOTOR_B_IN4 11  
#define PIN_SERVO 9
#define PIN_BUT1 2
#define PIN_BUT2 4

// Дополнительные настройки
#define MAX_TASK 6
#define DISPLAY_DELAY 1500  // Задержка показа сообщения

// Константы скорости
#define MIN_SPEED 40     // минимальная скорость 40%
#define SPEED_STEP 10    // шаг изменения скорости

// Настройка отладки
#define DEBUG_OUTPUT 1   // 1 - включить вывод в Serial, 0 - выключить

// Переменные
int task = 1;
unsigned long lastPressTime1 = 0;
unsigned long lastPressTime2 = 0;
const unsigned long debounceTime = 200;
bool button1Active = false; // Флаг активности кнопки 1
bool button2Active = false; // Флаг активности кнопки 2

Servo servo;
// Пины для LCD (RS, E, D4, D5, D6, D7)
LiquidCrystal lcd(7, 8, 10, 12, 13, 9);  

// Компактное состояние: 2 байта, 13 бит данных + 3 бита резерв
struct {
  // Первый байт (полностью заполнен - 8 бит)
  uint8_t curSpeed : 7;    // Текущая скорость (7 бит, 0-127)
  uint8_t isForward : 1;   // Движение вперед (1 бит)
  
  // Второй байт (5 бит используется, 3 бита резерв)
  uint8_t isBackward : 1;  // Движение назад
  uint8_t isLeft : 1;      // Поворот влево
  uint8_t isRight : 1;     // Поворот вправо
  uint8_t isMoving : 1;    // Вообще движется
  uint8_t isHolding : 1;   // Сервопривод держит
  uint8_t : 3;             // 3 свободных бита (резерв) ✓
} state;

void setup() {
  // Настройка пинов
  pinMode(MOTOR_A_IN1, OUTPUT);
  pinMode(MOTOR_A_IN2, OUTPUT);
  pinMode(MOTOR_B_IN3, OUTPUT);
  pinMode(MOTOR_B_IN4, OUTPUT);
  pinMode(PIN_BUT1, INPUT_PULLUP);
  pinMode(PIN_BUT2, INPUT_PULLUP);
  
  
  // Serial всегда инициализируем для приема команд
  Serial.begin(9600);
  
  #if DEBUG_OUTPUT
  Serial.println(F("Готов"));
  Serial.println(F("F,B,L,R,S,G,H,V"));
  Serial.print(F("Стартовая скорость: "));
  Serial.print(MIN_SPEED);
  Serial.println(F("%"));
  Serial.print(F("Отладка: "));
  Serial.println(DEBUG_OUTPUT ? F("ВКЛ") : F("ВЫКЛ"));
  
  // Проверка размера структуры
  Serial.print(F("Размер state: "));
  Serial.print(sizeof(state));
  Serial.print(F(" байт ("));
  Serial.print(sizeof(state) * 8);
  Serial.print(F(" бит, из них "));
  Serial.print(13);  // 7+1+1+1+1+1+1 = 13 бит данных
  Serial.println(F(" бит данных, 3 бита резерв)"));
  #endif
  
  servo.attach(PIN_SERVO);
  servo.write(0);
  
  // Инициализация состояния
  state.curSpeed = MIN_SPEED;
  state.isForward = 0;
  state.isBackward = 0;
  state.isLeft = 0;
  state.isRight = 0;
  state.isMoving = 0;
  state.isHolding = 0;
  
  stopMotors();


 // Инициализация LCD (16x2)
  lcd.begin(16, 2);
  
  // Вывод начального значения
  updateDisplay();
}

void loop() {
  // Всегда проверяем Serial для приема команд
  if (Serial.available()) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') return;
    handleCommand(c);
  }

  // Обработка кнопки 1
  if (digitalRead(PIN_BUT1) == LOW) {
    // Кнопка нажата
    if (!button1Active) {
      // Если кнопка еще не была активна
      if (millis() - lastPressTime1 > debounceTime) {
        task++;
        if (task > 6) task = 1;
        
        Serial.print("Button 1 pressed. Task: ");
        Serial.println(task);
        
        updateDisplay();
        lastPressTime1 = millis();
        button1Active = true; // Помечаем кнопку как активную
      }
    }
  } else {
    // Кнопка отпущена
    button1Active = false;
  }

  // Обработка кнопки 2
  if (digitalRead(PIN_BUT2) == LOW) {
    if (!button2Active) {
      if (millis() - lastPressTime2 > debounceTime) {
        Serial.println("Button 2 pressed");
        
        lcd.clear();
        lcd.print("Set task = ");
        lcd.print(task);
        delay(1500);
        updateDisplay();
        
        lastPressTime2 = millis();
        button2Active = true;
      }
    }
  } else {
    button2Active = false;
  }
  
  delay(10);
  
}

void handleCommand(char c) {
  switch(c) {
    case 'F': case 'f': setForward(); break;
    case 'B': case 'b': setBackward(); break;
    case 'L': case 'l': setLeft(); break;
    case 'R': case 'r': setRight(); break;
    case 'S': case 's': setStop(); break;
    case 'G': case 'g': setGrab(); break;
    case 'H': case 'h': setRelease(); break;
    case 'V': case 'v': 
      #if DEBUG_OUTPUT
      showSpeed(); 
      #endif
      break;
    default: 
      #if DEBUG_OUTPUT
      Serial.println(F("? F,B,L,R,S,G,H,V"));
      #endif
      break;
  }
}

void setForward() {
  if (state.isMoving && !state.isForward) {
    stopMotors();
    resetMove();
    state.curSpeed = MIN_SPEED;
  }
  
  if (state.isForward && state.curSpeed < 100) {
    state.curSpeed += SPEED_STEP;
    if (state.curSpeed > 100) state.curSpeed = 100;
  } else if (!state.isForward) {
    state.curSpeed = MIN_SPEED;
  }
  
  state.isForward = 1;
  state.isBackward = 0;
  state.isLeft = 0;
  state.isRight = 0;
  state.isMoving = 1;
  
  setMotor(MOTOR_A_IN1, MOTOR_A_IN2, state.curSpeed, 1);
  setMotor(MOTOR_B_IN3, MOTOR_B_IN4, state.curSpeed, 1);
  
  #if DEBUG_OUTPUT
  Serial.print(F("Вперед: "));
  Serial.print(state.curSpeed);
  Serial.println(F("%"));
  #endif
}

void setBackward() {
  if (state.isMoving && !state.isBackward) {
    stopMotors();
    resetMove();
    state.curSpeed = MIN_SPEED;
  }
  
  if (state.isBackward && state.curSpeed < 100) {
    state.curSpeed += SPEED_STEP;
    if (state.curSpeed > 100) state.curSpeed = 100;
  } else if (!state.isBackward) {
    state.curSpeed = MIN_SPEED;
  }
  
  state.isBackward = 1;
  state.isForward = 0;
  state.isLeft = 0;
  state.isRight = 0;
  state.isMoving = 1;
  
  setMotor(MOTOR_A_IN1, MOTOR_A_IN2, state.curSpeed, 0);
  setMotor(MOTOR_B_IN3, MOTOR_B_IN4, state.curSpeed, 0);
  
  #if DEBUG_OUTPUT
  Serial.print(F("Назад: "));
  Serial.print(state.curSpeed);
  Serial.println(F("%"));
  #endif
}

void setLeft() {
  if (state.isMoving && !state.isLeft) {
    stopMotors();
    resetMove();
    state.curSpeed = MIN_SPEED;
  }
  
  if (state.isLeft && state.curSpeed < 100) {
    state.curSpeed += SPEED_STEP;
    if (state.curSpeed > 100) state.curSpeed = 100;
  } else if (!state.isLeft) {
    state.curSpeed = MIN_SPEED;
  }
  
  state.isLeft = 1;
  state.isForward = 0;
  state.isBackward = 0;
  state.isRight = 0;
  state.isMoving = 1;
  
  uint8_t leftSpd = state.curSpeed / 2;
  if (leftSpd < MIN_SPEED) leftSpd = MIN_SPEED / 2;
  
  setMotor(MOTOR_A_IN1, MOTOR_A_IN2, leftSpd, 0);
  setMotor(MOTOR_B_IN3, MOTOR_B_IN4, state.curSpeed, 1);
  
  #if DEBUG_OUTPUT
  Serial.print(F("Влево: "));
  Serial.print(state.curSpeed);
  Serial.print(F("%, левый мотор: "));
  Serial.print(leftSpd);
  Serial.println(F("%"));
  #endif
}

void setRight() {
  if (state.isMoving && !state.isRight) {
    stopMotors();
    resetMove();
    state.curSpeed = MIN_SPEED;
  }
  
  if (state.isRight && state.curSpeed < 100) {
    state.curSpeed += SPEED_STEP;
    if (state.curSpeed > 100) state.curSpeed = 100;
  } else if (!state.isRight) {
    state.curSpeed = MIN_SPEED;
  }
  
  state.isRight = 1;
  state.isForward = 0;
  state.isBackward = 0;
  state.isLeft = 0;
  state.isMoving = 1;
  
  uint8_t rightSpd = state.curSpeed / 2;
  if (rightSpd < MIN_SPEED) rightSpd = MIN_SPEED / 2;
  
  setMotor(MOTOR_A_IN1, MOTOR_A_IN2, state.curSpeed, 1);
  setMotor(MOTOR_B_IN3, MOTOR_B_IN4, rightSpd, 0);
  
  #if DEBUG_OUTPUT
  Serial.print(F("Вправо: "));
  Serial.print(state.curSpeed);
  Serial.print(F("%, правый мотор: "));
  Serial.print(rightSpd);
  Serial.println(F("%"));
  #endif
}

void setStop() {
  stopMotors();
  
  state.isMoving = 0;
  state.isForward = 0;
  state.isBackward = 0;
  state.isLeft = 0;
  state.isRight = 0;
  state.curSpeed = MIN_SPEED;
  
  #if DEBUG_OUTPUT
  Serial.println(F("Стоп (скорость 0%)"));
  #endif
}

void resetMove() {
  state.isMoving = 0;
  state.isForward = 0;
  state.isBackward = 0;
  state.isLeft = 0;
  state.isRight = 0;
  state.curSpeed = MIN_SPEED;
}

void setMotor(uint8_t pin1, uint8_t pin2, uint8_t spd, bool fwd) {
  spd = min(spd, 100);
  uint8_t pwm = map(spd, 0, 100, 0, 255);
  
  if (spd == 0) {
    analogWrite(pin1, 0);
    analogWrite(pin2, 0);
  } else if (fwd) {
    analogWrite(pin1, pwm);
    analogWrite(pin2, 0);
  } else {
    analogWrite(pin1, 0);
    analogWrite(pin2, pwm);
  }
}

void stopMotors() {
  analogWrite(MOTOR_A_IN1, 0);
  analogWrite(MOTOR_A_IN2, 0);
  analogWrite(MOTOR_B_IN3, 0);
  analogWrite(MOTOR_B_IN4, 0);
}

void setGrab() {
  if (!state.isHolding) {
    servo.write(90);
    state.isHolding = 1;
    delay(300);
    #if DEBUG_OUTPUT
    Serial.println(F("Захват: ВЗЯТЬ"));
    #endif
  }
}

void setRelease() {
  if (state.isHolding) {
    servo.write(0);
    state.isHolding = 0;
    delay(300);
    #if DEBUG_OUTPUT
    Serial.println(F("Захват: ОТПУСТИТЬ"));
    #endif
  }
}

#if DEBUG_OUTPUT
void showSpeed() {
  Serial.print(F("Текущая скорость: "));
  Serial.print(state.curSpeed);
  Serial.println(F("%"));
  
  Serial.print(F("Направление: "));
  if (state.isForward) Serial.println(F("вперед"));
  else if (state.isBackward) Serial.println(F("назад"));
  else if (state.isLeft) Serial.println(F("влево"));
  else if (state.isRight) Serial.println(F("вправо"));
  else Serial.println(F("стоп"));
  
  Serial.print(F("Сервопривод: "));
  Serial.println(state.isHolding ? F("держит") : F("отпущен"));
}
#endif


void updateDisplay() {
  lcd.clear();
  lcd.print("Task: ");
  lcd.print(task);
  lcd.cursor(); // Включаем курсор (мигающий)
}

void showSetTask() {
  lcd.clear();
  lcd.print("Set task = ");
  lcd.print(task);
  delay(DISPLAY_DELAY); // Показываем сообщение
  updateDisplay(); // Возвращаемся к обычному отображению
}
