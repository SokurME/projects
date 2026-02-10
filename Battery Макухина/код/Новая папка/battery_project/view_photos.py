import cv2
import os
import matplotlib.pyplot as plt

def view_sample_photos():
    """Просмотр примеров фото"""
    
    base_path = "raw_images"
    
    # Покажем по 2 фото из каждой категории
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    idx = 0
    for category in ['AA', 'CR']:
        path = os.path.join(base_path, category)
        
        if os.path.exists(path):
            # Берём первые 2 фото
            photos = [f for f in os.listdir(path) 
                     if f.lower().endswith(('.jpg', '.jpeg', '.png'))][:2]
            
            for photo in photos:
                img_path = os.path.join(path, photo)
                img = cv2.imread(img_path)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                axes[idx].imshow(img_rgb)
                axes[idx].set_title(f"{category}: {photo}")
                axes[idx].axis('off')
                idx += 1
    
    # Скрываем пустые оси
    for i in range(idx, len(axes)):
        axes[i].axis('off')
    
    plt.tight_layout()
    plt.show()
    
    # Информация о фото
    print("📸 ИНФОРМАЦИЯ О ФОТО:")
    print("="*40)
    
    for category in ['AA', 'CR']:
        path = os.path.join(base_path, category)
        photos = [f for f in os.listdir(path) 
                 if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if photos:
            sample = os.path.join(path, photos[0])
            img = cv2.imread(sample)
            h, w = img.shape[:2]
            
            print(f"\n{category} батарейки:")
            print(f"  • Количество: {len(photos)} фото")
            print(f"  • Размер: {w}x{h} пикселей")
            print(f"  • Пример: {photos[0]}")
            print(f"  • Цветовые каналы: {img.shape[2]} (BGR)")

if __name__ == "__main__":
    view_sample_photos()
