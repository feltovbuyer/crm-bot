import time
from datetime import datetime
from aiohttp import web

POSTBACK_TOKEN = "372f7e5"

REG_STATUSES = {"reg", "registration", "register"}
DEP_STATUSES = {"sale", "deposit", "dep", "ftd"}


def ensure_columns(db_query):
    # Колонки в users
    for sql in [
        "ALTER TABLE users ADD COLUMN subid TEXT",
        "ALTER TABLE users ADD COLUMN keitaro_reg INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN keitaro_deposit INTEGER DEFAULT 0",
        "ALTER TABLE users ADD COLUMN keitaro_payout TEXT DEFAULT ''",
    ]:
        try:
            db_query(sql)
        except:
            pass

    # Таблица для всех депозитов
    try:
        db_query("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subid TEXT,
                payout TEXT,
                tid TEXT,
                created_at TEXT
            )
        """)
    except:
        pass


def add_system_message(db_query, user_id, text):
    db_query(
        """
        INSERT INTO messages (user_id, sender, text, is_read, time, media_type, media_id)
        VALUES (?, 'user', ?, 0, ?, NULL, NULL)
        """,
        (user_id, text, datetime.now().strftime("%H:%M"))
    )

    db_query(
        "UPDATE users SET last_ts=? WHERE user_id=?",
        (time.time(), user_id)
    )


def to_float(value):
    try:
        return float(str(value).replace(",", "."))
    except:
        return 0.0


async def keitaro_postback(request):
    return web.json_response({"test": "MY_KEITARO_TRACKER_IS_WORKING"})
    db_query = request.app["db_query"]

    subid = request.query.get("subid")
    status = (request.query.get("status") or "").lower().strip()
    payout = request.query.get("payout")
    tid = request.query.get("tid")

    if not subid:
        return web.json_response({
            "ok": False,
            "error": "no_subid"
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

    # --- РЕГИСТРАЦИЯ ---
    if status in REG_STATUSES:
        db_query(
            """
            UPDATE users
            SET keitaro_reg=1, last_ts=?
            WHERE user_id=?
            """,
            (time.time(), user_id)
        )

        add_system_message(
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

    # --- ДЕПОЗИТ / МУЛЬТИ-ДЕПЫ ---
    if status in DEP_STATUSES:
        payout_value = payout or "0"

        db_query(
            """
            INSERT INTO deposits (user_id, subid, payout, tid, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                subid,
                payout_value,
                tid or "",
                datetime.now().strftime("%d.%m.%Y %H:%M")
            )
        )

        deposits = db_query(
            """
            SELECT payout
            FROM deposits
            WHERE user_id=?
            """,
            (user_id,),
            fetch=True
        )

        dep_count = len(deposits) if deposits else 0
        dep_sum = sum(to_float(row[0]) for row in deposits) if deposits else 0.0

        db_query(
            """
            UPDATE users
            SET keitaro_deposit=1, keitaro_payout=?, last_ts=?
            WHERE user_id=?
            """,
            (
                str(dep_sum),
                time.time(),
                user_id
            )
        )

        add_system_message(
            db_query,
            user_id,
            (
                "💰 KEITARO: ДЕПОЗИТ\n\n"
                f"Лид: {name}\n"
                f"TG ID: {user_id}\n"
                f"Канал: {channel or '-'}\n"
                f"Сумма депа: {payout or '-'}\n"
                f"Всего депов: {dep_count}\n"
                f"Сумма всего: {dep_sum}\n"
                f"SubID: {subid}\n"
                f"TID: {tid or '-'}"
            )
        )

        return web.json_response({
            "ok": True,
            "event": "deposit",
            "user_id": user_id,
            "subid": subid,
            "payout": payout,
            "deposit_count": dep_count,
            "deposit_total": dep_sum
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
    ensure_columns(db_query)

    app = web.Application()
    app["db_query"] = db_query

    app.router.add_get(f"/{POSTBACK_TOKEN}/postback", keitaro_postback)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    print(
        f"[Keitaro] postback server started: "
        f"http://{host}:{port}/{POSTBACK_TOKEN}/postback"
    )