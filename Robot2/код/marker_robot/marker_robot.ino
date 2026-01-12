#include <Servo.h>
#include <LiquidCrystal.h>

// Пины
#define MOTOR_A_IN1 3   
#define MOTOR_A_IN2 5   
#define MOTOR_B_IN3 6  
#define MOTOR_B_IN4 11  
#define PIN_SERVO 9
#define PIN_BUT1 A1
#define PIN_BUT2 A2
#define PIN_PORTB 2
#define LED_OUTPUT_PIN A3
#define SensorPIN A0 // фоторезистор
#define PIN_PORTA A4

// Дополнительные настройки
#define MAX_TASK 6
#define DISPLAY_DELAY 1500  // Задержка показа сообщения
#define SERVO_UP 180 // сервопривод вверх
#define SERVO_DOWN 0 // сервопривод вниз

// Константы скорости
#define MIN_SPEED 40     // минимальная скорость 40%
#define SPEED_STEP 10    // шаг изменения скорости

// Настройка отладки
#define DEBUG_OUTPUT 1   // 1 - включить вывод в Serial, 0 - выключить

// Переменные
byte task = 1; // для выбора задачи
byte ActiveTask = 0; // активная задача
unsigned long lastPressTime1 = 0;
unsigned long lastPressTime2 = 0;
const unsigned long debounceTime = 200;
bool button1Active = false; // Флаг активности кнопки 1
bool button2Active = false; // Флаг активности кнопки 2
bool isMove = false; // флаг включения мотора
bool isTask = false; // задание выполняется
bool lineDetected = false; // обнаружение линии
byte minMoveTime = 71; // минимальное время движения в мс 
byte step = 0; // шаги выполнения задания
unsigned int light_sensor = 0; // датчик фоторезистор
unsigned int light_set = 700; // пороговое значение датчика
unsigned long startTime; // для отсчета времени

Servo servo;
// Пины для LCD (RS, E, D4, D5, D6, D7)
LiquidCrystal lcd(7, 8, 10, 12, 13, 4);  

void setup() {
  // Настройка пинов
  pinMode(MOTOR_A_IN1, OUTPUT);
  pinMode(MOTOR_A_IN2, OUTPUT);
  pinMode(MOTOR_B_IN3, OUTPUT);
  pinMode(MOTOR_B_IN4, OUTPUT);
  stopMotors();
  
  pinMode(PIN_BUT1, INPUT_PULLUP);
  pinMode(PIN_BUT2, INPUT_PULLUP);
  pinMode(PIN_PORTB, INPUT_PULLUP);
  pinMode(LED_OUTPUT_PIN, OUTPUT);
  digitalWrite(LED_OUTPUT_PIN, LOW);
  
  Serial.begin(9600);
  
  servo.attach(PIN_SERVO);
  servo.write(SERVO_UP);
  
  // Инициализация LCD (16x2)
  lcd.begin(16, 2);
  
  // Вывод начального значения
  updateDisplay();
}

void loop() {

  // Обработка кнопки 1
  if (digitalRead(PIN_BUT1) == LOW) {
    // Кнопка нажата
    if (!button1Active) {
      // Если кнопка еще не была активна
      if (millis() - lastPressTime1 > debounceTime) {
        task++;
        if (task > 6) task = 1;
        #if DEBUG_OUTPUT
        Serial.print("Button 1 pressed. Task: ");
        Serial.println(task);
        #endif
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
        #if DEBUG_OUTPUT
		Serial.println("Button 2 pressed");
        #endif
        if (!isTask) {
			lcd.clear();
			lcd.print("Set task = ");
			lcd.print(task);
			delay(1500);
			updateDisplay();
			lastPressTime2 = millis();
			button2Active = true;
			ActiveTask = task;
		}
      }
    }
  } else {
    button2Active = false;
  }
  
  //--------- выбор задания от 1 до 6-------------
  
  
  switch (ActiveTask) {
		
		case 1:
		isTask = true; // выполнение задания
		digitalWrite(LED_OUTPUT_PIN, HIGH); // включить светодиод
		while (isTask) {
			if (step == 0) {
				setForward();
				step++;
			}
			
			if (step == 1) {
			light_sensor = analogRead(SensorPIN);
				// пересечение
				if (light_sensor < light_set && !lineDetected) {
					lineDetected = true;
				}
				// выход из черной линии
				if (light_sensor > light_set && lineDetected) {
					lineDetected = false;
					startTime = millis();
					step++;
				}
			}
			
			if (step == 2) {
				if (millis() - startTime >= minMoveTime*15) {
					stopMotors();
					step++;
					servo.write(SERVO_DOWN);   // опустили маркер
					delay(500);
				}
			}
			
			if (step == 3) {
				setForward();
				startTime = millis();
				step++;
			}
			
			if (step == 4) {
				if (millis() - startTime >= minMoveTime*10) {
					stopMotors();
					step++;
					servo.write(SERVO_UP);   // подняли маркер
					delay(500); 
					setBackward(); // поехали назад
					startTime = millis();
				}
			}
			
			if (step == 5) {
				if (millis() - startTime >= minMoveTime*25) {
					stopMotors();
					step++;
					isTask =false; // Закончили задание!
				}
			}
					
		}
		digitalWrite(LED_OUTPUT_PIN, LOW); // выключить светодиод
		ActiveTask = 0;
		step = 0;
		break;
		
		
		case 2:
		
		break;
		
		case 3:
		
		break;
		
		case 4:
		
		break;
		
		case 5:
		
		break;
		
		case 6:
		
		break;
  
  }
  
}



void setForward() {
    stopMotors();
    setMotor(MOTOR_A_IN1, MOTOR_A_IN2, 100, 1);
    setMotor(MOTOR_B_IN3, MOTOR_B_IN4, 100, 1);
	isMove = true;
}

void setBackward() {
    stopMotors();
    setMotor(MOTOR_A_IN1, MOTOR_A_IN2, 100, 0);
    setMotor(MOTOR_B_IN3, MOTOR_B_IN4, 100, 0);
    isMove = true;
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
  isMove = false;
}



void updateDisplay() {
  lcd.clear();
  lcd.print("Task: ");
  lcd.print(task);
  lcd.cursor(); // Включаем курсор 
}

void showSetTask() {
  lcd.clear();
  lcd.print("Set task = ");
  lcd.print(task);
  delay(DISPLAY_DELAY); // Показываем сообщение
  updateDisplay(); // Возвращаемся к обычному отображению
}
