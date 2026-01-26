#!/usr/bin/env python3
# esp_squares_monitor.py

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time
import json
from datetime import datetime
from collections import Counter
import random  # Для эмуляции, если ESP не доступен

class ESPSquaresMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP Squares Monitor")
        self.root.geometry("1200x800")
        
        # Конфигурация
        self.esp_ip = "192.168.137.176"  # IP вашего ESP
        self.update_interval = 5  # секунд
        self.total_squares = 10
        self.is_monitoring = False
        
        # Цветовая схема для значений 1-6
        self.color_map = {
            1: "#2ecc71",  # зеленый
            2: "#e74c3c",  # красный
            3: "#3498db",  # синий
            4: "#f1c40f",  # желтый
            5: "#e67e22",  # оранжевый
            6: "#ecf0f1",  # белый
            0: "#95a5a6"   # серый (по умолчанию/нет данных)
        }
        
        # Состояние квадратов
        self.squares_state = [0] * self.total_squares  # 0 = нет данных
        
        # Для первого ESP (реальный)
        self.esp_state = 0  # Текущее значение с ESP
        
        # Статистика
        self.history = {i: [] for i in range(self.total_squares)}
        self.total_counts = Counter()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Главный контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Верхняя панель - заголовок и управление
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", pady=(0, 20))
        
        title = ttk.Label(top_frame, text="📊 ESP Squares Monitor", 
                         font=("Arial", 24, "bold"))
        title.pack(side="left", padx=10)
        
        # Панель управления
        control_frame = ttk.Frame(top_frame)
        control_frame.pack(side="right", padx=10)
        
        self.ip_var = tk.StringVar(value=self.esp_ip)
        ip_entry = ttk.Entry(control_frame, textvariable=self.ip_var, width=15)
        ip_entry.pack(side="left", padx=2)
        
        self.interval_var = tk.StringVar(value=str(self.update_interval))
        interval_spin = ttk.Spinbox(control_frame, from_=1, to=60, 
                                   textvariable=self.interval_var, width=5)
        interval_spin.pack(side="left", padx=2)
        ttk.Label(control_frame, text="сек").pack(side="left", padx=2)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ Старт", 
                                   command=self.toggle_monitoring)
        self.start_btn.pack(side="left", padx=2)
        
        ttk.Button(control_frame, text="🔄 Обновить", 
                  command=self.manual_update).pack(side="left", padx=2)
        
        ttk.Button(control_frame, text="📊 Статистика", 
                  command=self.show_stats).pack(side="left", padx=2)
        
        ttk.Button(control_frame, text="⚙️ Настройки", 
                  command=self.show_settings).pack(side="left", padx=2)
        
        # Основная область - квадраты
        squares_frame = ttk.LabelFrame(main_frame, text="ESP Squares (10 устройств)")
        squares_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Сетка 2x5 для квадратов
        grid_frame = ttk.Frame(squares_frame)
        grid_frame.pack(expand=True, padx=20, pady=20)
        
        self.square_canvases = []
        self.square_labels = []
        
        for i in range(self.total_squares):
            # Фрейм для каждого квадрата
            square_frame = ttk.Frame(grid_frame, relief="ridge", borderwidth=2)
            row = i // 5
            col = i % 5
            square_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Заголовок квадрата
            title = ttk.Label(square_frame, text=f"ESP #{i+1}", 
                             font=("Arial", 12, "bold"))
            title.pack(pady=(5, 0))
            
            # Canvas для цветного квадрата
            canvas = tk.Canvas(square_frame, width=100, height=100, 
                              bg=self.color_map[0], highlightthickness=0)
            canvas.pack(pady=5)
            
            # Рисуем квадрат
            canvas.create_rectangle(10, 10, 90, 90, fill=self.color_map[0], 
                                   outline="black", width=2)
            
            # Метка с текущим значением
            value_label = ttk.Label(square_frame, text="--", 
                                   font=("Arial", 16, "bold"))
            value_label.pack(pady=(0, 5))
            
            # Статус подключения
            status_label = ttk.Label(square_frame, text="❌ Нет данных", 
                                    font=("Arial", 8), foreground="gray")
            status_label.pack(pady=(0, 5))
            
            self.square_canvases.append({
                "canvas": canvas,
                "square": canvas.find_all()[0],  # ID квадрата
                "status": status_label
            })
            self.square_labels.append(value_label)
            
            # Делаем все колонки одинаковой ширины
            grid_frame.columnconfigure(col, weight=1)
        
        # Нижняя панель - статистика по цветам
        stats_frame = ttk.LabelFrame(main_frame, text="Статистика по цветам")
        stats_frame.pack(fill="x", pady=(0, 10))
        
        # Фрейм для цветовых индикаторов
        colors_frame = ttk.Frame(stats_frame)
        colors_frame.pack(pady=10)
        
        self.color_stats_labels = {}
        
        for value, color in self.color_map.items():
            if value == 0:
                continue  # Пропускаем серый цвет
                
            color_frame = ttk.Frame(colors_frame)
            color_frame.pack(side="left", padx=15)
            
            # Цветной квадратик
            color_canvas = tk.Canvas(color_frame, width=30, height=30, 
                                    bg=color, highlightthickness=1)
            color_canvas.pack()
            color_canvas.create_rectangle(2, 2, 28, 28, fill=color, 
                                         outline="black")
            
            # Описание и счетчик
            color_names = {
                1: "Зеленый", 2: "Красный", 3: "Синий",
                4: "Желтый", 5: "Оранжевый", 6: "Белый"
            }
            
            ttk.Label(color_frame, text=color_names[value]).pack()
            
            count_label = ttk.Label(color_frame, text="0", 
                                   font=("Arial", 14, "bold"))
            count_label.pack()
            
            self.color_stats_labels[value] = count_label
        
        # Общая статистика
        self.total_label = ttk.Label(stats_frame, 
                                    text="Всего обновлений: 0", 
                                    font=("Arial", 10))
        self.total_label.pack(pady=5)
        
        # Статус бар
        self.status_var = tk.StringVar(value="✅ Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                              relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")
        
        # Легенда
        legend_frame = ttk.Frame(main_frame)
        legend_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Label(legend_frame, text="Легенда:", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        for value in range(1, 7):
            color_names = ["Зеленый", "Красный", "Синий", "Желтый", "Оранжевый", "Белый"]
            legend_item = ttk.Frame(legend_frame)
            legend_item.pack(side="left", padx=5)
            
            tk.Canvas(legend_item, width=15, height=15, 
                     bg=self.color_map[value]).pack(side="left")
            ttk.Label(legend_item, text=f"={value} ({color_names[value-1]})").pack(side="left")
        
        # Для первого ESP (реальный) показываем его IP
        esp_info = ttk.Label(main_frame, 
                            text=f"ESP #1 подключается к: {self.esp_ip}",
                            font=("Arial", 10, "italic"))
        esp_info.pack(pady=5)
        
        # Эмуляция данных для остальных ESP
        self.emulate_check = tk.BooleanVar(value=True)
        emulate_checkbox = ttk.Checkbutton(main_frame, 
                                          text="Эмулировать данные для ESP #2-10",
                                          variable=self.emulate_check)
        emulate_checkbox.pack()
        
    def get_esp_data(self):
        """Получение данных с реального ESP"""
        try:
            response = requests.get(f"http://{self.esp_ip}/random", timeout=2)
            if response.status_code == 200:
                value = int(response.text.strip())
                if 1 <= value <= 6:
                    return value
        except requests.exceptions.RequestException as e:
            print(f"Ошибка подключения к ESP: {e}")
        
        return None  # Если не удалось получить данные
    
    def emulate_esp_data(self, esp_num):
        """Эмуляция данных для ESP (кроме первого)"""
        if esp_num == 0:  # Первый ESP - реальный
            return self.esp_state if self.esp_state != 0 else None
        
        # Для остальных ESP эмулируем данные
        if self.emulate_check.get():
            # Эмуляция: иногда возвращаем случайное значение, иногда ошибку
            if random.random() > 0.1:  # 90% успешных запросов
                # С небольшим шансом меняем значение
                if random.random() > 0.7:
                    return random.randint(1, 6)
                else:
                    # Сохраняем предыдущее значение или новое
                    current = self.squares_state[esp_num]
                    return current if current != 0 else random.randint(1, 6)
        return None
    
    def update_square(self, esp_num, value):
        """Обновление отображения квадрата"""
        if value is None:
            # Нет данных
            color = self.color_map[0]
            text = "--"
            status = "❌ Нет данных"
            self.squares_state[esp_num] = 0
        else:
            # Есть данные
            color = self.color_map[value]
            text = str(value)
            status = "✅ Данные получены"
            self.squares_state[esp_num] = value
            
            # Сохраняем в историю
            self.history[esp_num].append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "value": value
            })
        
        # Обновляем Canvas
        canvas_data = self.square_canvases[esp_num]
        canvas_data["canvas"].itemconfig(canvas_data["square"], fill=color)
        canvas_data["status"].config(text=status)
        
        # Обновляем метку
        self.square_labels[esp_num].config(text=text)
    
    def update_statistics(self):
        """Обновление статистики"""
        # Считаем количество каждого цвета
        counts = Counter(self.squares_state)
        
        # Обновляем счетчики
        for value in range(1, 7):
            count = counts.get(value, 0)
            self.color_stats_labels[value].config(text=str(count))
        
        # Общее количество обновлений
        total_updates = sum(len(h) for h in self.history.values())
        self.total_label.config(text=f"Всего обновлений: {total_updates}")
        
        # Обновляем общий счетчик
        self.total_counts.update(self.squares_state)
    
    def update_all_squares(self):
        """Обновление всех квадратов"""
        # Обновляем реальный ESP
        esp_value = self.get_esp_data()
        self.esp_state = esp_value if esp_value else 0
        self.update_square(0, esp_value)
        
        # Обновляем остальные ESP (эмулированные)
        for i in range(1, self.total_squares):
            value = self.emulate_esp_data(i)
            self.update_square(i, value)
        
        # Обновляем статистику
        self.update_statistics()
        
        # Обновляем статус
        success_count = sum(1 for v in self.squares_state if v != 0)
        self.status_var.set(f"✅ Обновлено: {success_count}/{self.total_squares} | Следующее обновление через {self.update_interval} сек")
    
    def manual_update(self):
        """Ручное обновление"""
        if not self.is_monitoring:
            self.update_all_squares()
    
    def monitoring_loop(self):
        """Цикл мониторинга"""
        while self.is_monitoring:
            try:
                self.update_all_squares()
            except Exception as e:
                self.status_var.set(f"❌ Ошибка: {str(e)[:50]}")
            
            # Ждем указанный интервал
            for i in range(self.update_interval * 10):  # Проверяем каждые 0.1 сек
                if not self.is_monitoring:
                    return
                time.sleep(0.1)
    
    def toggle_monitoring(self):
        """Включение/выключение мониторинга"""
        if not self.is_monitoring:
            # Начинаем мониторинг
            self.is_monitoring = True
            self.start_btn.config(text="⏸️ Стоп")
            
            # Обновляем конфигурацию
            try:
                self.esp_ip = self.ip_var.get()
                self.update_interval = int(self.interval_var.get())
            except:
                messagebox.showerror("Ошибка", "Некорректные настройки")
                self.is_monitoring = False
                self.start_btn.config(text="▶️ Старт")
                return
            
            # Запускаем поток мониторинга
            self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitor_thread.start()
            
            self.status_var.set("🚀 Мониторинг запущен")
        else:
            # Останавливаем мониторинг
            self.is_monitoring = False
            self.start_btn.config(text="▶️ Старт")
            self.status_var.set("⏸️ Мониторинг остановлен")
    
    def show_stats(self):
        """Показать подробную статистику"""
        # Создаем новое окно
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Подробная статистика")
        stats_window.geometry("800x600")
        
        # Создаем Notebook для вкладок
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Вкладка 1: Общая статистика
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="📊 Общая статистика")
        
        # Текстовое поле для статистики
        stats_text = tk.Text(general_frame, wrap="word", font=("Consolas", 10))
        scrollbar = ttk.Scrollbar(general_frame, orient="vertical", command=stats_text.yview)
        stats_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        stats_text.pack(side="left", fill="both", expand=True)
        
        # Генерируем статистику
        stats_lines = []
        stats_lines.append("=" * 60)
        stats_lines.append("ОБЩАЯ СТАТИСТИКА ESP КВАДРАТОВ")
        stats_lines.append("=" * 60)
        stats_lines.append("")
        
        # Текущее состояние
        stats_lines.append("Текущее состояние квадратов:")
        for i in range(self.total_squares):
            value = self.squares_state[i]
            color_name = {
                0: "Серый (нет данных)", 1: "Зеленый", 2: "Красный",
                3: "Синий", 4: "Желтый", 5: "Оранжевый", 6: "Белый"
            }.get(value, "Неизвестно")
            
            stats_lines.append(f"  ESP #{i+1}: значение={value} ({color_name})")
        
        stats_lines.append("")
        
        # Общее распределение цветов
        stats_lines.append("Распределение цветов:")
        total_non_zero = sum(1 for v in self.squares_state if v != 0)
        stats_lines.append(f"  Активных квадратов: {total_non_zero}/{self.total_squares}")
        
        for value in range(1, 7):
            count = sum(1 for v in self.squares_state if v == value)
            if count > 0:
                color_name = ["Зеленый", "Красный", "Синий", "Желтый", "Оранжевый", "Белый"][value-1]
                percentage = (count / total_non_zero * 100) if total_non_zero > 0 else 0
                stats_lines.append(f"  {color_name}: {count} ({percentage:.1f}%)")
        
        stats_lines.append("")
        
        # История изменений
        stats_lines.append("История изменений (последние 20):")
        all_events = []
        for i in range(self.total_squares):
            for event in self.history[i][-5:]:  # Последние 5 событий каждого ESP
                all_events.append((event["time"], i, event["value"]))
        
        # Сортируем по времени
        all_events.sort(key=lambda x: x[0], reverse=True)
        
        for time_str, esp_num, value in all_events[:20]:
            color_name = ["Зеленый", "Красный", "Синий", "Желтый", "Оранжевый", "Белый"][value-1]
            stats_lines.append(f"  [{time_str}] ESP #{esp_num+1} → {value} ({color_name})")
        
        # Вставляем текст
        stats_text.insert("1.0", "\n".join(stats_lines))
        stats_text.config(state="disabled")
        
        # Вкладка 2: График истории (простой текстовый)
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="📈 История значений")
        
        # Создаем Canvas для простого графика
        canvas = tk.Canvas(history_frame, bg="white")
        canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Рисуем простой график для первого ESP
        if self.history[0]:
            values = [entry["value"] for entry in self.history[0]]
            times = list(range(len(values)))
            
            if len(values) > 1:
                # Вычисляем масштаб
                width = 700
                height = 400
                max_val = max(values)
                min_val = min(values)
                
                # Рисуем оси
                canvas.create_line(50, 50, 50, height - 50, width=2)
                canvas.create_line(50, height - 50, width - 50, height - 50, width=2)
                
                # Рисуем график
                points = []
                for i, val in enumerate(values[-50:]):  # Последние 50 точек
                    x = 50 + (i * (width - 100) / min(49, len(values)-1))
                    y = height - 50 - ((val - min_val) * (height - 100) / max(1, max_val - min_val))
                    points.append((x, y))
                    
                    canvas.create_oval(x-3, y-3, x+3, y+3, fill=self.color_map[val])
                
                # Соединяем точки
                for i in range(len(points)-1):
                    canvas.create_line(points[i][0], points[i][1], 
                                      points[i+1][0], points[i+1][1], 
                                      width=2, fill="blue")
                
                # Подписи
                canvas.create_text(width // 2, height - 20, text="Время (последние значения)", font=("Arial", 10))
                canvas.create_text(20, height // 2, text="Значение", angle=90, font=("Arial", 10))
                
                # Легенда значений
                legend_y = 20
                for val in range(1, 7):
                    canvas.create_rectangle(60, legend_y, 80, legend_y + 15, 
                                           fill=self.color_map[val], outline="black")
                    color_name = ["Зеленый", "Красный", "Синий", "Желтый", "Оранжевый", "Белый"][val-1]
                    canvas.create_text(100, legend_y + 7, text=f"= {val} ({color_name})", 
                                      anchor="w", font=("Arial", 9))
                    legend_y += 25
        
        # Кнопка экспорта
        export_btn = ttk.Button(stats_window, text="📥 Экспорт данных", 
                               command=self.export_data)
        export_btn.pack(pady=10)
    
    def show_settings(self):
        """Окно настроек"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Настройки")
        settings_window.geometry("400x300")
        
        ttk.Label(settings_window, text="Настройки ESP Squares Monitor", 
                 font=("Arial", 14, "bold")).pack(pady=10)
        
        # Настройки соединения
        conn_frame = ttk.LabelFrame(settings_window, text="Настройки соединения")
        conn_frame.pack(fill="x", padx=20, pady=10)
        
        ttk.Label(conn_frame, text="IP адрес ESP:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ip_entry = ttk.Entry(conn_frame, textvariable=self.ip_var, width=20)
        ip_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(conn_frame, text="Интервал обновления (сек):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        interval_entry = ttk.Entry(conn_frame, textvariable=self.interval_var, width=10)
        interval_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Настройки эмуляции
        emul_frame = ttk.LabelFrame(settings_window, text="Настройки эмуляции")
        emul_frame.pack(fill="x", padx=20, pady=10)
        
        emulate_var = tk.BooleanVar(value=self.emulate_check.get())
        emulate_check = ttk.Checkbutton(emul_frame, text="Эмулировать данные для ESP #2-10",
                                       variable=emulate_var)
        emulate_check.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # Кнопки
        btn_frame = ttk.Frame(settings_window)
        btn_frame.pack(pady=20)
        
        def save_settings():
            self.esp_ip = ip_entry.get()
            try:
                self.update_interval = int(interval_entry.get())
            except:
                messagebox.showerror("Ошибка", "Интервал должен быть числом")
                return
            
            self.emulate_check.set(emulate_var.get())
            settings_window.destroy()
            messagebox.showinfo("Сохранено", "Настройки сохранены")
        
        ttk.Button(btn_frame, text="Сохранить", command=save_settings).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Отмена", command=settings_window.destroy).pack(side="left", padx=5)
    
    def export_data(self):
        """Экспорт данных в файл"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"esp_squares_data_{timestamp}.json"
        
        try:
            data = {
                "export_time": datetime.now().isoformat(),
                "esp_ip": self.esp_ip,
                "total_squares": self.total_squares,
                "current_state": self.squares_state,
                "history": self.history,
                "total_counts": dict(self.total_counts)
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Успех", f"Данные экспортированы в файл:\n{filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать данные:\n{str(e)}")

def main():
    root = tk.Tk()
    app = ESPSquaresMonitor(root)
    
    # Запускаем цикл обработки событий
    root.mainloop()

if __name__ == "__main__":
    main()
