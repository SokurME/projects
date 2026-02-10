# train_batteries_fixed.py
import os
import sys
from pathlib import Path

print("="*60)
print("🎯 ОБУЧЕНИЕ МОДЕЛИ ДЛЯ БАТАРЕЕК")
print("="*60)

# 1. НАХОДИМ YOLOv5
print("\n🔍 Ищу YOLOv5...")

# Возможные пути
possible_paths = [
    "yolov5",                    # рядом с вашей папкой
    "../yolov5",                 # на уровень выше
    "C:/Users/Mariia/yolov5",    # полный путь
    "yolov5-master",             # если скачали как архив
    "YOLOv5"                     # с большой буквы
]

yolo_path = None
for path in possible_paths:
    if os.path.exists(path) and os.path.exists(os.path.join(path, "train.py")):
        yolo_path = path
        print(f"✅ Нашёл YOLOv5 в: {yolo_path}")
        break

if not yolo_path:
    print("❌ YOLOv5 не найден!")
    print("\n📌 Скачайте YOLOv5:")
    print("   git clone https://github.com/ultralytics/yolov5")
    print("   или скачайте архив с GitHub")
    print("\n📌 И поместите папку yolov5 рядом с вашими файлами")
    exit()

# 2. ПРОВЕРЯЕМ ДАННЫЕ
print("\n📊 Проверяю данные...")

required_files = [
    "dataset.yaml",
    "images/",
    "labels/",
    "classes.txt"
]

all_ok = True
for file in required_files:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} не найден")
        all_ok = False

if not all_ok:
    print("\n📌 Сначала запустите prepare_all.py")
    exit()

# 3. ПОКАЗЫВАЕМ СТАТИСТИКУ
images_count = len(list(Path("images").glob("*.jpg")))
labels_count = len(list(Path("labels").glob("*.txt")))

print(f"\n📊 Статистика датасета:")
print(f"   • Изображений: {images_count}")
print(f"   • Меток: {labels_count}")
print(f"   • Классы: AA_battery, CR_battery")

# 4. ЗАПУСКАЕМ ОБУЧЕНИЕ
print("\n" + "="*60)
print("🚀 ЗАПУСКАЮ ОБУЧЕНИЕ...")
print("="*60)

# Команда для обучения
command = f"""
python "{os.path.join(yolo_path, 'train.py')}" \\
  --img 640 \\
  --batch 4 \\       # уменьшил для CPU
  --epochs 30 \\
  --data "{os.path.abspath('dataset.yaml')}" \\
  --weights "{os.path.join(yolo_path, 'yolov5s.pt')}" \\
  --name "battery_detector" \\
  --device cpu \\
  --patience 10 \\
  --exist-ok \\
  --workers 0
"""

print("⚙️ Команда:")
print(command)

# Запускаем обучение
import subprocess

try:
    print("\n⏳ Обучение началось...")
    print("   Это займёт 20-40 минут на CPU")
    print("   Можно свернуть окно, обучение продолжится")
    print("   Прогресс будет сохраняться в runs/train/battery_detector/")
    
    # Меняем рабочую директорию на yolov5
    original_dir = os.getcwd()
    os.chdir(yolo_path)
    
    # Запускаем обучение
    result = subprocess.run([
        "python", "train.py",
        "--img", "640",
        "--batch", "4",
        "--epochs", "30",
        "--data", os.path.join(original_dir, "dataset.yaml"),
        "--weights", "yolov5s.pt",
        "--name", "battery_detector",
        "--device", "cpu",
        "--patience", "10",
        "--exist-ok",
        "--workers", "0"
    ], check=True)
    
    os.chdir(original_dir)
    
    print("\n" + "="*60)
    print("✅ ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print("="*60)
    
    # Показываем результаты
    results_dir = "runs/train/battery_detector"
    if os.path.exists(results_dir):
        print(f"\n📁 РЕЗУЛЬТАТЫ:")
        print(f"   • Модель: {results_dir}/weights/best.pt")
        print(f"   • Последняя модель: {results_dir}/weights/last.pt")
        print(f"   • Графики: {results_dir}/*.png")
        
        # Показываем лучшую модель
        best_model = f"{results_dir}/weights/best.pt"
        if os.path.exists(best_model):
            print(f"\n🎯 Лучшая модель сохранена: {best_model}")
            
            # Тестируем модель
            print("\n🧪 Хотите протестировать модель? (y/n)")
            choice = input().strip().lower()
            
            if choice == 'y':
                test_model(best_model)
    
except subprocess.CalledProcessError as e:
    print(f"\n❌ Ошибка при обучении: {e}")
except KeyboardInterrupt:
    print("\n⏹️ Обучение прервано пользователем")
except Exception as e:
    print(f"\n❌ Неизвестная ошибка: {e}")
finally:
    # Возвращаемся в исходную директорию
    if 'original_dir' in locals():
        os.chdir(original_dir)

def test_model(model_path):
    """Тестирует модель на нескольких фото"""
    print("\n🧪 Тестирую модель...")
    
    try:
        from yolov5 import YOLOv5
        
        # Загружаем модель
        model = YOLOv5(model_path, device='cpu')
        
        # Тестируем на первых 3 фото
        test_images = list(Path("images").glob("*.jpg"))[:3]
        
        for img_path in test_images:
            print(f"\n📸 {img_path.name}:")
            results = model.predict(str(img_path))
            
            # Сохраняем результат
            output_path = f"results/test_{img_path.name}"
            results.save(output_path)
            
            # Показываем найденные объекты
            detections = results.pandas().xyxy[0]
            if len(detections) > 0:
                for _, row in detections.iterrows():
                    class_name = "AA" if row['class'] == 0 else "CR"
                    confidence = row['confidence']
                    print(f"   • {class_name}: уверенность {confidence:.1%}")
            else:
                print("   • Объекты не найдены")
            
            print(f"   💾 Результат сохранён: {output_path}")
            
    except Exception as e:
        print(f"⚠️ Не удалось протестировать: {e}")
        print("📌 Но модель всё равно обучена и сохранена")

print("\n" + "="*60)
print("📌 ИНСТРУКЦИЯ ПОСЛЕ ОБУЧЕНИЯ:")
print("="*60)
print("1. Модель будет в runs/train/battery_detector/weights/")
print("2. Для использования модели:")
print("   from yolov5 import YOLOv5")
print("   model = YOLOv5('runs/train/battery_detector/weights/best.pt')")
print("   results = model.predict('ваше_фото.jpg')")
