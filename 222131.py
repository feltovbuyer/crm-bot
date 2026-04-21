import sys
import pyautogui
import time
import json
import os
from datetime import datetime
import threading
import hashlib
import random

# Проверка наличия tkinter
try:
    import tkinter as tk
    from tkinter import ttk, messagebox

    TKINTER_AVAILABLE = True
except ImportError:
    print("Tkinter не установлен. Используем консольный режим.")
    TKINTER_AVAILABLE = False
    print("Для установки Tkinter выполните: pip install tk")

# Настройки
SCROLL_STEP = -82  # Отрицательное значение для прокрутки вниз
REPEAT_DELAY = 0
CHAT_CLICK_COORDS = (202, 274)
SCROLL_COUNT = 5  # Количество скроллов для перехода к следующему чату

# Глобальные переменные
running = False
stop_flag = False
click_coords_history = []
settings_file = "auto_sender_settings.json"


class ConsoleInterface:
    """Консольный интерфейс если Tkinter недоступен"""

    def __init__(self):
        self.stop_char = "/"
        self.scroll_step = SCROLL_STEP
        self.repeat_delay = REPEAT_DELAY
        self.chat_coords = CHAT_CLICK_COORDS
        self.input_coords = (584, 1016)
        self.send_coords = (686, 910)
        self.scroll_speed = 0.5
        self.max_scroll_attempts = 3
        self.check_duplicates = True
        self.record_clicks = True
        self.auto_stop_scroll = True
        self.scroll_count = SCROLL_COUNT  # Количество скроллов между чатами
        self.click_delay = 0.3  # Задержка между кликами

        self.load_settings()

    def show_menu(self):
        """Показать главное меню"""
        while True:
            print("\n" + "=" * 50)
            print("AUTO SENDER v2.0 - Консольный режим")
            print("НАВИГАЦИЯ С ПОМОЩЬЮ СКРОЛЛА МЫШИ")
            print("=" * 50)
            print("1. Настройки")
            print("2. Запустить рассылку")
            print("3. Записать координаты мыши")
            print("4. Показать историю координат")
            print("5. Сохранить настройки")
            print("6. Выход")

            choice = input("Выберите действие: ")

            if choice == "1":
                self.show_settings()
            elif choice == "2":
                self.run_sending()
            elif choice == "3":
                self.record_current_coords()
            elif choice == "4":
                self.show_coords_history()
            elif choice == "5":
                self.save_settings()
            elif choice == "6":
                break

    def show_settings(self):
        """Показать настройки"""
        print("\n--- НАСТРОЙКИ ---")
        print(f"1. Символ остановки: {self.stop_char}")
        print(f"2. Шаг прокрутки: {self.scroll_step}")
        print(f"3. Количество скроллов между чатами: {self.scroll_count}")
        print(f"4. Задержка между кликами: {self.click_delay}")
        print(f"5. Задержка повторения: {self.repeat_delay}")
        print(f"6. Координаты чата: {self.chat_coords}")
        print(f"7. Координаты ввода: {self.input_coords}")
        print(f"8. Координаты отправки: {self.send_coords}")
        print(f"9. Скорость прокрутки: {self.scroll_speed}")
        print(f"10. Макс. попыток прокрутки: {self.max_scroll_attempts}")
        print(f"11. Проверка дубликатов: {self.check_duplicates}")
        print(f"12. Запись координат: {self.record_clicks}")
        print(f"13. Авто-стоп прокрутки: {self.auto_stop_scroll}")

        choice = input("\nВведите номер настройки для изменения (или Enter для возврата): ")
        if choice:
            self.edit_setting(choice)

    def edit_setting(self, choice):
        """Изменить настройку"""
        try:
            if choice == "1":
                self.stop_char = input("Введите символ остановки: ")
            elif choice == "2":
                self.scroll_step = int(input("Введите шаг прокрутки: "))
            elif choice == "3":
                self.scroll_count = int(input("Введите количество скроллов между чатами: "))
            elif choice == "4":
                self.click_delay = float(input("Введите задержку между кликами: "))
            elif choice == "5":
                self.repeat_delay = float(input("Введите задержку повторения: "))
            elif choice == "6":
                x = int(input("Введите X координату чата: "))
                y = int(input("Введите Y координату чата: "))
                self.chat_coords = (x, y)
            elif choice == "7":
                x = int(input("Введите X координату ввода: "))
                y = int(input("Введите Y координату ввода: "))
                self.input_coords = (x, y)
            elif choice == "8":
                x = int(input("Введите X координату отправки: "))
                y = int(input("Введите Y координату отправки: "))
                self.send_coords = (x, y)
            elif choice == "9":
                self.scroll_speed = float(input("Введите скорость прокрутки: "))
            elif choice == "10":
                self.max_scroll_attempts = int(input("Введите макс. попыток прокрутки: "))
            elif choice == "11":
                self.check_duplicates = input("Проверять дубликаты? (y/n): ").lower() == 'y'
            elif choice == "12":
                self.record_clicks = input("Записывать координаты? (y/n): ").lower() == 'y'
            elif choice == "13":
                self.auto_stop_scroll = input("Авто-стоп при прокрутке? (y/n): ").lower() == 'y'
        except ValueError:
            print("Ошибка ввода!")

    def record_current_coords(self):
        """Записать текущие координаты мыши"""
        x, y = pyautogui.position()
        click_coords_history.append((x, y))
        print(f"Записаны координаты: ({x}, {y})")

    def show_coords_history(self):
        """Показать историю координат"""
        if not click_coords_history:
            print("История координат пуста")
            return

        print("\n--- ИСТОРИЯ КООРДИНАТ ---")
        for i, (x, y) in enumerate(click_coords_history, 1):
            print(f"{i}. ({x}, {y})")

    def save_settings(self):
        """Сохранить настройки"""
        settings = {
            "stop_char": self.stop_char,
            "scroll_step": self.scroll_step,
            "scroll_count": self.scroll_count,
            "click_delay": self.click_delay,
            "repeat_delay": self.repeat_delay,
            "chat_coords": self.chat_coords,
            "input_coords": self.input_coords,
            "send_coords": self.send_coords,
            "scroll_speed": self.scroll_speed,
            "max_scroll_attempts": self.max_scroll_attempts,
            "check_duplicates": self.check_duplicates,
            "record_clicks": self.record_clicks,
            "auto_stop_scroll": self.auto_stop_scroll
        }

        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=4)

        print("Настройки сохранены!")

    def load_settings(self):
        """Загрузить настройки"""
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r") as f:
                    settings = json.load(f)

                self.stop_char = settings.get("stop_char", "/")
                self.scroll_step = settings.get("scroll_step", SCROLL_STEP)
                self.scroll_count = settings.get("scroll_count", SCROLL_COUNT)
                self.click_delay = settings.get("click_delay", 0.3)
                self.repeat_delay = settings.get("repeat_delay", REPEAT_DELAY)
                self.chat_coords = tuple(settings.get("chat_coords", CHAT_CLICK_COORDS))
                self.input_coords = tuple(settings.get("input_coords", (584, 1016)))
                self.send_coords = tuple(settings.get("send_coords", (686, 910)))
                self.scroll_speed = settings.get("scroll_speed", 0.5)
                self.max_scroll_attempts = settings.get("max_scroll_attempts", 3)
                self.check_duplicates = settings.get("check_duplicates", True)
                self.record_clicks = settings.get("record_clicks", True)
                self.auto_stop_scroll = settings.get("auto_stop_scroll", True)

                print("Настройки загружены!")
            except Exception as e:
                print(f"Ошибка загрузки настроек: {e}")

    def run_sending(self):
        """Запустить рассылку"""
        global running, stop_flag

        if running:
            print("Рассылка уже запущена!")
            return

        print("\nЗапуск рассылки...")
        print("Навигация осуществляется скроллом мыши!")
        print("Нажмите Ctrl+C для остановки")

        running = True
        stop_flag = False

        try:
            self.main_loop()
        except KeyboardInterrupt:
            print("\nОстановлено пользователем")
        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            running = False
            stop_flag = False

    def main_loop(self):
        """Основной цикл рассылки - навигация только скроллом мыши"""
        global stop_flag

        scroll_attempts = 0
        last_chat_hash = None

        while not stop_flag:
            try:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Цикл #{scroll_attempts + 1}")

                # Проверка дубликатов
                if self.check_duplicates:
                    current_hash = self.get_chat_content_hash()
                    if current_hash == last_chat_hash:
                        print("Дубликат чата, делаем скролл...")
                        self.perform_scrolls(self.scroll_count)
                        scroll_attempts += 1
                        continue
                    last_chat_hash = current_hash

                # 1. Клик по чату (координаты не меняются)
                print(f"Клик в чат: {self.chat_coords}")
                pyautogui.click(self.chat_coords[0], self.chat_coords[1])
                time.sleep(self.click_delay)

                if self.record_clicks:
                    click_coords_history.append(self.chat_coords)

                # 2. Клик в поле ввода
                print(f"Клик в поле ввода: {self.input_coords}")
                pyautogui.click(self.input_coords[0], self.input_coords[1])
                time.sleep(self.click_delay)

                if self.record_clicks:
                    click_coords_history.append(self.input_coords)

                # 3. Ввод сообщения
                print(f"Ввод сообщения: '{self.stop_char}'")
                pyautogui.typewrite(self.stop_char.strip())
                time.sleep(self.click_delay)

                # 4. Отправка
                print(f"Клик отправки: {self.send_coords}")
                pyautogui.click(self.send_coords[0], self.send_coords[1])
                time.sleep(self.click_delay)

                if self.record_clicks:
                    click_coords_history.append(self.send_coords)

                # 5. Возврат курсора к позиции чата
                pyautogui.moveTo(self.chat_coords[0], self.chat_coords[1])
                time.sleep(0.5)

                # 6. Проверка возможности прокрутки
                if self.auto_stop_scroll and scroll_attempts >= self.max_scroll_attempts:
                    print("Достигнут лимит прокрутки. Остановка.")
                    break

                # 7. Прокрутка для перехода к следующему чату
                print(f"Прокрутка для перехода к следующему чату ({self.scroll_count} раз)")
                self.perform_scrolls(self.scroll_count)

                scroll_attempts += 1

                # Задержка между циклами
                if self.repeat_delay > 0:
                    time.sleep(self.repeat_delay)

            except KeyboardInterrupt:
                raise
            except Exception as e:
                print(f"Ошибка в цикле: {e}")
                time.sleep(5)

    def perform_scrolls(self, count):
        """Выполнить несколько скроллов"""
        for i in range(count):
            pyautogui.scroll(self.scroll_step)
            time.sleep(self.scroll_speed)

    def get_chat_content_hash(self):
        """Получить хэш содержимого чата (упрощенная версия)"""
        return hashlib.md5(str(random.random()).encode()).hexdigest()


class AutoSenderGUI:
    """GUI версия (если Tkinter доступен)"""

    def __init__(self, root):
        self.root = root
        self.root.title("Auto Sender v2.0 - НАВИГАЦИЯ СКРОЛЛОМ")
        self.root.geometry("650x450")

        # Переменные
        self.stop_char = tk.StringVar(value="/")
        self.scroll_step = tk.IntVar(value=SCROLL_STEP)
        self.scroll_count = tk.IntVar(value=SCROLL_COUNT)
        self.click_delay = tk.DoubleVar(value=0.3)
        self.repeat_delay = tk.DoubleVar(value=REPEAT_DELAY)
        self.chat_x = tk.IntVar(value=CHAT_CLICK_COORDS[0])
        self.chat_y = tk.IntVar(value=CHAT_CLICK_COORDS[1])
        self.input_x = tk.IntVar(value=584)
        self.input_y = tk.IntVar(value=1016)
        self.send_x = tk.IntVar(value=686)
        self.send_y = tk.IntVar(value=910)

        self.load_settings()
        self.setup_ui()

    def setup_ui(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Заголовок
        ttk.Label(main_frame, text="НАВИГАЦИЯ ОСУЩЕСТВЛЯЕТСЯ СКРОЛЛОМ МЫШИ",
                  font=("Arial", 10, "bold"), foreground="blue").grid(row=0, column=0, columnspan=3, pady=5)

        # Настройки
        row = 1
        ttk.Label(main_frame, text="Символ остановки:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.stop_char, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)

        row += 1
        ttk.Label(main_frame, text="Шаг прокрутки:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.scroll_step, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)

        row += 1
        ttk.Label(main_frame, text="Кол-во скроллов:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.scroll_count, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)

        row += 1
        ttk.Label(main_frame, text="Задержка кликов:").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.click_delay, width=10).grid(row=row, column=1, sticky=tk.W, pady=5)

        # Координаты чата
        row += 1
        ttk.Label(main_frame, text="Координаты чата (X, Y):").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.chat_x, width=8).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.chat_y, width=8).grid(row=row, column=2, sticky=tk.W, pady=5)

        # Координаты ввода
        row += 1
        ttk.Label(main_frame, text="Координаты ввода (X, Y):").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.input_x, width=8).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.input_y, width=8).grid(row=row, column=2, sticky=tk.W, pady=5)

        # Координаты отправки
        row += 1
        ttk.Label(main_frame, text="Координаты отправки (X, Y):").grid(row=row, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.send_x, width=8).grid(row=row, column=1, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.send_y, width=8).grid(row=row, column=2, sticky=tk.W, pady=5)

        # Кнопки
        row += 1
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=20)

        ttk.Button(btn_frame, text="Запуск", command=self.start_sending, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Стоп", command=self.stop_sending, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Записать координаты", command=self.record_coordinates, width=20).pack(side=tk.LEFT,
                                                                                                          padx=5)
        ttk.Button(btn_frame, text="Сохранить настройки", command=self.save_settings, width=20).pack(side=tk.LEFT,
                                                                                                     padx=5)

        # Логи
        row += 1
        ttk.Label(main_frame, text="Лог выполнения:").grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=5)

        row += 1
        self.log_text = tk.Text(main_frame, height=10, width=70)
        self.log_text.grid(row=row, column=0, columnspan=3, pady=10)

        scrollbar = ttk.Scrollbar(self.log_text, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_text.insert(tk.END, log_entry + "\n")
        self.log_text.see(tk.END)
        print(log_entry)

    def record_coordinates(self):
        x, y = pyautogui.position()
        coord_type = input("Тип координат (1-чат, 2-ввод, 3-отправка): ")
        if coord_type == "1":
            self.chat_x.set(x)
            self.chat_y.set(y)
        elif coord_type == "2":
            self.input_x.set(x)
            self.input_y.set(y)
        elif coord_type == "3":
            self.send_x.set(x)
            self.send_y.set(y)

        self.log_message(f"Записаны координаты: ({x}, {y})")
        click_coords_history.append((x, y))

    def start_sending(self):
        self.log_message("Запуск рассылки...")
        self.log_message("Навигация осуществляется скроллом мыши!")
        # Запуск в потоке
        thread = threading.Thread(target=self.run_sending, daemon=True)
        thread.start()

    def stop_sending(self):
        global stop_flag
        stop_flag = True
        self.log_message("Остановка...")

    def run_sending(self):
        """Основной цикл рассылки для GUI"""
        global stop_flag

        chat_coords = (self.chat_x.get(), self.chat_y.get())
        input_coords = (self.input_x.get(), self.input_y.get())
        send_coords = (self.send_x.get(), self.send_y.get())
        message = self.stop_char.get()
        scroll_count = self.scroll_count.get()
        scroll_step = self.scroll_step.get()

        while not stop_flag:
            try:
                # Клик по чату
                pyautogui.click(*chat_coords)
                time.sleep(self.click_delay.get())

                # Клик в поле ввода
                pyautogui.click(*input_coords)
                time.sleep(self.click_delay.get())

                # Ввод сообщения
                pyautogui.typewrite(message)
                time.sleep(self.click_delay.get())

                # Отправка
                pyautogui.click(*send_coords)
                time.sleep(self.click_delay.get())

                # Возврат к чату
                pyautogui.moveTo(*chat_coords)
                time.sleep(0.5)

                # Прокрутка для перехода к следующему чату
                self.log_message(f"Прокрутка ({scroll_count} раз)")
                for i in range(scroll_count):
                    pyautogui.scroll(scroll_step)
                    time.sleep(0.3)

                # Задержка между циклами
                if self.repeat_delay.get() > 0:
                    time.sleep(self.repeat_delay.get())

            except Exception as e:
                self.log_message(f"Ошибка: {e}")
                time.sleep(1)

        self.log_message("Рассылка остановлена")

    def save_settings(self):
        settings = {
            "stop_char": self.stop_char.get(),
            "scroll_step": self.scroll_step.get(),
            "scroll_count": self.scroll_count.get(),
            "click_delay": self.click_delay.get(),
            "repeat_delay": self.repeat_delay.get(),
            "chat_coords": (self.chat_x.get(), self.chat_y.get()),
            "input_coords": (self.input_x.get(), self.input_y.get()),
            "send_coords": (self.send_x.get(), self.send_y.get())
        }

        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=4)

        self.log_message("Настройки сохранены")

    def load_settings(self):
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r") as f:
                    settings = json.load(f)

                self.stop_char.set(settings.get("stop_char", "/"))
                self.scroll_step.set(settings.get("scroll_step", SCROLL_STEP))
                self.scroll_count.set(settings.get("scroll_count", SCROLL_COUNT))
                self.click_delay.set(settings.get("click_delay", 0.3))
                self.repeat_delay.set(settings.get("repeat_delay", REPEAT_DELAY))

                chat_coords = settings.get("chat_coords", CHAT_CLICK_COORDS)
                self.chat_x.set(chat_coords[0])
                self.chat_y.set(chat_coords[1])

                input_coords = settings.get("input_coords", (584, 1016))
                self.input_x.set(input_coords[0])
                self.input_y.set(input_coords[1])

                send_coords = settings.get("send_coords", (686, 910))
                self.send_x.set(send_coords[0])
                self.send_y.set(send_coords[1])

            except Exception as e:
                print(f"Ошибка загрузки: {e}")


def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("AUTO SENDER v2.0")
    print("НАВИГАЦИЯ ОСУЩЕСТВЛЯЕТСЯ СКРОЛЛОМ МЫШИ")
    print("=" * 60)

    if TKINTER_AVAILABLE:
        try:
            root = tk.Tk()
            app = AutoSenderGUI(root)
            root.mainloop()
        except Exception as e:
            print(f"Ошибка GUI: {e}")
            print("Переход в консольный режим...")
            console = ConsoleInterface()
            console.show_menu()
    else:
        console = ConsoleInterface()
        console.show_menu()


if __name__ == "__main__":
    main()