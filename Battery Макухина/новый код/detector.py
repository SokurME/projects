import cv2
import numpy as np
from datetime import datetime

cap = cv2.VideoCapture(0)

print("✅ AA BATTERY DETECTOR - FINAL VERSION")
print("=====================================")
print("✓ Center: (320, 240)")
print("✓ Outer radius: 40px")
print("\nPut battery END at RED CROSS")
print("Press SPACE to save photo")
print("Press ESC to exit")

# ФИКСИРОВАННЫЙ ЦЕНТР
CENTER_X = 320
CENTER_Y = 240
SEARCH_RADIUS = 200

# ТОЧНЫЙ РАДИУС ДЛЯ ВАШЕЙ БАТАРЕЙКИ
EXPECTED_RADIUS = 40  # 40 пикселей
RADIUS_TOLERANCE = 5  # погрешность ±5 пикселей

BATTERY_MIN_RADIUS = EXPECTED_RADIUS - RADIUS_TOLERANCE
BATTERY_MAX_RADIUS = EXPECTED_RADIUS + RADIUS_TOLERANCE

print(f"\n📏 Target radius: {EXPECTED_RADIUS}px ±{RADIUS_TOLERANCE}px")
print(f"   Range: {BATTERY_MIN_RADIUS}-{BATTERY_MAX_RADIUS}px")

detection_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    display = frame.copy()
    h, w = frame.shape[:2]
    
    # 1. КРАСНЫЙ КРЕСТ в центре
    cv2.line(display, (CENTER_X-60, CENTER_Y), (CENTER_X+60, CENTER_Y), 
            (0, 0, 255), 4)
    cv2.line(display, (CENTER_X, CENTER_Y-60), (CENTER_X, CENTER_Y+60), 
            (0, 0, 255), 4)
    cv2.circle(display, (CENTER_X, CENTER_Y), 8, (0, 0, 255), -1)
    
    # 2. Область поиска
    x1 = max(0, CENTER_X - SEARCH_RADIUS)
    y1 = max(0, CENTER_Y - SEARCH_RADIUS)
    x2 = min(w, CENTER_X + SEARCH_RADIUS)
    y2 = min(h, CENTER_Y + SEARCH_RADIUS)
    
    roi = frame[y1:y2, x1:x2]
    
    battery_detected = False
    battery_x = battery_y = battery_r = 0
    
    if roi.size > 0:
        # 3. ПОИСК КРУГОВ
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 30, 100)
        blurred = cv2.GaussianBlur(edges, (9, 9), 2)
        
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=50,
            param1=50,
            param2=20,
            minRadius=BATTERY_MIN_RADIUS,
            maxRadius=BATTERY_MAX_RADIUS
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles[0]))
            
            # Берем круг, ближайший к центру
            best_circle = None
            best_distance = SEARCH_RADIUS
            
            for circle in circles:
                x_local, y_local, r = circle
                x_global = x1 + x_local
                y_global = y1 + y_local
                
                distance = np.sqrt(
                    (x_global - CENTER_X)**2 + 
                    (y_global - CENTER_Y)**2
                )
                
                if distance < best_distance:
                    best_distance = distance
                    best_circle = (x_global, y_global, r)
            
            if best_circle is not None:
                battery_x, battery_y, battery_r = best_circle
                battery_detected = True
                
                # ✅ ЗЕЛЕНЫЙ КРУГ - внешний край батарейки
                cv2.circle(display, (battery_x, battery_y), battery_r, (0, 255, 0), 4)
                cv2.circle(display, (battery_x, battery_y), 5, (0, 0, 255), -1)
                
                # Надпись
                cv2.putText(display, "✅ AA BATTERY", 
                           (battery_x - battery_r, battery_y - battery_r - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Радиус
                cv2.putText(display, f"Radius: {battery_r}px", 
                           (battery_x - battery_r, battery_y + battery_r + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # 4. СТАТУС
    if battery_detected:
        status = f"✅ AA BATTERY - Radius: {battery_r}px"
        status_color = (0, 255, 0)
    else:
        status = "🔍 Put battery on RED CROSS"
        status_color = (0, 255, 255)
    
    cv2.putText(display, status, (10, 30), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
    
    cv2.putText(display, "SPACE = save photo | ESC = exit", 
               (10, h-20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    
    # 5. ПОКАЗ
    cv2.imshow('AA BATTERY DETECTOR', display)
    
    # 6. УПРАВЛЕНИЕ
    key = cv2.waitKey(1) & 0xFF
    
    if key == 27:  # ESC
        break
    elif key == 32:  # SPACE
        if battery_detected:
            detection_count += 1
            
            # СОХРАНЯЕМ ФОТО
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"aa_battery_{detection_count}_{timestamp}.png"
            cv2.imwrite(filename, display)
            
            print(f"\n✅ Photo saved: {filename}")
            print(f"   Radius: {battery_r}px")
            print(f"   Position: ({battery_x}, {battery_y})")
            
            # Мигающий зеленый экран подтверждения
            for _ in range(3):
                display_copy = display.copy()
                cv2.putText(display_copy, "✅ PHOTO SAVED!", 
                           (CENTER_X-120, CENTER_Y-100),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
                cv2.imshow('AA BATTERY DETECTOR', display_copy)
                cv2.waitKey(200)
                cv2.imshow('AA BATTERY DETECTOR', display)
                cv2.waitKey(100)
        else:
            print("\n❌ No battery detected!")

cap.release()
cv2.destroyAllWindows()

print(f"\n{'='*50}")
print(f"✅ PROGRAM FINISHED")
print(f"📸 Photos saved: {detection_count}")
print(f"{'='*50}")
