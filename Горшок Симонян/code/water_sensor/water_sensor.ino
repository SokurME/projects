// Тестирование фоторезистора на A2 (ОБРАТНАЯ логика)
// Подключение:
// - Один вывод фоторезистора → 5V
// - Другой вывод фоторезистора → A2 и через резистор 10кОм → GND

#define PHOTORESISTOR_PIN A2  // Фоторезистор на A2

void setup() {
  Serial.begin(9600);
  Serial.println("Тестирование фоторезистора на A2");
  Serial.println("---------------------------------");
  Serial.println("ОБРАТНАЯ ЛОГИКА:");
  Serial.println("ВЫСОКОЕ значение = СВЕТЛО");
  Serial.println("НИЗКОЕ значение = ТЕМНО");
  Serial.println("---------------------------------");
  delay(2000);
}

void loop() {
  // Считываем аналоговое значение (0-1023)
  int lightValue = analogRead(PHOTORESISTOR_PIN);
  
  // Преобразуем в проценты (прямая логика)
  // Высокое значение = светло = высокий процент освещенности
  int lightPercent = map(lightValue, 0, 1023, 0, 100);
  
  // Выводим данные
  Serial.print("Аналоговое значение: ");
  Serial.print(lightValue);
  Serial.print(" | Освещенность: ");
  Serial.print(lightPercent);
  Serial.println("%");
  
  // Определяем уровень освещенности (ОБРАТНАЯ логика)
  Serial.print("Уровень: ");
  
  if (lightValue > 900) {
    Serial.print("ОЧЕНЬ СВЕТЛО (яркий свет)");
  } else if (lightValue > 700) {
    Serial.print("СВЕТЛО");
  } else if (lightValue > 500) {
    Serial.print("СРЕДНЯЯ освещенность");
  } else if (lightValue > 300) {
    Serial.print("ТЕМНОВАТО");
  } else {
    Serial.print("ОЧЕНЬ ТЕМНО");
  }
  
  // Рекомендации для растений
  Serial.print(" | Для растений: ");
  if (lightValue > 800) {
    Serial.println("МНОГО света (возможно слишком)");
  } else if (lightValue > 400) {
    Serial.println("ИДЕАЛЬНО для растений");
  } else if (lightValue > 200) {
    Serial.println("МАЛО света");
  } else {
    Serial.println("ОЧЕНЬ МАЛО света!");
  }
  
  // Визуальная шкала в Serial Monitor
  Serial.print("Шкала: [");
  int bars = map(lightValue, 0, 1023, 0, 20);
  for (int i = 0; i < 20; i++) {
    if (i < bars) {
      Serial.print("#");
    } else {
      Serial.print(".");
    }
  }
  Serial.println("] #=светло, .=темно");
  
  Serial.println("---------------------------------");
  
  // Инструкция для теста
  static unsigned long startTime = millis();
  int elapsedSeconds = (millis() - startTime) / 1000;
  
  if (elapsedSeconds < 10) {
    Serial.println(">>> Полная темнота (накройте рукой)");
    Serial.println("Ожидаем НИЗКИЕ значения (0-300)");
  } else if (elapsedSeconds < 20) {
    Serial.println(">>> Нормальный свет комнаты");
    Serial.println("Ожидаем СРЕДНИЕ значения (400-700)");
  } else if (elapsedSeconds < 30) {
    Serial.println(">>> Яркий свет (фонарик/лампа)");
    Serial.println("Ожидаем ВЫСОКИЕ значения (800-1023)");
  } else {
    startTime = millis(); // Сброс таймера
  }
  
  delay(2000); // Пауза между измерениями
}
