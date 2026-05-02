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

        def open_photo_as_base64(e, u=url):
            try:
                import urllib.request
                import base64

                with urllib.request.urlopen(u, timeout=15) as response:
                    img_bytes = response.read()

                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                img_src = f"data:image/jpeg;base64,{img_base64}"

                if open_image_preview:
                    open_image_preview(img_src)

            except Exception as ex:
                print("OPEN PHOTO BASE64 ERROR:", ex)

        if show_preview:
            try:
                import urllib.request
                import base64

                with urllib.request.urlopen(url, timeout=10) as response:
                    img_bytes = response.read()

                img_base64 = base64.b64encode(img_bytes).decode("utf-8")
                img_src = f"data:image/jpeg;base64,{img_base64}"

                img = ft.Image(
                    src=img_src,
                    width=250,
                    height=250,
                    fit="contain",
                )

                if open_image_preview:
                    elements.append(
                        ft.GestureDetector(
                            content=img,
                            on_tap=lambda e, src=img_src: open_image_preview(src),
                        )
                    )
                else:
                    elements.append(img)

            except Exception as ex:
                print("PHOTO LOAD ERROR:", ex)
                elements.append(
                    ft.TextButton(
                        "🖼 Открыть фото",
                        on_click=open_photo_as_base64
                    )
                )

        else:
            elements.append(
                ft.TextButton(
                    "🖼 Открыть фото",
                    on_click=open_photo_as_base64
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