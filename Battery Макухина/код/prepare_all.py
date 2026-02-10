# prepare_all.py
import os
import shutil
from pathlib import Path

print("="*60)
print("🎯 ПОДГОТОВКА ВСЕХ ВАШИХ ФОТО")
print("="*60)

# 1. Проверяем, есть ли ваши фото
print("\n🔍 Ищу ваши фото...")

# Папка где лежат ваши фото (как в прошлом выводе)
source_folder = "raw_images"

if not os.path.exists(source_folder):
    print(f"❌ Папка '{source_folder}' не найдена!")
    print("📌 Создайте папку 'raw_images' и положите в неё:")
    print("   raw_images/AA/ - фото AA батареек")
    print("   raw_images/CR/ - фото CR батареек")
    exit()

# 2. Собираем все фото
print("\n📸 Собираю все фото...")

# AA батарейки
aa_folder = os.path.join(source_folder, "AA")
cr_folder = os.path.join(source_folder, "CR")

aa_files = []
cr_files = []

if os.path.exists(aa_folder):
    aa_files = list(Path(aa_folder).glob("*.jpg"))
    print(f"✅ Нашёл AA батареек: {len(aa_files)}")
else:
    print(f"⚠️ Папка AA не найдена: {aa_folder}")

if os.path.exists(cr_folder):
    cr_files = list(Path(cr_folder).glob("*.jpg"))
    print(f"✅ Нашёл CR батареек: {len(cr_files)}")
else:
    print(f"⚠️ Папка CR не найдена: {cr_folder}")

# 3. Создаём папки для датасета
print("\n📁 Создаю папки датасета...")

# Создаём папки прямо здесь
os.makedirs("images", exist_ok=True)
os.makedirs("labels", exist_ok=True)

print("✅ Папка: images/")
print("✅ Папка: labels/")

# 4. КОПИРУЕМ ВСЕ ФОТО
print("\n📁 Копирую фото...")

# AA батарейки
for i, file in enumerate(aa_files):
    new_name = f"battery_aa_{i:03d}.jpg"
    shutil.copy(file, f"images/{new_name}")
    print(f"   ✅ AA: {file.name} → {new_name}")

# CR батарейки
for i, file in enumerate(cr_files):
    new_name = f"battery_cr_{i:03d}.jpg"
    shutil.copy(file, f"images/{new_name}")
    print(f"   ✅ CR: {file.name} → {new_name}")

# 5. СОЗДАЁМ МЕТКИ (простые, примерные)
print("\n📝 Создаю метки...")

total_photos = len(aa_files) + len(cr_files)
print(f"📊 Всего фото: {total_photos}")

for i in range(total_photos):
    if i < len(aa_files):
        filename = f"battery_aa_{i:03d}.jpg"
        label = "0 0.5 0.5 0.2 0.1\n"  # класс 0 = AA
    else:
        j = i - len(aa_files)
        filename = f"battery_cr_{j:03d}.jpg"
        label = "1 0.5 0.5 0.15 0.15\n"  # класс 1 = CR
    
    # Создаём файл метки
    label_filename = filename.replace(".jpg", ".txt")
    with open(f"labels/{label_filename}", "w") as f:
        f.write(label)
    
    print(f"   ✅ {label_filename}")

# 6. СОЗДАЁМ КОНФИГУРАЦИОННЫЕ ФАЙЛЫ
print("\n⚙️ Создаю конфигурацию...")

# Файл классов
with open("classes.txt", "w") as f:
    f.write("AA_battery\n")
    f.write("CR_battery\n")

# YAML для YOLO
yaml_content = """# Battery Detection Dataset
path: .
train: images
val: images

# Number of classes
nc: 2

# Class names
names: ['AA_battery', 'CR_battery']
"""

with open("dataset.yaml", "w") as f:
    f.write(yaml_content)

print("✅ classes.txt")
print("✅ dataset.yaml")

# 7. ПРОВЕРКА
print("\n" + "="*60)
print("📊 ИТОГОВАЯ СТАТИСТИКА")
print("="*60)

images_count = len(list(Path("images").glob("*.*")))
labels_count = len(list(Path("labels").glob("*.txt")))

print(f"📸 Изображений: {images_count}")
print(f"📝 Меток: {labels_count}")
print(f"🎯 AA батареек: {len(aa_files)}")
print(f"🎯 CR батареек: {len(cr_files)}")

if images_count == labels_count:
    print("✅ Всё отлично! Можно обучать модель.")
else:
    print("⚠️  Что-то пошло не так")

print("\n📁 Созданы папки в текущей директории:")
print("   images/       - все ваши фото")
print("   labels/       - метки к фото")
print("   classes.txt   - названия классов")
print("   dataset.yaml  - конфиг для обучения")
