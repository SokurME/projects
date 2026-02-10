import os
import json
import shutil
from pathlib import Path

print("🎯 ПОДГОТОВКА COCO ДАТАСЕТА")

# 1. Путь к вашему JSON файлу от MakeSense
coco_json = "annotations.json"  # измените если файл называется иначе

if not os.path.exists(coco_json):
    print(f"❌ Файл {coco_json} не найден!")
    print("📌 Убедитесь, что вы скачали COCO JSON с MakeSense.ai")
    exit()

# 2. Загружаем COCO аннотации
with open(coco_json, 'r') as f:
    data = json.load(f)

print(f"✅ Загружен COCO файл:")
print(f"   📸 Изображений: {len(data['images'])}")
print(f"   🎯 Аннотаций: {len(data['annotations'])}")
print(f"   📋 Категорий: {len(data['categories'])}")

# 3. Показываем категории
print("\n📋 КАТЕГОРИИ:")
for cat in data['categories']:
    print(f"   • {cat['name']} (id: {cat['id']})")

# 4. Создаём папки для Detectron2/Faster R-CNN
folders = [
    'coco_dataset/train',
    'coco_dataset/val',
    'models',
    'results'
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"✅ Создана папка: {folder}")

# 5. Копируем изображения (если они отдельно)
# MakeSense обычно не включает изображения в JSON, только ссылки
print("\n🔍 Ищу изображения...")

# Ищем изображения в разных местах
possible_locations = [
    '.',  # текущая папка
    'raw_images',
    'dataset',
    'train',
    'images'
]

image_files = []
for location in possible_locations:
    if os.path.exists(location):
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            images = list(Path(location).rglob(ext))
            image_files.extend(images)
            if images:
                print(f"   📁 {location}: {len(images)} фото")

if not image_files:
    print("❌ Изображения не найдены!")
    print("📌 Поместите ваши фото в папку 'raw_images/' и запустите скрипт снова")
else:
    print(f"✅ Найдено {len(image_files)} изображений")
    
    # Копируем первые 20 для теста
    print("\n📁 Копирую изображения в coco_dataset/train/...")
    for i, img_path in enumerate(image_files[:20]):
        shutil.copy(img_path, f"coco_dataset/train/{img_path.name}")
        print(f"   ✅ {img_path.name}")

# 6. Сохраняем подготовленный COCO файл
shutil.copy(coco_json, "coco_dataset/annotations.json")
print(f"\n💾 COCO аннотации сохранены: coco_dataset/annotations.json")

print("\n" + "="*50)
print("✅ COCO ДАТАСЕТ ГОТОВ!")
print("="*50)
