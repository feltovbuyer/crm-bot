def init_custom_tags(db_query):
    db_query("""
    CREATE TABLE IF NOT EXISTS custom_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        color TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    db_query("""
    CREATE TABLE IF NOT EXISTS instant_tag_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag_id INTEGER,
        action_order INTEGER,
        action_type TEXT,
        text TEXT,
        file_path TEXT,
        delay_seconds INTEGER,
        active INTEGER DEFAULT 1
    )
    """)


def get_custom_tags(db_query, search=""):
    return db_query("""
    SELECT id, name, color
    FROM custom_tags
    WHERE active=1 AND name LIKE ?
    """, (f"%{search}%",), fetch=True) or []


def add_custom_tag(db_query, name, color):
    db_query("""
    INSERT INTO custom_tags (name, color)
    VALUES (?, ?)
    """, (name, color))


def delete_custom_tag(db_query, tag_id):
    db_query("UPDATE custom_tags SET active=0 WHERE id=?", (tag_id,))


def add_tag_to_user(db_query, user_id, tag):
    row = db_query("SELECT tags FROM users WHERE user_id=?", (user_id,), fetch=True)
    old = row[0][0] if row else ""

    tags = [t for t in old.split(",") if t]

    if tag not in tags:
        tags.append(tag)

    db_query("UPDATE users SET tags=? WHERE user_id=?", (",".join(tags), user_id))


def add_instant_action(db_query, tag_id, action_order, action_type, text, file_path, delay):
    db_query("""
    INSERT INTO instant_tag_actions
    (tag_id, action_order, action_type, text, file_path, delay_seconds)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (tag_id, action_order, action_type, text, file_path, delay))


def get_actions(db_query, tag_id):
    return db_query("""
    SELECT action_type, text, file_path, delay_seconds
    FROM instant_tag_actions
    WHERE tag_id=? AND active=1
    ORDER BY action_order
    """, (tag_id,), fetch=True) or []


async def run_instant_tag_actions(db_query, bot, user_id, tag_id, send_crm_message):
    import asyncio

    actions = get_actions(db_query, tag_id)

    for action_type, text, file_path, delay in actions:
        if delay:
            await asyncio.sleep(delay)

        await send_crm_message(
            bot=bot,
            user_id=user_id,
            text=text or "",
            media_type=None if action_type == "text" else action_type,
            media_id=file_path or None
        )


def delete_instant_action(db_query, action_id):
    db_query("UPDATE instant_tag_actions SET active=0 WHERE id=?", (action_id,))