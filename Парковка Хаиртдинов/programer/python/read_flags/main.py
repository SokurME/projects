import requests
import time

esp_ip = "http://192.168.4.1"

max_retries = 3  # Максимальное количество попыток
retry_delay = 5  # Задержка между попытками (в секундах)

for attempt in range(1, max_retries + 1):
    try:
        print(f"Попытка {attempt} из {max_retries}...")
        response = requests.get(f"{esp_ip}/status", timeout=5)
        response.raise_for_status()
        
        data = response.json()
        park_flag = data.get("parkFlag", False)
        print(f"Значение parkFlag: {park_flag}")
        task_End = data.get("taskEnd", False)
        print(f"Значение task_End: {task_End}")
        break  # Успешное выполнение, выходим из цикла
    except requests.exceptions.Timeout:
        print("Ошибка: Превышено время ожидания ответа от ESP8266.")
    except requests.exceptions.ConnectionError:
        print("Ошибка: Невозможно подключиться к ESP8266.")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе: {e}")
    
    if attempt < max_retries:
        print(f"Повторная попытка через {retry_delay} секунд...")
        time.sleep(retry_delay)
    else:
        print("Максимальное количество попыток исчерпано. Завершение.")
