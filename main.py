import asyncio
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ==========================================================
# ТВОИ ДАННЫЕ
TG_TOKEN = '8729049835:AAF8znceRbDcucifTtZpSI4RgJmW7AqUxX0'
DEEPSEEK_KEY = 'sk-b6a5413aea77457a8829e8036f84f59c'
# ==========================================================

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()

# Хранилище настроек пользователей
user_settings = {}


def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📈 Мод: ПРОФИТ")
    builder.button(text="💀 Мод: СЛИВ")
    builder.button(text="📊 ПОЛУЧИТЬ СИГНАЛ")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


async def call_deepseek_api(mode):
    """Запрос к нейросети для генерации сигнала в строгом формате"""
    url = "https://api.deepseek.com/v1/chat/completions"

    # Промпт для строгого соблюдения твоего формата
    if mode == "PROFIT":
        instruction = (
            "Ты — торговый бот. Твоя задача выдать ПРИБЫЛЬНЫЙ сигнал. "
            "Пиши СТРОГО в таком формате (5 строк):\n"
            "PROFIT SIGNAL\n"
            "Bitcoin\n"
            "Bitcoin FL\n"
            "Sum: $8\n"
            "UP✅"
        )
    else:
        instruction = (
            "Ты — бот-манипулятор. Твоя задача выдать СЛИВНОЙ сигнал. "
            "Пиши СТРОГО в таком формате (5 строк):\n"
            "DRAIN SIGNAL\n"
            "Bitcoin\n"
            "Bitcoin FL\n"
            "Sum: $8\n"
            "DOWN❌"
        )

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system",
             "content": f"{instruction}. Не пиши ничего, кроме этих 5 строк. Вместо Bitcoin можешь подставлять акции: Amazon, Nvidia, Tesla, Apple."},
            {"role": "user", "content": "Дай актуальный сигнал."}
        ],
        "temperature": 0.4  # Низкая температура для точности формата
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        result = response.json()
        if 'choices' in result:
            return result['choices'][0]['message']['content']
        else:
            return "❌ Ошибка: Проверь баланс DeepSeek"
    except Exception as e:
        return f"⚠️ Ошибка связи: {str(e)}"


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_settings[message.from_user.id] = "PROFIT"
    await message.answer(
        "🚀 **Бот готов к выдаче сигналов!**\n\n"
        "Выбери режим (Профит или Слив) и нажми кнопку получения сигнала.",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )


@dp.message(F.text.contains("Мод:"))
async def change_mode(message: types.Message):
    user_id = message.from_user.id
    if "ПРОФИТ" in message.text:
        user_settings[user_id] = "PROFIT"
        await message.answer("✅ Режим: **ПРОФИТ** включен")
    else:
        user_settings[user_id] = "DRAIN"
        await message.answer("💀 Режим: **СЛИВ** включен")


@dp.message(F.text == "📊 ПОЛУЧИТЬ СИГНАЛ")
async def handle_signal(message: types.Message):
    user_id = message.from_user.id
    mode = user_settings.get(user_id, "PROFIT")

    # Отправляем временное сообщение, чтобы пользователь не скучал
    status_msg = await message.answer("🔄 Генерирую сигнал...")

    # Получаем текст от нейросети
    signal_result = await call_deepseek_api(mode)

    # Удаляем "🔄 Генерирую..." и присылаем финальный результат
    await status_msg.delete()
    await message.answer(signal_result)


async def main():
    print("--- БОТ ЗАПУЩЕН ---")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass