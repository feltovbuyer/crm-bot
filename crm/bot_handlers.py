import sqlite3
import time
import asyncio
from aiogram import Router, types, Bot
from datetime import datetime
from utils import get_geo_data
import os
from dotenv import load_dotenv
from traffic_router import route_new_lead, get_channel_route, get_funnel_step

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
    print("LEAD RAW:", uid, repr(text), message.content_type)
    now_time = datetime.now().strftime("%H:%M")
    current_ts = time.time()

    # --- 1. АДМИН (ОТПРАВКА ИЗ ТГ) ---
    if uid == ADMIN_ID:
        parts = text.split(maxsplit=1)

        if parts and parts[0].isdigit() and (
                len(parts) > 1
                or message.photo
                or message.voice
                or message.document
                or message.video_note
                or message.video
        ):
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
        file = await message.bot.get_file(message.photo[-1].file_id)
        media_type = "photo"
        media_id = file.file_path
    elif message.voice:
        file = await message.bot.get_file(message.voice.file_id)
        media_type = "voice"
        media_id = file.file_path

    elif message.document:
        file = await message.bot.get_file(message.document.file_id)
        media_type = "document"
        media_id = file.file_path

    elif message.video_note:
        file = await message.bot.get_file(message.video_note.file_id)
        media_type = "video_note"
        media_id = file.file_path

    elif message.video:
        file = await message.bot.get_file(message.video.file_id)
        media_type = "video"
        media_id = file.file_path

    db_query_local(
        """
        INSERT INTO messages (user_id, sender, text, is_read, time, media_type, media_id)
        VALUES (?, 'user', ?, 0, ?, ?, ?)
        """,
        (uid, text, now_time, media_type, media_id)
    )

    # --- 3. ВОРОНКА ---
    res = db_query_local(
        "SELECT step, tags FROM users WHERE user_id=?",
        (uid,),
        fetch=True
    )

    channel = getattr(message.bot, "crm_channel", BOT_CHANNEL)
    route = get_channel_route(db_query_local, channel)

    if not res:
        args = extract_start_arg(text)

        if route:
            start_tags = route.get("geo") or ""
        else:
            geo = get_geo_data("Г")
            start_tags = geo["label"]

        db_query_local(
            """
            INSERT INTO users (
                user_id, username, full_name, created_at, last_ts,
                step, tags, is_blocked, channel, subid
            )
            VALUES (?, ?, ?, ?, ?, '1', ?, 0, ?, ?)
            """,
            (
                uid,
                message.from_user.username,
                message.from_user.full_name,
                datetime.now().strftime("%d.%m.%Y %H:%M"),
                current_ts,
                start_tags,
                channel,
                args
            )
        )

        final_tags = route_new_lead(
            db_query_local,
            uid,
            channel,
            start_tags
        )

        curr_step, curr_tags = "1", final_tags

        if text.startswith("/start"):
            stage = None

            if route and route.get("funnel"):
                stage = get_funnel_step(db_query_local, route["funnel"], "1")

            if not stage:
                stage = FUNNEL.get("1")

            if stage and stage.get("text"):
                db_query_local(
                    "UPDATE users SET step='processing' WHERE user_id=?",
                    (uid,)
                )

                for part in [p.strip() for p in stage["text"].split("\n\n") if p.strip()]:
                    await asyncio.sleep(float(stage.get("delay_seconds", 2.5)))
                    await message.answer(part)

                    db_query_local(
                        """
                        INSERT INTO messages (user_id, sender, text, is_read, time)
                        VALUES (?, 'admin', ?, 1, ?)
                        """,
                        (uid, part, datetime.now().strftime("%H:%M"))
                    )

                t_list = [
                    t.strip() for t in (final_tags or "").split(",")
                    if t.strip() and "шаг" not in t
                ]

                if stage.get("tag"):
                    t_list.append(stage.get("tag"))
                else:
                    t_list.append("1 шаг")

                db_query_local(
                    "UPDATE users SET step='1', tags=? WHERE user_id=?",
                    (",".join(t_list), uid)
                )

            return

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

    if curr_step == "processing":
        return

    current_stage = None

    if route and route.get("funnel") and str(curr_step).isdigit():
        current_stage = get_funnel_step(db_query_local, route["funnel"], curr_step)

    if not current_stage and curr_step in FUNNEL:
        current_stage = FUNNEL[curr_step]

    if not current_stage:
        return

    if current_stage.get("save_to"):
        db_query_local(
            f"UPDATE users SET {current_stage['save_to']} = ? WHERE user_id = ?",
            (text, uid)
        )

    next_step = current_stage.get("next")

    if next_step == "FINISH":
        t_list = [
            t.strip()
            for t in (curr_tags or "").split(",")
            if t.strip() and "шаг" not in t
        ]
        t_list.append("Прошел воронку")

        db_query_local(
            "UPDATE users SET step='FINISH', tags=? WHERE user_id=?",
            (",".join(t_list), uid)
        )
        return

    stage = None

    if route and route.get("funnel") and str(next_step).isdigit():
        stage = get_funnel_step(db_query_local, route["funnel"], next_step)

    if not stage:
        stage = FUNNEL.get(next_step)

    if not stage:
        return

    db_query_local(
        "UPDATE users SET step='processing' WHERE user_id=?",
        (uid,)
    )

    if stage.get("text"):
        for part in [p.strip() for p in stage["text"].split("\n\n") if p.strip()]:
            await asyncio.sleep(float(stage.get("delay_seconds", 2.5)))
            try:
                await message.answer(part)

                db_query_local(
                    """
                    INSERT INTO messages (user_id, sender, text, is_read, time)
                    VALUES (?, 'admin', ?, 1, ?)
                    """,
                    (uid, part, datetime.now().strftime("%H:%M"))
                )
            except:
                pass

    t_list = [
        t.strip()
        for t in (curr_tags or "").split(",")
        if t.strip() and "шаг" not in t
    ]

    if stage.get("tag"):
        t_list.append(stage.get("tag"))

    db_query_local(
        "UPDATE users SET step=?, tags=? WHERE user_id=?",
        (next_step, ",".join(filter(None, t_list)), uid)
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