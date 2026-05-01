import flet as ft


def build_message_content(m_sender, m_text, m_time, m_type, bot_token, media_id=None, open_image_preview=None):
    elements = []

    if m_type == "photo" and media_id:
        if "/" in media_id:
            url = f"https://api.telegram.org/file/bot{bot_token}/{media_id}"

            if m_type == "photo" and media_id:
                if "/" in media_id:
                    url = f"https://api.telegram.org/file/bot{bot_token}/{media_id}"

                    image = ft.Image(
                        src=url,
                        width=250,
                        height=250,
                        fit="contain",
                        error_content=ft.Text("🖼 Фото не загрузилось, откройте кнопкой")
                    )

                    elements.append(image)

                    # кнопка открытия (обязательно оставляем)
                    elements.append(
                        ft.TextButton("🔗 Открыть фото", url=url)
                    )
                else:
                    elements.append(ft.Text("🖼 Фото без предпросмотра", size=13))

    elif m_type == "document" and media_id:
        if "/" in media_id:
            url = f"https://api.telegram.org/file/bot{bot_token}/{media_id}"
            elements.append(
                ft.Row([
                    ft.Text("📄 Файл"),
                    ft.TextButton("⬇ Скачать", url=url)
                ])
            )
        else:
            elements.append(ft.Text("📄 Старый файл без ссылки", size=13))

    elif m_type == "voice" and media_id:
        if "/" in media_id:
            url = f"https://api.telegram.org/file/bot{bot_token}/{media_id}"
            elements.append(
                ft.Row([
                    ft.Text("🎤 Голосовое"),
                    ft.TextButton("▶ Открыть", url=url)
                ])
            )
        else:
            elements.append(ft.Text("🎤 Старое голосовое без ссылки", size=13))

    elif m_type == "video_note" and media_id:
        if "/" in media_id:
            url = f"https://api.telegram.org/file/bot{bot_token}/{media_id}"
            elements.append(
                ft.Row([
                    ft.Text("🔘 Кружок"),
                    ft.TextButton("▶ Открыть", url=url)
                ])
            )
        else:
            elements.append(ft.Text("🔘 Старый кружок без ссылки", size=13))

    elif m_type == "video" and media_id:
        if "/" in media_id:
            url = f"https://api.telegram.org/file/bot{bot_token}/{media_id}"
            elements.append(
                ft.Row([
                    ft.Text("🎬 Видео"),
                    ft.TextButton("▶ Открыть", url=url)
                ])
            )
        else:
            elements.append(ft.Text("🎬 Старое видео без ссылки", size=13))

    if m_text:
        elements.append(ft.Text(m_text, size=15))

    elements.append(ft.Text(m_time, size=10, color="#707579"))

    return ft.Row(
        [
            ft.Container(
                content=ft.Column(elements, spacing=5),
                bgcolor="#182533" if m_sender == "admin" else "#2b5278",
                padding=12,
                border_radius=12,
                width=350
            )
        ],
        alignment=ft.MainAxisAlignment.END if m_sender == "admin" else ft.MainAxisAlignment.START
    )