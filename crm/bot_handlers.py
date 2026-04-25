import sqlite3
import time
import asyncio
from aiogram import Router, types, Bot
from datetime import datetime
from utils import get_geo_data
import os
from dotenv import load_dotenv

load_dotenv()
BOT_CHANNEL = os.getenv("BOT_CHANNEL", "Г1")

try:
    from config import FUNNEL
except ImportError:
    FUNNEL = {}

router = Router()
ADMIN_ID = 8544500750
BOT_CHANNEL = os.getenv("BOT_CHANNEL", "Г1")
print("BOT_CHANNEL:", BOT_CHANNEL)


def db_query_local(sql, params=(), fetch=False):
    conn = sqlite3.connect('crm.db', timeout=10, check_same_thread=False)
    cursor = conn.cursor()
    res = None
    try:
        cursor.execute(sql, params)
        if fetch:
            res = cursor.fetchall()
        conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        conn.close()
    return res


def extract_start_arg(text: str) -> str:
    """
    Достаёт subid из /start.
    Нормально должно приходить так:
    /start abc123

    На всякий случай поддерживает и кривой вариант:
    /startabc123
    """
    text = text or ""

    if text.startswith("/start "):
        return text.split(maxsplit=1)[1].strip()

    if text.startswith("/start") and len(text) > 6:
        return text.replace("/start", "", 1).strip()

    return ""


@router.message()
async def handle_any_message(message: types.Message):
    uid = message.from_user.id
    text = message.text or message.caption or ""
    now_time = datetime.now().strftime("%H:%M")
    current_ts = time.time()

    # --- 1. АДМИН (ОТПРАВКА ИЗ ТГ) ---
    if uid == ADMIN_ID:
        parts = text.split(maxsplit=1)
        if parts and parts[0].isdigit():
            target_id = int(parts[0])
            reply_text = parts[1] if len(parts) > 1 else ""
            try:
                if message.photo:
                    await message.bot.send_photo(target_id, message.photo[-1].file_id, caption=reply_text)
                elif message.voice:
                    await message.bot.send_voice(target_id, message.voice.file_id, caption=reply_text)
                elif message.document:
                    await message.bot.send_document(target_id, message.document.file_id, caption=reply_text)
                elif message.video_note:
                    await message.bot.send_video_note(target_id, message.video_note.file_id)
                else:
                    await message.bot.send_message(target_id, reply_text)

                db_query_local(
                    "INSERT INTO messages (user_id, sender, text, is_read, time, media_type) VALUES (?, 'admin', ?, 1, ?, ?)",
                    (target_id, reply_text, now_time, "media" if not message.text else None)
                )
                db_query_local(
                    "UPDATE users SET last_ts = ? WHERE user_id = ?",
                    (current_ts, target_id)
                )
                return
            except:
                return

    # --- 2. ЛИД (ЗАПИСЬ И ПЕРЕСЫЛКА) ---
    media_type, media_id = None, None

    if message.photo:
        media_type, media_id = "photo", message.photo[-1].file_id
    elif message.voice:
        media_type, media_id = "voice", message.voice.file_id
    elif message.video_note:
        media_type, media_id = "video_note", message.video_note.file_id
    elif message.document:
        media_type, media_id = "document", message.document.file_id

    # Запись сообщения лида в базу
    db_query_local(
        """
        INSERT INTO messages (user_id, sender, text, is_read, time, media_type, media_id)
        VALUES (?, 'user', ?, 0, ?, ?, ?)
        """,
        (uid, text, now_time, media_type, media_id)
    )

    if media_id:
        try:
            if media_type == "video_note":
                await message.copy_to(chat_id=ADMIN_ID)
            else:
                await message.copy_to(chat_id=ADMIN_ID, caption=f"Медиа от {uid}\n{text}")
        except:
            pass

    # --- 3. ВОРОНКА ---
    res = db_query_local(
        "SELECT step, tags FROM users WHERE user_id=?",
        (uid,),
        fetch=True
    )

    if not res:
        args = extract_start_arg(text)
        geo = get_geo_data("Г")
        channel = getattr(message.bot, "crm_channel", BOT_CHANNEL)

        db_query_local(
            """
            INSERT INTO users (
                user_id,
                username,
                full_name,
                created_at,
                last_ts,
                step,
                tags,
                is_blocked,
                channel,
                subid
            )
            VALUES (?, ?, ?, ?, ?, '1', ?, 0, ?, ?)
            """,
            (
                uid,
                message.from_user.username,
                message.from_user.full_name,
                datetime.now().strftime("%d.%m.%Y %H:%M"),
                current_ts,
                geo["label"],
                channel,
                args
            )
        )

        curr_step, curr_tags = "1", geo["label"]

    else:
        curr_step, curr_tags = res[0]

        args = extract_start_arg(text)
        if args:
            db_query_local(
                "UPDATE users SET subid=?, last_ts=?, is_blocked=0 WHERE user_id=?",
                (args, current_ts, uid)
            )
        else:
            db_query_local(
                "UPDATE users SET last_ts=?, is_blocked=0 WHERE user_id=?",
                (current_ts, uid)
            )

    if "Прошел воронку" in (curr_tags or ""):
        return

    # Если бот уже в процессе отправки воронки для этого юзера
    if curr_step == 'processing':
        db_query_local(
            "UPDATE users SET step='1' WHERE user_id=?",
            (uid,)
        )

    if curr_step in FUNNEL:
        stage = FUNNEL[curr_step]

        next_step_final = stage["next"]
        db_query_local(
            "UPDATE users SET step='processing' WHERE user_id=?",
            (uid,)
        )

        if stage.get("save_to"):
            db_query_local(
                f"UPDATE users SET {stage['save_to']} = ? WHERE user_id = ?",
                (text, uid)
            )

        if stage.get("text"):
            for part in [p.strip() for p in stage["text"].split("\n\n") if p.strip()]:
                await asyncio.sleep(2.5)
                try:
                    await message.answer(part)

                    db_query_local(
                        """
                        INSERT INTO messages (user_id, sender, text, is_read, time)
                        VALUES (?, 'admin', ?, 1, ?)
                        """,
                        (uid, part, now_time)
                    )
                except:
                    pass

        # Завершаем этап: ставим финальный шаг и теги
        t_list = [
            t.strip()
            for t in (curr_tags or "").split(",")
            if t.strip() and "шаг" not in t
        ]

        if stage.get("tag"):
            t_list.append(stage.get("tag"))

        db_query_local(
            "UPDATE users SET step=?, tags=? WHERE user_id=?",
            (next_step_final, ",".join(filter(None, t_list)), uid)
        )


async def send_crm_message(bot: Bot, user_id: int, text: str, media_type=None, media_id=None):
    try:
        if media_type == "voice":
            await bot.send_voice(user_id, voice=media_id, caption=text)
        elif media_type == "video_note":
            await bot.send_video_note(user_id, video_note=media_id)
        elif media_type == "photo":
            await bot.send_photo(user_id, photo=media_id, caption=text)
        elif media_type == "document":
            await bot.send_document(user_id, document=media_id, caption=text)
        else:
            await bot.send_message(user_id, text=text)

        db_query_local(
            """
            INSERT INTO messages (user_id, sender, text, is_read, time, media_type, media_id)
            VALUES (?, 'admin', ?, 1, ?, ?, ?)
            """,
            (
                user_id,
                text,
                datetime.now().strftime("%H:%M"),
                media_type,
                media_id
            )
        )

        return True

    except:
        return False