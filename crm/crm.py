import flet as ft
import sqlite3
import asyncio
import time
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from filescrm import build_message_content
from admin_panel import create_admin_ui
from utils import get_geo_data
from aiogram.exceptions import TelegramForbiddenError

import os
from dotenv import load_dotenv

from broadcast_module import run_broadcast
from authadmin import open_admin_login



# Импортируем твои компоненты и логику из внешних файлов
from ui_components import create_lead_card, create_broadcast_ui
from auto_push import start_scheduler
from left_panel import update_left_panel
from keitaro_tracker import start_keitaro_server
from bot_handlers import router as bot_router, send_crm_message  # Подключаем новый хендлер

try:
    from config import FUNNEL
except ImportError:
    FUNNEL = {}

bots_config = []

for key, value in os.environ.items():
    if key.startswith("BOT_G") and value.strip():
        channel = "Г" + key.replace("BOT_G", "")
        bots_config.append((channel, value.strip()))

bots_by_channel = {}
default_bot = None


# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def db_query(sql, params=(), fetch=False):
    conn = sqlite3.connect('crm.db', timeout=10, check_same_thread=False)
    cursor = conn.cursor()
    res = None
    try:
        cursor.execute(sql, params)
        if fetch: res = cursor.fetchall()
        conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        conn.close()
    return res


def init_db():
    # Таблица юзеров
    db_query(
        "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, full_name TEXT, step TEXT DEFAULT '1', tags TEXT DEFAULT '', step1_ans TEXT DEFAULT '-', step2_ans TEXT DEFAULT '-', step3_ans TEXT DEFAULT '-', phone TEXT DEFAULT '', created_at TEXT, channel TEXT DEFAULT 'Г1', comment TEXT DEFAULT '', media TEXT DEFAULT '', last_ts REAL DEFAULT 0, is_blocked INTEGER DEFAULT 0)")

    # Таблица сообщений (сразу с колонками для медиа)
    db_query(
        "CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, sender TEXT, text TEXT, is_read INTEGER DEFAULT 0, time TEXT, media_type TEXT, media_id TEXT)")

    # Принудительная проверка колонок (если база уже была создана без них)
    try:
        db_query("ALTER TABLE messages ADD COLUMN media_type TEXT")
        db_query("ALTER TABLE messages ADD COLUMN media_id TEXT")
        db_query("ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0")
    except:
        pass


init_db()

async def start_bot_instance(token, channel):
    local_bot = Bot(token=token)
    local_bot.crm_channel = channel

    local_dp = Dispatcher()
    local_dp.include_router(bot_router)

    bots_by_channel[channel] = local_bot

    print(f"Запущен бот {channel}")
    await local_dp.start_polling(local_bot)


def get_bot_for_user(user_id):
    res = db_query("SELECT channel FROM users WHERE user_id=?", (user_id,), fetch=True)
    if res:
        return bots_by_channel.get(res[0][0]) or default_bot
    return default_bot


# --- ОСНОВНОЙ ИНТЕРФЕЙС FLET ---
async def main(page: ft.Page):
    selected_file = {"path": None, "name": None}
    selected_file_label = ft.Text("", size=12, color="#a2c7f5")
    page.title = "Adeola CRM PRO"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1450
    state = {
        "active_id": None,
        "last_count": 0,
        "folder": "ФД",
        "search_text": "",
        "search_tag": ""
    }

    def clear_selected_file(e=None):
        selected_file["path"] = None
        selected_file["name"] = None
        selected_file_label.value = ""



        page.update()

        clear_btn = ft.IconButton(
            ft.Icons.CLOSE,
            icon_size=16,
            on_click=clear_selected_file,
            icon_color="#ff6b6b",
            visible=False
        )




    # Удаление тега кликом по нему
    async def delete_tag(tag_val):
        if not state["active_id"]: return
        res = db_query("SELECT tags FROM users WHERE user_id=?", (state["active_id"],), fetch=True)
        if res:
            tags = [t.strip() for t in res[0][0].split(',') if t.strip()]
            if tag_val in tags:
                tags.remove(tag_val)
                db_query("UPDATE users SET tags=? WHERE user_id=?", (",".join(tags), state["active_id"]))
                await select_user(state["active_id"])

    def toggle_admin(s):
        admin_view.visible = s
        crm_view.visible = not s
        br_ui["view"].visible = False
        page.update()

    admin_view = create_admin_ui(lambda e: toggle_admin(False), db_query)

    # Окно выбора статуса (тега)
    async def show_tag_dialog(e):
        if not state["active_id"]: return
        available = ["ФД", "РД", "Депозит", "Регистрация", "Прошел воронку", "403"]

        def add_tag(t):
            res = db_query("SELECT tags FROM users WHERE user_id=?", (state["active_id"],), fetch=True)
            if res:
                tags = [x.strip() for x in res[0][0].split(',') if x.strip()]
                if t not in tags:
                    tags.append(t)
                    db_query("UPDATE users SET tags=? WHERE user_id=?", (",".join(tags), state["active_id"]))
            dlg.open = False
            page.run_task(select_user, state["active_id"])

        dlg = ft.AlertDialog(
            title=ft.Text("Выберите статус"),
            content=ft.Column(
                [ft.ListTile(title=ft.Text(tag), on_click=lambda e, t=tag: add_tag(t)) for tag in available],
                tight=True, height=300),
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # Сохранение комментария и ссылки
    async def save_data(e):
        if not state["active_id"]: return
        db_query("UPDATE users SET comment=?, media=? WHERE user_id=?",
                 (ui["comment"].value, ui["media"].value, state["active_id"]))
        ui["save_btn"].text, ui["save_btn"].bgcolor = "ОК!", "green"
        page.update()
        await asyncio.sleep(1)
        ui["save_btn"].text, ui["save_btn"].bgcolor = "Сохранить", None
        page.update()

    async def pick_file(e):
        file_picker = ft.FilePicker()
        files = await file_picker.pick_files(allow_multiple=False)

        if files:
            selected_file["path"] = files[0].path
            selected_file["name"] = files[0].name
            clear_btn.visible = True
            clear_btn.visible = False

            ext = os.path.splitext(files[0].name)[1].lower()

            if ext in [".jpg", ".jpeg", ".png", ".webp"]:
                icon = "🖼"
            elif ext in [".mp4", ".mov", ".avi", ".mkv"]:
                icon = "🎬"
            elif ext in [".mp3", ".ogg", ".wav", ".m4a"]:
                icon = "🎤"
            else:
                icon = "📄"

            selected_file_label.value = f"{icon} {files[0].name}"
            page.update()

    # Выбор пользователя в левой панели
    async def select_user(uid):
        state["active_id"], state["last_count"] = int(uid), 0
        db_query("UPDATE messages SET is_read=1 WHERE user_id=? AND sender='user'", (uid,))

        r = db_query(
            "SELECT full_name, step1_ans, step2_ans, step3_ans, tags, created_at, comment, media FROM users WHERE user_id=?",
            (uid,), fetch=True)

        if r:
            fn, s1, s2, s3, tags_raw, dt, comm, med = r[0]
            ui["name"].value, ui["id"].value, ui["date"].value = fn or str(uid), str(uid), dt or "-"
            ui["s1"].value, ui["s2"].value, ui["s3"].value = s1 or "", s2 or "", s3 or ""
            ui["comment"].value, ui["media"].value = comm or "", med or ""
            ui["tags"].controls = []

            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    geos = json.load(f).get("geos", {})
            except:
                geos = {}

            if tags_raw:
                for t in tags_raw.split(','):
                    t = t.strip()
                    if not t: continue
                    tag_config = next((g for g in geos.values() if g.get("label") == t), None)
                    is_geo = tag_config is not None
                    bg_color = tag_config["color"] if is_geo else None
                    ui["tags"].controls.append(
                        ft.Chip(
                            label=ft.Text(t, size=10, color="white" if is_geo else "#707579",
                                          weight="bold" if is_geo else "normal"),
                            bgcolor=bg_color, on_click=lambda e, v=t: page.run_task(delete_tag, v)
                        )
                    )

            update_left_panel(user_list, db_query, state, page, select_user)
            await refresh_c(force=True)

    def open_image_preview(url):
        dlg = ft.AlertDialog(
            modal=True,
            content=ft.Container(
                content=ft.Image(
                    src=url,
                    width=700,
                    height=700,
                    fit="contain"
                ),
                padding=10
            ),
            actions=[
                ft.TextButton(
                    "Закрыть",
                    on_click=lambda e: close_image_preview(dlg)
                )
            ]
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def close_image_preview(dlg):
        dlg.open = False
        page.update()

    # Обновление чата
    async def refresh_c(force=False):
        if not state["active_id"]: return
        res = db_query("SELECT COUNT(*) FROM messages WHERE user_id=?", (state["active_id"],), fetch=True)
        count = res[0][0] if res else 0
        if count != state["last_count"] or force:
            # ТЯНЕМ КОЛОНКУ media_type (msg[3])
            ms = db_query(
                "SELECT sender, text, time, media_type, media_id FROM messages WHERE user_id=? ORDER BY id ASC",
                          (state["active_id"],), fetch=True)

            chat_col.controls = []
            for m in ms:
                m_sender, m_text, m_time, m_type, m_media_id = m

                # Логика заглушек для медиа в чате CRM
                if not m_text and m_type:
                    d_text = {
                        "voice": "🎤 Голосовое сообщение",
                        "video_note": "🔘 Кружок",
                        "photo": "🖼 Фотография",
                        "document": "📄 Файл / Скриншот документом"
                    }.get(m_type, "📎 Файл")
                else:
                    d_text = m_text

                chat_col.controls.append(
                    build_message_content(
                        m_sender,
                        m_text,
                        m_time,
                        m_type,
                        get_bot_for_user(state["active_id"]).token,
                        m_media_id,
                        open_image_preview
                    )
                )
            db_query("UPDATE messages SET is_read=1 WHERE user_id=? AND sender='user'", (state["active_id"],))
            state["last_count"] = count
            page.update()
            await asyncio.sleep(0.1)
            await chat_col.scroll_to(offset=-1, duration=200)

    # Отправка сообщения админом
    async def send_m(e=None):
        clear_btn.visible = True
        clear_btn.visible = False
        if not state["active_id"]:
            return

        txt = msg_in.value or ""
        file_path = selected_file.get("path")
        file_name = selected_file.get("name")


        if not txt and not file_path:
            return

        msg_in.value = ""

        target_bot = get_bot_for_user(state["active_id"])
        if not target_bot:
            print("Нет бота для отправки")
            return

        media_type = None
        media_id = None
        success = False

        try:
            if file_path:
                ext = os.path.splitext(file_path)[1].lower()

                if ext in [".jpg", ".jpeg", ".png", ".webp"]:
                    sent = await target_bot.send_photo(
                        state["active_id"],
                        photo=types.FSInputFile(file_path),
                        caption=txt
                    )
                    file = await target_bot.get_file(sent.photo[-1].file_id)
                    media_type = "photo"
                    media_id = file.file_path

                else:
                    sent = await target_bot.send_document(
                        state["active_id"],
                        document=types.FSInputFile(file_path),
                        caption=txt
                    )
                    file = await target_bot.get_file(sent.document.file_id)
                    media_type = "document"
                    media_id = file.file_path

                db_query(
                    """
                    INSERT INTO messages (user_id, sender, text, is_read, time, media_type, media_id)
                    VALUES (?, 'admin', ?, 1, ?, ?, ?)
                    """,
                    (
                        state["active_id"],
                        txt or file_name or "",
                        datetime.now().strftime("%H:%M"),
                        media_type,
                        media_id
                    )
                )

                selected_file["path"] = None
                selected_file["name"] = None
                success = True

            else:
                success = await send_crm_message(target_bot, state["active_id"], txt)

            if success:
                clear_btn.visible = True
                clear_btn.visible = False
                db_query(
                    "UPDATE users SET last_ts = ? WHERE user_id = ?",
                    (time.time(), state["active_id"])
                )

                selected_file["path"] = None
                selected_file["name"] = None
                selected_file_label.value = ""

                await refresh_c(force=True)

                selected_file["path"] = None
                selected_file["name"] = None
                selected_file_label.value = ""

                page.update()

        except Exception as ex:
            print("FILE SEND ERROR:", ex)

    # Инициализация интерфейса
    ui, br_ui = create_lead_card(), create_broadcast_ui()

    async def pick_broadcast_file(e):
        print("КНОПКА ФАЙЛА НАЖАТА")

        file_picker = ft.FilePicker()
        files = await file_picker.pick_files(allow_multiple=False)

        if files:
            br_ui["file_path"] = files[0].path
            br_ui["file_label"].value = f"📎 {files[0].name}"
            page.update()
            print("Файл рассылки выбран:", files[0].path)

    br_ui["file_btn"].on_click = pick_broadcast_file
    async def on_broadcast_start(e):
        if not br_ui["input"].value:
            br_ui["status"].value = "⚠️ Введите текст!"
            page.update()
            return



        br_ui["status"].value = "🚀 Рассылка запущена..."
        br_ui["btn"].disabled = True
        page.update()

        # Функция для обновления прогресса на экране
        async def update_status(current, total):
            br_ui["status"].value = f"Отправлено: {current} / {total}"
            page.update()

        # Вызываем логику из файла
        success_count = await run_broadcast(
            bot=default_bot,
            text=br_ui["input"].value,
            progress_callback=update_status,
            target_tag=br_ui["tag"].value,
            target_date=br_ui["date"].value if br_ui["date"].value else None,
            target_date_to=br_ui["date_to"].value if br_ui["date_to"].value else None,
            file_path=br_ui["file_path"],
            get_bot_for_user=get_bot_for_user
        )

        br_ui["status"].value = f"✅ Готово! Отправлено: {success_count}"
        br_ui["file_path"] = None
        br_ui["file_label"].value = ""
        br_ui["btn"].disabled = False
        page.update()

    # ПРИВЯЗЫВАЕМ ФУНКЦИЮ К КНОПКЕ (Этого не было в твоем коде)
    br_ui["btn"].on_click = on_broadcast_start
    ui["save_btn"].on_click, ui["add_tag_btn"].on_click = save_data, show_tag_dialog

    user_list, chat_col = ft.Column(scroll="always", expand=True), ft.Column(scroll="always", expand=True, spacing=10)
    msg_in = ft.TextField(hint_text="Введите сообщение...", expand=True, on_submit=send_m, border_radius=10)

    clear_btn = ft.IconButton(
        ft.Icons.CLOSE,
        icon_size=16,
        on_click=clear_selected_file,
        icon_color="#ff6b6b",
        visible=False
    )

    crm_view = ft.Row([
    ft.Container(
        content=ft.Column([
            ft.FilledButton(
                "Рассылка",
                on_click=lambda _: toggle(True),
                width=330,
                height=45
            ),
            ft.Divider(height=10, color="transparent"),
            user_list
        ]),
        width=360,
        bgcolor="#17212b",
        padding=15
    ),

    ft.Container(
        content=ft.Column([
            chat_col,
            ft.Column([
                ft.Row([
                    selected_file_label,
                    clear_btn
                ]),
                ft.Row([
                    ft.IconButton(
                        ft.Icons.ATTACH_FILE,
                        icon_size=28,
                        on_click=pick_file,
                        icon_color="#a2c7f5"
                    ),
                    msg_in,
                    ft.IconButton(
                        ft.Icons.SEND_ROUNDED,
                        icon_size=30,
                        on_click=send_m,
                        icon_color="#a2c7f5"
                    )
                ])
            ])
        ]),
        expand=True,
        bgcolor="#0e1621",
        padding=20
    ),

    ui["view"]
], expand=True)

    def toggle(s):
        br_ui["view"].visible, crm_view.visible = s, not s
        page.update()

    br_ui["back_btn"].on_click = lambda _: toggle(False)

    def toggle_admin(s):
        admin_view.visible = s
        crm_view.visible = not s
        br_ui["view"].visible = False
        page.update()


    page.add(
        ft.Stack([
            crm_view,
            br_ui["view"],
            admin_view,

            ft.Container(
                content=ft.IconButton(
                    ft.Icons.ADMIN_PANEL_SETTINGS,
                    on_click=lambda _: open_admin_login(page, lambda: toggle_admin(True)),
                    icon_size=6,
                    icon_color="#1e2732",
                    style=ft.ButtonStyle(padding=0)
                ),
                top=-20,
                left=-22,
                padding=0
            )
        ],
            expand=True)
    )

    # Запуск бота
    global default_bot

    global default_bot

    polling_bots = []

    for i, (channel, token) in enumerate(bots_config):
        task_bot = Bot(token=token)
        task_bot.crm_channel = channel

        if i == 0:
            default_bot = task_bot

        bots_by_channel[channel] = task_bot
        polling_bots.append(task_bot)

        print(f"Запущен бот {channel}")

    multi_dp = Dispatcher()
    multi_dp.include_router(bot_router)

    asyncio.create_task(multi_dp.start_polling(*polling_bots))

    asyncio.create_task(start_keitaro_server(db_query, port=80))

    # Цикл обновления UI
    while True:
        if crm_view.visible:
            # Обновление левой панели (здесь должна быть сортировка DESC по last_ts)
            update_left_panel(user_list, db_query, state, page, select_user)
            await refresh_c()
        await asyncio.sleep(1)


if __name__ == "__main__":
    ft.run(main)