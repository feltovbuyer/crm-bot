import json


def get_geo_data(start_arg: str):
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except:
        return {"channel": "Г1", "label": "Гана", "funnel_id": "ghana_main", "color": "#FFD700"}

    channel = start_arg.upper() if start_arg else "Г1"
    prefix = channel[0]
    geos = config.get("geos", {})

    conf = geos.get(prefix, geos.get(config.get("default_geo", "Г")))

    # Если в конфиге нет такого ключа, возвращаем дефолт, чтобы не было ошибки subscriptable
    if not conf:
        return {"channel": channel, "label": "Неизвестно", "funnel_id": "main", "color": "#707579"}

    return {
        "channel": channel,
        "label": conf["label"],
        "funnel_id": conf["funnel_id"],
        "color": conf["color"]
    }