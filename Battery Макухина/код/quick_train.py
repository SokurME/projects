# quick_train.py
import subprocess
import os

print("="*60)
print("🚀 БЫСТРОЕ ОБУЧЕНИЕ ЗА 5 МИНУТ")
print("="*60)

# Создаём команду для обучения
command = [
    "python", "-m", "torch.distributed.run",
    "--nproc_per_node", "1",
    "yolov5/train.py",
    "--img", "640",
    "--batch", "8",
    "--epochs", "30",
    "--data", "dataset.yaml",
    "--weights", "yolov5s.pt",
    "--name", "battery_v1",
    "--device", "cpu",
    "--patience", "10",
    "--exist-ok"
]

print("⚙️ Параметры обучения:")
print(f"   • Модель: YOLOv5s")
print(f"   • Изображений: 22")
print(f"   • Классы: AA_battery, CR_battery")
print(f"   • Эпох: 30")
print(f"   • Устройство: CPU")

print("\n🚀 Запускаю обучение...")
print("⏳ Это займёт 10-30 минут в зависимости от CPU")

try:
    # Запускаем обучение
    subprocess.run(command, check=True)
    
    print("\n" + "="*60)
    print("✅ ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print("="*60)
    
    # Показываем где результаты
    print("\n📁 РЕЗУЛЬТАТЫ:")
    print("   • Модель: runs/train/battery_v1/weights/best.pt")
    print("   • Графики: runs/train/battery_v1/results.png")
    print("   • Логи: runs/train/battery_v1/results.csv")
    
except FileNotFoundError:
    print("\n❌ YOLOv5 не найден!")
    print("📌 Установите YOLOv5:")
    print("   git clone https://github.com/ultralytics/yolov5")
    print("   cd yolov5")
    print("   pip install -r requirements.txt")
    print("\n📌 Затем вернитесь в вашу папку и запустите снова")
    
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
