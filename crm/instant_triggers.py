import asyncio
from datetime import datetime
from aiogram.types import FSInputFile

INSTANT_CONFIG = {
    "Нет денег": [
        {"type": "text", "content": "Понимаю. Посмотри отзывы тех, кто тоже начинал с нуля:"},
        {"type": "photo", "content": "media/otzyv1.jpg", "caption": "Результат за вчера!"}
    ],
    "РД": [
        {"type": "text", "content": "Реквизиты выше. Жду чек!"}
    ]
}


async def send_instant_push(bot, db_query, uid, tag_name):
    if tag_name in INSTANT_CONFIG:
        for action in INSTANT_CONFIG[tag_name]:
            await asyncio.sleep(2.5)  # Задержка 2-3 секунды
            try:
                msg_log = ""
                if action["type"] == "text":
                    await bot.send_message(uid, action["content"])
                    msg_log = action["content"]
                elif action["type"] == "photo":
                    await bot.send_photo(uid, photo=FSInputFile(action["content"]), caption=action.get("caption", ""))
                    msg_log = f"[Фото] {action.get('caption', '')}"

                db_query("INSERT INTO messages (user_id, sender, text, is_read, time) VALUES (?, 'admin', ?, 1, ?)",
                         (uid, msg_log, datetime.now().strftime("%H:%M")))
            except:
                continue