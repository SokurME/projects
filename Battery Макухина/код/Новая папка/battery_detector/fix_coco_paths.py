import json
import os
from pathlib import Path

print("🔧 ИСПРАВЛЕНИЕ ПУТЕЙ В COCO JSON")

# 1. Загружаем ваш COCO JSON
coco_file = "data/annotations.json"
with open(coco_file, 'r') as f:
    data = json.load(f)

print(f"📊 Исходные данные:")
print(f"   Изображений: {len(data['images'])}")

# 2. Получаем список реальных файлов
raw_images_dir = "data/raw_images"
real_files = []

# Рекурсивно ищем все изображения
for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG']:
    real_files.extend(Path(raw_images_dir).rglob(ext))

print(f"📁 Найдено реальных файлов: {len(real_files)}")

# 3. Создаем mapping: имя файла -> полный путь
file_mapping = {}
for file_path in real_files:
    # Используем только имя файла
    file_name = file_path.name
    file_mapping[file_name] = str(file_path.relative_to(raw_images_dir))
    
    # Также добавляем варианты без расширения (на всякий случай)
    file_name_no_ext = file_path.stem
    file_mapping[file_name_no_ext] = str(file_path.relative_to(raw_images_dir))

print(f"\n📋 Примеры найденных файлов:")
for i, file_path in enumerate(list(real_files)[:5]):
    print(f"   {i+1}. {file_path.name}")

# 4. Исправляем пути в COCO данных
print("\n🔧 Исправляю пути в COCO JSON...")

fixed_count = 0
for img_info in data['images']:
    original_filename = img_info['file_name']
    
    # Пробуем найти реальный файл
    if original_filename in file_mapping:
        new_filename = file_mapping[original_filename]
        if new_filename != original_filename:
            print(f"   Исправлено: {original_filename} -> {new_filename}")
            img_info['file_name'] = new_filename
            fixed_count += 1
    else:
        # Пробуем найти по имени без расширения
        original_no_ext = Path(original_filename).stem
        if original_no_ext in file_mapping:
            new_filename = file_mapping[original_no_ext]
            print(f"   Исправлено: {original_filename} -> {new_filename}")
            img_info['file_name'] = new_filename
            fixed_count += 1
        else:
            print(f"   ⚠️ Не найден: {original_filename}")

# 5. Сохраняем исправленный файл
fixed_file = "data/annotations_fixed.json"
with open(fixed_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"\n✅ Исправлено {fixed_count} путей")
print(f"💾 Исправленный файл сохранен: {fixed_file}")

# 6. Создаем простой файл для проверки
print("\n🔍 Проверка первого изображения:")
if data['images']:
    first_img = data['images'][0]
    expected_path = os.path.join(raw_images_dir, first_img['file_name'])
    
    print(f"   Имя файла: {first_img['file_name']}")
    print(f"   Ожидаемый путь: {expected_path}")
    print(f"   Файл существует: {os.path.exists(expected_path)}")
