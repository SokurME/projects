import os
from PIL import Image
import matplotlib.pyplot as plt

# Укажите путь к вашей папке с изображениями
IMAGES_PATH = "raw_images"

def quick_check():
    print("🔍 Проверяем изображения...")
    
    for category in ['AA', 'CR', 'caps']:
        category_path = os.path.join(IMAGES_PATH, category)
        
        if not os.path.exists(category_path):
            print(f"❌ Папка {category} не найдена!")
            continue
            
        images = [f for f in os.listdir(category_path) 
                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        print(f"\n📁 {category}: {len(images)} фото")
        
        # Покажем первое изображение из каждой категории
        if images:
            img_path = os.path.join(category_path, images[0])
            try:
                img = Image.open(img_path)
                print(f"   Первое фото: {images[0]} ({img.size[0]}x{img.size[1]})")
            except:
                print(f"   Ошибка открытия {images[0]}")

if __name__ == "__main__":
    quick_check()
    print("\n✅ Готово! Если видите количество фото - всё ок.")