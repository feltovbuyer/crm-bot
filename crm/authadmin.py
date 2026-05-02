import flet as ft
import os
from dotenv import load_dotenv

load_dotenv()

ADMIN_ADMINOV = os.getenv("ADMIN_ADMINOV", "1234")


def open_admin_login(page, on_success):
    pwd_input = ft.TextField(
        password=True,
        can_reveal_password=True,
        hint_text="Пароль админки",
        width=300
    )

    def submit(e):
        if pwd_input.value == ADMIN_ADMINOV:
            dlg.open = False
            on_success()
            page.update()
        else:
            pwd_input.error_text = "Неверный пароль"
            page.update()

    def close():
        dlg.open = False
        page.update()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Вход в админку"),
        content=pwd_input,
        actions=[
            ft.TextButton("Закрыть", on_click=lambda e: close()),
            ft.TextButton("Войти", on_click=submit)
        ]
    )

    page.overlay.append(dlg)
    dlg.open = True
    page.update()