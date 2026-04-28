import flet as ft
from admin_stats import build_stats_row


def create_admin_ui(on_back, db_query):
    total_text = ft.Text("0", size=28, weight="bold")
    regs_text = ft.Text("0", size=28, weight="bold")
    deps_text = ft.Text("0", size=28, weight="bold")
    blocked_text = ft.Text("0", size=28, weight="bold")
    broadcasts_text = ft.Text("0", size=28, weight="bold")

    def refresh_stats(e=None):
        total_text.value = str(db_query("SELECT COUNT(*) FROM users", fetch=True)[0][0])

        regs_text.value = str(db_query(
            "SELECT COUNT(*) FROM users WHERE tags LIKE '%Регистрация%'",
            fetch=True
        )[0][0])

        deps_text.value = str(db_query(
            "SELECT COUNT(*) FROM users WHERE tags LIKE '%Депозит%'",
            fetch=True
        )[0][0])

        blocked_text.value = str(db_query(
            "SELECT COUNT(*) FROM users WHERE is_blocked=1",
            fetch=True
        )[0][0])

        broadcasts_text.value = str(db_query(
            "SELECT COUNT(*) FROM messages WHERE sender='admin'",
            fetch=True
        )[0][0])

    refresh_stats()

    return ft.Container(
        visible=False,
        expand=True,
        bgcolor="#0e1621",
        padding=25,
        content=ft.Column([
            ft.TextButton("← Назад", on_click=on_back),

            ft.Text("Админ панель", size=24, weight="bold"),
            ft.Text("Статистика CRM", size=14, color="#707579"),

            ft.Divider(),

            build_stats_row(
                total_text,
                regs_text,
                deps_text,
                blocked_text,
                broadcasts_text
            ),

            ft.FilledButton(
                "Обновить статистику",
                on_click=lambda e: (
                    refresh_stats(),
                    e.page.update()
                )
            ),

            ft.Divider(),

            ft.Text("Позже сюда добавим пуши, рассылки и авто-теги", color="#707579")
        ])
    )