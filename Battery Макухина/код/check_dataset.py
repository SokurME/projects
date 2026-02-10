# check_dataset.py
import cv2
import matplotlib.pyplot as plt
from pathlib import Path

print("🔍 ПРОВЕРКА ДАТАСЕТА")

# Берём первое изображение
img_files = list(Path("dataset/images").glob("*.jpg"))
label_files = list(Path("dataset/labels").glob("*.txt"))

if img_files and label_files:
    img_path = img_files[0]
    label_path = label_files[0]
    
    print(f"📸 Изображение: {img_path.name}")
    print(f"📝 Метка: {label_path.name}")
    
    # Загружаем изображение
    img = cv2.imread(str(img_path))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    
    # Загружаем метку
    with open(label_path, 'r') as f:
        labels = f.readlines()
    
    print(f"🎯 Объектов на фото: {len(labels)}")
    
    # Рисуем
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    ax.imshow(img)
    
    for label in labels:
        class_id, x_center, y_center, box_w, box_h = map(float, label.split())
        
        # Конвертируем в пиксели
        x1 = int((x_center - box_w/2) * w)
        y1 = int((y_center - box_h/2) * h)
        x2 = int((x_center + box_w/2) * w)
        y2 = int((y_center + box_h/2) * h)
        
        # Рисуем прямоугольник
        color = 'green' if class_id == 0 else 'red'
        rect = plt.Rectangle((x1, y1), x2-x1, y2-y1,
                           fill=False, edgecolor=color, linewidth=3)
        ax.add_patch(rect)
        
        # Подпись
        class_name = "AA" if class_id == 0 else "CR"
        ax.text(x1, y1-10, class_name,
               color='white', fontsize=12,
               bbox=dict(facecolor=color, alpha=0.8))
    
    ax.axis('off')
    ax.set_title("Пример разметки датасета")
    plt.savefig("dataset_check.jpg", dpi=120, bbox_inches='tight')
    plt.show()
    
    print("💾 Пример сохранён: dataset_check.jpg")
else:
    print("❌ Файлы не найдены!")
