#include <SPI.h>
#include <MFRC522.h>
// Константы подключения контактов RST и SS
#define RST_PIN    9    
#define SS_PIN    10    

MFRC522 mfrc522(SS_PIN, RST_PIN); 

void setup() {
  Serial.begin(9600);   // Инициализация монитора последовательного порта
  while (!Serial);    // Ожидание включения монитора последовательного порта
  SPI.begin();      // Инициализация SPI шины
  mfrc522.PCD_Init();   // Инициализация RC522
  ShowReaderDetails();          // Вывод данных о модуле RC522
  Serial.println(F("Scan PICC to see UID, type, and data blocks..."));
}

void loop() {
  // Поиск новой метки
  if ( ! mfrc522.PICC_IsNewCardPresent()) {
    return;
  }

  // Выбор метки
  if ( ! mfrc522.PICC_ReadCardSerial()) {
    return;
  }
        // Вывод данных с карты
  mfrc522.PICC_DumpToSerial(&(mfrc522.uid));
}

void ShowReaderDetails() {
  // Получение номера программной версии модуля RC522 
  byte v = mfrc522.PCD_ReadRegister(mfrc522.VersionReg);
  Serial.print(F("MFRC522 Software Version: 0x"));
  Serial.print(v, HEX);
  if (v == 0x91)
    Serial.print(F(" = v1.0"));
  else if (v == 0x92)
    Serial.print(F(" = v2.0"));
  else
    Serial.print(F(" (unknown)"));
  Serial.println("");
  // Когда получено 0x00 или 0xFF, передача данных нарушена
  if ((v == 0x00) || (v == 0xFF)) {
    Serial.println(F("WARNING: Communication failure, is the MFRC522 properly connected?"));
  }
}
