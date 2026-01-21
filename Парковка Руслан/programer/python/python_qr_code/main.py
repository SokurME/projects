import logging
from qr import recognize_qr_code_from_camera    # Импорт функции recognize_qr_code_from_camera из модуля qr.py
from park import ParkingSystem # Импорт класса ParkingSystem из модуля parking.py
import requests
import json
import time
import wiringpi


def control_leds(red_pin, green_pin, blue_pin, red, green, blue):
# Управляет светодиодами на основе входных сигналов.
    wiringpi.digitalWrite(red_pin, red)
    wiringpi.digitalWrite(green_pin, green)
    wiringpi.digitalWrite(blue_pin, blue)


# настройка логгера
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# настройка обработчика и форматировщика для logger2
handler = logging.FileHandler(f"{__name__}.log", mode='a')
formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
# добавление форматировщика к обработчику
handler.setFormatter(formatter)
# добавление обработчика к логгеру
logger.addHandler(handler)

esp_ip = "http://192.168.4.1"
max_retries = 10  # Максимальное количество запросов к ESP8266
retry_delay = 5  # Задержка между попытками (в секундах)


# Основная программа
def main():
    logger.debug("Запуск программы.")
    orangePi = True
    if orangePi:
        
        RED_PIN = 10
        GREEN_PIN = 9
        BLUE_PIN = 6
        wiringpi.wiringPiSetup()
        wiringpi.pinMode(RED_PIN, 1)       # Set pin  to   OUTPUT
        wiringpi.pinMode(GREEN_PIN, 1) 
        wiringpi.pinMode(BLUE_PIN, 1) 

    parking_system = ParkingSystem(port='/dev/ttyUSB0', baudrate=9600)
    if parking_system.serial_port is None:
        logger.error("Система управления недоступна: последовательный порт не открыт.")
        print("Система управления недоступна: последовательный порт не открыт.")
        return
    # основной цикл программы
    while True:
        # распознаем QR-код с камеры и пытаемся припарковать машину
        if orangePi:
            control_leds(RED_PIN, GREEN_PIN, BLUE_PIN, 0, 0, 1)  # Включаем синий светодиод
        plate_number = recognize_qr_code_from_camera()
        control_cmd = parking_system.assign_slot(plate_number)
        if (control_cmd ==1):
            print("Хранение")
            logger.info("Хранение")
            data = None
            while data == None: 
                data = parking_system.receive_from_serial()
            # print (f'data from serial {data}')
            if orangePi:
                control_leds(RED_PIN, GREEN_PIN, BLUE_PIN, 0, 1, 0)  # Включаем зеленый светодиод
            print("Разрешена загрузка")
            logger.info("Разрешена загрузка")
            # выводим состояние парковки
            parked_cars = ", ".join([f"({i+1}, {car_number})" for i, car_number in enumerate(parking_system.parking_slots) ])
            logger.info("Состояние парковки: %s", parked_cars)
            # делаем запросы к ESP8266
            for attempt in range(1, max_retries + 1):
            # читаем данные с ESP8266
                try:
                    response = requests.get(f"{esp_ip}/status", timeout=5)
                    response.raise_for_status()
                    raw_response = response.text
                    # print("Сырой ответ сервера:", raw_response)
                # Пробуем разобрать JSON
                    try:
                        data = json.loads(raw_response)  # Разбор вручную
                        taskEnd = data.get("taskEnd", False)
                        print(f"Значение taskEnd: {taskEnd}")
                    except json.JSONDecodeError as e:
                        print(f"Ошибка разбора JSON: {e}")
                        logger.error("Ошибка разбора JSON: %s", e)
                except requests.exceptions.Timeout:
                    print("Ошибка: Превышено время ожидания ответа от ESP8266.")
                    logger.error("Ошибка: Превышено время ожидания ответа от ESP8266.")
                except requests.exceptions.ConnectionError:
                    print("Ошибка: Невозможно подключиться к ESP8266.")
                    logger.error("Ошибка: Невозможно подключиться к ESP8266.")
                except requests.exceptions.RequestException as e:
                    logger.error("Ошибка при запросе к ESP8266: %s", e)
                    print(f"Ошибка при запросе: {e}")
                
                if taskEnd:
                    try:
                    # Отправляем запрос на изменение флага
                        response = requests.get(f"{esp_ip}/set_flag", params={"flag": "taskEnd", "value": "false"}, timeout=5)
                        response.raise_for_status()
                        response.encoding = 'utf-8'
                    # Выводим ответ сервера
                        print("Ответ от ESP:", response.text)
                        taskEnd  = False
                        if orangePi:
                            control_leds(RED_PIN, GREEN_PIN, BLUE_PIN, 1, 0, 0)  # Включаем красный светодиод
                        break
                    except requests.exceptions.RequestException as e:
                        print(f"Ошибка при запросе: {e}")
                        logger.error("Ошибка при запросе к ESP826: %s", e)


                if attempt < max_retries:
                    print(f"Повторная попытка через {retry_delay} секунд...")
                    time.sleep(retry_delay)
                else:
                    print("Максимальное количество попыток исчерпано. Завершение.")
                    print("Нет ответа от машины о парковке!")
                    logger.error("Нет ответа от машины о парковке!")
        if (control_cmd ==2):
            print("Перемещение ячеек")
            logger.info("Перемещение ячеек")
            data = None
            while data == None: 
                data = parking_system.receive_from_serial()
            # print (f'data from serial {data}') 
            print("Разрешена выгрузка")
            logger.info("Разрешена выгрузка")   
            # выводим состояние парковки
            parked_cars = ", ".join([f"({i+1}, {car_number})" for i, car_number in enumerate(parking_system.parking_slots) ])
            logger.info("Состояние парковки: %s", parked_cars)
            if orangePi:
                control_leds(RED_PIN, GREEN_PIN, BLUE_PIN, 1, 0, 0)  # Включаем красный светодиод
            time.sleep(7)
            if orangePi:
                control_leds(RED_PIN, GREEN_PIN, BLUE_PIN, 0, 0, 0)
        if (control_cmd ==0):
                logger.error("Нет свободных ячеек на парковке.")

    logger.debug("Завершение программы.")


if __name__ == "__main__":
    main()
