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


def route_new_lead(db_query, user_id, channel, current_tags):
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
        return current_tags

    channel_id, geo, funnel = row[0]

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