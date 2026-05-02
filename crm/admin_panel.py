import flet as ft
from admin_stats import build_stats_row
from traffic_router import init_traffic_router


def create_admin_ui(on_back, db_query):
    init_traffic_router(db_query)

    total_text = ft.Text("0", size=28, weight="bold")
    regs_text = ft.Text("0", size=28, weight="bold")
    deps_text = ft.Text("0", size=28, weight="bold")
    blocked_text = ft.Text("0", size=28, weight="bold")
    broadcasts_text = ft.Text("0", size=28, weight="bold")

    push_tag = ft.TextField(label="Тег", width=250, hint_text="Например: РД")
    push_delay = ft.TextField(label="Задержка в минутах", width=250, value="15")
    push_text = ft.TextField(label="Текст автопуша", width=500, multiline=True, min_lines=3, max_lines=5)
    push_status = ft.Text("", color="#a8c7fa")
    push_filter = ft.TextField(label="Фильтр по тегу", width=250, hint_text="Например: РД")
    push_list = ft.ListView(expand=True, spacing=8, auto_scroll=False)

    staff_login = ft.TextField(label="Логин менеджера", width=250)
    staff_password = ft.TextField(label="Пароль", width=250)
    staff_status = ft.Text("", color="#a8c7fa")
    staff_list = ft.Column(spacing=8)

    router_channel = ft.TextField(label="Канал", width=120, hint_text="П4")
    router_token = ft.TextField(label="Токен бота", width=360, password=True)
    router_geo = ft.Dropdown(label="Гео/тег гео", width=220, options=[])
    router_funnel = ft.TextField(label="Воронка", width=220, hint_text="Парагвай")
    router_status = ft.Text("", color="#a8c7fa")

    router_channels_list = ft.Column(spacing=8)
    router_rules_list = ft.Column(spacing=8)

    router_channel_dd = ft.Dropdown(label="Канал", width=220, options=[])
    router_staff_dd = ft.Dropdown(label="Менеджер", width=220, options=[])
    router_percent = ft.TextField(label="%", width=90, value="100")
    router_manager_tag = ft.TextField(label="Тег менеджера", width=180, hint_text="135")

    funnel_name = ft.TextField(label="Название воронки", width=180, hint_text="Парагвай")
    funnel_step = ft.TextField(label="Шаг", width=80, value="1")
    funnel_tag = ft.TextField(label="Тег шага", width=160, hint_text="1 шаг")
    funnel_next = ft.TextField(label="Следующий шаг", width=140, hint_text="2 или FINISH")
    funnel_text = ft.TextField(label="Текст шага", width=520, multiline=True, min_lines=2, max_lines=5)
    funnel_steps_list = ft.Column(spacing=8)

    tag_name = ft.TextField(label="Тег", width=180, hint_text="Парагвай")
    tag_color = ft.TextField(label="Цвет", width=160, hint_text="#2196F3")
    tag_list = ft.Column(spacing=8)

    main_content = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)
    pushes_content = ft.Column(expand=True)
    router_content = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO)

    admin_container = ft.Container(
        visible=False,
        expand=True,
        bgcolor="#0e1621",
        padding=25
    )

    db_query("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'manager',
            active INTEGER DEFAULT 1
        )
    """)

    def refresh_stats(e=None):
        total_text.value = str(db_query("SELECT COUNT(*) FROM users", fetch=True)[0][0])
        regs_text.value = str(db_query("SELECT COUNT(*) FROM users WHERE tags LIKE '%Регистрация%'", fetch=True)[0][0])
        deps_text.value = str(db_query("SELECT COUNT(*) FROM users WHERE tags LIKE '%Депозит%'", fetch=True)[0][0])
        blocked_text.value = str(db_query("SELECT COUNT(*) FROM users WHERE is_blocked=1", fetch=True)[0][0])
        broadcasts_text.value = str(db_query("SELECT COUNT(*) FROM messages WHERE sender='admin'", fetch=True)[0][0])
        if e:
            e.page.update()

    def load_pushes(e=None):
        push_list.controls.clear()
        filter_tag = (push_filter.value or "").strip()

        if filter_tag:
            rows = db_query("""
                SELECT id, tag, text, delay_minutes, enabled
                FROM auto_push_rules
                WHERE tag LIKE ?
                ORDER BY id DESC
            """, (f"%{filter_tag}%",), fetch=True) or []
        else:
            rows = db_query("""
                SELECT id, tag, text, delay_minutes, enabled
                FROM auto_push_rules
                ORDER BY id DESC
            """, fetch=True) or []

        for rule_id, tag, text, delay, enabled in rows:
            preview = text[:120] + ("..." if len(text) > 120 else "")

            push_list.controls.append(
                ft.Container(
                    bgcolor="#17212b",
                    border_radius=10,
                    padding=10,
                    content=ft.Row([
                        ft.Text(tag or "-", width=150, weight="bold"),
                        ft.Text(f"{delay} мин", width=100),
                        ft.Text(preview, expand=True, size=13),
                        ft.Text("Вкл" if enabled else "Выкл", width=60),
                        ft.TextButton("Удалить", on_click=lambda e, rid=rule_id: delete_push(rid)),
                    ])
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

        db_query("""
            INSERT INTO auto_push_rules (tag, text, delay_minutes, enabled)
            VALUES (?, ?, ?, 1)
        """, (tag, text, delay))

        push_status.value = "✅ Автопуш добавлен"
        push_tag.value = ""
        push_text.value = ""
        push_delay.value = "15"

        load_pushes()
        e.page.update()

    def delete_push(rule_id):
        db_query("DELETE FROM auto_push_rules WHERE id=?", (rule_id,))
        load_pushes()

    def load_staff(e=None):
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
                        ft.TextButton("Удалить", on_click=lambda e, sid=staff_id: delete_staff(sid))
                    ])
                )
            )

        if e:
            e.page.update()

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
            load_router()
            e.page.update()

        except Exception as ex:
            staff_status.value = f"❌ Ошибка: {ex}"
            e.page.update()

    def delete_staff(staff_id):
        db_query("DELETE FROM staff WHERE id=?", (staff_id,))
        db_query("DELETE FROM traffic_distribution WHERE staff_id=?", (staff_id,))
        load_staff()
        load_router()

    def load_router(e=None):
        router_channels_list.controls.clear()
        router_rules_list.controls.clear()

        channels = db_query("""
            SELECT id, channel, geo, funnel, active
            FROM traffic_channels
            ORDER BY id DESC
        """, fetch=True) or []

        router_channel_dd.options = [
            ft.dropdown.Option(str(cid), f"{channel} | {geo} | {funnel}")
            for cid, channel, geo, funnel, active in channels
            if active
        ]

        staff_rows = db_query(
            "SELECT id, login FROM staff WHERE active=1 ORDER BY login",
            fetch=True
        ) or []

        router_staff_dd.options = [
            ft.dropdown.Option(str(sid), login)
            for sid, login in staff_rows
        ]

        for cid, channel, geo, funnel, active in channels:
            router_channels_list.controls.append(
                ft.Container(
                    bgcolor="#17212b",
                    border_radius=10,
                    padding=10,
                    content=ft.Row([
                        ft.Text(f"{channel} | {geo} | {funnel} | {'вкл' if active else 'выкл'}", expand=True),
                        ft.TextButton("Удалить", on_click=lambda e, x=cid: delete_router_channel(x))
                    ])
                )
            )

        rules = db_query("""
            SELECT d.id, c.channel, s.login, d.percent, d.manager_tag, d.active
            FROM traffic_distribution d
            LEFT JOIN traffic_channels c ON c.id=d.channel_id
            LEFT JOIN staff s ON s.id=d.staff_id
            ORDER BY d.id DESC
        """, fetch=True) or []

        for rid, channel, login, percent, tag, active in rules:
            router_rules_list.controls.append(
                ft.Container(
                    bgcolor="#17212b",
                    border_radius=10,
                    padding=10,
                    content=ft.Row([
                        ft.Text(f"{channel} → {login} | {percent}% | тег: {tag} | {'вкл' if active else 'выкл'}", expand=True),
                        ft.TextButton("Удалить", on_click=lambda e, x=rid: delete_router_rule(x))
                    ])
                )
            )

        if e:
            e.page.update()

    def load_funnel_steps(e=None):
        funnel_steps_list.controls.clear()

        rows = db_query("""
            SELECT id, funnel, step_order, text, tag, next_step, active
            FROM funnel_steps
            ORDER BY funnel ASC, step_order ASC
        """, fetch=True) or []

        for step_id, funnel, step_order, text, tag, next_step, active in rows:
            preview = (text or "")[:100] + ("..." if text and len(text) > 100 else "")

            funnel_steps_list.controls.append(
                ft.Container(
                    bgcolor="#17212b",
                    border_radius=10,
                    padding=10,
                    content=ft.Row([
                        ft.Text(funnel or "-", width=130, weight="bold"),
                        ft.Text(f"Шаг {step_order}", width=80),
                        ft.Text(tag or "-", width=120),
                        ft.Text(next_step or "-", width=90),
                        ft.Text(preview, expand=True, size=13),
                        ft.TextButton("Удалить", on_click=lambda e, x=step_id: delete_funnel_step(x))
                    ])
                )
            )

        if e:
            e.page.update()

    def add_funnel_step(e):
        name = (funnel_name.value or "").strip()
        text = (funnel_text.value or "").strip()
        tag = (funnel_tag.value or "").strip()
        next_step = (funnel_next.value or "").strip()

        try:
            step_order = int(funnel_step.value or "1")
        except:
            step_order = 1

        if not name or not text:
            router_status.value = "⚠️ Введи название воронки и текст шага"
            e.page.update()
            return

        if not tag:
            tag = f"{step_order} шаг"

        if not next_step:
            next_step = str(step_order + 1)

        db_query("""
            INSERT INTO funnel_steps
            (funnel, step_order, text, tag, next_step, active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (name, step_order, text, tag, next_step))

        funnel_step.value = str(step_order + 1)
        funnel_text.value = ""
        funnel_tag.value = ""
        funnel_next.value = ""

        router_status.value = "✅ Шаг воронки добавлен"
        load_funnel_steps()
        e.page.update()

    def delete_funnel_step(step_id):
        db_query("DELETE FROM funnel_steps WHERE id=?", (step_id,))
        load_funnel_steps()

    def load_tags(e=None):
        tag_list.controls.clear()

        rows = db_query(
            "SELECT id, tag, color FROM tag_colors ORDER BY id DESC",
            fetch=True
        ) or []
        router_geo.options = [
            ft.dropdown.Option(tag)
            for _, tag, color in rows
        ]

        for tag_id, tag, color in rows:
            tag_list.controls.append(
                ft.Container(
                    bgcolor="#17212b",
                    border_radius=10,
                    padding=10,
                    content=ft.Row([
                        ft.Text(tag or "-", expand=True, color=color or None, weight="bold"),
                        ft.Text(color or "-", width=120),
                        ft.TextButton("Удалить", on_click=lambda e, x=tag_id: delete_tag_color(x))
                    ])
                )
            )

        if e:
            e.page.update()

    def add_tag_color(e):
        tag = (tag_name.value or "").strip()
        color = (tag_color.value or "").strip()

        if not tag:
            router_status.value = "⚠️ Введи тег"
            e.page.update()
            return

        if not color:
            color = "#4da3ff"

        db_query("""
            INSERT OR REPLACE INTO tag_colors (tag, color)
            VALUES (?, ?)
        """, (tag, color))

        tag_name.value = ""
        tag_color.value = ""
        router_status.value = "✅ Тег добавлен"

        load_tags()
        e.page.update()

    def delete_tag_color(tag_id):
        db_query("DELETE FROM tag_colors WHERE id=?", (tag_id,))
        load_tags()

    def add_router_channel(e):
        channel = (router_channel.value or "").strip()
        token = (router_token.value or "").strip()
        geo = (router_geo.value or "").strip()
        funnel = (router_funnel.value or "").strip()

        if not channel or not token or not geo:
            router_status.value = "⚠️ Канал, токен и гео обязательны"
            e.page.update()
            return

        db_query("""
            INSERT OR REPLACE INTO traffic_channels
            (channel, bot_token, geo, funnel, active)
            VALUES (?, ?, ?, ?, 1)
        """, (channel, token, geo, funnel))

        router_channel.value = ""
        router_token.value = ""
        router_geo.value = ""
        router_funnel.value = ""
        router_status.value = "✅ Канал добавлен. Чтобы бот запустился — restart crm"

        load_router()
        e.page.update()

    def add_router_rule(e):
        if not router_channel_dd.value or not router_staff_dd.value:
            router_status.value = "⚠️ Выбери канал и менеджера"
            e.page.update()
            return

        try:
            percent = int(router_percent.value or "0")
        except:
            percent = 0

        if percent < 0:
            percent = 0

        tag = (router_manager_tag.value or "").strip()

        db_query("""
            INSERT INTO traffic_distribution
            (channel_id, staff_id, percent, manager_tag, access_mode, active)
            VALUES (?, ?, ?, ?, 'percent', 1)
        """, (
            int(router_channel_dd.value),
            int(router_staff_dd.value),
            percent,
            tag
        ))

        router_percent.value = "100"
        router_manager_tag.value = ""
        router_status.value = "✅ Распределение добавлено"

        load_router()
        e.page.update()

    def delete_router_channel(channel_id):
        db_query("DELETE FROM traffic_channels WHERE id=?", (channel_id,))
        db_query("DELETE FROM traffic_distribution WHERE channel_id=?", (channel_id,))
        load_router()

    def delete_router_rule(rule_id):
        db_query("DELETE FROM traffic_distribution WHERE id=?", (rule_id,))
        load_router()

    def show_main(e=None):
        admin_container.content = main_content
        if e:
            e.page.update()

    def show_pushes(e=None):
        load_pushes()
        admin_container.content = pushes_content
        if e:
            e.page.update()

    def show_router(e=None):
        load_router()
        load_funnel_steps()
        load_tags()
        admin_container.content = router_content
        if e:
            e.page.update()

    refresh_stats()
    load_staff()
    load_router()
    load_funnel_steps()
    load_tags()

    main_content.controls = [
        ft.TextButton("← Назад", on_click=on_back),

        ft.Text("Админ панель", size=24, weight="bold"),
        ft.Text("Статистика CRM", size=14, color="#707579"),

        ft.Divider(),

        build_stats_row(total_text, regs_text, deps_text, blocked_text, broadcasts_text),

        ft.FilledButton("Обновить статистику", on_click=refresh_stats),

        ft.Divider(),

        ft.Row([
            ft.Text("Автопуши по тегам", size=20, weight="bold", expand=True),
            ft.FilledButton("Открыть список автопушей", on_click=show_pushes),
        ]),

        ft.Text(
            "Когда менеджер присваивает тег, CRM сама отправит сообщение через указанное время.",
            color="#707579"
        ),

        ft.Row([push_tag, push_delay]),
        push_text,
        ft.FilledButton("Добавить автопуш", on_click=add_push),
        push_status,

        ft.Divider(),

        ft.Row([
            ft.Text("Трафик-роутер", size=20, weight="bold", expand=True),
            ft.FilledButton("Открыть", on_click=show_router),
        ]),

        ft.Text(
            "Боты, гео, воронки и распределение лидов по уже созданным менеджерам.",
            color="#707579"
        ),

        ft.Divider(),

        ft.Text("Аккаунты менеджеров", size=20, weight="bold"),
        ft.Text("Создай логин/пароль для входа в CRM", color="#707579"),

        ft.Row([staff_login, staff_password]),
        ft.FilledButton("Создать аккаунт", on_click=add_staff),
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

        ft.Container(content=push_list, expand=True),
    ]

    router_content.controls = [
        ft.Row([
            ft.TextButton("← Назад в админку", on_click=show_main),
            ft.Text("Трафик-роутер", size=22, weight="bold"),
        ]),

        ft.Divider(),

        ft.Text("Боты / Каналы", size=18, weight="bold"),
        ft.Row([router_channel, router_geo, router_funnel]),
        router_token,
        ft.FilledButton("Добавить канал", on_click=add_router_channel),
        router_status,

        ft.Text("Список каналов", size=16, weight="bold"),
        router_channels_list,

        ft.Divider(),

        ft.Text("Распределение по менеджерам", size=18, weight="bold"),
        ft.Row([router_channel_dd, router_staff_dd, router_percent, router_manager_tag]),
        ft.FilledButton("Добавить распределение", on_click=add_router_rule),

        ft.Text("Список распределений", size=16, weight="bold"),
        router_rules_list,

        ft.Divider(),

        ft.Text("Воронки", size=18, weight="bold"),
        ft.Text(
            "Название воронки должно совпадать с полем 'Воронка' у канала.",
            color="#707579"
        ),

        ft.Row([funnel_name, funnel_step, funnel_tag, funnel_next]),
        funnel_text,
        ft.FilledButton("Добавить шаг воронки", on_click=add_funnel_step),

        ft.Text("Список шагов воронок", size=16, weight="bold"),
        funnel_steps_list,

        ft.Divider(),

        ft.Text("Теги и цвета", size=18, weight="bold"),
        ft.Text("Создай тег и цвет. Например: Парагвай / #2196F3", color="#707579"),

        ft.Row([tag_name, tag_color]),
        ft.FilledButton("Добавить тег", on_click=add_tag_color),

        ft.Text("Список тегов", size=16, weight="bold"),
        tag_list,
    ]

    admin_container.content = main_content
    return admin_container