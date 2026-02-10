# setup_project.py
import os
import shutil
from sklearn.model_selection import train_test_split

def prepare_yolo_dataset():
    """Подготовка датасета для YOLO"""
    
    # Создаём структуру папок
    folders = [
        'dataset/images/train',
        'dataset/images/val',
        'dataset/labels/train', 
        'dataset/labels/val',
        'dataset/backup'  # для весов модели
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    
    # Собираем все фото
    all_images = []
    all_labels = []
    
    # Классы: 0=AA, 1=CR, 2=cap (пока нет)
    for class_id, category in enumerate(['AA', 'CR']):
        category_path = f'raw_images/{category}'
        if os.path.exists(category_path):
            for img_file in os.listdir(category_path):
                if img_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    all_images.append(f'{category_path}/{img_file}')
                    all_labels.append(class_id)
    
    print(f"Всего фото: {len(all_images)}")
    print(f"AA батарейки: {all_labels.count(0)}")
    print(f"CR батарейки: {all_labels.count(1)}")
    
    # Разделяем на train/val (80/20)
    train_imgs, val_imgs, train_labels, val_labels = train_test_split(
        all_images, all_labels, test_size=0.2, random_state=42
    )
    
    # Копируем фото
    print("\nКопируем изображения...")
    for i, img_path in enumerate(train_imgs):
        shutil.copy(img_path, f'dataset/images/train/img_{i:04d}.jpg')
    
    for i, img_path in enumerate(val_imgs):
        shutil.copy(img_path, f'dataset/images/val/img_{i+len(train_imgs):04d}.jpg')
    
    print("✅ Датасет подготовлен!")
    print(f"   Train: {len(train_imgs)} фото")
    print(f"   Val: {len(val_imgs)} фото")
    
    # Создаём файл classes.names
    with open('dataset/classes.names', 'w') as f:
        f.write('AA_battery\n')
        f.write('CR_battery\n')
        f.write('plastic_cap\n')
    
    return len(train_imgs), len(val_imgs)

if __name__ == "__main__":
    train_count, val_count = prepare_yolo_dataset()
    print(f"\n🎯 Готово к разметке!")
    print(f"📊 Train: {train_count} фото | Val: {val_count} фото")
    print("\n📌 Теперь запустите разметку:")
    print("   labelImg dataset/images/train/ dataset/classes.names")
