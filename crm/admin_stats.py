import flet as ft


def stat_card(title, text_control):
    return ft.Container(
        width=180,
        height=95,
        bgcolor="#17212b",
        border_radius=12,
        padding=15,
        content=ft.Column([
            ft.Text(title, size=13, color="#707579"),
            text_control,
        ])
    )


def build_stats_row(total_text, regs_text, deps_text, blocked_text, broadcasts_text):
    return ft.Row([
        stat_card("Всего лидов", total_text),
        stat_card("Регистрации", regs_text),
        stat_card("Депозиты", deps_text),
        stat_card("Блокнули бота", blocked_text),
        stat_card("Сообщений админа", broadcasts_text),
    ], spacing=15)