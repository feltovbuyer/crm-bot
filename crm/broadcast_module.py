import asyncio, sqlite3
from datetime import datetime


async def run_broadcast(bot, text, progress_callback, target_tag=None, target_date=None):
    conn = sqlite3.connect('crm.db')
    cursor = conn.cursor()

    query = "SELECT user_id FROM users WHERE 1=1"
    params = []
    if target_tag and target_tag != "Все":
        query += " AND tags LIKE ?"
        params.append(f"%{target_tag}%")
    if target_date:
        query += " AND created_at LIKE ?"
        params.append(f"%{target_date}%")

    cursor.execute(query, params)
    users = cursor.fetchall()
    total = len(users)
    count = 0
    now_t = datetime.now().strftime("%H:%M")

    print(f"Найдено пользователей для рассылки: {total}")  # Для отладки в консоли

    for (uid,) in users:
        try:
            # Важно: uid должен быть числом
            await bot.send_message(chat_id=int(uid), text=text)

            # Записываем в базу, чтобы админ видел в чате
            cursor.execute("INSERT INTO messages (user_id, sender, text, is_read, time) VALUES (?, 'admin', ?, 1, ?)",
                           (uid, text, now_t))
            conn.commit()
            count += 1
        except Exception as e:
            print(f"Ошибка отправки пользователю {uid}: {e}")

        # В любом случае обновляем прогресс-бар
        await progress_callback(count, total)
        await asyncio.sleep(0.05)  # Небольшая пауза, чтобы не поймать бан

    conn.close()
    return count