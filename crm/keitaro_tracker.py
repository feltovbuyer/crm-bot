# keitaro_tracker.py

import time
from datetime import datetime
from aiohttp import web


POSTBACK_TOKEN = "372f7e5"

REG_STATUSES = {"reg", "registration", "register"}
DEP_STATUSES = {"sale", "deposit", "dep", "ftd"}


def ensure_keitaro_columns(db_query):
    """
    Добавляет нужные поля в users, если их ещё нет.
    Ошибки игнорируем, потому что SQLite ругнётся, если колонка уже существует.
    """
    try:
        db_query("ALTER TABLE users ADD COLUMN subid TEXT")
    except:
        pass

    try:
        db_query("ALTER TABLE users ADD COLUMN keitaro_reg INTEGER DEFAULT 0")
    except:
        pass

    try:
        db_query("ALTER TABLE users ADD COLUMN keitaro_deposit INTEGER DEFAULT 0")
    except:
        pass

    try:
        db_query("ALTER TABLE users ADD COLUMN keitaro_payout TEXT DEFAULT ''")
    except:
        pass


def add_crm_system_message(db_query, user_id, text):
    """
    Добавляет системное сообщение в центральный чат лида.
    sender='user', чтобы сообщение было видно как входящее событие.
    """
    db_query(
        """
        INSERT INTO messages (user_id, sender, text, is_read, time, media_type, media_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            "user",
            text,
            0,
            datetime.now().strftime("%H:%M"),
            None,
            None
        )
    )

    db_query(
        "UPDATE users SET last_ts=? WHERE user_id=?",
        (time.time(), user_id)
    )


async def keitaro_postback(request):
    db_query = request.app["db_query"]

    subid = request.query.get("subid")
    status = (request.query.get("status") or "").lower().strip()
    payout = request.query.get("payout")
    tid = request.query.get("tid")

    if not subid:
        return web.json_response({
            "ok": False,
            "error": "no_subid",
            "message": "Нет subid. Связка должна идти через subid."
        })

    lead = db_query(
        """
        SELECT user_id, full_name, channel
        FROM users
        WHERE subid=?
        """,
        (subid,),
        fetch=True
    )

    if not lead:
        return web.json_response({
            "ok": False,
            "error": "lead_not_found",
            "subid": subid,
            "status": status,
            "payout": payout,
            "tid": tid
        })

    user_id, full_name, channel = lead[0]
    name = full_name or str(user_id)

    if status in REG_STATUSES:
        db_query(
            """
            UPDATE users
            SET keitaro_reg=1, last_ts=?
            WHERE user_id=?
            """,
            (time.time(), user_id)
        )

        add_crm_system_message(
            db_query,
            user_id,
            (
                "✅ KEITARO: РЕГИСТРАЦИЯ\n\n"
                f"Лид: {name}\n"
                f"TG ID: {user_id}\n"
                f"Канал: {channel or '-'}\n"
                f"SubID: {subid}\n"
                f"TID: {tid or '-'}"
            )
        )

        return web.json_response({
            "ok": True,
            "event": "registration",
            "user_id": user_id,
            "subid": subid
        })

    if status in DEP_STATUSES:
        db_query(
            """
            UPDATE users
            SET keitaro_deposit=1, keitaro_payout=?, last_ts=?
            WHERE user_id=?
            """,
            (payout or "", time.time(), user_id)
        )

        add_crm_system_message(
            db_query,
            user_id,
            (
                "💰 KEITARO: ДЕПОЗИТ\n\n"
                f"Лид: {name}\n"
                f"TG ID: {user_id}\n"
                f"Канал: {channel or '-'}\n"
                f"Сумма: {payout or '-'}\n"
                f"SubID: {subid}\n"
                f"TID: {tid or '-'}"
            )
        )

        return web.json_response({
            "ok": True,
            "event": "deposit",
            "user_id": user_id,
            "subid": subid,
            "payout": payout
        })

    return web.json_response({
        "ok": False,
        "error": "unknown_status",
        "status": status,
        "subid": subid,
        "payout": payout,
        "tid": tid
    })


async def start_keitaro_server(db_query, host="0.0.0.0", port=80):
    ensure_keitaro_columns(db_query)

    app = web.Application()
    app["db_query"] = db_query

    app.router.add_get(f"/{POSTBACK_TOKEN}/postback", keitaro_postback)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    print(
        f"--> [Keitaro] Postback server started: "
        f"http://{host}:{port}/{POSTBACK_TOKEN}/postback"
    )