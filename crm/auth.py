import flet as ft
import crm

USER_LOGIN = "admin"
USER_PASS = "adeola2026"

async def main(page: ft.Page):
    page.title = "Adeola CRM - Вход"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 600
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    login_field = ft.TextField(label="Логин", width=300, border_radius=10)
    pass_field = ft.TextField(label="Пароль", width=300, password=True, can_reveal_password=True, border_radius=10)
    error_text = ft.Text("", color="red")

    async def login_click(e):
        if login_field.value == USER_LOGIN and pass_field.value == USER_PASS:
            page.controls.clear()
            await crm.show_crm(page)
        else:
            error_text.value = "Неверный логин или пароль!"
            page.update()

    page.add(
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK_PERSON_ROUNDED, size=80, color="#a8c7fa"),
                ft.Text("Adeola CRM PRO", size=24, weight="bold"),
                login_field, pass_field, error_text,
                ft.ElevatedButton("Войти", width=300, height=50, on_click=login_click, bgcolor="#2b5278", color="white"),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40, bgcolor="#17212b", border_radius=20
        )
    )

if __name__ == "__main__":
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,
        host="0.0.0.0",
        port=8550
    )