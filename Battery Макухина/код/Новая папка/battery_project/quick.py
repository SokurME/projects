import cv2
import numpy as np
import os

def detect_circles(image_path):
    """Обнаружение круглых объектов (CR батарейки)"""
    
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Детекция кругов
    circles = cv2.HoughCircles(
        gray, 
        cv2.HOUGH_GRADIENT, 
        dp=1.2, 
        minDist=50,
        param1=50, 
        param2=30, 
        minRadius=20, 
        maxRadius=100
    )
    
    if circles is not None:
        circles = np.uint16(np.around(circles))
        print(f"Найдено {len(circles[0])} круглых объектов")
        
        # Рисуем круги
        for i in circles[0, :]:
            cv2.circle(img, (i[0], i[1]), i[2], (0, 255, 0), 2)
            cv2.circle(img, (i[0], i[1]), 2, (0, 0, 255), 3)
    
    return img

# Тест на одном фото
test_photo = "raw_images/CR/WIN_20260209_19_04_57_Pro.jpg"
if os.path.exists(test_photo):
    result = detect_circles(test_photo)
    cv2.imwrite("detection_test.jpg", result)
    print("✅ Результат сохранён как 'detection_test.jpg'")
else:
    print("❌ Тестовое фото не найдено")
