# detect_batteries.py
from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
from pathlib import Path
import os

class BatteryDetector:
    def __init__(self, model_path="runs/detect/battery_detector_v1/weights/best.pt"):
        """Инициализация детектора батареек"""
        print("🔋 Загружаю модель для распознавания батареек...")
        self.model = YOLO(model_path)
        self.classes = ['AA_battery', 'CR_battery']
        print("✅ Модель загружена!")
    
    def detect(self, image_path, confidence=0.5):
        """Распознавание батареек на изображении"""
        print(f"🔍 Анализирую {image_path}...")
        
        # Предсказание
        results = self.model.predict(
            source=image_path,
            conf=confidence,
            save=False
        )
        
        # Обработка результатов
        detections = []
        for r in results:
            img = r.plot()  # изображение с bounding boxes
            for box in r.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                
                detections.append({
                    'class': self.classes[class_id],
                    'confidence': confidence,
                    'bbox': [int(x) for x in bbox]
                })
        
        return detections, img
    
    def detect_and_show(self, image_path, confidence=0.5, save_path=None):
        """Распознавание с отображением результатов"""
        detections, result_img = self.detect(image_path, confidence)
        
        # Конвертируем BGR в RGB для matplotlib
        result_img_rgb = cv2.cvtColor(result_img, cv2.COLOR_BGR2RGB)
        
        # Отображаем
        plt.figure(figsize=(12, 8))
        plt.imshow(result_img_rgb)
        plt.title(f"Найдено {len(detections)} объектов", fontsize=16)
        plt.axis('off')
        
        # Вывод информации
        print(f"\n📊 РЕЗУЛЬТАТЫ:")
        print(f"   Найдено объектов: {len(detections)}")
        for i, det in enumerate(detections, 1):
            print(f"   {i}. {det['class']}: уверенность {det['confidence']:.1%}")
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"💾 Результат сохранён: {save_path}")
        
        plt.show()
        return detections

# Пример использования
if __name__ == "__main__":
    # Создаём детектор
    detector = BatteryDetector()
    
    # Тестируем на вашем фото
    test_image = input("Введите путь к фото (или нажмите Enter для теста): ").strip()
    
    if not test_image:
        # Ищем любое фото в папке
        if os.path.exists("images"):
            test_images = list(Path("images").glob("*.jpg"))
            if test_images:
                test_image = str(test_images[0])
                print(f"🎯 Использую тестовое фото: {test_image}")
            else:
                print("❌ Фото для теста не найдены")
                exit()
    
    if os.path.exists(test_image):
        detector.detect_and_show(
            image_path=test_image,
            confidence=0.5,
            save_path="detection_result.jpg"
        )
    else:
        print(f"❌ Файл не найден: {test_image}")
