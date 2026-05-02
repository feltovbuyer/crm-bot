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
        regs_text.value = str(db_query("SELECT COUNT(*) FROM users WHERE tags LIKE '%Регистрация%'", fetch=True)[0][0])
        deps_text.value = str(db_query("SELECT COUNT(*) FROM users WHERE tags LIKE '%Депозит%'", fetch=True)[0][0])
        blocked_text.value = str(db_query("SELECT COUNT(*) FROM users WHERE is_blocked=1", fetch=True)[0][0])
        broadcasts_text.value = str(db_query("SELECT COUNT(*) FROM messages WHERE sender='admin'", fetch=True)[0][0])

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

    push_filter = ft.TextField(
        label="Фильтр по тегу",
        width=250,
        hint_text="Например: РД"
    )

    push_list = ft.ListView(
        expand=True,
        spacing=8,
        auto_scroll=False
    )

    def load_pushes(e=None):
        push_list.controls.clear()

        filter_tag = (push_filter.value or "").strip()

        if filter_tag:
            rows = db_query(
                """
                SELECT id, tag, text, delay_minutes, enabled
                FROM auto_push_rules
                WHERE tag LIKE ?
                ORDER BY id DESC
                """,
                (f"%{filter_tag}%",),
                fetch=True
            ) or []
        else:
            rows = db_query(
                """
                SELECT id, tag, text, delay_minutes, enabled
                FROM auto_push_rules
                ORDER BY id DESC
                """,
                fetch=True
            ) or []

        for rule_id, tag, text, delay, enabled in rows:
            preview = text[:120] + ("..." if len(text) > 120 else "")

            push_list.controls.append(
                ft.Container(
                    bgcolor="#17212b",
                    border_radius=10,
                    padding=10,
                    content=ft.Row(
                        [
                            ft.Text(tag or "-", width=150, weight="bold"),
                            ft.Text(f"{delay} мин", width=100),
                            ft.Text(preview, expand=True, size=13),
                            ft.Text("Вкл" if enabled else "Выкл", width=60),
                            ft.TextButton(
                                "Удалить",
                                on_click=lambda e, rid=rule_id: delete_push(rid)
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                )
            )

        if e:
            e.page.update()

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

    staff_login = ft.TextField(label="Логин менеджера", width=250)
    staff_password = ft.TextField(label="Пароль", width=250)
    staff_status = ft.Text("", color="#a8c7fa")
    staff_list = ft.Column(spacing=8)

    db_query("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'manager',
            active INTEGER DEFAULT 1
        )
    """)

    def load_staff():
        staff_list.controls.clear()

        rows = db_query(
            "SELECT id, login, role, active FROM staff ORDER BY id DESC",
            fetch=True
        ) or []

        for staff_id, login, role, active in rows:
            staff_list.controls.append(
                ft.Container(
                    bgcolor="#17212b",
                    border_radius=10,
                    padding=10,
                    content=ft.Row([
                        ft.Text(f"{login} | {role} | {'активен' if active else 'выключен'}", expand=True),
                        ft.TextButton(
                            "Удалить",
                            on_click=lambda e, sid=staff_id: delete_staff(sid)
                        )
                    ])
                )
            )

    def add_staff(e):
        login = (staff_login.value or "").strip()
        password = (staff_password.value or "").strip()

        if not login or not password:
            staff_status.value = "⚠️ Введи логин и пароль"
            e.page.update()
            return

        try:
            db_query(
                "INSERT INTO staff (login, password, role, active) VALUES (?, ?, 'manager', 1)",
                (login, password)
            )

            staff_status.value = "✅ Аккаунт создан"
            staff_login.value = ""
            staff_password.value = ""

            load_staff()
            e.page.update()

        except Exception as ex:
            staff_status.value = f"❌ Ошибка: {ex}"
            e.page.update()

    def delete_staff(staff_id):
        db_query("DELETE FROM staff WHERE id=?", (staff_id,))
        load_staff()

    load_staff()

    main_content = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO
    )

    pushes_content = ft.Column(
        expand=True
    )

    admin_container = ft.Container(
        visible=False,
        expand=True,
        bgcolor="#0e1621",
        padding=25
    )

    def show_main(e=None):
        admin_container.content = main_content
        if e:
            e.page.update()

    def show_pushes(e=None):
        load_pushes()
        admin_container.content = pushes_content
        if e:
            e.page.update()

    main_content.controls = [
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

        ft.Row([
            ft.Text("Автопуши по тегам", size=20, weight="bold", expand=True),
            ft.FilledButton(
                "Открыть список автопушей",
                on_click=show_pushes
            ),
        ]),

        ft.Text(
            "Когда менеджер присваивает тег, CRM сама отправит сообщение через указанное время.",
            color="#707579"
        ),

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

        ft.Text("Аккаунты менеджеров", size=20, weight="bold"),
        ft.Text("Создай логин/пароль для входа в CRM", color="#707579"),

        ft.Row([
            staff_login,
            staff_password,
        ]),

        ft.FilledButton(
            "Создать аккаунт",
            on_click=add_staff
        ),

        staff_status,

        ft.Text("Список аккаунтов", size=16, weight="bold"),
        staff_list,
    ]

    pushes_content.controls = [
        ft.Row([
            ft.TextButton("← Назад в админку", on_click=show_main),
            ft.Text("Список автопушей", size=22, weight="bold"),
        ]),

        ft.Row([
            push_filter,
            ft.FilledButton("Найти", on_click=load_pushes),
            ft.TextButton(
                "Сбросить",
                on_click=lambda e: (
                    setattr(push_filter, "value", ""),
                    load_pushes(e)
                )
            ),
        ]),

        ft.Container(
            padding=10,
            bgcolor="#17212b",
            border_radius=8,
            content=ft.Row([
                ft.Text("Тег", width=150, weight="bold"),
                ft.Text("Время", width=100, weight="bold"),
                ft.Text("Текст", expand=True, weight="bold"),
                ft.Text("Статус", width=60, weight="bold"),
                ft.Text("", width=80),
            ])
        ),

        ft.Container(
            content=push_list,
            expand=True,
        )
    ]

    admin_container.content = main_content
    return admin_container