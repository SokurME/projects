import cv2
import socket
import requests
import numpy as np
import time
import threading
import os

# ===== Настройки =====
PI_HOST = "10.42.0.1"  # IP Raspberry Pi
PI_PORT = 5000
VIDEO_URL = f"http://{PI_HOST}:8000/video"

# ===== TCP connection =====
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((PI_HOST, PI_PORT))
print("Connected to Raspberry Pi TCP server")

# ===== Выбор режима =====
mode = input("Выберите режим (m = manual, a = auto): ").lower()

# ===== Глобальные переменные для видео =====
current_frame = None
frame_lock = threading.Lock()
video_active = True

# ===== Функция для получения видео в отдельном потоке =====
def video_stream_thread():
    """Поток для непрерывного получения видео."""
    global current_frame, video_active
    
    try:
        print("Запускаю видеопоток...")
        stream = requests.get(VIDEO_URL, stream=True, timeout=5)
        bytes_data = b""
        
        for chunk in stream.iter_content(chunk_size=1024):
            if not video_active:
                break
                
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')
            b = bytes_data.find(b'\xff\xd9')
            
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]
                
                frame = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
                if frame is not None:
                    with frame_lock:
                        current_frame = frame.copy()
    
    except Exception as e:
        print(f"Ошибка видеопотока: {e}")
        video_active = False

# ===== Функция для обнаружения зеленых объектов =====
def detect_green_objects(frame, object_type="cylinder"):
    """
    Обнаруживает зеленые объекты на изображении.
    object_type: "cylinder" - высокий цилиндр, "stripe" - зеленая полоска
    Возвращает обработанный кадр и флаг обнаружения
    """
    if frame is None:
        return frame, False
    
    result = frame.copy()
    height, width = frame.shape[:2]
    
    # Конвертируем в HSV для лучшего выделения цвета
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Диапазон зеленого цвета в HSV
    lower_green = np.array([40, 50, 50])
    upper_green = np.array([80, 255, 255])
    
    # Создаем маску зеленого цвета
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Убираем шум
    kernel = np.ones((5, 5), np.uint8)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)
    green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)
    
    # Находим контуры
    contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    found = False
    
    if object_type == "cylinder":
        # Параметры для цилиндра (высокий объект)
        MIN_AREA = 1000
        MIN_ASPECT_RATIO = 1.5  # Высокий объект
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > MIN_AREA:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = h / w if w > 0 else 0
                
                if aspect_ratio > MIN_ASPECT_RATIO:
                    found = True
                    # Рисуем bounding box
                    cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 3)
                    
                    # Текст обнаружения
                    cv2.putText(result, "GREEN CYLINDER DETECTED", 
                               (width//4, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                               1, (0, 255, 0), 2)
                    
                    # Информация
                    cv2.putText(result, f"Area: {area:.0f}", (x, y - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    elif object_type == "stripe":
        # Параметры для полоски (горизонтальный объект)
        MIN_AREA = 500
        MAX_ASPECT_RATIO = 0.5  # Широкий горизонтальный объект
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > MIN_AREA:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = h / w if w > 0 else 0
                
                if aspect_ratio < MAX_ASPECT_RATIO:
                    found = True
                    # Рисуем bounding box
                    cv2.rectangle(result, (x, y), (x + w, y + h), (0, 200, 100), 3)
                    
                    # Текст обнаружения
                    cv2.putText(result, "GREEN STRIPE DETECTED", 
                               (width//4, 50), cv2.FONT_HERSHEY_SIMPLEX, 
                               1, (0, 200, 100), 2)
                    
                    # Информация
                    cv2.putText(result, f"Area: {area:.0f}", (x, y - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 100), 1)
    
    # Показываем количество найденных контуров
    cv2.putText(result, f"Green contours: {len(contours)}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    return result, found

# ===== АВТОРЕЖИМ - НОВЫЙ АЛГОРИТМ =====
if mode == "a":
    print("=" * 60)
    print("АВТОРЕЖИМ: НОВЫЙ АЛГОРИТМ")
    print("=" * 60)
    print("Алгоритм:")
    print("1. 'r' на 1 с (поворот вправо)")
    print("2. 'f' на 0.6 с (вперед)")
    print("3. Обнаружение зеленого цилиндра")
    print("4. 'f' на 0.5 с (вперед)")
    print("5. 'h' (спец команда)")
    print("6. 'u' (спец команда)")
    print("7. 'b' на 1 с (назад)")
    print("8. 'l' на 2 с (влево)")
    print("9. Обнаружение зеленой полоски")
    print("10. 'f' на 1 с (вперед)")
    print("11. 'g' (спец команда)")
    print("12. 'b' на 1 с (назад)")
    print("=" * 60)
    
    # Запускаем поток видео
    video_thread = threading.Thread(target=video_stream_thread)
    video_thread.daemon = True
    video_thread.start()
    
    # Ждем немного, чтобы видео запустилось
    time.sleep(2)
    
    try:
        # Создаем окно
        cv2.namedWindow("КАМЕРА - АВТОРЕЖИМ", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("КАМЕРА - АВТОРЕЖИМ", 800, 600)
        
        # === ШАГ 1: Поворот вправо 1 секунда ===
        print("\n[ШАГ 1] Поворот вправо 1 секунда...")
        sock.send(b"r")
        
        start_time = time.time()
        while time.time() - start_time < 1.0:
            # Показываем видео
            with frame_lock:
                if current_frame is not None:
                    # Отображаем кадр без обработки
                    cv2.imshow("КАМЕРА - АВТОРЕЖИМ", current_frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                raise KeyboardInterrupt
            time.sleep(0.01)
        
        sock.send(b"s")
        print("[ШАГ 1] Завершено")
        
        # === ШАГ 2: Движение вперед 0.6 секунды ===
        print("\n[ШАГ 2] Движение вперед 0.6 секунды...")
        sock.send(b"f")
        
        start_time = time.time()
        while time.time() - start_time < 0.6:
            with frame_lock:
                if current_frame is not None:
                    cv2.imshow("КАМЕРА - АВТОРЕЖИМ", current_frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                raise KeyboardInterrupt
            time.sleep(0.01)
        
        sock.send(b"s")
        print("[ШАГ 2] Завершено")
        
        # === ШАГ 3: Обнаружение зеленого цилиндра ===
        print("\n[ШАГ 3] Поиск зеленого цилиндра (3 секунды)...")
        detection_start = time.time()
        cylinder_detected = False
        
        while time.time() - detection_start < 3.0:
            with frame_lock:
                if current_frame is not None:
                    # Ищем зеленый цилиндр
                    processed, found = detect_green_objects(current_frame, "cylinder")
                    cv2.imshow("КАМЕРА - АВТОРЕЖИМ", processed)
                    
                    if found and not cylinder_detected:
                        cylinder_detected = True
                        print("[ШАГ 3] Зеленый цилиндр обнаружен!")
            
            if cv2.waitKey(1) & 0xFF == 27:
                raise KeyboardInterrupt
            time.sleep(0.01)
        
        if not cylinder_detected:
            print("[ШАГ 3] Цилиндр не обнаружен, продолжаем...")
        
        # === ШАГ 4: Движение вперед 0.5 секунды ===
        print("\n[ШАГ 4] Движение вперед 0.5 секунды...")
        sock.send(b"f")
        
        start_time = time.time()
        while time.time() - start_time < 0.5:
            with frame_lock:
                if current_frame is not None:
                    cv2.imshow("КАМЕРА - АВТОРЕЖИМ", current_frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                raise KeyboardInterrupt
            time.sleep(0.01)
        
        sock.send(b"s")
        print("[ШАГ 4] Завершено")
        
        # === ШАГ 5: Команда 'h' ===
        print("\n[ШАГ 5] Отправка команды 'h'...")
        sock.send(b"h")
        print("[ШАГ 5] Команда 'h' отправлена")
        time.sleep(0.5)  # Пауза
        
        # === ШАГ 6: Команда 'u' ===
        print("\n[ШАГ 6] Отправка команды 'u'...")
        sock.send(b"u")
        print("[ШАГ 6] Команда 'u' отправлена")
        time.sleep(0.5)  # Пауза
        
        # === ШАГ 7: Движение назад 1 секунда ===
        print("\n[ШАГ 7] Движение назад 1 секунда...")
        sock.send(b"b")
        
        start_time = time.time()
        while time.time() - start_time < 1.0:
            with frame_lock:
                if current_frame is not None:
                    cv2.imshow("КАМЕРА - АВТОРЕЖИМ", current_frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                raise KeyboardInterrupt
            time.sleep(0.01)
        
        sock.send(b"s")
        print("[ШАГ 7] Завершено")
        
        # === ШАГ 8: Поворот влево 2 секунды ===
        print("\n[ШАГ 8] Поворот влево 2 секунды...")
        sock.send(b"l")
        
        start_time = time.time()
        while time.time() - start_time < 2.0:
            with frame_lock:
                if current_frame is not None:
                    cv2.imshow("КАМЕРА - АВТОРЕЖИМ", current_frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                raise KeyboardInterrupt
            time.sleep(0.01)
        
        sock.send(b"s")
        print("[ШАГ 8] Завершено")
        
        # === ШАГ 9: Обнаружение зеленой полоски ===
        print("\n[ШАГ 9] Поиск зеленой полоски (3 секунды)...")
        detection_start = time.time()
        stripe_detected = False
        
        while time.time() - detection_start < 3.0:
            with frame_lock:
                if current_frame is not None:
                    # Ищем зеленую полоску
                    processed, found = detect_green_objects(current_frame, "stripe")
                    cv2.imshow("КАМЕРА - АВТОРЕЖИМ", processed)
                    
                    if found and not stripe_detected:
                        stripe_detected = True
                        print("[ШАГ 9] Зеленая полоска обнаружена!")
            
            if cv2.waitKey(1) & 0xFF == 27:
                raise KeyboardInterrupt
            time.sleep(0.01)
        
        if not stripe_detected:
            print("[ШАГ 9] Полоска не обнаружена, продолжаем...")
        
        # === ШАГ 10: Движение вперед 1 секунда ===
        print("\n[ШАГ 10] Движение вперед 1 секунда...")
        sock.send(b"f")
        
        start_time = time.time()
        while time.time() - start_time < 1.0:
            with frame_lock:
                if current_frame is not None:
                    cv2.imshow("КАМЕРА - АВТОРЕЖИМ", current_frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                raise KeyboardInterrupt
            time.sleep(0.01)
        
        sock.send(b"s")
        print("[ШАГ 10] Завершено")
        
        # === ШАГ 11: Команда 'g' ===
        print("\n[ШАГ 11] Отправка команды 'g'...")
        sock.send(b"g")
        print("[ШАГ 11] Команда 'g' отправлена")
        time.sleep(0.5)  # Пауза
        
        # === ШАГ 12: Движение назад 1 секунда ===
        print("\n[ШАГ 12] Движение назад 1 секунда...")
        sock.send(b"b")
        
        start_time = time.time()
        while time.time() - start_time < 1.0:
            with frame_lock:
                if current_frame is not None:
                    cv2.imshow("КАМЕРА - АВТОРЕЖИМ", current_frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                raise KeyboardInterrupt
            time.sleep(0.01)
        
        sock.send(b"s")
        print("[ШАГ 12] Завершено")
        
        # === ФИНАЛ ===
        print("\n" + "=" * 60)
        print("АВТОРЕЖИМ УСПЕШНО ЗАВЕРШЕН!")
        print("=" * 60)
        print("Итог:")
        print(f"  - Зеленый цилиндр: {'ДА' if cylinder_detected else 'НЕТ'}")
        print(f"  - Зеленая полоска: {'ДА' if stripe_detected else 'НЕТ'}")
        print("=" * 60)
        print("Нажмите ESC для выхода...")
        
        # Показываем видео еще 5 секунд
        end_time = time.time() + 5
        while time.time() < end_time:
            with frame_lock:
                if current_frame is not None:
                    cv2.imshow("КАМЕРА - АВТОРЕЖИМ", current_frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                break
    
    except KeyboardInterrupt:
        print("\nПрервано пользователем")
    
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        video_active = False
        sock.send(b"s")  # Финальная остановка
        sock.close()
        cv2.destroyAllWindows()

# ===== РУЧНОЙ РЕЖИМ (остается без изменений) =====
elif mode == "m":
    print("=" * 50)
    print("РУЧНОЙ РЕЖИМ: Запуск")
    print("Управление: W S A D Q ПРОБЕЛ G H U")
    print("ESC - выход")
    print("=" * 50)
    
    # Запускаем поток видео
    video_thread = threading.Thread(target=video_stream_thread)
    video_thread.daemon = True
    video_thread.start()
    
    # Ждем немного, чтобы видео запустилось
    time.sleep(2)
    
    try:
        cv2.namedWindow("КАМЕРА - РУЧНОЙ РЕЖИМ", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("КАМЕРА - РУЧНОЙ РЕЖИМ", 800, 600)
        
        while True:
            # Показываем текущий кадр
            with frame_lock:
                if current_frame is not None:
                    # В ручном режиме можно также показывать детекцию
                    processed, _ = detect_green_objects(current_frame, "cylinder")
                    cv2.imshow("КАМЕРА - РУЧНОЙ РЕЖИМ", processed)
            
            # Обработка клавиш
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC
                break
            elif key == ord('w'):
                sock.send(b"f")
                print("Вперед")
            elif key == ord('s'):
                sock.send(b"b")
                print("Назад")
            elif key == ord('a'):
                sock.send(b"l")
                print("Влево")
            elif key == ord('d'):
                sock.send(b"r")
                print("Вправо")
            elif key == ord('q'):
                sock.send(b"s")
                print("Стоп")
            elif key == 32:  # ПРОБЕЛ
                sock.send(b"s")
                print("Экстренный стоп")
            elif key == ord('g'):
                sock.send(b"g")
                print("Команда G")
            elif key == ord('h'):
                sock.send(b"h")
                print("Команда H")
            elif key == ord('u'):
                sock.send(b"u")
                print("Команда U")
    
    except Exception as e:
        print(f"Ошибка: {e}")
    
    finally:
        video_active = False
        sock.send(b"s")
        sock.close()
        cv2.destroyAllWindows()

else:
    print("Неверный режим!")
    sock.close()
