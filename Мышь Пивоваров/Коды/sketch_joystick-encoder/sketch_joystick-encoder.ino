 #include <Wire.h>
 #include <MPU6050_light.h>
 #include <Mouse.h>
 #include <Keyboard.h>
 MPU6050 mpu(Wire);
#define PIN_S1 4
#define PIN_S2 5
volatile int8_t encDir = 0;
uint8_t lastAB = 0;
static const int8_t encTable[16] = {
   0, -1,  1,  0,
   1,  0,  0, -1,
  -1,  0,  0,  1,
   0,  1, -1,  0
};
 bool prev;
 int wheel = 0;
 unsigned long timer = 0;
 int Xang, Yang, Zang;
 int linkerknop = 7;
 int middenknop = 8;
 int rechterknop = 9;
 void setup() {
  pinMode(PIN_S1, INPUT_PULLUP);
  pinMode(PIN_S2, INPUT_PULLUP);
  lastAB = (digitalRead(PIN_S1) << 1) | digitalRead(PIN_S2);
  pinMode(linkerknop, INPUT_PULLUP);
  pinMode(middenknop, INPUT_PULLUP);
  pinMode(rechterknop, INPUT_PULLUP);
  Wire.begin();
  byte status = mpu.begin();
  while (status != 0) { } 
  delay(1000);
  mpu.calcOffsets(); 
  Mouse.begin();    
  Keyboard.begin();
 }
 void loop() {
 mpu.update();  
 if (millis() - timer > 60) { 
  //проверяем наклон гироскопа
  Xang=mpu.getAngleX();
  Yang=mpu.getAngleY();
  Zang=mpu.getAngleZ();
  int liknopstate = digitalRead(linkerknop);
  int miknopstate = digitalRead(middenknop);
  int reknopstate = digitalRead(rechterknop);
  bool vlagli = 0;
  bool vlagmi = 0;
  bool vlagre = 0;
    if ( liknopstate > 0){
    if (vlagli = 1){
    Mouse.release(MOUSE_LEFT);
    vlagli = 0;
    }
    }
  else {
    Mouse.press(MOUSE_LEFT);
    vlagli = 1;
    } 
    
  if ( miknopstate > 0){
    if (vlagmi = 1){
    Mouse.release(MOUSE_MIDDLE);
    vlagmi = 0;
    }
    }
  else {
    Mouse.press(MOUSE_MIDDLE);
    vlagmi = 1;
    } 
   
   if ( reknopstate > 0){
   if (vlagre = 1){
    Mouse.release(MOUSE_RIGHT);
    vlagre = 0;
    }
    }
  else {
    Mouse.press(MOUSE_RIGHT);
    vlagre=1;
    }   
    
    
   if ((Yang > 6) || (Yang < -6) || (Xang > 6) || (Xang < -6)){  
  
     if (Yang > 6){
     Yang = map(Yang, 6, 10, 1, 10);
     }

     else if (Yang < -6) {
     Yang = map(Yang, -10, -6, -10, -1); 
     }
      
     else if (Xang > 6) {  
     Xang = map(Xang, 6, 10, 1, 10); 
     }

     else if (Xang < -6) {
     Xang = map(Xang, -10, -6, -10, -1); 
     }
     Mouse.move(Yang, Xang, 0); //двигаем мышь
     }
     static uint32_t lastTime = 0;
     static int8_t accum = 0;
     uint8_t newAB = (digitalRead(PIN_S1) << 1) | digitalRead(PIN_S2);
     uint8_t idx = (lastAB << 2) | newAB;
     int8_t step = encTable[idx & 0x0F];
     if (step) {
       accum += step;
       lastAB = newAB;
     }
     if (accum >= 2) { //отслеживаем энкодер(колёсико мыши)
      Mouse.move(0, 0, -1);
      accum = 0;
    } else if (accum <= -2) {
      Mouse.move(0, 0, 1);
      accum = 0;
    }
   timer = millis();
   }
  }