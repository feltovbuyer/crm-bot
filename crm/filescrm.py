import flet as ft


def build_message_content(m_sender, m_text, m_time, m_type, bot_token, media_id=None, open_image_preview=None):
    elements = []

    if m_type == "photo" and media_id:
        if media_id.startswith("photos/"):
            url = f"https://api.telegram.org/file/bot{bot_token}/{media_id}"

            image = ft.Image(
                src=url,
                width=250,
                height=250,
                fit="contain"
            )

            if open_image_preview:
                elements.append(
                    ft.GestureDetector(
                        content=image,
                        on_tap=lambda e, u=url: open_image_preview(u)
                    )
                )
            else:
                elements.append(image)
        else:
            elements.append(
                ft.Text("🖼 Фото без предпросмотра", size=13)
            )

    elif m_type == "document" and media_id:
        url = f"https://api.telegram.org/file/bot{bot_token}/{media_id}"
        elements.append(
            ft.TextButton("📄 Скачать файл", url=url)
        )

    elif m_type == "voice" and media_id:
        url = f"https://api.telegram.org/file/bot{bot_token}/{media_id}"
        elements.append(
            ft.TextButton("🎤 Открыть голосовое", url=url)
        )

    elif m_type == "video_note" and media_id:
        url = f"https://api.telegram.org/file/bot{bot_token}/{media_id}"
        elements.append(
            ft.TextButton("🔘 Открыть кружок", url=url)
        )

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