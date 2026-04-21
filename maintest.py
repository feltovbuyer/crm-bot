import pyautogui
import time

# Настройки
SCROLL_STEP = -100  # Шаг прокрутки вниз (отрицательное значение для прокрутки вниз)
REPEAT_DELAY = 0  # Задержка между повторениями в секундах
CHAT_CLICK_COORDS = (250, 250)  # Начальная координата первого чата


def write_message():
    """Написать сообщение, но не отправлять"""
    message = '/'
    # Просто пишем сообщение
    pyautogui.typewrite(message.strip())
    time.sleep(0.2)


def main_loop():
    """Основной бесконечный цикл выполнения скрипта"""

    while True:
        try:
            print("=" * 50)

            # Шаг 1: Клик по чату (фиксированная начальная координата)
            print(f"Клик по чату: {CHAT_CLICK_COORDS}")
            pyautogui.click(CHAT_CLICK_COORDS[0], CHAT_CLICK_COORDS[1])
            time.sleep(1)

            # Шаг 2: Клик по полю ввода (фиксированная координата)
            print("Клик по полю ввода: (584, 1016)")
            pyautogui.click(754, 1016)
            time.sleep(1.7)

            # Шаг 3: Написать сообщение (но не отправлять)
            print("Написание сообщения '/'")
            write_message()

            # Шаг 4: Клик для отправки (фиксированная координата)
            print("Клик для отправки: (686, 910)")
            pyautogui.click(686, 910)
            time.sleep(1.6)

            # Шаг 5: Возвращаемся в исходное положение (координаты первого чата)
            print(f"Возврат к начальной позиции чата: {CHAT_CLICK_COORDS}")
            pyautogui.moveTo(CHAT_CLICK_COORDS[0], CHAT_CLICK_COORDS[1])
            time.sleep(1)

            # Шаг 6: Прокрутка вниз (скроллом мыши на той же позиции)
            print(f"Прокрутка вниз на {SCROLL_STEP} пикселей")
            pyautogui.scroll(SCROLL_STEP)
            time.sleep(REPEAT_DELAY)

            # Пауза перед следующим циклом
            time.sleep(1)

        except KeyboardInterrupt:
            print("\nСкрипт остановлен пользователем")
            break
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            # Пауза при ошибке перед продолжением
            time.sleep(5)


if __name__ == "__main__":
    print("Скрипт запущен. Нажмите Ctrl+C для остановки.")
    print(f"Шаг прокрутки: {SCROLL_STEP} пикселей")
    print("Порядок действий:")
    print("1. Клик по чату (фиксированная начальная координата)")
    print("2. Клик по полю ввода (фиксированная координата)")
    print("3. Написать '/' (не отправлять)")
    print("4. Клик для отправки (фиксированная координата)")
    print("5. Возврат курсора к начальному чату")
    print("6. Прокрутка вниз (для перехода к следующему чату)")
    print("=" * 50)
    main_loop()