import sqlite3
import asyncio
import time
from datetime import datetime


def init_auto_push_db():
    conn = sqlite3.connect("crm.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auto_push_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tag TEXT NOT NULL,
            text TEXT NOT NULL,
            delay_minutes INTEGER DEFAULT 0,
            enabled INTEGER DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS auto_push_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            rule_id INTEGER NOT NULL,
            send_at REAL NOT NULL,
            sent INTEGER DEFAULT 0,
            created_at REAL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def create_push_tasks_for_tag(user_id, tag):
    conn = sqlite3.connect("crm.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, delay_minutes FROM auto_push_rules WHERE tag=? AND enabled=1",
        (tag,)
    )
    rules = cursor.fetchall()

    now = time.time()

    for rule_id, delay_minutes in rules:
        cursor.execute(
            "SELECT id FROM auto_push_queue WHERE user_id=? AND rule_id=?",
            (user_id, rule_id)
        )
        exists = cursor.fetchone()

        if exists:
            continue

        send_at = now + int(delay_minutes) * 60

        cursor.execute(
            """
            INSERT INTO auto_push_queue (user_id, rule_id, send_at, sent, created_at)
            VALUES (?, ?, ?, 0, ?)
            """,
            (user_id, rule_id, send_at, now)
        )

    conn.commit()
    conn.close()


async def check_auto_push_queue(get_bot_for_user):
    conn = sqlite3.connect("crm.db")
    cursor = conn.cursor()

    now = time.time()

    cursor.execute("""
        SELECT q.id, q.user_id, r.text
        FROM auto_push_queue q
        JOIN auto_push_rules r ON q.rule_id = r.id
        WHERE q.sent=0 AND q.send_at<=? AND r.enabled=1
        ORDER BY q.send_at ASC
        LIMIT 20
    """, (now,))

    tasks = cursor.fetchall()

    for queue_id, user_id, text in tasks:
        bot = get_bot_for_user(user_id)

        if not bot:
            continue

        try:
            await bot.send_message(user_id, text)

            cursor.execute(
                """
                INSERT INTO messages (user_id, sender, text, is_read, time)
                VALUES (?, 'admin', ?, 1, ?)
                """,
                (user_id, text, datetime.now().strftime("%H:%M"))
            )

            cursor.execute(
                "UPDATE auto_push_queue SET sent=1 WHERE id=?",
                (queue_id,)
            )

            conn.commit()

        except Exception as ex:
            print("AUTO PUSH SEND ERROR:", ex)

    conn.close()


async def start_scheduler(get_bot_for_user):
    init_auto_push_db()

    while True:
        await check_auto_push_queue(get_bot_for_user)
        await asyncio.sleep(10)