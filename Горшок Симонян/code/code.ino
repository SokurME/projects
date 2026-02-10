// Умный горшок. Проверка датчика DHT11 на D5
#include <DHT.h>

#define DHTPIN 5      // Пин D5, к которому подключен DATA датчика
#define DHTTYPE DHT11 // Тип датчика

// Создаем объект датчика
DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  Serial.println("Тест DHT11 на D5...");
  dht.begin(); // Инициализируем датчик
}

void loop() {
  // Ждем минимум 2 секунды между измерениями (DHT11 очень медленный)
  delay(2000);

  // Считываем влажность
  float humidity = dht.readHumidity();
  // Считываем температуру (в градусах Цельсия)
  float temperature = dht.readTemperature();

  // Проверяем, удалось ли считать данные
  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("Ошибка чтения с DHT11!");
    return;
  }

  // Выводим данные в монитор порта
  Serial.print("Влажность: ");
  Serial.print(humidity);
  Serial.print(" %\t");
  Serial.print("Температура: ");
  Serial.print(temperature);
  Serial.println(" °C");
}
