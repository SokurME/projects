# prepare_for_makesense.py
import os
import shutil
from pathlib import Path

print("🎯 ПОДГОТОВКА ФОТО ДЛЯ MAKESENSE.AI")

# Создаём папку для загрузки
upload_folder = "for_makesense"
os.makedirs(upload_folder, exist_ok=True)

# Копируем по 5-10 фото каждого класса
print("\n📁 Копирую фото...")

# AA батарейки
aa_files = list(Path("raw_images/AA").glob("*.jpg"))[:8]
for i, file in enumerate(aa_files):
    shutil.copy(file, f"{upload_folder}/aa_{i:03d}.jpg")
    print(f"  ✅ AA: aa_{i:03d}.jpg")

# CR батарейки  
cr_files = list(Path("raw_images/CR").glob("*.jpg"))[:8]
for i, file in enumerate(cr_files):
    shutil.copy(file, f"{upload_folder}/cr_{i:03d}.jpg")
    print(f"  ✅ CR: cr_{i:03d}.jpg")

print(f"\n📊 Всего подготовлено: {len(aa_files) + len(cr_files)} фото")
print(f"📁 Фото лежат в папке: {upload_folder}/")
print("\n" + "="*50)
print("🎮 ТЕПЕРЬ ПЕРЕЙДИТЕ НА https://www.makesense.ai/")
print("="*50)
