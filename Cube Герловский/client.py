#!/usr/bin/env python3
# cube_server_final.py

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import sys

class CubeServer:
    def __init__(self, root):
        self.root = root
        self.root.title("Cube Server Monitor")
        self.root.geometry("1200x800")
        
        # Конфигурация сервера
        self.server_port = 8000
        self.total_cubes = 10  # Всего 10 кубов
        self.server_running = False
        self.http_server = None
        self.server_thread = None
        
        # Информация о гранях (цвета и статусы) - БЕЗ РЕБРО/УГОЛ
        self.face_info = {
            1: {"name": "ВЕРХНЯЯ", "color": "#2ecc71", "status": "Завершил", "ru_name": "Верхняя"},
            2: {"name": "НИЖНЯЯ", "color": "#e74c3c", "status": "Не понимаю", "ru_name": "Нижняя"},
            3: {"name": "ЛЕВАЯ", "color": "#90ee90", "status": "Готов", "ru_name": "Левая"},
            4: {"name": "ПРАВАЯ", "color": "#f1c40f", "status": "Выполняю", "ru_name": "Правая"},
            5: {"name": "ПЕРЕДНЯЯ", "color": "#FFFFFF", "status": "Устал", "ru_name": "Передняя"},  # Чисто белый
            6: {"name": "ЗАДНЯЯ", "color": "#3498db", "status": "Вопрос", "ru_name": "Задняя"},
            # 0: {"name": "РЕБРО/УГОЛ", "color": "#95a5a6", "status": "Ребро/Угол", "ru_name": "Ребро/Угол"} - УБРАНО
        }
        
        # Состояние кубов
        self.cubes_state = [0] * self.total_cubes  # 0 = нет данных/ребро/угол
        self.cubes_last_update = [0] * self.total_cubes
        self.cube_data = {i: {} for i in range(self.total_cubes)}
        
        # Статистика - время в каждом статусе для каждого куба (только для статусов 1-6)
        self.status_timers = {i: {} for i in range(self.total_cubes)}
        self.status_start_time = {i: {} for i in range(self.total_cubes)}
        self.total_time_in_status = {i: defaultdict(float) for i in range(self.total_cubes)}
        
        # История изменений (только статусы 1-6)
        self.history = {i: [] for i in range(self.total_cubes)}
        self.total_counts = Counter()
        
        # Получаем IP адрес
        self.computer_ip = self.get_local_ip()
        
        self.setup_ui()
        
        # Запускаем обновление интерфейса
        self.update_interval = 1000  # 1 секунда
        self.root.after(self.update_interval, self.update_display)
        
        # Запускаем таймер для статистики времени
        self.root.after(1000, self.update_status_timers)
    
    def get_local_ip(self):
        """Получение локального IP адреса"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            try:
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                return ip
            except:
                return "192.168.137.1"
    
    def update_status_timers(self):
        """Обновление таймеров для каждого статуса (только 1-6)"""
        current_time = time.time()
        
        for cube_id in range(self.total_cubes):
            current_status = self.cubes_state[cube_id]
            
            # Обновляем только для статусов 1-6
            if current_status in self.face_info:
                # Обновляем время для предыдущего статуса
                for status in list(self.status_timers[cube_id].keys()):
                    if status != current_status and status in self.face_info:
                        if self.status_start_time[cube_id].get(status):
                            elapsed = current_time - self.status_start_time[cube_id][status]
                            self.total_time_in_status[cube_id][status] += elapsed
                            self.status_start_time[cube_id][status] = current_time
                
                # Начинаем отсчет для нового статуса
                if current_status not in self.status_start_time[cube_id]:
                    self.status_start_time[cube_id][current_status] = current_time
                    self.total_time_in_status[cube_id][current_status] = 0.0
                
                # Обновляем текущее время для активного статуса
                if current_status in self.status_start_time[cube_id]:
                    elapsed = current_time - self.status_start_time[cube_id][current_status]
                    self.status_timers[cube_id][current_status] = elapsed
        
        # Повторяем каждую секунду
        self.root.after(1000, self.update_status_timers)
    
    def format_time(self, seconds):
        """Форматирование времени в читаемый вид"""
        if seconds < 60:
            return f"{int(seconds)} сек"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes} мин {secs} сек"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            secs = int(seconds % 60)
            return f"{hours} ч {minutes} мин {secs} сек"
    
    def setup_ui(self):
        """Настройка графического интерфейса"""
        # Главный контейнер
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Верхняя панель
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", pady=(0, 20))
        
        title = ttk.Label(top_frame, text="🎲 Cube Server Monitor", 
                         font=("Arial", 24, "bold"))
        title.pack(side="left", padx=10)
        
        # Панель управления
        control_frame = ttk.Frame(top_frame)
        control_frame.pack(side="right", padx=10)
        
        # Информация о сервере
        server_info = ttk.Label(control_frame, 
                               text=f"IP: {self.computer_ip}:{self.server_port}",
                               font=("Arial", 10))
        server_info.pack(side="left", padx=5)
        
        self.start_btn = ttk.Button(control_frame, text="▶️ Запустить сервер", 
                                   command=self.toggle_server)
        self.start_btn.pack(side="left", padx=2)
        
        ttk.Button(control_frame, text="📊 Статистика", 
                  command=self.show_detailed_stats).pack(side="left", padx=2)
        
        # Основная область - кубы
        cubes_frame = ttk.LabelFrame(main_frame, text="Статус кубов (10 устройств)")
        cubes_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Сетка 2x5 для кубов
        grid_frame = ttk.Frame(cubes_frame)
        grid_frame.pack(expand=True, padx=20, pady=20)
        
        self.cube_canvases = []
        self.status_labels = []
        self.time_labels = []
        self.conn_labels = []
        
        for i in range(self.total_cubes):
            # Фрейм для каждого куба
            cube_frame = ttk.Frame(grid_frame, relief="ridge", borderwidth=2)
            row = i // 5
            col = i % 5
            cube_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Заголовок куба
            title = ttk.Label(cube_frame, text=f"Куб #{i+1}", 
                             font=("Arial", 12, "bold"))
            title.pack(pady=(5, 0))
            
            # Canvas для цветного квадрата
            canvas = tk.Canvas(cube_frame, width=100, height=100, 
                              bg="#95a5a6", highlightthickness=0)
            canvas.pack(pady=5)
            
            # Рисуем квадрат с закругленными углами
            square_id = canvas.create_rectangle(15, 15, 85, 85, 
                                               fill="#95a5a6", 
                                               outline="black", 
                                               width=2,
                                               tags="square")
            
            # Метка со статусом
            status_label = ttk.Label(cube_frame, text="Нет данных", 
                                    font=("Arial", 10))
            status_label.pack(pady=(0, 2))
            
            # Метка со временем последнего обновления
            time_label = ttk.Label(cube_frame, text="", 
                                  font=("Arial", 8), foreground="gray")
            time_label.pack(pady=(0, 2))
            
            # Метка с IP/статусом подключения
            conn_label = ttk.Label(cube_frame, text="Не подключен", 
                                  font=("Arial", 8), foreground="red")
            conn_label.pack(pady=(0, 5))
            
            self.cube_canvases.append({
                "canvas": canvas,
                "square": square_id
            })
            self.status_labels.append(status_label)
            self.time_labels.append(time_label)
            self.conn_labels.append(conn_label)
            
            # Делаем все колонки одинаковой ширины
            grid_frame.columnconfigure(col, weight=1)
        
        # Нижняя панель - улучшенная легенда статусов
        legend_frame = ttk.LabelFrame(main_frame, text="Легенда статусов")
        legend_frame.pack(fill="x", pady=(0, 10))
        
        # Контейнер для легенды с сеткой
        legend_container = ttk.Frame(legend_frame)
        legend_container.pack(pady=15, padx=15)
        
        # Создаем сетку 3x2 для красивого расположения
        legend_items = [
            (2, "#e74c3c", "Красный - Не понимаю"),
            (5, "#FFFFFF", "Белый - Устал"),  # Белый с черной рамкой
            (3, "#90ee90", "Салатовый - Готов"),
            (1, "#2ecc71", "Зеленый - Завершил"),
            (6, "#3498db", "Синий - Вопрос"),
            (4, "#f1c40f", "Желтый - Выполняю")
        ]
        
        # Создаем 2 строки по 3 элемента
        for row in range(2):
            row_frame = ttk.Frame(legend_container)
            row_frame.pack(pady=8)
            
            for col in range(3):
                idx = row * 3 + col
                if idx < len(legend_items):
                    face_num, color, text = legend_items[idx]
                    
                    item_frame = ttk.Frame(row_frame)
                    item_frame.pack(side="left", padx=25, fill="x", expand=True)
                    
                    # Фрейм для квадрата
                    color_frame = ttk.Frame(item_frame)
                    color_frame.pack(side="left", padx=(0, 8))
                    
                    # Создаем красивый квадрат с тенью
                    if face_num == 5:  # Белый цвет - с черной рамкой
                        square_canvas = tk.Canvas(color_frame, width=28, height=28, 
                                                 bg="white", highlightthickness=0)
                        square_canvas.pack()
                        # Черная рамка для белого квадрата
                        square_canvas.create_rectangle(2, 2, 26, 26, 
                                                      fill=color, 
                                                      outline="black", 
                                                      width=2)
                    else:
                        square_canvas = tk.Canvas(color_frame, width=28, height=28, 
                                                 bg="white", highlightthickness=0)
                        square_canvas.pack()
                        # Квадрат с тенью
                        square_canvas.create_rectangle(4, 4, 28, 28, 
                                                      fill="#d0d0d0",  # Серая тень
                                                      outline="")
                        square_canvas.create_rectangle(2, 2, 26, 26, 
                                                      fill=color, 
                                                      outline="black", 
                                                      width=1)
                    
                    # Текст легенды
                    ttk.Label(item_frame, text=text, font=("Arial", 10)).pack(side="left")
        
        # Статистика активности
        stats_frame = ttk.LabelFrame(main_frame, text="Активность сервера")
        stats_frame.pack(fill="x", pady=(0, 10))
        
        self.active_label = ttk.Label(stats_frame, 
                                     text="Активных кубов: 0/10", 
                                     font=("Arial", 10))
        self.active_label.pack(side="left", padx=20)
        
        self.server_status_label = ttk.Label(stats_frame, 
                                           text="Сервер: Остановлен", 
                                           font=("Arial", 10), foreground="red")
        self.server_status_label.pack(side="left", padx=20)
        
        # Статус бар
        self.status_var = tk.StringVar(value="🔄 Сервер не запущен")
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                              relief="sunken", anchor="w")
        status_bar.pack(side="bottom", fill="x")
    
    class RequestHandler(BaseHTTPRequestHandler):
        def __init__(self, request, client_address, server):
            self.server_obj = server.server_obj
            super().__init__(request, client_address, server)
        
        def do_GET(self):
            if self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                html = f"""<!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>Cube Server</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; margin: 20px; }}
                        .status {{ font-size: 24px; margin: 20px; }}
                        .info {{ margin: 10px; }}
                        .ip {{ font-family: monospace; background: #f0f0f0; padding: 5px; }}
                    </style>
                </head>
                <body>
                    <h1>🎲 Cube Server</h1>
                    <div class="status">Сервер работает ✅</div>
                    <p class="info">Для подключения ESP укажите этот IP в коде:</p>
                    <p class="ip">{self.server_obj.computer_ip}</p>
                    <p class="info">ESP будет отправлять данные на: http://{self.server_obj.computer_ip}:8000/data</p>
                </body>
                </html>"""
                
                self.wfile.write(html.encode('utf-8'))
                
            elif self.path == '/data':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                
                response = {
                    "status": "server_running",
                    "server_ip": self.server_obj.computer_ip,
                    "total_cubes": self.server_obj.total_cubes,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"404 Not Found")
        
        def do_POST(self):
            if self.path == '/data':
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    
                    data = json.loads(post_data.decode('utf-8'))
                    cube_id = data.get('cube_id', 1)
                    
                    if 1 <= cube_id <= self.server_obj.total_cubes:
                        idx = cube_id - 1
                        
                        # Получаем новый статус (только 1-6, остальное игнорируем)
                        new_status = data.get('face_number', 0)
                        if new_status not in self.server_obj.face_info:
                            new_status = 0  # Игнорируем ребро/угол
                        
                        old_status = self.server_obj.cubes_state[idx]
                        
                        # Обновляем данные
                        self.server_obj.cube_data[idx] = data
                        self.server_obj.cubes_last_update[idx] = time.time()
                        
                        # Если статус изменился и это валидный статус (1-6)
                        if old_status != new_status and new_status in self.server_obj.face_info:
                            current_time = time.time()
                            
                            # Добавляем время старого статуса к общему (если это был валидный статус)
                            if old_status in self.server_obj.face_info and old_status in self.server_obj.status_start_time[idx]:
                                elapsed = current_time - self.server_obj.status_start_time[idx][old_status]
                                self.server_obj.total_time_in_status[idx][old_status] += elapsed
                            
                            # Начинаем отсчет для нового статуса
                            self.server_obj.status_start_time[idx][new_status] = current_time
                            self.server_obj.cubes_state[idx] = new_status
                            
                            # Добавляем в историю (только валидные статусы)
                            self.server_obj.history[idx].append({
                                "time": datetime.now().strftime("%H:%M:%S"),
                                "face": data.get('face', 'Неизвестно'),
                                "face_number": new_status,
                                "status": self.server_obj.face_info[new_status]["status"],
                                "ip": data.get('ip', ''),
                                "mac": data.get('mac', '')
                            })
                            self.server_obj.total_counts[new_status] += 1
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        
                        response = {
                            "status": "received",
                            "cube_id": cube_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                    else:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        
                        response = {"error": f"cube_id должен быть от 1 до {self.server_obj.total_cubes}"}
                        self.wfile.write(json.dumps(response).encode('utf-8'))
                        
                except json.JSONDecodeError as e:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    response = {"error": f"Invalid JSON: {str(e)}"}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    response = {"error": f"Server error: {str(e)}"}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"404 Not Found")
        
        def log_message(self, format, *args):
            pass
    
    def start_server(self):
        try:
            class CustomHTTPServer(HTTPServer):
                def __init__(self, server_address, handler_class, server_obj):
                    super().__init__(server_address, handler_class)
                    self.server_obj = server_obj
            
            handler = lambda request, client_address, server: self.RequestHandler(
                request, client_address, server
            )
            
            self.http_server = CustomHTTPServer(('0.0.0.0', self.server_port), handler, self)
            
            print("=" * 50)
            print(f"Сервер запущен!")
            print(f"Доступ по адресу: http://{self.computer_ip}:{self.server_port}")
            print("=" * 50)
            
            self.server_running = True
            self.http_server.serve_forever()
            
        except OSError as e:
            if e.errno == 98:
                print(f"Ошибка: Порт {self.server_port} уже используется")
                messagebox.showerror("Ошибка", f"Порт {self.server_port} уже используется.")
            elif e.errno == 13:
                print(f"Ошибка: Нет прав для запуска на порту {self.server_port}")
                messagebox.showerror("Ошибка", f"Нет прав для запуска сервера на порту {self.server_port}.")
            else:
                print(f"Ошибка запуска сервера: {e}")
                messagebox.showerror("Ошибка", f"Не удалось запустить сервер: {e}")
            self.server_running = False
            
        except Exception as e:
            print(f"Ошибка запуска сервера: {e}")
            self.server_running = False
    
    def stop_server(self):
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()
            print("Сервер остановлен")
        
        self.server_running = False
    
    def toggle_server(self):
        if not self.server_running:
            self.server_thread = threading.Thread(target=self.start_server, daemon=True)
            self.server_thread.start()
            
            self.root.after(500, self.update_server_status)
            self.start_btn.config(text="⏸️ Остановить сервер")
            
        else:
            self.stop_server()
            self.start_btn.config(text="▶️ Запустить сервер")
            self.server_status_label.config(text="Сервер: Остановлен", foreground="red")
            self.status_var.set("⏸️ Сервер остановлен")
    
    def update_server_status(self):
        if self.server_running:
            self.server_status_label.config(text="Сервер: Запущен", foreground="green")
            self.status_var.set(f"✅ Сервер запущен на {self.computer_ip}:{self.server_port}")
        else:
            self.root.after(500, self.update_server_status)
    
    def update_display(self):
        active_cubes = 0
        
        for i in range(self.total_cubes):
            data = self.cube_data.get(i, {})
            
            if data:
                face_num = data.get('face_number', 0)
                last_update = self.cubes_last_update[i]
                
                if time.time() - last_update > 10:
                    color = "#95a5a6"
                    display_status = "Нет связи"
                    conn_status = "Неактивен"
                    self.cubes_state[i] = 0
                else:
                    if face_num in self.face_info:
                        color = self.face_info[face_num]["color"]
                        display_status = self.face_info[face_num]["status"]
                        self.cubes_state[i] = face_num
                    else:
                        color = "#95a5a6"
                        display_status = "Нет данных"
                        self.cubes_state[i] = 0
                    
                    conn_status = "Активен"
                    active_cubes += 1
                
                time_diff = int(time.time() - last_update)
                if time_diff < 60:
                    time_str = f"{time_diff} сек назад"
                else:
                    time_str = datetime.fromtimestamp(last_update).strftime("%H:%M:%S")
                
                ip_info = data.get('ip', '')
                if ip_info:
                    conn_status = f"Активен ({ip_info})"
                
            else:
                color = "#95a5a6"
                display_status = "Нет данных"
                conn_status = "Не подключен"
                time_str = ""
                self.cubes_state[i] = 0
            
            canvas_data = self.cube_canvases[i]
            canvas_data["canvas"].itemconfig(canvas_data["square"], fill=color)
            self.status_labels[i].config(text=display_status)
            self.time_labels[i].config(text=time_str)
            self.conn_labels[i].config(
                text=conn_status,
                foreground="green" if "Активен" in conn_status else "red"
            )
        
        self.active_label.config(text=f"Активных кубов: {active_cubes}/10")
        self.root.after(self.update_interval, self.update_display)
    
    def show_detailed_stats(self):
        """Показать детальную статистику по времени (без ребро/угол)"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Детальная статистика по времени")
        stats_window.geometry("900x700")
        
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Вкладка 1: Сводная статистика
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="📊 Сводная статистика")
        
        summary_text = tk.Text(summary_frame, wrap="word", font=("Consolas", 10))
        summary_scrollbar = ttk.Scrollbar(summary_frame, orient="vertical", command=summary_text.yview)
        summary_text.configure(yscrollcommand=summary_scrollbar.set)
        
        summary_scrollbar.pack(side="right", fill="y")
        summary_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        # Генерируем сводную статистику (только статусы 1-6)
        summary_lines = []
        summary_lines.append("=" * 70)
        summary_lines.append("СВОДНАЯ СТАТИСТИКА ПО ВРЕМЕНИ")
        summary_lines.append("=" * 70)
        summary_lines.append("")
        
        # Активные кубы
        active_cubes = sum(1 for i in range(self.total_cubes) 
                          if self.cube_data.get(i) and 
                          time.time() - self.cubes_last_update[i] <= 10)
        
        summary_lines.append(f"Активных кубов: {active_cubes}/{self.total_cubes}")
        summary_lines.append("")
        
        # Общее время по статусам (только 1-6)
        summary_lines.append("ОБЩЕЕ ВРЕМЯ ПО СТАТУСАМ:")
        
        total_times = defaultdict(float)
        for cube_id in range(self.total_cubes):
            for status, t in self.total_time_in_status[cube_id].items():
                if status in self.face_info:  # Только статусы 1-6
                    total_times[status] += t
        
        # Добавляем текущее время для активных статусов
        current_time = time.time()
        for cube_id in range(self.total_cubes):
            current_status = self.cubes_state[cube_id]
            if current_status in self.face_info and current_status in self.status_start_time[cube_id]:
                elapsed = current_time - self.status_start_time[cube_id][current_status]
                total_times[current_status] += elapsed
        
        # Сортируем по убыванию времени
        sorted_times = []
        for status, total_time in total_times.items():
            if status in self.face_info and total_time > 0:
                sorted_times.append((status, total_time))
        
        sorted_times.sort(key=lambda x: x[1], reverse=True)
        
        if sorted_times:
            total_all_time = sum(t for _, t in sorted_times)
            for status, total_time in sorted_times:
                status_name = self.face_info[status]["status"]
                percentage = (total_time / total_all_time * 100) if total_all_time > 0 else 0
                summary_lines.append(f"  {status_name}: {self.format_time(total_time)} ({percentage:.1f}%)")
        else:
            summary_lines.append("  Нет данных о времени в статусах")
        
        summary_lines.append("")
        
        # Частота статусов
        if self.total_counts:
            summary_lines.append("ЧАСТОТА ИЗМЕНЕНИЙ СТАТУСОВ:")
            valid_counts = [(s, c) for s, c in self.total_counts.items() if s in self.face_info]
            if valid_counts:
                for status, count in sorted(valid_counts, key=lambda x: x[1], reverse=True)[:5]:
                    status_name = self.face_info[status]["status"]
                    summary_lines.append(f"  {status_name}: {count} раз")
        
        summary_text.insert("1.0", "\n".join(summary_lines))
        summary_text.config(state="disabled")
        
        # Вкладки для каждого куба (только активные кубы)
        active_cube_ids = [i for i in range(self.total_cubes) 
                          if self.cube_data.get(i) and 
                          time.time() - self.cubes_last_update[i] <= 10]
        
        for cube_id in active_cube_ids:
            cube_frame = ttk.Frame(notebook)
            notebook.add(cube_frame, text=f"Куб {cube_id+1}")
            
            cube_text = tk.Text(cube_frame, wrap="word", font=("Consolas", 10))
            cube_scrollbar = ttk.Scrollbar(cube_frame, orient="vertical", command=cube_text.yview)
            cube_text.configure(yscrollcommand=cube_scrollbar.set)
            
            cube_scrollbar.pack(side="right", fill="y")
            cube_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            
            cube_lines = []
            cube_lines.append("=" * 70)
            cube_lines.append(f"СТАТИСТИКА КУБА #{cube_id+1}")
            cube_lines.append("=" * 70)
            cube_lines.append("")
            
            # Информация о кубе
            data = self.cube_data[cube_id]
            current_status = self.cubes_state[cube_id]
            
            if current_status in self.face_info:
                cube_lines.append(f"Текущий статус: {self.face_info[current_status]['status']}")
            else:
                cube_lines.append("Текущий статус: Нет данных")
            
            cube_lines.append(f"IP адрес: {data.get('ip', 'Неизвестно')}")
            cube_lines.append(f"Последнее обновление: {datetime.fromtimestamp(self.cubes_last_update[cube_id]).strftime('%H:%M:%S')}")
            cube_lines.append("")
            
            # Время в каждом статусе (только 1-6)
            cube_lines.append("ВРЕМЯ В КАЖДОМ СТАТУСЕ:")
            
            # Собираем все времена для этого куба
            status_times = {}
            current_time = time.time()
            
            for status in range(1, 7):  # Только статусы 1-6
                total_time = self.total_time_in_status[cube_id].get(status, 0.0)
                
                # Добавляем текущее время если это активный статус
                if status == current_status and status in self.status_start_time[cube_id]:
                    current_elapsed = current_time - self.status_start_time[cube_id][status]
                    total_time += current_elapsed
                
                if total_time > 0:
                    status_times[status] = total_time
            
            # Сортируем по убыванию времени
            sorted_cube_times = sorted(status_times.items(), key=lambda x: x[1], reverse=True)
            
            if sorted_cube_times:
                total_cube_time = sum(t for _, t in sorted_cube_times)
                
                for status, time_spent in sorted_cube_times:
                    status_name = self.face_info[status]["status"]
                    percentage = (time_spent / total_cube_time * 100) if total_cube_time > 0 else 0
                    cube_lines.append(f"  {status_name}: {self.format_time(time_spent)} ({percentage:.1f}%)")
            else:
                cube_lines.append("  Нет данных о времени в статусах")
            
            cube_lines.append("")
            
            # История изменений (только последние 5 записей)
            cube_lines.append("ИСТОРИЯ ИЗМЕНЕНИЙ:")
            if self.history[cube_id]:
                # Берем только последние 5 записей
                recent_history = self.history[cube_id][-5:]
                for record in recent_history:
                    cube_lines.append(f"  [{record['time']}] → {record['status']}")
            else:
                cube_lines.append("  История пуста")
            
            cube_text.insert("1.0", "\n".join(cube_lines))
            cube_text.config(state="disabled")
        
        # Если нет активных кубов, добавляем заглушку
        if not active_cube_ids:
            no_data_frame = ttk.Frame(notebook)
            notebook.add(no_data_frame, text="Нет данных")
            
            no_data_label = ttk.Label(no_data_frame, 
                                     text="Нет активных кубов для отображения статистики",
                                     font=("Arial", 12))
            no_data_label.pack(expand=True, padx=20, pady=20)
        
        # Кнопка экспорта
        def export_stats():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"cube_stats_{timestamp}.json"
            
            try:
                data = {
                    "export_time": datetime.now().isoformat(),
                    "server_ip": self.computer_ip,
                    "total_cubes": self.total_cubes,
                    "cube_data": {},
                    "time_stats": {}
                }
                
                for cube_id in range(self.total_cubes):
                    data["cube_data"][cube_id] = self.cube_data.get(cube_id, {})
                    # Экспортируем только время для статусов 1-6
                    filtered_times = {k: v for k, v in self.total_time_in_status[cube_id].items() 
                                     if k in self.face_info}
                    data["time_stats"][cube_id] = dict(filtered_times)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                messagebox.showinfo("Успех", f"Статистика экспортирована в файл:\n{filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать данные:\n{str(e)}")
        
        ttk.Button(stats_window, text="📥 Экспорт статистики", 
                  command=export_stats).pack(pady=10)

def main():
    root = tk.Tk()
    app = CubeServer(root)
    
    messagebox.showinfo("Cube Server", 
        f"Программа запущена!\n\n"
        f"Ваш IP адрес: {app.computer_ip}\n"
        f"Порт сервера: {app.server_port}\n\n"
        f"Для подключения ESP измените в его коде строку:\n"
        f'const char* serverIP = "{app.computer_ip}";')
    
    root.mainloop()

if __name__ == "__main__":
    main()
