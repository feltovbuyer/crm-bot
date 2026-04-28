import flet as ft


def create_lead_card():
    name_txt = ft.Text(size=24, weight="bold", selectable=True)
    id_txt = ft.Text(size=15, color="#707579", selectable=True)
    date_txt = ft.Text(size=15, color="#707579")
    s1, s2, s3 = ft.Text(size=15), ft.Text(size=15), ft.Text(size=15)
    tags_row = ft.Row(wrap=True, spacing=5)

    comment_field = ft.TextField(label="Комментарий", multiline=True, min_lines=4, text_size=15)
    media_field = ft.TextField(label="Медиа ссылка", text_size=15)

    save_btn = ft.ElevatedButton("Сохранить", icon="SAVE", width=300, height=45)
    add_tag_btn = ft.ElevatedButton("Статус", icon="ADD", width=300, height=45)

    view = ft.Container(
        content=ft.Column([
            ft.Row([name_txt, ft.IconButton(ft.Icons.COPY, on_click=lambda e: e.page.set_clipboard(name_txt.value))],
                   alignment="spaceBetween"),
            ft.Row([id_txt, ft.IconButton(ft.Icons.COPY, on_click=lambda e: e.page.set_clipboard(id_txt.value))],
                   alignment="spaceBetween"),
            ft.Text("Создан:", size=15), date_txt,
            ft.Divider(),
            ft.Row([ft.Text("Шаг 1:", size=15), s1]),
            ft.Row([ft.Text("Шаг 2:", size=15), s2]),
            ft.Row([ft.Text("Шаг 3:", size=15), s3]),
            ft.Divider(),
            ft.Text("ТЕГИ (клик для удаления):", size=13, weight="bold", color="#707579"),
            tags_row,
            add_tag_btn,
            ft.Divider(),
            comment_field,
            media_field,
            save_btn
        ], scroll="always"), width=340, padding=20, bgcolor="#17212b"
    )
    return {
        "view": view, "name": name_txt, "id": id_txt, "date": date_txt,
        "s1": s1, "s2": s2, "s3": s3, "tags": tags_row,
        "comment": comment_field, "media": media_field,
        "save_btn": save_btn, "add_tag_btn": add_tag_btn
    }


def create_broadcast_ui():
    msg = ft.TextField(label="Текст", multiline=True)

    tag = ft.Dropdown(
        label="Тег",
        value="Все",
        options=[
            ft.dropdown.Option("Все"),
            ft.dropdown.Option("Гана"),
            ft.dropdown.Option("ФД"),
            ft.dropdown.Option("РД"),
            ft.dropdown.Option("Регистрация"),
            ft.dropdown.Option("Депозит"),
            ft.dropdown.Option("Прошел воронку"),
            ft.dropdown.Option("403"),
        ]
    )

    date_from = ft.TextField(label="Дата от", hint_text="18.04.2026", width=160)
    date_to = ft.TextField(label="Дата до", hint_text="20.04.2026", width=160)

    file_label = ft.Text("", size=12, color="#a2c7f5")
    file_btn = ft.ElevatedButton("Прикрепить файл", icon="ATTACH_FILE")

    count = ft.Text("Активных чатов: 0")
    status = ft.Text("Готов")
    btn = ft.ElevatedButton("Пуск", icon="PLAY_ARROW")
    back = ft.TextButton("Назад")

    view = ft.Container(
        content=ft.Column([
            ft.Text("Рассылка", size=24),
            msg,
            tag,
            ft.Row([date_from, date_to]),
            ft.Row([file_btn, file_label]),
            count,
            status,
            ft.Row([btn, back])
        ]),
        visible=False,
        padding=40,
        bgcolor="#0e1621",
        expand=True
    )

    return {
        "view": view,
        "input": msg,
        "tag": tag,
        "date": date_from,
        "date_to": date_to,
        "file_btn": file_btn,
        "file_label": file_label,
        "file_path": None,
        "count_info": count,
        "btn": btn,
        "back_btn": back,
        "status": status
    }