import serial
import logging

logger3 = logging.getLogger(__name__)
logger3.setLevel(logging.DEBUG)
# настройка обработчика и форматировщика для logger2
handler3 = logging.FileHandler(f"{__name__}.log", mode='a')
formatter3 = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
# добавление форматировщика к обработчику
handler3.setFormatter(formatter3)
# добавление обработчика к логгеру
logger3.addHandler(handler3)

class ParkingSystem:
    def __init__(self, port, baudrate):
        self.parking_slots = [None] * 6  # Список для хранения номеров машин в ячейках
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=1)  # Настройка последовательного порта
            logger3.info(f"Последовательный порт {port} открыт успешно.")
        except serial.SerialException as e:
            logger3.error(f"Не удалось открыть порт {port}: {e}")
            self.serial_port = None

    def find_free_slot(self):
        """Ищет первую свободную ячейку."""
        for i, slot in enumerate(self.parking_slots):
            if slot is None:
                return i
        return None

    def find_slot_by_car(self, car_number):
        """Ищет ячейку, где находится машина с заданным номером."""
        for i, slot in enumerate(self.parking_slots):
            if slot == car_number:
                return i
        return None

    def assign_slot(self, car_number):
        """Назначает ячейку машине и отправляет команду в систему управления."""
        if self.serial_port is None:
            print("Система управления недоступна: последовательный порт не открыт.")
            return

        slot = self.find_slot_by_car(car_number)
        if slot is not None:
            # Машина уже на парковке, отправляем номер ячейки и освобождаем её
            self.send_to_serial(slot + 1)  # Номер ячейки (от 1 до 6)
            self.parking_slots[slot] = None
            print(f"Машина {car_number} покинула ячейку {slot + 1}.")
            logger3.info(f"Машина {car_number} покинула ячейку {slot + 1}.")
            return 2
        else:
            # Ищем первую свободную ячейку
            slot = self.find_free_slot()
            if slot is not None:
                self.parking_slots[slot] = car_number
                self.send_to_serial(slot + 1)  # Номер ячейки (от 1 до 6)
                print(f"Номер ячейки хранения автомобиля {car_number} : {slot + 1}.")
                logger3.info(f"Номер ячейки хранения автомобиля {car_number} : {slot + 1}.")
                return 1
            else:
                print("Нет свободных ячеек на парковке.")
                return 0

    def send_to_serial(self, slot_number):
        """Отправляет номер ячейки в систему управления через последовательный порт."""
        if self.serial_port is not None:
            command = f"{slot_number}\n"  # команда для системы управления
            self.serial_port.write(command.encode('utf-8'))
    
    def receive_from_serial(self):
    # Принимает данные с последовательного порта.
        if self.serial_port is not None and self.serial_port.in_waiting > 0:
            data = self.serial_port.readline().decode('utf-8').strip()
            print(f"Получено с Serial: {data}")
            return data
        return None

    def remove_car(self, car_number):
        """Удаляет машину с парковки."""
        slot = self.find_slot_by_car(car_number)
        if slot is not None:
            self.parking_slots[slot] = None
            print(f"Машина {car_number} покинула ячейку {slot + 1}.")
        else:
            print(f"Машина {car_number} не найдена на парковке.")