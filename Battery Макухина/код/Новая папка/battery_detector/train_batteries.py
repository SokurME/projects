"""
🎯 ПОЛНЫЙ СКРИПТ ОБУЧЕНИЯ МОДЕЛИ ДЛЯ РАСПОЗНАВАНИЯ БАТАРЕЕК
Использует предобученную COCO модель из torchvision
"""

import torch
import torchvision
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torch.utils.data import Dataset, DataLoader
import torch.optim as optim
from torchvision.transforms import functional as F
import json
import os
import cv2
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import shutil

print("="*70)
print("🔋 ДЕТЕКЦИЯ БАТАРЕЕК С ПОМОЩЬЮ TRANSFER LEARNING")
print("="*70)

# ============================================================================
# 1. НАСТРОЙКИ
# ============================================================================
class Config:
    # Пути
    RAW_IMAGES_DIR = "data/raw_images"
    COCO_ANNOTATIONS = "data/annotations.json"
    OUTPUT_DIR = "output"
    
    # Классы (ваши с MakeSense.ai)
    CLASSES = ['AA_battery', 'CR_battery', 'plastic_cap']
    
    # Параметры обучения
    BATCH_SIZE = 4
    NUM_EPOCHS = 20
    LEARNING_RATE = 0.005
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Порог уверенности при детекции
    CONFIDENCE_THRESHOLD = 0.5

config = Config()

# ============================================================================
# 2. КЛАСС ДАТАСЕТА ДЛЯ COCO ФОРМАТА
# ============================================================================
class CocoBatteryDataset(Dataset):
    """Датасет для COCO формата из MakeSense.ai"""
    
    def __init__(self, root_dir, annotation_file, transforms=None):
        """
        Args:
            root_dir: Папка с изображениями
            annotation_file: JSON файл с COCO аннотациями
            transforms: трансформации для изображений
        """
        self.root_dir = root_dir
        self.transforms = transforms
        
        # Загружаем COCO аннотации
        print(f"📂 Загружаю COCO аннотации из {annotation_file}...")
        with open(annotation_file, 'r') as f:
            self.coco_data = json.load(f)
        
        # Создаём mapping для быстрого доступа
        self._create_mappings()
        
        print(f"✅ Загружено: {len(self.images)} изображений, "
              f"{len(self.annotations)} аннотаций, "
              f"{len(self.categories)} категорий")
    
    def _create_mappings(self):
        """Создаёт маппинги для быстрого доступа к данным"""
        # Маппинг image_id -> информация об изображении
        self.image_info = {img['id']: img for img in self.coco_data['images']}
        
        # Маппинг image_id -> список аннотаций
        self.img_to_anns = {}
        for ann in self.coco_data['annotations']:
            img_id = ann['image_id']
            if img_id not in self.img_to_anns:
                self.img_to_anns[img_id] = []
            self.img_to_anns[img_id].append(ann)
        
        # Маппинг category_id -> имя класса
        self.cat_id_to_name = {cat['id']: cat['name'] for cat in self.coco_data['categories']}
        
        # Списки
        self.images = self.coco_data['images']
        self.annotations = self.coco_data['annotations']
        self.categories = self.coco_data['categories']
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        # Получаем информацию об изображении
        img_info = self.images[idx]
        img_id = img_info['id']
        
        # Загружаем изображение
        img_path = os.path.join(self.root_dir, img_info['file_name'])
        try:
            image = Image.open(img_path).convert("RGB")
        except:
            print(f"❌ Ошибка загрузки: {img_path}")
            # Возвращаем пустые данные
            image = Image.new('RGB', (100, 100), color='white')
        
        # Получаем аннотации для этого изображения
        anns = self.img_to_anns.get(img_id, [])
        
        boxes = []
        labels = []
        
        for ann in anns:
            # COCO bbox: [x, y, width, height]
            x, y, w, h = ann['bbox']
            
            # Преобразуем в формат [x1, y1, x2, y2]
            x1, y1, x2, y2 = x, y, x + w, y + h
            
            # Проверяем валидность координат
            if x2 > x1 and y2 > y1:
                boxes.append([x1, y1, x2, y2])
                labels.append(ann['category_id'])
        
        # Конвертируем в тензоры
        boxes = torch.as_tensor(boxes, dtype=torch.float32)
        labels = torch.as_tensor(labels, dtype=torch.int64)
        
        target = {
            "boxes": boxes,
            "labels": labels,
            "image_id": torch.tensor([img_id])
        }
        
        # Применяем трансформации
        if self.transforms:
            image = self.transforms(image)
        else:
            image = F.to_tensor(image)
        
        return image, target

# ============================================================================
# 3. ПОДГОТОВКА ДАННЫХ
# ============================================================================
def prepare_data():
    """Подготавливает данные для обучения"""
    print("\n📁 ПОДГОТОВКА ДАННЫХ")
    print("-" * 40)
    
    # Проверяем наличие аннотаций
    if not os.path.exists(config.COCO_ANNOTATIONS):
        print(f"❌ Файл аннотаций не найден: {config.COCO_ANNOTATIONS}")
        print("📌 Скачайте COCO JSON с MakeSense.ai и поместите в data/")
        return None
    
    # Проверяем наличие изображений
    if not os.path.exists(config.RAW_IMAGES_DIR):
        print(f"❌ Папка с изображениями не найдена: {config.RAW_IMAGES_DIR}")
        return None
    
    # Создаём датасет
    dataset = CocoBatteryDataset(
        root_dir=config.RAW_IMAGES_DIR,
        annotation_file=config.COCO_ANNOTATIONS
    )
    
    return dataset

# ============================================================================
# 4. СОЗДАНИЕ И НАСТРОЙКА МОДЕЛИ
# ============================================================================
def create_model(num_classes):
    """
    Создаёт модель на основе предобученной COCO модели
    
    Args:
        num_classes: количество классов (ваши классы + background)
    
    Returns:
        Настроенная модель
    """
    print(f"\n🤖 СОЗДАНИЕ МОДЕЛИ ({num_classes} классов)")
    print("-" * 40)
    
    # Загружаем предобученную модель COCO
    print("📦 Загружаю Faster R-CNN предобученную на COCO...")
    model = fasterrcnn_resnet50_fpn(pretrained=True)
    
    # Заменяем классификатор головы для нашего числа классов
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
    
    print(f"✅ Модель создана:")
    print(f"   • Архитектура: Faster R-CNN with ResNet-50-FPN")
    print(f"   • Предобучена на: COCO dataset")
    print(f"   • Адаптирована для: {num_classes} классов")
    
    return model

# ============================================================================
# 5. ОБУЧЕНИЕ МОДЕЛИ
# ============================================================================
def train_model(model, train_loader, val_loader=None):
    """
    Обучает модель
    
    Args:
        model: модель для обучения
        train_loader: DataLoader для обучающих данных
        val_loader: DataLoader для валидационных данных (опционально)
    
    Returns:
        Обученная модель
    """
    print("\n🎯 ОБУЧЕНИЕ МОДЕЛИ")
    print("=" * 70)
    
    # Переносим модель на устройство
    model.to(config.DEVICE)
    print(f"📱 Устройство для обучения: {config.DEVICE}")
    
    # Оптимизатор
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = optim.SGD(
        params, 
        lr=config.LEARNING_RATE,
        momentum=0.9,
        weight_decay=0.0005
    )
    
    # Scheduler для изменения learning rate
    lr_scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.1)
    
    # Режим обучения
    model.train()
    
    # История потерь
    train_loss_history = []
    
    print(f"\n🚀 Начинаю обучение ({config.NUM_EPOCHS} эпох)...")
    
    for epoch in range(config.NUM_EPOCHS):
        print(f"\n📊 ЭПОХА {epoch + 1}/{config.NUM_EPOCHS}")
        print("-" * 40)
        
        epoch_loss = 0
        num_batches = 0
        
        for batch_idx, (images, targets) in enumerate(train_loader):
            # Переносим данные на устройство
            images = [img.to(config.DEVICE) for img in images]
            targets = [{k: v.to(config.DEVICE) for k, v in t.items()} for t in targets]
            
            # Forward pass
            loss_dict = model(images, targets)
            losses = sum(loss for loss in loss_dict.values())
            
            # Backward pass
            optimizer.zero_grad()
            losses.backward()
            optimizer.step()
            
            epoch_loss += losses.item()
            num_batches += 1
            
            # Вывод прогресса
            if batch_idx % 10 == 0:
                current_loss = losses.item()
                print(f"   Батч {batch_idx:3d} | Loss: {current_loss:.4f}")
        
        # Средняя потеря за эпоху
        avg_loss = epoch_loss / num_batches
        train_loss_history.append(avg_loss)
        
        # Обновляем learning rate
        lr_scheduler.step()
        
        print(f"📈 Средний Loss: {avg_loss:.4f}")
        print(f"📉 Learning Rate: {lr_scheduler.get_last_lr()[0]:.6f}")
        
        # Сохраняем модель каждые 5 эпох
        if (epoch + 1) % 5 == 0:
            save_path = f"{config.OUTPUT_DIR}/model_epoch_{epoch+1}.pth"
            torch.save(model.state_dict(), save_path)
            print(f"💾 Модель сохранена: {save_path}")
    
    # Сохраняем финальную модель
    final_path = f"{config.OUTPUT_DIR}/battery_detector_final.pth"
    torch.save(model.state_dict(), final_path)
    print(f"\n✅ Финальная модель сохранена: {final_path}")
    
    # Сохраняем историю обучения
    history_path = f"{config.OUTPUT_DIR}/training_history.npy"
    np.save(history_path, np.array(train_loss_history))
    
    # График потерь
    plt.figure(figsize=(10, 6))
    plt.plot(train_loss_history, 'b-', linewidth=2)
    plt.title('История обучения (Loss)', fontsize=14)
    plt.xlabel('Эпоха', fontsize=12)
    plt.ylabel('Loss', fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{config.OUTPUT_DIR}/training_loss.png", dpi=100)
    plt.show()
    
    return model

# ============================================================================
# 6. ТЕСТИРОВАНИЕ МОДЕЛИ
# ============================================================================
def test_model(model, test_image_path):
    """
    Тестирует модель на новом изображении
    
    Args:
        model: обученная модель
        test_image_path: путь к тестовому изображению
    """
    print("\n🧪 ТЕСТИРОВАНИЕ МОДЕЛИ")
    print("=" * 70)
    
    if not os.path.exists(test_image_path):
        print(f"❌ Тестовое изображение не найдено: {test_image_path}")
        return
    
    # Загружаем изображение
    image = cv2.imread(test_image_path)
    if image is None:
        print(f"❌ Не удалось загрузить изображение: {test_image_path}")
        return
    
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    original_image = image_rgb.copy()
    
    # Преобразуем для модели
    image_tensor = F.to_tensor(image_rgb)
    
    # Режим оценки
    model.eval()
    
    # Предсказание
    with torch.no_grad():
        predictions = model([image_tensor.to(config.DEVICE)])
    
    # Извлекаем результаты
    boxes = predictions[0]['boxes'].cpu().numpy()
    scores = predictions[0]['scores'].cpu().numpy()
    labels = predictions[0]['labels'].cpu().numpy()
    
    # Фильтруем по порогу уверенности
    mask = scores > config.CONFIDENCE_THRESHOLD
    boxes = boxes[mask]
    scores = scores[mask]
    labels = labels[mask]
    
    print(f"📊 Результаты детекции:")
    print(f"   • Всего обнаружено: {len(boxes)} объектов")
    print(f"   • Порог уверенности: {config.CONFIDENCE_THRESHOLD}")
    
    # Визуализация
    fig, axes = plt.subplots(1, 2, figsize=(15, 8))
    
    # Оригинальное изображение
    axes[0].imshow(original_image)
    axes[0].set_title("Оригинальное изображение", fontsize=14)
    axes[0].axis('off')
    
    # Результаты детекции
    axes[1].imshow(original_image)
    
    # Цвета для классов
    colors = {
        'AA_battery': (0, 255, 0),    # Зеленый
        'CR_battery': (255, 0, 0),    # Красный
        'plastic_cap': (255, 255, 0)  # Желтый
    }
    
    detected_objects = []
    
    for i, (box, score, label) in enumerate(zip(boxes, scores, labels)):
        if label > 0 and label <= len(config.CLASSES):  # Пропускаем background
            x1, y1, x2, y2 = box.astype(int)
            
            # Получаем имя класса
            class_name = config.CLASSES[label-1]
            
            # Получаем цвет
            color = colors.get(class_name, (255, 255, 255))
            color_normalized = tuple(c/255 for c in color)
            
            # Рисуем bounding box
            rect = plt.Rectangle(
                (x1, y1), x2-x1, y2-y1,
                fill=False, 
                edgecolor=color_normalized, 
                linewidth=2
            )
            axes[1].add_patch(rect)
            
            # Подпись
            label_text = f"{class_name}: {score:.2f}"
            axes[1].text(
                x1, y1-10, label_text,
                color='white',
                fontsize=10,
                bbox=dict(facecolor=color_normalized, alpha=0.8, boxstyle='round,pad=0.3')
            )
            
            detected_objects.append({
                'class': class_name,
                'confidence': score,
                'bbox': [x1, y1, x2, y2]
            })
            
            print(f"   {i+1:2d}. {class_name:15s} уверенность: {score:.2%}")
    
    axes[1].set_title(f"Результаты детекции ({len(detected_objects)} объектов)", fontsize=14)
    axes[1].axis('off')
    
    plt.tight_layout()
    
    # Сохраняем результат
    result_path = f"{config.OUTPUT_DIR}/detection_result.jpg"
    plt.savefig(result_path, dpi=150, bbox_inches='tight')
    print(f"\n💾 Результат сохранён: {result_path}")
    
    plt.show()
    
    return detected_objects

# ============================================================================
# 7. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================
def setup_directories():
    """Создаёт необходимые папки"""
    directories = [
        config.OUTPUT_DIR,
        "models",
        "results",
        "data/dataset"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Создана папка: {directory}")

def check_environment():
    """Проверяет окружение"""
    print("\n🔍 ПРОВЕРКА ОКРУЖЕНИЯ")
    print("-" * 40)
    
    print(f"PyTorch версия: {torch.__version__}")
    print(f"Torchvision версия: {torchvision.__version__}")
    print(f"CUDA доступна: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA версия: {torch.version.cuda}")
    else:
        print("⚠️  CUDA не доступна, обучение будет на CPU (медленнее)")

# ============================================================================
# 8. ОСНОВНАЯ ФУНКЦИЯ
# ============================================================================
def main():
    """Основная функция"""
    print("\n" + "="*70)
    print("🔋 ЗАПУСК ПРОЕКТА ПО ДЕТЕКЦИИ БАТАРЕЕК")
    print("="*70)
    
    # 1. Настройка
    check_environment()
    setup_directories()
    
    # 2. Подготовка данных
    dataset = prepare_data()
    if dataset is None:
        return
    
    # 3. Создание DataLoader
    train_loader = DataLoader(
        dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=True,
        num_workers=0,
        collate_fn=lambda x: tuple(zip(*x))
    )
    
    # 4. Создание модели
    num_classes = len(config.CLASSES) + 1  # +1 для background
    model = create_model(num_classes)
    
    # 5. Обучение модели
    trained_model = train_model(model, train_loader)
    
    # 6. Тестирование модели
    print("\n" + "="*70)
    print("🧪 ТЕСТИРОВАНИЕ НА НОВЫХ ИЗОБРАЖЕНИЯХ")
    print("="*70)
    
    # Тестируем на нескольких изображениях
    test_images = [
        "data/raw_images/AA/WIN_20260209_18_59_58_Pro.jpg",  # пример
        "data/raw_images/CR/WIN_20260209_19_04_57_Pro.jpg",
    ]
    
    for test_img in test_images:
        if os.path.exists(test_img):
            print(f"\n📸 Тестирую: {test_img}")
            test_model(trained_model, test_img)
        else:
            print(f"⚠️  Изображение не найдено: {test_img}")
    
    print("\n" + "="*70)
    print("✅ ПРОЕКТ УСПЕШНО ЗАВЕРШЁН!")
    print("="*70)
    print("\n📁 Результаты сохранены в папке 'output/':")
    print("   • Модели (.pth файлы)")
    print("   • График обучения")
    print("   • Примеры детекции")
    print("\n🎯 Для использования модели смотрите скрипт detect.py")

# ============================================================================
# 9. СКРИПТ ДЛЯ ИСПОЛЬЗОВАНИЯ МОДЕЛИ
# ============================================================================
def create_detection_script():
    """Создаёт скрипт для использования обученной модели"""
    detection_script = """
# detect.py - Использование обученной модели
import torch
import torchvision
from torchvision.models.detection import fasterrcnn_resnet50_fpn
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.transforms import functional as F
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os

class BatteryDetector:
    def __init__(self, model_path, confidence_threshold=0.5):
        self.confidence_threshold = confidence_threshold
        self.classes = ['AA_battery', 'CR_battery', 'plastic_cap']
        
        # Загружаем модель
        self.model = self._load_model(model_path)
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        self.model.eval()
    
    def _load_model(self, model_path):
        """Загружает обученную модель"""
        model = fasterrcnn_resnet50_fpn(pretrained=False)
        num_classes = len(self.classes) + 1
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
        
        model.load_state_dict(torch.load(model_path, map_location='cpu'))
        return model
    
    def detect(self, image_path):
        """Детектирует объекты на изображении"""
        # Загрузка изображения
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Преобразование для модели
        image_tensor = F.to_tensor(image_rgb)
        
        # Предсказание
        with torch.no_grad():
            predictions = self.model([image_tensor.to(self.device)])
        
        # Обработка результатов
        boxes = predictions[0]['boxes'].cpu().numpy()
        scores = predictions[0]['scores'].cpu().numpy()
        labels = predictions[0]['labels'].cpu().numpy()
        
        # Фильтрация по порогу уверенности
        mask = scores > self.confidence_threshold
        boxes = boxes[mask]
        scores = scores[mask]
        labels = labels[mask]
        
        # Форматирование результатов
        results = []
        for box, score, label in zip(boxes, scores, labels):
            if label > 0 and label <= len(self.classes):
                results.append({
                    'class': self.classes[label-1],
                    'confidence': float(score),
                    'bbox': box.astype(int).tolist()
                })
        
        return results, image_rgb
    
    def visualize(self, image_path, results=None, save_path=None):
        """Визуализирует результаты детекции"""
        if results is None:
            results, image = self.detect(image_path)
        else:
            _, image = self.detect(image_path)
        
        # Рисуем bounding boxes
        plt.figure(figsize=(10, 8))
        plt.imshow(image)
        
        colors = {'AA_battery': 'green', 'CR_battery': 'red', 'plastic_cap': 'yellow'}
        
        for result in results:
            x1, y1, x2, y2 = result['bbox']
            class_name = result['class']
            confidence = result['confidence']
            color = colors.get(class_name, 'white')
            
            # Прямоугольник
            rect = plt.Rectangle((x1, y1), x2-x1, y2-y1,
                               fill=False, edgecolor=color, linewidth=2)
            plt.gca().add_patch(rect)
            
            # Подпись
            plt.text(x1, y1-10, f"{class_name}: {confidence:.2f}",
                    color='white', fontsize=10,
                    bbox=dict(facecolor=color, alpha=0.8))
        
        plt.axis('off')
        plt.title(f"Обнаружено {len(results)} объектов", fontsize=14)
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Результат сохранён: {save_path}")
        
        plt.show()
        return results

# Пример использования
if __name__ == "__main__":
    # Инициализация детектора
    detector = BatteryDetector("output/battery_detector_final.pth")
    
    # Детекция на изображении
    results = detector.visualize("your_photo.jpg", save_path="detection_result.jpg")
    
    # Вывод результатов
    print(f"\\nНайдено объектов: {len(results)}")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['class']}: уверенность {result['confidence']:.2%}")
"""
    
    with open("detect.py", "w", encoding="utf-8") as f:
        f.write(detection_script)
    
    print("\n📝 Создан скрипт для использования модели: detect.py")

# ============================================================================
# ЗАПУСК
# ============================================================================
if __name__ == "__main__":
    try:
        main()
        create_detection_script()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("\n🔧 Возможные решения:")
        print("1. Убедитесь, что файл аннотаций в формате COCO JSON")
        print("2. Проверьте пути к изображениям")
        print("3. Установите зависимости: pip install torch torchvision opencv-python")
