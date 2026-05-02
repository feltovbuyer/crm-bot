import asyncio
import sqlite3
import os
from datetime import datetime
from aiogram import types


async def run_broadcast(
    bot,
    text,
    progress_callback,
    target_tag=None,
    target_date=None,
    target_date_to=None,
    file_path=None,
    get_bot_for_user=None
):
    conn = sqlite3.connect("crm.db")
    cursor = conn.cursor()

    query = "SELECT user_id FROM users WHERE 1=1"
    params = []

    if target_tag and target_tag != "Все":
        query += " AND tags LIKE ?"
        params.append(f"%{target_tag}%")

    if target_date:
        query += " AND created_at >= ?"
        params.append(target_date)

    if target_date_to:
        query += " AND created_at <= ?"
        params.append(target_date_to + " 23:59")

    cursor.execute(query, params)
    users = cursor.fetchall()

    total = len(users)
    count = 0
    now_t = datetime.now().strftime("%H:%M")

    print(f"Найдено пользователей для рассылки: {total}")

    for (uid,) in users:
        target_bot = get_bot_for_user(uid) if get_bot_for_user else bot

        media_type = None
        media_id = None

        try:
            if file_path:
                ext = os.path.splitext(file_path)[1].lower()

                if ext in [".jpg", ".jpeg", ".png", ".webp"]:
                    sent = await target_bot.send_photo(
                        uid,
                        photo=types.FSInputFile(file_path),
                        caption=text
                    )
                    file = await target_bot.get_file(sent.photo[-1].file_id)
                    media_type = "photo"
                    media_id = file.file_path

                elif ext in [".ogg", ".oga"]:
                    sent = await target_bot.send_voice(
                        uid,
                        voice=types.FSInputFile(file_path),
                        caption=text
                    )
                    file = await target_bot.get_file(sent.voice.file_id)
                    media_type = "voice"
                    media_id = file.file_path

                elif ext in [".mp4", ".mov", ".avi", ".mkv"]:
                    sent = await target_bot.send_video(
                        uid,
                        video=types.FSInputFile(file_path),
                        caption=text
                    )
                    file = await target_bot.get_file(sent.video.file_id)
                    media_type = "video"
                    media_id = file.file_path

                else:
                    sent = await target_bot.send_document(
                        uid,
                        document=types.FSInputFile(file_path),
                        caption=text
                    )
                    file = await target_bot.get_file(sent.document.file_id)
                    media_type = "document"
                    media_id = file.file_path

                cursor.execute(
                    """
                    INSERT INTO messages (user_id, sender, text, is_read, time, media_type, media_id)
                    VALUES (?, 'admin', ?, 1, ?, ?, ?)
                    """,
                    (uid, text or "", now_t, media_type, media_id)
                )

            else:
                await target_bot.send_message(uid, text)

                cursor.execute(
                    """
                    INSERT INTO messages (user_id, sender, text, is_read, time)
                    VALUES (?, 'admin', ?, 1, ?)
                    """,
                    (uid, text, now_t)
                )

            conn.commit()
            count += 1

        except Exception as e:
            print(f"Ошибка отправки пользователю {uid}: {e}")

        await progress_callback(count, total)
        await asyncio.sleep(0.08)

    conn.close()
    return count