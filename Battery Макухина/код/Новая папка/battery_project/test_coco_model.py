# test_coco_model.py
import torch
import torchvision
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.transforms import functional as F
import cv2
import matplotlib.pyplot as plt
import numpy as np

def test_model():
    print("🧪 ТЕСТИРОВАНИЕ МОДЕЛИ")
    
    # 1. Загружаем модель
    model = fasterrcnn_resnet50_fpn(pretrained=False)
    num_classes = 4  # как при обучении
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    
    model.load_state_dict(torch.load("models/battery_detector_coco.pth", map_location=torch.device('cpu')))
    model.eval()
    
    print("✅ Модель загружена")
    
    # 2. Классы
    classes = ['background', 'AA_battery', 'CR_battery', 'plastic_cap']
    
    # 3. Тестируем на новом изображении
    test_image_path = "raw_images/AA/WIN_20260209_18_59_58_Pro.jpg"  # ваше фото
    
    if not os.path.exists(test_image_path):
        print("❌ Тестовое изображение не найдено")
        return
    
    # 4. Загружаем и преобразуем изображение
    image = cv2.imread(test_image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Преобразуем для модели
    image_tensor = F.to_tensor(image_rgb)
    
    # 5. Предсказание
    with torch.no_grad():
        prediction = model([image_tensor])
    
    # 6. Визуализируем результаты
    boxes = prediction[0]['boxes'].cpu().numpy()
    scores = prediction[0]['scores'].cpu().numpy()
    labels = prediction[0]['labels'].cpu().numpy()
    
    # Фильтруем по confidence
    confidence_threshold = 0.5
    indices = scores > confidence_threshold
    
    filtered_boxes = boxes[indices]
    filtered_scores = scores[indices]
    filtered_labels = labels[indices]
    
    print(f"\n🔍 Результаты (порог уверенности: {confidence_threshold}):")
    print(f"   Найдено объектов: {len(filtered_boxes)}")
    
    # Рисуем bounding boxes
    fig, ax = plt.subplots(1, 2, figsize=(15, 7))
    
    # Оригинальное изображение
    ax[0].imshow(image_rgb)
    ax[0].set_title("Оригинальное изображение")
    ax[0].axis('off')
    
    # С детекциями
    ax[1].imshow(image_rgb)
    
    colors = ['red', 'green', 'blue']  # для каждого класса
    
    for i, (box, score, label) in enumerate(zip(filtered_boxes, filtered_scores, filtered_labels)):
        if label > 0:  # пропускаем background
            x1, y1, x2, y2 = box
            color = colors[label-1] if label-1 < len(colors) else 'yellow'
            
            # Рисуем прямоугольник
            rect = plt.Rectangle((x1, y1), x2-x1, y2-y1, 
                               fill=False, color=color, linewidth=2)
            ax[1].add_patch(rect)
            
            # Подпись
            class_name = classes[label] if label < len(classes) else f"class_{label}"
            ax[1].text(x1, y1-10, f"{class_name}: {score:.2f}", 
                      color='white', fontsize=10,
                      bbox=dict(facecolor=color, alpha=0.7))
            
            print(f"   {i+1}. {class_name}: уверенность {score:.2%}")
    
    ax[1].set_title("Результаты детекции")
    ax[1].axis('off')
    
    plt.tight_layout()
    plt.savefig("results/test_detection.jpg", dpi=150, bbox_inches='tight')
    plt.show()
    
    print(f"\n💾 Результат сохранён: results/test_detection.jpg")

if __name__ == "__main__":
    test_model()
