import cv2
import numpy as np
from pathlib import Path
import torch
import torchvision
from PIL import Image
import matplotlib.pyplot as plt

class BatteryDetector:
    def __init__(self, model_path=None, conf_threshold=0.5):
        """
        Инициализация детектора
        
        Args:
            model_path: путь к обученной модели YOLO
            conf_threshold: порог уверенности для детекции
        """
        self.conf_threshold = conf_threshold
        
        # Используем YOLOv5 (можно заменить на YOLOv8)
        if model_path:
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path)
        else:
            # Используем предобученную модель COCO как fallback
            self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
        
        self.class_names = ['AA_battery', 'CR_battery', 'plastic_cap']
        
    def detect_objects(self, image_path):
        """
        Детекция объектов на изображении
        """
        # Загрузка изображения
        img = Image.open(image_path)
        
        # Детекция
        results = self.model(img)
        
        # Фильтрация результатов по порогу уверенности
        detections = []
        for *xyxy, conf, cls in results.xyxy[0]:
            if conf > self.conf_threshold:
                detections.append({
                    'bbox': [int(x) for x in xyxy],
                    'confidence': float(conf),
                    'class': int(cls),
                    'class_name': self.class_names[int(cls)] if int(cls) < len(self.class_names) else f'class_{int(cls)}'
                })
        
        return detections, results
    
    def draw_detections(self, image_path, detections, output_path=None):
        """
        Отрисовка bounding boxes на изображении
        """
        # Чтение изображения
        img = cv2.imread(str(image_path))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Цвета для разных классов
        colors = {
            'AA_battery': (0, 255, 0),      # Зеленый
            'CR_battery': (255, 0, 0),      # Синий
            'plastic_cap': (255, 255, 0)    # Голубой
        }
        
        # Отрисовка bounding boxes
        for det in detections:
            bbox = det['bbox']
            class_name = det['class_name']
            confidence = det['confidence']
            
            # Выбор цвета
            color = colors.get(class_name, (255, 255, 255))
            
            # Рисуем прямоугольник
            cv2.rectangle(img_rgb, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            
            # Подпись с классом и уверенностью
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(img_rgb, label, (bbox[0], bbox[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Сохранение или отображение
        if output_path:
            cv2.imwrite(output_path, cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR))
        
        return img_rgb
    
    def analyze_image(self, image_path, output_path=None):
        """
        Полный анализ изображения
        """
        print(f"Анализ изображения: {image_path}")
        
        # Детекция объектов
        detections, results = self.detect_objects(image_path)
        
        # Вывод результатов
        print(f"\nНайдено объектов: {len(detections)}")
        for i, det in enumerate(detections, 1):
            print(f"{i}. {det['class_name']}: уверенность {det['confidence']:.2%}")
        
        # Визуализация
        img_with_boxes = self.draw_detections(image_path, detections, output_path)
        
        return detections, img_with_boxes

def process_folder(folder_path, output_folder=None):
    """
    Обработка всех изображений в папке
    """
    detector = BatteryDetector()
    
    # Поиск всех изображений
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
    image_paths = []
    for ext in image_extensions:
        image_paths.extend(Path(folder_path).glob(ext))
    
    print(f"Найдено {len(image_paths)} изображений")
    
    # Обработка каждого изображения
    for img_path in image_paths:
        print(f"\n{'='*50}")
        print(f"Обработка: {img_path.name}")
        
        # Создание папки для результатов
        if output_folder:
            output_dir = Path(output_folder)
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"detected_{img_path.name}"
        else:
            output_path = None
        
        # Анализ изображения
        detections, img = detector.analyze_image(str(img_path), str(output_path) if output_path else None)
        
        # Отображение результатов
        plt.figure(figsize=(10, 8))
        plt.imshow(img)
        plt.title(f"Результаты распознавания: {img_path.name}")
        plt.axis('off')
        plt.show()

def simple_detection(image_path):
    """
    Простая детекция с использованием цветового анализа
    """
    # Загрузка изображения
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Цветовые диапазоны для разных объектов
    # Батарейки AA (серебристые/серые)
    gray_lower = np.array([0, 0, 50])
    gray_upper = np.array([180, 50, 220])
    
    # Пластиковые крышки (часто цветные)
    plastic_lower = np.array([10, 100, 100])
    plastic_upper = np.array([25, 255, 255])
    
    # Создание масок
    gray_mask = cv2.inRange(hsv, gray_lower, gray_upper)
    plastic_mask = cv2.inRange(hsv, plastic_lower, plastic_upper)
    
    # Поиск контуров
    contours_gray, _ = cv2.findContours(gray_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_plastic, _ = cv2.findContours(plastic_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Отрисовка результатов
    result = img.copy()
    
    # Батарейки
    for contour in contours_gray:
        area = cv2.contourArea(contour)
        if area > 500:  # фильтр по размеру
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(result, "Battery", (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Крышки
    for contour in contours_plastic:
        area = cv2.contourArea(contour)
        if area > 300:  # фильтр по размеру
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(result, (x, y), (x + w, y + h), (255, 255, 0), 2)
            cv2.putText(result, "Plastic Cap", (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
    
    return result

if __name__ == "__main__":
    # Пример использования
    
    # Инициализация детектора
    detector = BatteryDetector()
    
    # 1. Анализ одного изображения
    image_path = "data/images/your_photo.jpg"  # укажите путь к вашему фото
    detections, result_img = detector.analyze_image(
        image_path,
        output_path="result_detected.jpg"
    )
    
    # 2. Отображение результатов
    plt.figure(figsize=(12, 8))
    plt.subplot(1, 2, 1)
    original_img = Image.open(image_path)
    plt.imshow(original_img)
    plt.title("Оригинальное изображение")
    plt.axis('off')
    
    plt.subplot(1, 2, 2)
    plt.imshow(result_img)
    plt.title("Результаты распознавания")
    plt.axis('off')
    
    plt.tight_layout()
    plt.show()
    
    # 3. Простая цветовая детекция (альтернативный метод)
    print("\n" + "="*50)
    print("Цветовая детекция:")
    simple_result = simple_detection(image_path)
    plt.figure(figsize=(8, 6))
    plt.imshow(cv2.cvtColor(simple_result, cv2.COLOR_BGR2RGB))
    plt.title("Цветовая детекция")
    plt.axis('off')
    plt.show()
    
    # 4. Обработка всей папки с изображениями
    # process_folder("data/images", output_folder="results")
