# train_with_detectron2.py
import torch
import torchvision
import detectron2
from detectron2.utils.logger import setup_logger
from detectron2 import model_zoo
from detectron2.engine import DefaultTrainer
from detectron2.config import get_cfg
from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.data.datasets import register_coco_instances
import os
import json

print("🎯 ОБУЧЕНИЕ НА ОСНОВЕ COCO МОДЕЛИ")

# 1. Установите Detectron2 если ещё не установлен
print("🔧 Проверка установки...")
try:
    import detectron2
    print("✅ Detectron2 установлен")
except:
    print("❌ Detectron2 не установлен")
    print("📌 Установите: pip install detectron2")
    exit()

# 2. Регистрируем наш датасет
print("\n📁 Регистрирую датасет...")

# Загружаем COCO аннотации
with open("coco_dataset/annotations.json", 'r') as f:
    coco_data = json.load(f)

# Регистрируем датасет для Detectron2
register_coco_instances(
    "battery_train", 
    {}, 
    "coco_dataset/annotations.json", 
    "coco_dataset/train"
)

print("✅ Датасет зарегистрирован как 'battery_train'")

# 3. Настраиваем конфигурацию
cfg = get_cfg()
cfg.merge_from_file(model_zoo.get_config_file("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml"))
cfg.DATASETS.TRAIN = ("battery_train",)
cfg.DATASETS.TEST = ()  # нет тестовых данных
cfg.DATALOADER.NUM_WORKERS = 2

# Предобученные веса COCO
cfg.MODEL.WEIGHTS = model_zoo.get_checkpoint_url("COCO-Detection/faster_rcnn_R_50_FPN_3x.yaml")

# Параметры обучения
cfg.SOLVER.IMS_PER_BATCH = 2  # размер батча (уменьшите если мало памяти)
cfg.SOLVER.BASE_LR = 0.00025
cfg.SOLVER.MAX_ITER = 1000  # количество итераций
cfg.SOLVER.STEPS = []  # нет schedule
cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128
cfg.MODEL.ROI_HEADS.NUM_CLASSES = len(coco_data['categories'])  # ваши классы

# Папка для сохранения
cfg.OUTPUT_DIR = "./output"

print("\n⚙️  КОНФИГУРАЦИЯ:")
print(f"   Модель: Faster R-CNN (предобученная на COCO)")
print(f"   Классы: {cfg.MODEL.ROI_HEADS.NUM_CLASSES}")
print(f"   Итераций: {cfg.SOLVER.MAX_ITER}")
print(f"   Папка вывода: {cfg.OUTPUT_DIR}")

# 4. Создаём папку для результатов
os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)

# 5. Запускаем обучение
print("\n🚀 НАЧИНАЮ ОБУЧЕНИЕ...")
trainer = DefaultTrainer(cfg)
trainer.resume_or_load(resume=False)
trainer.train()

print("✅ Обучение завершено!")
