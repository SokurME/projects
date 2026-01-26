// подсистема перемещения ячеек (ППЯ) 

#include <TaskScheduler.h>

// шаговый мотор
#define in1 2
#define in2 3
#define in3 4
#define in4 5
#define STOP_PIN 7 // пин выключатель останова
#define in1_2 8
#define in2_2 9
#define in3_2 10
#define in4_2 11

const unsigned int cnt_60deg = 2048/6; // счетчик на один оборот
byte ph_cnt = 1; // счетчик фаз
unsigned long step_cnt = 0; // счетчик шагов двигателя
bool stopBtn = false; // кнопка останова
byte cur_position = 1 ; // текущая позиция
byte go_position = 1 ; // заданная позиция
boolean recievedFlag = false; // флаг получения данных на 
String strData = ""; // для данных с Serial
String tempStr = "";
unsigned int cnt_toStop = 0; // счетчик до останова

// прототип функций
void motor1Clockwise();   //задаем прототип мотор 1 по часовой
void motor1CounterClockwise();   //задаем прототип мотор 1 против часовой

String recieveData(); // данные с Serial

// Создаем объекты 
Scheduler userScheduler;   // планировщик

Task taskMotor1Up(TASK_MILLISECOND * 30 , TASK_FOREVER, &motor1Clockwise);   // задание для мотора 1 по часовой
Task taskMotor1Down(TASK_MILLISECOND * 30 , TASK_FOREVER, &motor1CounterClockwise);   // задание для мотора 1 против часовой


void setup() {

Serial.begin(9600);
pinMode(STOP_PIN, INPUT_PULLUP);
pinMode(in1, OUTPUT);
pinMode(in2, OUTPUT);
pinMode(in3, OUTPUT);
pinMode(in4, OUTPUT);
pinMode(in1_2, OUTPUT);
pinMode(in2_2, OUTPUT);
pinMode(in3_2, OUTPUT);
pinMode(in4_2, OUTPUT);


// добавляем задания в обработчик
userScheduler.addTask(taskMotor1Up);
userScheduler.addTask(taskMotor1Down);


 
// калибровка при нажатой кнопке стоп
 if (!digitalRead(STOP_PIN)) {
   taskMotor1Up.enable();
   while (!digitalRead(STOP_PIN)) {
    userScheduler.execute(); // обновляем задания планировщика
   }
  taskMotor1Up.disable();
  step_cnt = 0;
 }

}

void loop() {
userScheduler.execute();
tempStr = recieveData();
 if (tempStr != "") {
 go_position = tempStr.toInt();
  if (go_position != cur_position) {
      if (go_position > cur_position) {
        // поворачиваем по часовой
        cnt_toStop = (go_position - cur_position)*cnt_60deg;
        cur_position = go_position;
        taskMotor1Up.enable();
          while (step_cnt < cnt_toStop) {
             userScheduler.execute();
         }
        taskMotor1Up.disable();
        step_cnt = 0;
        Serial.println(go_position); 
      }

        if (go_position < cur_position) {
        // поворачиваем против часовой
        cnt_toStop = (cur_position - go_position)*cnt_60deg;
        cur_position = go_position;
        taskMotor1Down.enable();
          while (step_cnt < cnt_toStop) {
             userScheduler.execute();
         }
        taskMotor1Down.disable();
        step_cnt = 0;
        Serial.println(go_position);  
      }
  }

  if (go_position == cur_position) {
      Serial.println(go_position); 
  }
 }
}

// Фазы 1...4 шагового двигателя:
void phase1(){
  digitalWrite(in1, HIGH);
  digitalWrite(in2, LOW); 
  digitalWrite(in3, LOW); 
  digitalWrite(in4, HIGH);
  }

void phase2(){
  digitalWrite(in1, HIGH);
  digitalWrite(in2, HIGH);
  digitalWrite(in3, LOW); 
  digitalWrite(in4, LOW);
  }

void phase3(){
  digitalWrite(in1, LOW); 
  digitalWrite(in2, HIGH); 
  digitalWrite(in3, HIGH);
  digitalWrite(in4, LOW);
  }

void phase4(){
  digitalWrite(in1, LOW); 
  digitalWrite(in2, LOW);
  digitalWrite(in3, HIGH); 
  digitalWrite(in4, HIGH);
  }

void phase1_2(){
  digitalWrite(in1_2, HIGH); 
  digitalWrite(in2_2, LOW);
  digitalWrite(in3_2, LOW);
  digitalWrite(in4_2, HIGH);
  }

void phase2_2(){
  digitalWrite(in1_2, HIGH); 
  digitalWrite(in2_2, HIGH); 
  digitalWrite(in3_2, LOW);
  digitalWrite(in4_2, LOW);
 }

void phase3_2(){
  digitalWrite(in1_2, LOW);
  digitalWrite(in2_2, HIGH);
  digitalWrite(in3_2, HIGH); 
  digitalWrite(in4_2, LOW);
 }

void phase4_2(){
  digitalWrite(in1_2, LOW);
  digitalWrite(in2_2, LOW); 
  digitalWrite(in3_2, HIGH);
  digitalWrite(in4_2, HIGH);
}

void motor1Clockwise(){
  switch (ph_cnt) { 
   case 1:
   phase4();
   phase1_2();
   break;
   case 2:
   phase3();
   phase2_2();
   break;
   case 3:
   phase2();
   phase3_2();
   break;
   case 4:
   phase1();
   phase4_2();
   break;
 }
 ph_cnt++;
 step_cnt++;
 if (ph_cnt>4)
   ph_cnt = 1;
}

void motor1CounterClockwise(){

  switch (ph_cnt) { 
   case 1:
   phase1();
   phase4_2();
   break;
   case 2:
   phase2();
   phase3_2();
   break;
   case 3:
   phase3();
   phase2_2();
   break;
   case 4:
   phase4();
   phase1_2();
   break;
 }
 ph_cnt++;
 step_cnt++;
 if (ph_cnt>4)
   ph_cnt = 1;
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
