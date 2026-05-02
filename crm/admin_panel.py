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

    push_tag = ft.TextField(label="Тег", width=250, hint_text="Например: РД")
    push_delay = ft.TextField(label="Задержка в минутах", width=250, value="15")
    push_text = ft.TextField(
        label="Текст автопуша",
        width=500,
        multiline=True,
        min_lines=3,
        max_lines=5
    )
    push_status = ft.Text("", color="#a8c7fa")
    push_list = ft.Column(spacing=8)

    def load_pushes():
        push_list.controls.clear()

        rows = db_query(
            """
            SELECT id, tag, text, delay_minutes, enabled
            FROM auto_push_rules
            ORDER BY id DESC
            """,
            fetch=True
        ) or []

        for rule_id, tag, text, delay, enabled in rows:
            push_list.controls.append(
                ft.Container(
                    bgcolor="#17212b",
                    border_radius=10,
                    padding=12,
                    content=ft.Column([
                        ft.Text(f"Тег: {tag} | Через: {delay} мин | {'Вкл' if enabled else 'Выкл'}", weight="bold"),
                        ft.Text(text, size=13),
                        ft.Row([
                            ft.TextButton(
                                "Удалить",
                                on_click=lambda e, rid=rule_id: delete_push(rid)
                            )
                        ])
                    ])
                )
            )

    def add_push(e):
        tag = (push_tag.value or "").strip()
        text = (push_text.value or "").strip()

        try:
            delay = int(push_delay.value or "0")
        except:
            delay = 0

        if not tag or not text:
            push_status.value = "⚠️ Укажи тег и текст"
            e.page.update()
            return

        db_query(
            """
            INSERT INTO auto_push_rules (tag, text, delay_minutes, enabled)
            VALUES (?, ?, ?, 1)
            """,
            (tag, text, delay)
        )

        push_status.value = "✅ Автопуш добавлен"
        push_tag.value = ""
        push_text.value = ""
        push_delay.value = "15"

        load_pushes()
        e.page.update()

    def delete_push(rule_id):
        db_query("DELETE FROM auto_push_rules WHERE id=?", (rule_id,))
        load_pushes()

    load_pushes()

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
            ft.Text("Автопуши по тегам", size=20, weight="bold"),
            ft.Text("Когда менеджер присваивает тег, CRM сама отправит сообщение через указанное время.",
                    color="#707579"),

            ft.Row([
                push_tag,
                push_delay,
            ]),

            push_text,

            ft.FilledButton(
                "Добавить автопуш",
                on_click=add_push
            ),

            push_status,

            ft.Divider(),

            ft.Text("Активные автопуши", size=16, weight="bold"),
            push_list,

            ft.Text("Позже сюда добавим пуши, рассылки и авто-теги", color="#707579")
        ])
    )