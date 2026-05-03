import flet as ft
import json

# --- ОБЪЕКТЫ ПОИСКА ---
search_field = ft.TextField(
    hint_text="ID или Имя",
    expand=2, height=40, text_size=12,
    content_padding=10, border_radius=10,
    bgcolor="#242f3d", border_color="#333d49"
)

tag_search_field = ft.TextField(
    hint_text="Тег",
    expand=1, height=40, text_size=12,
    content_padding=10, border_radius=10,
    bgcolor="#242f3d", border_color="#333d49"
)


def update_left_panel(user_list, db_query, state, page, select_user):
    if "folder" not in state: state["folder"] = "Рега"

    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            geos = json.load(f).get("geos", {})
    except:
        geos = {}

    def refresh_list_only(target_container):
        tag_colors = {}

        try:
            tag_color_rows = db_query(
                "SELECT tag, color FROM tag_colors",
                fetch=True
            ) or []

            tag_colors = {
                tag: color for tag, color in tag_color_rows
            }
        except:
            tag_colors = {}

        sql_base = "SELECT user_id, full_name, channel, tags, is_blocked FROM users WHERE 1=1"
        params = []

        if search_field.value:
            sql_base += " AND (full_name LIKE ? OR CAST(user_id AS TEXT) LIKE ?)"
            val = f"%{search_field.value}%"
            params.extend([val, val])

        if tag_search_field.value:
            sql_base += " AND tags LIKE ?"
            params.append(f"%{tag_search_field.value}%")

        # --- ЛОГИКА ВОРОНКИ ---
        if state["folder"] == "Рега":
            # Ищем и "Рега" и "Регистрация", но исключаем депы
            sql_base += """ AND (tags LIKE '%Рега%' OR tags LIKE '%Регистрация%') 
                            AND tags NOT LIKE '%ФД%' 
                            AND tags NOT LIKE '%РД%' 
                            AND is_blocked=0 AND tags NOT LIKE '%403%'"""
        elif state["folder"] == "ФД":
            sql_base += " AND tags LIKE '%ФД%' AND is_blocked=0 AND tags NOT LIKE '%403%'"
        elif state["folder"] == "РД":
            sql_base += " AND tags LIKE '%РД%' AND is_blocked=0 AND tags NOT LIKE '%403%'"
        elif state["folder"] == "403":
            sql_base += " AND (is_blocked=1 OR tags LIKE '%403%')"
        elif state["folder"] == "all":
            sql_base += " AND is_blocked=0 AND tags NOT LIKE '%403%'"

        sql_base += " ORDER BY last_ts DESC"
        ls = db_query(sql_base, params, fetch=True) or []

        target_container.controls = []
        for l in ls:
            uid, name, channel, tags_str, is_bl = l
            last_m = db_query(
                "SELECT text, time, sender, is_read FROM messages WHERE user_id=? ORDER BY id DESC LIMIT 1", (uid,),
                fetch=True)
            txt, tm, unread_msg, needs_reply = "Нет сообщений", "", False, False
            if last_m:
                txt, tm, sender, is_read = last_m[0]
                unread_msg = (sender == 'user' and is_read == 0)
                needs_reply = (sender == 'user')

            chips = []
            for t in tags_str.split(','):
                t = t.strip()
                if not t: continue
                # цвет из tag_colors
                tag_color = tag_colors.get(t)

                # цвет из custom_tags
                custom_tag_row = db_query(
                    "SELECT color FROM custom_tags WHERE name=? AND active=1",
                    (t,),
                    fetch=True
                )
                custom_tag_color = custom_tag_row[0][0] if custom_tag_row else None

                # цвет из гео
                geo_color = next((g['color'] for g in geos.values() if g['label'] == t), None)

                # финальный цвет
                bg_color = custom_tag_color or tag_color or geo_color or "#2b5278"

                bg_color = tag_color if tag_color else "#2b5278"
                chips.append(ft.Container(
                    content=ft.Text(t, size=10, color="white", weight="bold"),
                    padding=ft.padding.symmetric(horizontal=5, vertical=2),
                    bgcolor=bg_color, border_radius=4,
                    border=ft.border.all(1, "white30") if tag_color else None
                ))

            target_container.controls.append(ft.ListTile(
                leading=ft.Container(
                    content=ft.Text(channel or "Г1", size=11, weight="bold"),
                    width=38, height=38, bgcolor="#37474f", border_radius=19,
                    alignment=ft.alignment.Alignment(0, 0),
                    border=ft.border.all(2, ft.Colors.RED_ACCENT) if needs_reply else None
                ),
                title=ft.Row([
                    ft.Container(width=10, height=10, bgcolor="red", border_radius=5) if unread_msg else ft.Container(),
                    ft.Text(name or str(uid), size=17, weight="bold", color="white"),
                    ft.Icon(ft.Icons.BLOCK, size=16, color="red") if is_bl or "403" in tags_str else ft.Container()
                ], spacing=8),
                subtitle=ft.Column([
                    ft.Text(txt, size=14, max_lines=1, color="white" if unread_msg else "#cfd8dc",
                            weight="bold" if unread_msg else "normal"),
                    ft.Row(chips, wrap=True, spacing=3) if chips else ft.Container()
                ], spacing=2),
                trailing=ft.Text(tm, size=11),
                on_click=lambda e, u=uid: page.run_task(select_user, u),
                selected=(state["active_id"] == uid)
            ))

        try:
            target_container.update()
        except:
            pass

    # Ищем контейнер
    leads_view = None
    if len(user_list.controls) > 3:
        leads_view = user_list.controls[3]

    def set_f(f):
        state["folder"] = f
        update_left_panel(user_list, db_query, state, page, select_user)
        page.update()

    # Создаем кнопки заново при каждом вызове для надежности стилей
    folder_tabs = ft.Row([
        ft.TextButton("Рега", on_click=lambda _: set_f("Рега"),
                      style=ft.ButtonStyle(color="white" if state["folder"] == "Рега" else "#707579")),
        ft.TextButton("ФД", on_click=lambda _: set_f("ФД"),
                      style=ft.ButtonStyle(color="white" if state["folder"] == "ФД" else "#707579")),
        ft.TextButton("РД", on_click=lambda _: set_f("РД"),
                      style=ft.ButtonStyle(color="white" if state["folder"] == "РД" else "#707579")),
        ft.TextButton("403", on_click=lambda _: set_f("403"),
                      style=ft.ButtonStyle(color="red" if state["folder"] == "403" else "#707579")),
        ft.TextButton("Все", on_click=lambda _: set_f("all"),
                      style=ft.ButtonStyle(color="white" if state["folder"] == "all" else "#707579")),
    ], alignment="center", spacing=0)

    if not leads_view:
        leads_view = ft.Column(scroll="always", expand=True)
        search_field.on_change = lambda _: refresh_list_only(leads_view)
        tag_search_field.on_change = lambda _: refresh_list_only(leads_view)

    # Обновляем структуру user_list
    user_list.controls = [
        ft.Container(content=ft.Row([search_field, tag_search_field], spacing=5), padding=ft.padding.only(bottom=10)),
        folder_tabs,
        ft.Divider(height=1, color="#333d49"),
        leads_view
    ]

    refresh_list_only(leads_view)