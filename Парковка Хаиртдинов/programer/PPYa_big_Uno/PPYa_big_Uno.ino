#include <AFMotor.h>                      // Подключаем библиотеку AFMotor
const int stepsPerRevolution = 200;       // Указываем количество шагов на 1 оборот двигателя
const unsigned int cnt_60deg = stepsPerRevolution/6; // счетчик на один оборот
byte cur_position = 1 ; // текущая позиция
byte go_position = 1 ; // заданная позиция
unsigned int cnt_toStop = 0; // счетчик до останова
boolean recievedFlag = false; // флаг получения данных на 
String strData = ""; // для данных с Serial
String tempStr = "";
 
AF_Stepper motor(stepsPerRevolution, 2);  // Указываем что двигатель подключен к портам №1 (М3 - М4)
 
void setup()\
 {
  motor.setSpeed(10);                     // Скорость двигателя в минуту
  Serial.begin(9600);
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

void loop() {

tempStr = recieveData();
 if (tempStr != "") {
 go_position = tempStr.toInt();
  if (go_position != cur_position) {
      if (go_position > cur_position) {
        // поворачиваем по часовой
        cnt_toStop = (go_position - cur_position)*cnt_60deg;
        cur_position = go_position;
        motor.step(cnt_toStop, FORWARD, MICROSTEP);  
        motor.release();  // Отключаем питание обмоток
        Serial.println(go_position); 
      }

        if (go_position < cur_position) {
        // поворачиваем против часовой
        cnt_toStop = (cur_position - go_position)*cnt_60deg;
        cur_position = go_position;
        motor.step(cnt_toStop, BACKWARD, MICROSTEP);  
        motor.release();  // Отключаем питание обмоток
        Serial.println(go_position);  
      }
  }

  if (go_position == cur_position) {
      Serial.println(go_position); 
  }
 }
}
