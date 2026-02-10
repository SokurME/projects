# detector.py
import tensorflow.compat.v1 as tf
import numpy as np
from PIL import Image
import cv2
import time
import os

class BatteryDetector:
    """Детектор батареек и компонентов для камеры №1"""
    
    def __init__(self, model_dir='tensorflow'):
        """
        Инициализация детектора
        
        Args:
            model_dir: папка с моделью TensorFlow
        """
        self.model_dir = model_dir
        self.camera_id = 1  # Камера №1
        self.labels = self._load_labels()
        self.session = None
        self.input_tensor = None
        self.scores_tensor = None
        self.classes_tensor = None
        
        self._setup_tensorflow()
        self._load_model()
    
    def _setup_tensorflow(self):
        """Настройка TensorFlow"""
        # Подавляем предупреждения
        tf.compat.v1.logging.set_verbosity(tf.compat.v1.logging.ERROR)
        tf.disable_eager_execution()
    
    def _load_labels(self):
        """Загрузка меток классов"""
        labels_file = os.path.join(self.model_dir, 'labels.txt')
        if os.path.exists(labels_file):
            with open(labels_file, 'r', encoding='utf-8') as f:
                labels = [line.strip() for line in f if line.strip()]
                print(f"Загружены метки: {labels}")
                return labels
        else:
            print("Файл labels.txt не найден, используем стандартные метки")
            return ["aa", "crone", "not battary"]
    
    def _load_model(self):
        """Загрузка модели TensorFlow"""
        try:
            model_path = os.path.join(self.model_dir, 'saved_model.pb')
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Файл модели не найден: {model_path}")
            
            print("Загрузка модели...")
            
            # Загружаем граф модели
            with tf.gfile.GFile(model_path, 'rb') as f:
                graph_def = tf.GraphDef().FromString(f.read())
            
            graph = tf.Graph()
            with graph.as_default():
                tf.import_graph_def(graph_def, name='')
            
            # Создаем сессию
            self.session = tf.Session(graph=graph)
            
            # Получаем тензоры
            self.input_tensor = graph.get_tensor_by_name('image_tensor:0')
            self.scores_tensor = graph.get_tensor_by_name('detected_scores:0')
            self.classes_tensor = graph.get_tensor_by_name('detected_classes:0')
            
            print("✓ Модель загружена")
            
        except Exception as e:
            print(f"✗ Ошибка загрузки модели: {e}")
            raise
    
    def detect_frame(self, frame):
        """
        Детекция объектов на кадре
        
        Args:
            frame: numpy array изображения (BGR от OpenCV)
            
        Returns:
            Список обнаруженных объектов с confidence > 50%
        """
        try:
            # Конвертируем BGR в RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Создаем PIL изображение и ресайзим
            img = Image.fromarray(rgb).resize((320, 320))
            
            # Подготавливаем для модели (0-255, без нормализации!)
            img_array = np.array(img, dtype=np.float32)
            img_array = np.expand_dims(img_array, axis=0)
            
            # Запускаем детекцию
            scores, classes = self.session.run(
                [self.scores_tensor, self.classes_tensor],
                feed_dict={self.input_tensor: img_array}
            )
            
            # Обработка результатов
            if not hasattr(scores, '__len__') or scores.shape == ():
                scores = np.array([scores])
                classes = np.array([classes])
            
            detected = []
            
            for i in range(len(scores)):
                confidence = float(scores[i])
                if confidence > 0.5:  # порог 50%
                    class_id = int(classes[i]) if i < len(classes) else 0
                    label = self.labels[class_id] if class_id < len(self.labels) else f'obj_{class_id}'
                    
                    detected.append({
                        'label': label,
                        'confidence': confidence,
                        'class_id': class_id
                    })
            
            return detected
            
        except Exception as e:
            print(f"Ошибка детекции: {e}")
            return []
    
    def monitor_camera(self, show_preview=False):
        """
        Мониторинг камеры №1
        
        Args:
            show_preview: показывать ли окно с превью
        """
        print("=" * 50)
        print("ДЕТЕКТОР БАТАРЕЕК И КОМПОНЕНТОВ")
        print("=" * 50)
        print(f"Камера: #{self.camera_id}")
        print("Поиск: 'aa' (батарейка) и 'crone' (компонент)")
        print(f"Превью: {'ВКЛ' if show_preview else 'ВЫКЛ'}")
        print("Нажмите Ctrl+C для остановки")
        print("=" * 50)
        
        # Открываем камеру
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            print(f"✗ Ошибка: не удалось открыть камеру {self.camera_id}")
            print("Проверьте подключение камеры")
            return
        
        # Настраиваем камеру
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        last_check = 0
        check_interval = 1.0  # проверка каждую секунду
        
        try:
            while True:
                # Читаем кадр
                ret, frame = cap.read()
                if not ret:
                    print("Ошибка чтения кадра")
                    time.sleep(0.1)
                    continue
                
                current_time = time.time()
                
                # Проверяем по времени
                if current_time - last_check > check_interval:
                    # Детекция
                    detected = self.detect_frame(frame)
                    last_check = current_time
                    
                    # Проверяем на aa и crone
                    for obj in detected:
                        label = obj['label']
                        confidence = obj['confidence']
                        
                        if label == 'aa':
                            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ ОБНАРУЖЕНА БАТАРЕЙКА 'aa'! ({confidence:.1%})")
                        
                        if label == 'crone':
                            print(f"[{time.strftime('%H:%M:%S')}] ⚠️ ОБНАРУЖЕН КОМПОНЕНТ 'crone'! ({confidence:.1%})")
                    
                    # Выводим все обнаруженные объекты
                    if detected:
                        print(f"Всего объектов: {len(detected)}")
                        for obj in detected:
                            print(f"  - {obj['label']}: {obj['confidence']:.1%}")
                        print("-" * 40)
                
                # Показываем превью если нужно
                if show_preview:
                    # Добавляем текст на превью
                    display = frame.copy()
                    cv2.putText(display, f"Camera {self.camera_id} - Battery Detector", 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    
                    # Статус
                    status_y = display.shape[0] - 20
                    status_text = "STATUS: MONITORING"
                    cv2.putText(display, status_text, (10, status_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    cv2.imshow('Battery Detector', display)
                    
                    # Выход по 'q' из окна превью
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("\nВыход по запросу (кнопка 'q' в окне)")
                        break
        
        except KeyboardInterrupt:
            print("\n\nОстановка по запросу пользователя (Ctrl+C)")
        except Exception as e:
            print(f"\nОшибка: {e}")
        finally:
            # Очистка
            cap.release()
            if show_preview:
                cv2.destroyAllWindows()
            print("Камера закрыта")
    
    def single_check(self):
        """Однократная проверка камеры"""
        print("Однократная проверка камеры...")
        
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            print(f"Ошибка: камера {self.camera_id} недоступна")
            return
        
        try:
            # Захватываем кадр
            ret, frame = cap.read()
            if not ret:
                print("Не удалось получить изображение")
                return
            
            # Детекция
            detected = self.detect_frame(frame)
            
            print("\n" + "="*40)
            print("РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
            print("="*40)
            
            if detected:
                aa_found = False
                crone_found = False
                
                for obj in detected:
                    label = obj['label']
                    confidence = obj['confidence']
                    
                    print(f"- {label}: {confidence:.1%}")
                    
                    if label == 'aa':
                        aa_found = True
                        print("  ⚠️ ВНИМАНИЕ: Обнаружена батарейка!")
                    
                    if label == 'crone':
                        crone_found = True
                        print("  ⚠️ ВНИМАНИЕ: Обнаружен компонент!")
                
                if aa_found and crone_found:
                    print("\n🔴 КРИТИЧЕСКОЕ ОБНАРУЖЕНИЕ: найдены и батарейка и компонент!")
                elif aa_found:
                    print("\n🟡 ОБНАРУЖЕНО: батарейка 'aa'")
                elif crone_found:
                    print("\n🟡 ОБНАРУЖЕНО: компонент 'crone'")
                    
            else:
                print("Объекты не обнаружены")
                print("🟢 Безопасно")
            
        finally:
            cap.release()
    
    def close(self):
        """Закрытие ресурсов"""
        if self.session:
            self.session.close()
            print("Ресурсы TensorFlow освобождены")


def main():
    """Основная функция"""
    try:
        # Создаем детектор
        detector = BatteryDetector(model_dir='tensorflow')
        
        # Меню
        print("\nВыберите режим работы:")
        print("1 - Непрерывный мониторинг (без превью)")
        print("2 - Непрерывный мониторинг (с превью)")
        print("3 - Однократная проверка")
        print("0 - Выход")
        
        choice = input("\nВаш выбор: ").strip()
        
        if choice == '1':
            detector.monitor_camera(show_preview=False)
        elif choice == '2':
            detector.monitor_camera(show_preview=True)
        elif choice == '3':
            detector.single_check()
        elif choice == '0':
            print("Выход")
        else:
            print("Неверный выбор, запускаю мониторинг без превью...")
            detector.monitor_camera(show_preview=False)
    
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        if 'detector' in locals():
            detector.close()


if __name__ == "__main__":
    # Проверяем OpenCV
    try:
        import cv2
        main()
    except ImportError:
        print("Ошибка: OpenCV не установлен!")
        print("Установите: pip install opencv-python")
