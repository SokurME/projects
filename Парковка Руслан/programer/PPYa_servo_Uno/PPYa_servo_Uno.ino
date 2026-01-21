// подсистема перемещения ячеек (ППЯ) 
// (c) школа 1103

#include "ServoSmooth.h" 

#define SERVO_PIN 9
# define TOL 2 // точность установки угла
ServoSmooth servo(180);   // создали с указанием макс. угла серво

uint32_t servoTimer=0;
uint32_t turnTimer=0;
bool startFlag = false; // флаг старта
byte cur_position = 1 ; // текущая позиция
byte go_position = 1 ; // заданная позиция
boolean recievedFlag = false; // флаг получения данных на 
String strData = ""; // для данных с Serial
String tempStr = "";
unsigned int cur_deg = 0; // текущий угол
int delta = 0; // рассогласование угла

String recieveData(); // данные с Serial

void setup() {

Serial.begin(9600);
//pinMode(STOP_PIN, INPUT_PULLUP);
servo.attach(SERVO_PIN);  // стартовый угол 0 градусов
servo.smoothStart();  // "плавно" движемся к нему
servo.setSpeed(10); // скорость
 
}


void loop() {

  // каждые 20 мс
  if (millis() - servoTimer >= 20) {  // взводим таймер на 20 мс (как в библиотеке)
    servoTimer += 20;
    servo.tickManual();   // двигаем  серво. 
  }


tempStr = recieveData();
 if (tempStr != "") {
 go_position = tempStr.toInt();
  if (go_position != cur_position) {
      
        // поворачиваем на заданный угол
       cur_deg = (go_position - 1)*60;
       servo.setTargetDeg(cur_deg);
       startFlag = true;
       cur_position = go_position;
  }

  if (go_position == cur_position) {
      Serial.println(go_position); 
      }
  }

  if (startFlag){
      delta = servo.getCurrentDeg()- cur_deg;
      if (abs(delta) <= TOL) {
       Serial.println(go_position);
       startFlag = false;
       }
  }
  
}



//прием данных с serial
String recieveData(){
if (Serial.available() > 0) {  // если есть что-то на вход
  strData = "";                // очистить строку
    while (Serial.available() > 0) {
      // пока идут данные
      strData += (char)Serial.read();  // получаем данные
      delay(2);                        // обязательно задержка, иначе вылетим из цикла раньше времени
    }
    recievedFlag = true;  // поднять флаг что получили данные
  }

 if (recievedFlag) {
      recievedFlag = false;  // данные приняты
      return strData;
     }
  else
     return "";

}
