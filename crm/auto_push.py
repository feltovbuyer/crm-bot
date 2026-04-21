import sqlite3
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

PUSH_CONFIG = {
    "РД": [
        {"delay": 15, "text": "Вижу реквизиты у тебя, скоро сделаешь деп?"},
        {"delay": 30, "text": "Бро, всё в силе? Жду скриншот."},
    ]
}

async def check_and_send_pushes(bot):
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()
    now = datetime.now()
    for tag, steps in PUSH_CONFIG.items():
        cursor.execute("SELECT user_id, created_at FROM users WHERE tags LIKE ?", (f"%{tag}%",))
        for uid, c_str in cursor.fetchall():
            try:
                c_dt = datetime.strptime(c_str, "%d.%m.%Y %H:%M")
                for s in steps:
                    if now >= c_dt + timedelta(minutes=s["delay"]):
                        cursor.execute("SELECT id FROM messages WHERE user_id=? AND text=?", (uid, s["text"]))
                        if not cursor.fetchone():
                            await bot.send_message(uid, s["text"])
                            cursor.execute("INSERT INTO messages (user_id, sender, text, is_read, time) VALUES (?, 'admin', ?, 1, ?)", (uid, s["text"], now.strftime("%H:%M")))
                            conn.commit()
                            break
            except: continue
    conn.close()

def start_scheduler(bot):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_and_send_pushes, 'interval', minutes=5, args=[bot])
    scheduler.start()