import random


def init_traffic_router(db_query):
    db_query("""
    CREATE TABLE IF NOT EXISTS traffic_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel TEXT UNIQUE,
        bot_token TEXT,
        geo TEXT,
        funnel TEXT,
        active INTEGER DEFAULT 1
    )
    """)

    db_query("""
    CREATE TABLE IF NOT EXISTS traffic_distribution (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER,
        staff_id INTEGER,
        percent INTEGER DEFAULT 0,
        manager_tag TEXT DEFAULT '',
        access_mode TEXT DEFAULT 'percent',
        active INTEGER DEFAULT 1
    )
    """)

    db_query("""
    CREATE TABLE IF NOT EXISTS funnel_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funnel TEXT,
        step_order INTEGER,
        text TEXT,
        tag TEXT DEFAULT '',
        next_step TEXT DEFAULT '',
        active INTEGER DEFAULT 1
    )
    """)
    try:
        db_query("ALTER TABLE funnel_steps ADD COLUMN delay_seconds REAL DEFAULT 2.5")
    except:
        pass

    db_query("""
    CREATE TABLE IF NOT EXISTS tag_colors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag TEXT UNIQUE,
        color TEXT DEFAULT '#4da3ff'
    )
    """)

    try:
        db_query("ALTER TABLE users ADD COLUMN assigned_staff_id INTEGER")
    except:
        pass

    try:
        db_query("ALTER TABLE users ADD COLUMN traffic_funnel TEXT DEFAULT ''")
    except:
        pass


def get_db_bots(db_query):
    rows = db_query(
        """
        SELECT channel, bot_token
        FROM traffic_channels
        WHERE active=1 AND bot_token IS NOT NULL AND bot_token!=''
        """,
        fetch=True
    ) or []

    return [(channel, token) for channel, token in rows]


def get_channel_route(db_query, channel):
    row = db_query(
        """
        SELECT id, geo, funnel
        FROM traffic_channels
        WHERE active=1 AND channel=?
        LIMIT 1
        """,
        (channel,),
        fetch=True
    )

    if not row:
        return None

    return {
        "channel_id": row[0][0],
        "geo": row[0][1] or "",
        "funnel": row[0][2] or "",
    }


def get_funnel_step(db_query, funnel, step):
    row = db_query(
        """
        SELECT text, tag, next_step, delay_seconds
        FROM funnel_steps
        WHERE funnel=? AND step_order=? AND active=1
        LIMIT 1
        """,
        (funnel, int(step)),
        fetch=True
    )

    if not row:
        return None

    text, tag, next_step, delay_seconds = row[0]

    return {
        "text": text or "",
        "tag": tag or f"{step} шаг",
        "next": next_step or str(int(step) + 1),
        "save_to": f"step{step}_ans",
        "delay_seconds": float(delay_seconds or 2.5),
    }


def get_tag_color(db_query, tag):
    row = db_query(
        "SELECT color FROM tag_colors WHERE tag=? LIMIT 1",
        (tag,),
        fetch=True
    )

    if not row:
        return None

    return row[0][0]


def route_new_lead(db_query, user_id, channel, current_tags):
    route = get_channel_route(db_query, channel)

    if not route:
        return current_tags

    channel_id = route["channel_id"]
    geo = route["geo"]
    funnel = route["funnel"]

    rules = db_query(
        """
        SELECT staff_id, percent, manager_tag
        FROM traffic_distribution
        WHERE channel_id=? AND active=1
        ORDER BY id ASC
        """,
        (channel_id,),
        fetch=True
    ) or []

    chosen_staff_id = None
    chosen_tag = ""

    if rules:
        total = sum(int(r[1] or 0) for r in rules)

        if total > 0:
            rnd = random.randint(1, total)
            current = 0

            for staff_id, percent, manager_tag in rules:
                current += int(percent or 0)
                if rnd <= current:
                    chosen_staff_id = staff_id
                    chosen_tag = manager_tag or ""
                    break
        else:
            chosen_staff_id = rules[0][0]
            chosen_tag = rules[0][2] or ""

    tags = [t.strip() for t in (current_tags or "").split(",") if t.strip()]

    if geo and geo not in tags:
        tags.append(geo)

    if chosen_tag and chosen_tag not in tags:
        tags.append(chosen_tag)

    final_tags = ",".join(tags)

    db_query(
        """
        UPDATE users
        SET tags=?, assigned_staff_id=?, traffic_funnel=?
        WHERE user_id=?
        """,
        (final_tags, chosen_staff_id, funnel or "", user_id)
    )

    return final_tags