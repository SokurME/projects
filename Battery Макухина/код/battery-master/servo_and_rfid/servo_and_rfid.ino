#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>

// ===== RFID =====
#define SS_PIN 10
#define RST_PIN 9
MFRC522 rfid(SS_PIN, RST_PIN);

// ===== SERVO PINS =====
#define SERVO_CONT_1_PIN 3
#define SERVO_CONT_2_PIN 5
#define SERVO_POS_PIN    6

// ===== DEFINES =====
#define SERVO_RUN_TIME   2000   // мс
#define COMMAND_TIMEOUT 5000  // мс — ожидание команды от Raspberry Pi
#define SERVO_STOP       90
#define SERVO_RUN_1      110
#define SERVO_RUN_2      70
#define SERVO_POS_ANGLE  45

// ===== DEBUG =========
#define DEBUG_OTPUT 1

// ===== STATE MACHINE =====
enum State {
  IDLE,
  WAIT_COMMAND,
  RUN_CONT_SERVOS,
  MOVE_POSITION_SERVO
};

State currentState = IDLE;
unsigned long stateStartTime = 0;

Servo servo1;
Servo servo2;
Servo servo3;

// ===== RFID UID → CLASS =====
String getClassFromUID(byte *uid, byte size) {
  if (size == 4 &&
      uid[0] == 0xF3 && uid[1] == 0xB8 &&
      uid[2] == 0x92 && uid[3] == 0xA5) {
    return "9I";
  }

  if (size == 4 &&
      uid[0] == 0x11 && uid[1] == 0x22 &&
      uid[2] == 0x33 && uid[3] == 0x44) {
    return "7B";
  }

  return "UNKNOWN";
}

void setup() {
  Serial.begin(9600);

  SPI.begin();
  rfid.PCD_Init();

  servo1.attach(SERVO_CONT_1_PIN);
  servo2.attach(SERVO_CONT_2_PIN);
  servo3.attach(SERVO_POS_PIN);

  servo1.write(SERVO_STOP);
  servo2.write(SERVO_STOP);

  Serial.println("READY");
}

void loop() {
  switch (currentState) {

    // ================= IDLE =================
    case IDLE:
      handleRFID();
        #if (DEBUG_OTPUT)
          Serial.println("st IDLE");
        #endif
      break;

    // ================= WAIT COMMAND =================
    case WAIT_COMMAND:
      handleCommand();
        #if (DEBUG_OTPUT)
          Serial.println("st WAIT_COMMAND");
        #endif
      break;

    // ================= RUN CONTINUOUS SERVOS =================
    case RUN_CONT_SERVOS:
      if (millis() - stateStartTime >= SERVO_RUN_TIME) {
        servo1.write(SERVO_STOP);
        servo2.write(SERVO_STOP);

        stateStartTime = millis();
        currentState = MOVE_POSITION_SERVO;
      }
      break;

    // ================= MOVE POSITION SERVO =================
    case MOVE_POSITION_SERVO:
      servo3.write(SERVO_POS_ANGLE);
      currentState = IDLE;
        #if (DEBUG_OTPUT)
          Serial.println("MOVE_POSITION_SERVO");
        #endif
      break;
  }
}

// ===== RFID HANDLER =====
void handleRFID() {
  if (!rfid.PICC_IsNewCardPresent()) return;
  if (!rfid.PICC_ReadCardSerial()) return;

  String schoolClass = getClassFromUID(rfid.uid.uidByte, rfid.uid.size);

  Serial.print("CLASS:");
  Serial.println(schoolClass);

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  stateStartTime = millis();
  currentState = WAIT_COMMAND;
}

// ===== SERIAL COMMAND HANDLER =====
void handleCommand() {
  // таймаут ожидания команды
  if (millis() - stateStartTime > COMMAND_TIMEOUT) {
    currentState = IDLE;
    return;
  }

  if (!Serial.available()) return;

  String cmd = Serial.readStringUntil('\n');
  cmd.trim();

  if (cmd == "RUN") {
    servo1.write(SERVO_RUN_1);
    servo2.write(SERVO_RUN_2);
    stateStartTime = millis();
    currentState = RUN_CONT_SERVOS;
        #if (DEBUG_OTPUT)
          Serial.println("start servo cnt");
        #endif
  } 
  else {
    // SKIP или неизвестная команда
    currentState = IDLE;
  }
}
