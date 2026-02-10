# prepare_simple.py - ЕДИНСТВЕННЫЙ СКРИПТ КОТОРЫЙ НУЖЕН
import os
import shutil
from pathlib import Path

print("="*60)
print("🎯 ПОДГОТОВКА ДАТАСЕТА ЗА 2 МИНУТЫ")
print("="*60)

# 1. СОЗДАЁМ ПРОСТУЮ СТРУКТУРУ
print("\n📁 Создаю структуру...")

folders = [
    "dataset/images",
    "dataset/labels", 
    "models",
    "results"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"✅ {folder}")

# 2. БЕРЁМ ВАШИ ФОТО (первые 20 для теста)
print("\n📸 Беру ваши фото...")

# AA батарейки
aa_files = list(Path("raw_images/AA").glob("*.jpg"))[:10]
# CR батарейки  
cr_files = list(Path("raw_images/CR").glob("*.jpg"))[:10]

print(f"📊 Нашёл:")
print(f"   AA батареек: {len(aa_files)}")
print(f"   CR батареек: {len(cr_files)}")

# 3. КОПИРУЕМ ФОТО В ДАТАСЕТ
print("\n📁 Копирую фото...")

for i, file in enumerate(aa_files):
    new_name = f"battery_aa_{i:03d}.jpg"
    shutil.copy(file, f"dataset/images/{new_name}")
    print(f"   ✅ {file.name} -> {new_name}")

for i, file in enumerate(cr_files):
    new_name = f"battery_cr_{i+10:03d}.jpg"
    shutil.copy(file, f"dataset/images/{new_name}")
    print(f"   ✅ {file.name} -> {new_name}")

# 4. СОЗДАЁМ ПРОСТЫЕ МЕТКИ (примерные координаты)
print("\n📝 Создаю метки...")

# Примерные размеры батареек на фото 2560x1440
for i in range(len(aa_files) + len(cr_files)):
    filename = f"battery_{'aa' if i < 10 else 'cr'}_{i:03d}.jpg"
    label_file = f"dataset/labels/{filename.replace('.jpg', '.txt')}"
    
    with open(label_file, 'w') as f:
        if i < 10:  # AA батарейки (вытянутые)
            # Примерные координаты: x_center, y_center, width, height (нормализованные)
            f.write("0 0.5 0.5 0.2 0.1\n")  # класс 0 = AA
        else:  # CR батарейки (круглые)
            f.write("1 0.5 0.5 0.15 0.15\n")  # класс 1 = CR
    
    print(f"   ✅ {label_file}")

# 5. СОЗДАЁМ КОНФИГУРАЦИОННЫЕ ФАЙЛЫ
print("\n⚙️ Создаю конфигурацию...")

# Файл классов
with open("dataset/classes.txt", "w") as f:
    f.write("AA_battery\n")
    f.write("CR_battery\n")
    # f.write("plastic_cap\n")  # раскомментируйте когда будут фото крышек

# YAML для YOLO
yaml_content = """# Battery Detection Dataset
path: ./dataset
train: images
val: images  # для теста используем те же данные

# Number of classes
nc: 2

# Class names
names: ['AA_battery', 'CR_battery']
"""

with open("dataset/dataset.yaml", "w") as f:
    f.write(yaml_content)

print("✅ dataset/classes.txt")
print("✅ dataset/dataset.yaml")

# 6. ПРОВЕРКА
print("\n🔍 ПРОВЕРКА ДАТАСЕТА:")
total_images = len(list(Path("dataset/images").glob("*.*")))
total_labels = len(list(Path("dataset/labels").glob("*.txt")))

print(f"📸 Изображений: {total_images}")
print(f"📝 Меток: {total_labels}")

if total_images == total_labels:
    print("✅ Всё отлично! Датасет сбалансирован.")
else:
    print("⚠️  Количество изображений и меток не совпадает")

print("\n" + "="*60)
print("🎉 ДАТАСЕТ ГОТОВ!")
print("="*60)
print("\n📁 Что создано:")
print("   dataset/images/     - 20 фото")
print("   dataset/labels/     - 20 меток")
print("   dataset/classes.txt - названия классов")
print("   dataset/dataset.yaml - конфиг для YOLO")
