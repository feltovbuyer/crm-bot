import asyncio
import random
from google import genai
from aiogram import Bot, Dispatcher, types
from openai import OpenAI

# ================= КОНФИГ =================
TG_TOKEN = "8667051646:AAFCg9hBCPOtLGLDhOhIQO8GQAJxrOOro40"
GEMINI_KEY = "AIzaSyDlyuEJNe7meGV64WDRgU067QLqKtVbRus"
DEEPSEEK_KEY = "sk-6f949ec82fd64d7a92ca18ea7b72ae18"

# Инициализация
bot = Bot(token=TG_TOKEN)
dp = Dispatcher()
gemini_client = genai.Client(api_key=GEMINI_KEY)
ds_client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")

# ================= БАЗА ДАННЫХ ГЕО =================
GEO_DATA = {
    "кр": "27.500 -> 1.500.000 / 50.000 -> 2.500.000 / 90.000 -> 3.500.000 colones",
    "гв": "390 -> 23.600 / 800 -> 39.800 / 1.200 -> 55.750 quetzales",
    "кол": "200.000 -> 12.3M / 450.000 -> 23.5M / 640.000 -> 44.7M pesos",
    "ур": "2.250 -> 127.500 / 3.600 -> 146.200 / 4.500 -> 160.750 UYU",
    "п": "380.000 -> 23.8M / 490.000 -> 36.2M / 800.000 -> 56.6M PYG",
    "г": "1.275 -> 76.575 / 2.500 -> 93.450 / 3.750 -> 132.250 HNL",
    "мх": "1.000 -> 60.800 / 1.500 -> 91.300 / 2.300 -> 120.600 pesos",
    "пер": "190 -> 2.600 / 340 -> 4.700 / 550 -> 6.400 soles",
    "бол": "350 -> 20.700 / 800 -> 35.300 / 1.200 -> 43.600 bolivianos",
    "чи": "48.000 -> 2.8M / 90.000 -> 4.8M / 140.000 -> 9.7M CLP",
    "ар": "50.000 -> 3.5M / 90.000 -> 7.8M / 140.000 -> 19.7M pesos",
    "вен": "2.000 -> 48.000 / 5.000 -> 71.800 / 9.000 -> 103.750 VES",
    "бр": "150 -> 7.435 / 350 -> 12.250 / 490 -> 19.600 reais",
    "усд": "50 -> 3000 / 100 -> 5800 / 200 -> 9800 dólares",
    "пн": "50 -> 3000 / 100 -> 5800 / 200 -> 9800 dólares"
}

# ================= СТРОЖАЙШАЯ ЛОГИКА PROMPT (V6) =================
PROMPT_LOGIC = (
    "Eres el CLOSER mas agresivo y profesional. Tu meta: El lead debe depositar hoy. "
    "ВЕРТИКАЛЬ (ТОТАЛЬНЫЙ ЗАПРЕТ): "
    "1. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО использовать слова: trading, señales, mercado, exchange, binance, cripto, activos, inversion. "
    "2. СУТЬ: Лид НЕ РАБОТАЕТ сам. Лид делает депозит, ТЫ все делаешь за него своим методом. Через 3 часа — выплата. "
    "ГРАММАТИКА И РОД: "
    "1. Если в запросе ЖЕНСКОЕ ИМЯ (Lola, Maria, и т.д.) — используй ЖЕНСКИЙ род (lista, enfocada, decidida). "
    "2. В остальных случаях — МУЖСКОЙ род. "
    "СТРОГИЕ ЗАПРЕТЫ: "
    "1. НИКАКИХ 'hermano', 'amigo', 'socio'. Имя только если оно в запросе. "
    "2. ЗАПРЕЩЕНО оправдываться 'no hay pagos adicionales'. Вместо этого дави авторитетом. "
    "3. СУММЫ: Нет ГЕО в контексте — НЕТ ЧИСЕЛ в ответе. ГЕО-коды не называть. "
    "ОТРАБОТКА ПО ТВОИМ ШАБЛОНАМ: "
    "- На сомнения/честность: Siempre valoro mi reputación y siempre muestro mi rostro. Doy la cara porque mi trabajo es real. Proporciono la licencia oficial. Si algo saliera mal, devuelvo el depósito y pago 30% adicional. "
    "- На 'Нет денег': Будь жестким. Пусть займет, заложит вещи. Деньги должны работать и приносить прибыль через 3 часа. "
    "ОБЯЗАТЕЛЬНЫЙ ФИНАЛЬНЫЙ ВОПРОС: "
    "- Нет денег: Cuanto tiempo necesitas para encontrar los fondos o puedes conseguirlos hoy mismo? "
    "- Сомнения/процесс: Estas listo/a para hacer el deposito ahora mismo? "
    "- Игнор: Me confirmas si vas a aprovechar tu cupo o se lo doy al siguiente? "
    "СТИЛЬ: Latino, слитный текст, 3-6 строк, без ¿ и ¡. Эмодзи в конце."
)


async def get_ai_response(user_text, geo_status):
    full_prompt = f"{PROMPT_LOGIC}\n\nКОНТЕКСТ ДАННЫХ: {geo_status}\n\nЗАПРОС ЛИДА: {user_text}"
    try:
        response = ds_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": full_prompt}, {"role": "user", "content": user_text}],
            timeout=15
        )
        return response.choices[0].message.content
    except Exception:
        try:
            response = gemini_client.models.generate_content(model="gemini-1.5-flash", contents=full_prompt)
            return response.text
        except Exception:
            return "El cupo se agota y hay personas esperando. Me confirmas si estas listo para iniciar ahora? 🚀"


@dp.message()
async def handle_message(message: types.Message):
    user_input = message.text.lower()

    # Поиск ГЕО
    geo_info = ""
    words = user_input.replace(",", " ").replace(".", " ").split()
    for code, values in GEO_DATA.items():
        if code in words:
            geo_info = values
            break

    if not geo_info:
        geo_status = "НЕТ ГЕО. ЧИСЛА ЗАПРЕЩЕНЫ."
    else:
        geo_status = f"ИСПОЛЬЗУЙ ЭТИ СУММЫ (БЕЗ УПОМИНАНИЯ ТРЕЙДИНГА): {geo_info}"

    # Добавление контекста пуша
    push_context = ""
    if any(trigger in user_input for trigger in ["молчит", "игнор", "игнорит"]):
        push_context = "ESTRATEGIA: Lead ignora, presiona con la perdida del cupo."

    final_query = f"{push_context} | {message.text}"
    answer = await get_ai_response(final_query, geo_status)

    # ФИНАЛЬНЫЙ ФИЛЬТР: чистка текста
    cleaned_text = answer.replace("¿", "").replace("¡", "").replace('"', "").replace("'", "")

    # Жесткая замена запрещенки, если ИИ ошибся
    forbidden = ["trading", "señales", "mercado", "exchange", "binance", "broker"]
    for word in forbidden:
        cleaned_text = cleaned_text.replace(word, "proceso")
        cleaned_text = cleaned_text.replace(word.capitalize(), "Proceso")

    final_text = " ".join(cleaned_text.splitlines())
    await message.answer(final_text)


async def main():
    print(">>> БОТ ЗАПУЩЕН: ВЕРТИКАЛЬ ИСПРАВЛЕНА, РОД НАСТРОЕН <<<")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())