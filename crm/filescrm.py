import flet as ft


def tg_file_url(bot_token, media_id):
    if not media_id or "/" not in media_id:
        return None

    return f"https://api.telegram.org/file/bot{bot_token}/{media_id}"


def build_message_content(
    m_sender,
    m_text,
    m_time,
    m_type,
    bot_token,
    media_id=None,
    open_image_preview=None,
    show_preview=True,
):
    elements = []
    url = tg_file_url(bot_token, media_id)

    if m_type == "photo" and url:

        def load_photo_base64(u=url):
            import urllib.request
            import base64

            with urllib.request.urlopen(u, timeout=10) as response:
                img_bytes = response.read()

            return base64.b64encode(img_bytes).decode("utf-8")

        if show_preview:
            try:
                img_base64 = load_photo_base64(url)

                elements.append(
                    ft.Column([
                        ft.Image(
                            src_base64=img_base64,
                            width=180,
                            height=180,
                            fit="contain",
                        ),
                        ft.TextButton(
                            "Открыть фото",
                            url=url
                        )
                    ])
                )

            except Exception as ex:
                print("PHOTO PREVIEW ERROR:", ex)
                elements.append(
                    ft.TextButton(
                        "🖼 Открыть фото",
                        url=url
                    )
                )

        else:
            elements.append(
                ft.TextButton(
                    "🖼 Открыть фото",
                    url=url
                )
            )

    elif m_type == "document" and url:
        elements.append(
            ft.Row([
                ft.Text("📄 Файл"),
                ft.TextButton("⬇ Скачать", url=url),
            ])
        )

    elif m_type == "voice" and url:
        elements.append(
            ft.Row([
                ft.Text("🎤 Голосовое"),
                ft.TextButton("▶ Открыть", url=url),
            ])
        )

    elif m_type == "video_note" and url:
        elements.append(
            ft.Row([
                ft.Text("🔘 Кружок"),
                ft.TextButton("▶ Открыть", url=url),
            ])
        )

    elif m_type == "video" and url:
        elements.append(
            ft.Row([
                ft.Text("🎬 Видео"),
                ft.TextButton("▶ Открыть", url=url),
            ])
        )

    elif m_type and not url:
        elements.append(ft.Text("📎 Медиа без ссылки", size=13))

    if m_text:
        elements.append(ft.Text(m_text, size=15, selectable=True))

    elements.append(ft.Text(m_time, size=10, color="#707579"))

    return ft.Row(
        [
            ft.Container(
                content=ft.Column(elements, spacing=5),
                bgcolor="#182533" if m_sender == "admin" else "#2b5278",
                padding=12,
                border_radius=12,
                width=350,
            )
        ],
        alignment=ft.MainAxisAlignment.END if m_sender == "admin" else ft.MainAxisAlignment.START,
    )