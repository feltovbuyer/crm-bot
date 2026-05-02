import os
import flet as ft
import sqlite3
import crm
import os
from dotenv import load_dotenv
os.environ["FLET_SECRET_KEY"] = "adeola_upload_secret_2026"

load_dotenv()
USER_LOGIN = os.getenv("ADMIN_LOGIN")
USER_PASS = os.getenv("ADMIN_PASSWORD")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def main(page: ft.Page):
    page.title = "Adeola CRM - Вход"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 600
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    login_field = ft.TextField(label="Логин", width=300, border_radius=10)
    pass_field = ft.TextField(
        label="Пароль",
        width=300,
        password=True,
        can_reveal_password=True,
        border_radius=10,
    )
    error_text = ft.Text("", color="red")

    async def login_click(e):
        staff_user = check_staff_login(login_field.value, pass_field.value)

        if staff_user or (login_field.value == USER_LOGIN and pass_field.value == USER_PASS):
            page.controls.clear()
            page.update()
            await crm.show_crm(page)
        else:
            error_text.value = "Неверный логин или пароль!"
            page.update()

    page.controls.clear()
    page.add(
        ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.LOCK_PERSON_ROUNDED, size=80, color="#a8c7fa"),
                    ft.Text("Adeola CRM PRO", size=24, weight="bold"),
                    login_field,
                    pass_field,
                    error_text,
                    ft.ElevatedButton(
                        "Войти",
                        width=300,
                        height=50,
                        on_click=login_click,
                        bgcolor="#2b5278",
                        color="white",
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,
            bgcolor="#17212b",
            border_radius=20,
        )
    )
    page.update()

    def check_staff_login(login, password):
        conn = sqlite3.connect("crm.db")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT UNIQUE,
                password TEXT,
                role TEXT DEFAULT 'manager',
                active INTEGER DEFAULT 1
            )
        """)

        cursor.execute(
            "SELECT id, role FROM staff WHERE login=? AND password=? AND active=1",
            (login, password)
        )

        user = cursor.fetchone()
        conn.close()
        return user


if __name__ == "__main__":
    ft.run(
        main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=8550,
        upload_dir=UPLOAD_DIR,
    )