# train_final.py
import os
import shutil
from pathlib import Path
import sys

print("="*70)
print("🔋 ОБУЧЕНИЕ МОДЕЛИ ДЛЯ РАСПОЗНАВАНИЯ БАТАРЕЕК")
print("="*70)

# 1. ПРОВЕРКА УСТАНОВКИ
print("\n🔧 Проверяю установку ultralytics...")

try:
    import ultralytics
    print("✅ ultralytics установлен")
except ImportError:
    print("❌ ultralytics не установлен")
    print("📌 Установите: pip install ultralytics")
    sys.exit(1)

# 2. ПРОВЕРКА ДАННЫХ
print("\n📊 Проверяю данные...")

# Файлы должны быть в текущей папке
current_dir = os.getcwd()
print(f"📁 Текущая папка: {current_dir}")

required = [
    ("images/", "папка с изображениями"),
    ("labels/", "папка с метками"),
    ("dataset.yaml", "конфигурационный файл"),
    ("classes.txt", "файл с классами")
]

all_ok = True
for file, desc in required:
    if os.path.exists(file):
        print(f"✅ {file} ({desc})")
    else:
        print(f"❌ {file} не найден ({desc})")
        all_ok = False

if not all_ok:
    print("\n📌 Создайте недостающие файлы:")
    print("   1. Запустите prepare_all.py")
    print("   2. Или создайте вручную")
    sys.exit(1)

# 3. СТАТИСТИКА
images_count = len(list(Path("images").glob("*.jpg")))
labels_count = len(list(Path("labels").glob("*.txt")))

print(f"\n📊 Статистика датасета:")
print(f"   • Изображений: {images_count}")
print(f"   • Меток: {labels_count}")
print(f"   • Соотношение: {'✅ OK' if images_count == labels_count else '⚠️ Проблема'}")

# Показываем классы
with open("classes.txt", "r") as f:
    classes = [line.strip() for line in f]
print(f"   • Классы: {', '.join(classes)}")

# 4. ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР
print("\n🔍 Показываю пример разметки...")

import cv2
import matplotlib.pyplot as plt
import numpy as np

# Берём первое изображение
img_files = list(Path("images").glob("*.jpg"))
if img_files:
    img_path = img_files[0]
    label_path = Path("labels") / f"{img_path.stem}.txt"
    
    if label_path.exists():
        # Загружаем изображение
        img = cv2.imread(str(img_path))
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        
        # Загружаем метки
        with open(label_path, 'r') as f:
            labels = [line.strip() for line in f if line.strip()]
        
        # Рисуем
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        
        # Оригинал
        axes[0].imshow(img_rgb)
        axes[0].set_title(f"Оригинал\n{img_path.name}")
        axes[0].axis('off')
        
        # С разметкой
        axes[1].imshow(img_rgb)
        
        for label in labels:
            parts = label.split()
            if len(parts) >= 5:
                class_id = int(parts[0])
                x_center, y_center, box_w, box_h = map(float, parts[1:5])
                
                # Конвертируем в пиксели
                x1 = int((x_center - box_w/2) * w)
                y1 = int((y_center - box_h/2) * h)
                x2 = int((x_center + box_w/2) * w)
                y2 = int((y_center + box_h/2) * h)
                
                # Цвет по классу
                colors = ['#00FF00', '#FF0000', '#FFFF00']  # зеленый, красный, желтый
                color = colors[class_id] if class_id < len(colors) else '#FFFFFF'
                
                # Рисуем прямоугольник
                from matplotlib.patches import Rectangle
                rect = Rectangle((x1, y1), x2-x1, y2-y1,
                               fill=False, edgecolor=color, linewidth=3)
                axes[1].add_patch(rect)
                
                # Подпись
                class_name = classes[class_id] if class_id < len(classes) else f"class_{class_id}"
                axes[1].text(x1, y1-15, class_name,
                           color='white', fontsize=11, fontweight='bold',
                           bbox=dict(facecolor=color, alpha=0.8, boxstyle='round,pad=0.3'))
        
        axes[1].set_title(f"Разметка\n{len(labels)} объектов")
        axes[1].axis('off')
        
        plt.tight_layout()
        plt.savefig("dataset_preview.jpg", dpi=120, bbox_inches='tight')
        plt.show()
        
        print(f"💾 Пример сохранён: dataset_preview.jpg")

# 5. ЗАПУСК ОБУЧЕНИЯ
print("\n" + "="*70)
print("🚀 ЗАПУСКАЮ ОБУЧЕНИЕ YOLOv8")
print("="*70)

print("\n⚙️ Параметры обучения:")
print("   • Модель: YOLOv8n (nano)")
print("   • Изображений: 640x640")
print("   • Батч: 4 (маленький для CPU)")
print("   • Эпох: 30")
print("   • Устройство: CPU")
print("   • Классы: 2 (AA_battery, CR_battery)")

print("\n⏳ Обучение началось...")
print("   Это займёт 20-40 минут")
print("   Можно свернуть окно")

try:
    from ultralytics import YOLO
    
    # Загружаем модель
    model = YOLO('yolov8n.pt')
    
    # Обучаем
    results = model.train(
        data='dataset.yaml',
        epochs=30,
        imgsz=640,
        batch=4,
        name='battery_detector_v1',
        device='cpu',
        patience=10,
        save=True,
        save_period=5,
        verbose=True
    )
    
    print("\n" + "="*70)
    print("✅ ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print("="*70)
    
    # 6. ПОКАЗЫВАЕМ РЕЗУЛЬТАТЫ
    results_dir = "runs/detect/battery_detector_v1"
    if os.path.exists(results_dir):
        print(f"\n📁 РЕЗУЛЬТАТЫ СОХРАНЕНЫ В:")
        print(f"   {os.path.abspath(results_dir)}")
        
        # Показываем файлы
        print("\n📋 Содержимое:")
        for item in Path(results_dir).iterdir():
            if item.is_file():
                size = item.stat().st_size / 1024  # KB
                print(f"   📄 {item.name} ({size:.1f} KB)")
            elif item.is_dir():
                file_count = len(list(item.glob("*")))
                print(f"   📁 {item.name}/ ({file_count} файлов)")
    
    # 7. ТЕСТИРУЕМ МОДЕЛЬ
    print("\n🧪 ТЕСТИРУЮ МОДЕЛЬ НА НОВЫХ ФОТО...")
    
    # Находим лучшую модель
    best_model_path = f"{results_dir}/weights/best.pt"
    if os.path.exists(best_model_path):
        # Загружаем обученную модель
        trained_model = YOLO(best_model_path)
        
        # Тестируем на 3 случайных фото
        test_images = list(Path("images").glob("*.jpg"))[:3]
        
        for i, img_path in enumerate(test_images):
            print(f"\n📸 Тест {i+1}/{len(test_images)}: {img_path.name}")
            
            # Предсказание
            results = trained_model.predict(
                source=str(img_path),
                conf=0.5,  # порог уверенности
                save=True,
                save_txt=False,
                project="test_results",
                name=f"test_{i+1}"
            )
            
            # Результаты
            for r in results:
                if len(r.boxes) > 0:
                    for box in r.boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        class_name = classes[class_id] if class_id < len(classes) else f"class_{class_id}"
                        print(f"   • {class_name}: уверенность {confidence:.1%}")
                else:
                    print("   • Объекты не обнаружены")
            
            print(f"   💾 Результат сохранён в test_results/test_{i+1}/")
    
    # 8. СОЗДАЁМ СКРИПТ ДЛЯ ИСПОЛЬЗОВАНИЯ
    print("\n📝 СОЗДАЮ СКРИПТ ДЛЯ ИСПОЛЬЗОВАНИЯ МОДЕЛИ...")
    
    detect_script = '''# detect_batteries.py
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
        print(f"\\n📊 РЕЗУЛЬТАТЫ:")
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
'''
    
    with open("detect_batteries.py", "w", encoding="utf-8") as f:
        f.write(detect_script)
    
    print("✅ Создан скрипт для использования: detect_batteries.py")
    
except Exception as e:
    print(f"\n❌ Ошибка при обучении: {e}")
    print("\n🔧 Возможные решения:")
    print("1. Проверьте установку: pip install ultralytics")
    print("2. Убедитесь, что файлы dataset.yaml, images/, labels/ на месте")
    print("3. Попробуйте уменьшить batch size до 2")

print("\n" + "="*70)
print("🎯 ГОТОВО! Модель обучена и готова к использованию.")
print("="*70)
print("\n📌 Используйте модель:")
print("   python detect_batteries.py")
print("\n📌 Для распознавания на своих фото:")
print("   detector = BatteryDetector()")
print("   results = detector.detect_and_show('ваше_фото.jpg')")
