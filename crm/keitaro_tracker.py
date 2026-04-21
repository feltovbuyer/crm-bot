import aiohttp
import ssl

# Константы из твоих скриншотов
KEITARO_DOMAIN = "adeolafinancehelp.click"
CAMPAIGN_TOKEN = "vktwQsNW"
PIXEL_ID = "1465787968474694"


async def send_keitaro_postback(uid, channel="Г1"):
    """
    Легкий метод отправки лида без использования браузера.
    """
    # Формируем URL точно по твоим настройкам Tracking
    url = (
        f"https://{KEITARO_DOMAIN}/{CAMPAIGN_TOKEN}?"
        f"status=lead&"
        f"external_id={uid}&"
        f"pixel={PIXEL_ID}&"
        f"_is_lead=1&"
        f"sub_id_1={channel}"
    )

    # Имитируем реальный браузер через заголовки
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive"
    }

    # Игнорируем возможные проблемы с SSL сертификатами Cloudflare
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=10, ssl=ssl_context) as response:
                if response.status == 200:
                    print(f"--> [Keitaro OK] Лид отправлен для ID: {uid}")
                else:
                    print(f"--> [Keitaro Error] Код: {response.status}")
    except Exception as e:
        print(f"--> [Keitaro Connection Error]: {e}")