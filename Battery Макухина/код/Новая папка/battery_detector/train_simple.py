"""
🎯 ПРОСТОЙ СКРИПТ ОБУЧЕНИЯ - РАБОЧАЯ ВЕРСИЯ
"""

import torch
import torchvision
import os
import json
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

print("="*60)
print("🔋 ОБУЧЕНИЕ МОДЕЛИ ДЛЯ БАТАРЕЕК")
print("="*60)

# 1. ПРОВЕРКА ДАННЫХ
print("\n🔍 Проверяю данные...")

# Путь к вашим данным
COCO_JSON = "data/annotations.json"  # от MakeSense.ai
IMAGES_DIR = "data/raw_images"       # ваши фото

if not os.path.exists(COCO_JSON):
    print(f"❌ Не найден файл аннотаций: {COCO_JSON}")
    print("📌 Скачайте COCO JSON с MakeSense.ai")
    exit()

if not os.path.exists(IMAGES_DIR):
    print(f"❌ Не найдена папка с изображениями: {IMAGES_DIR}")
    exit()

# 2. ЗАГРУЗКА COCO АННОТАЦИЙ
print(f"\n📂 Загружаю аннотации из {COCO_JSON}...")
with open(COCO_JSON, 'r') as f:
    coco_data = json.load(f)

print(f"✅ Загружено:")
print(f"   • Изображений: {len(coco_data['images'])}")
print(f"   • Аннотаций: {len(coco_data['annotations'])}")
print(f"   • Категорий: {len(coco_data['categories'])}")

# 3. ПОКАЗЫВАЕМ КАТЕГОРИИ
print("\n📋 Категории:")
for cat in coco_data['categories']:
    print(f"   • {cat['name']} (id: {cat['id']})")

# 4. СОЗДАЁМ ПРОСТОЙ ДАТАСЕТ
print("\n📁 Создаю датасет...")

# Создаём маппинги
image_info = {img['id']: img for img in coco_data['images']}
img_to_anns = {}

for ann in coco_data['annotations']:
    img_id = ann['image_id']
    if img_id not in img_to_anns:
        img_to_anns[img_id] = []
    img_to_anns[img_id].append(ann)

# 5. ПРОВЕРЯЕМ ПЕРВОЕ ИЗОБРАЖЕНИЕ
print("\n🔍 Проверяю первое изображение...")

if coco_data['images']:
    first_img = coco_data['images'][0]
    img_path = os.path.join(IMAGES_DIR, first_img['file_name'])
    
    if os.path.exists(img_path):
        print(f"✅ Найдено изображение: {first_img['file_name']}")
        print(f"   Размер: {first_img['width']}x{first_img['height']}")
        
        # Показываем аннотации
        anns = img_to_anns.get(first_img['id'], [])
        print(f"   Аннотаций: {len(anns)}")
        
        for ann in anns:
            cat_id = ann['category_id']
            cat_name = next((c['name'] for c in coco_data['categories'] 
                           if c['id'] == cat_id), f"class_{cat_id}")
            print(f"   • {cat_name}: {ann['bbox']}")
    else:
        print(f"❌ Изображение не найдено: {img_path}")

# 6. ЗАГРУЗКА ПРЕДОБУЧЕННОЙ МОДЕЛИ
print("\n🤖 Загружаю предобученную модель COCO...")

try:
    from torchvision.models.detection import fasterrcnn_resnet50_fpn
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
    
    # Количество классов
    num_classes = len(coco_data['categories']) + 1  # + background
    
    # Загружаем модель
    model = fasterrcnn_resnet50_fpn(pretrained=True)
    
    # Заменяем классификатор
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    
    print(f"✅ Модель загружена!")
    print(f"   • Классов: {num_classes}")
    print(f"   • Архитектура: Faster R-CNN")
    
    # 7. СОХРАНЯЕМ МОДЕЛЬ ДЛЯ ТЕСТА
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), "models/test_model.pth")
    print("💾 Тестовая модель сохранена: models/test_model.pth")
    
except Exception as e:
    print(f"❌ Ошибка при загрузке модели: {e}")
    print("\n🔧 Решение:")
    print("1. Проверьте установку torchvision: pip install torchvision")
    print("2. Обновите PyTorch: pip install --upgrade torch torchvision")

# 8. ПРОСТОЙ ТЕСТ НА ОДНОМ ИЗОБРАЖЕНИИ
print("\n🧪 Тестирую на одном изображении...")

if coco_data['images']:
    # Берём первое изображение
    test_img = coco_data['images'][0]
    img_path = os.path.join(IMAGES_DIR, test_img['file_name'])
    
    if os.path.exists(img_path):
        # Показываем изображение
        img = Image.open(img_path)
        
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))
        
        # Оригинал
        axes[0].imshow(img)
        axes[0].set_title("Оригинал")
        axes[0].axis('off')
        
        # С аннотациями
        axes[1].imshow(img)
        
        # Рисуем bounding boxes
        anns = img_to_anns.get(test_img['id'], [])
        colors = ['red', 'green', 'blue', 'yellow', 'purple']
        
        for i, ann in enumerate(anns):
            x, y, w, h = ann['bbox']
            
            # Получаем имя класса
            cat_id = ann['category_id']
            cat_name = next((c['name'] for c in coco_data['categories'] 
                           if c['id'] == cat_id), f"class_{cat_id}")
            
            color = colors[i % len(colors)]
            
            # Рисуем прямоугольник
            rect = plt.Rectangle((x, y), w, h, 
                               fill=False, color=color, linewidth=2)
            axes[1].add_patch(rect)
            
            # Подпись
            axes[1].text(x, y-10, cat_name,
                        color='white', fontsize=10,
                        bbox=dict(facecolor=color, alpha=0.7))
        
        axes[1].set_title(f"Разметка ({len(anns)} объектов)")
        axes[1].axis('off')
        
        plt.tight_layout()
        plt.savefig("test_annotation.jpg", dpi=150)
        plt.show()
        
        print("✅ Тестовая визуализация сохранена: test_annotation.jpg")
    else:
        print(f"❌ Изображение не найдено: {img_path}")

print("\n" + "="*60)
print("🎯 ЧТО ДЕЛАТЬ ДАЛЬШЕ:")
print("="*60)
print("1. ✅ Проверьте, что видите изображение с разметкой")
print("2. 📁 Убедитесь, что модель сохранена в models/test_model.pth")
print("3. 🚀 Запустите полное обучение командой:")
print("   python train_final.py")
