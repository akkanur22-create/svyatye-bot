import os
import logging
from flask import Flask, request
from aiogram import Bot, Dispatcher
from aiogram.types import Message, Update
from aiogram.filters import Command
import asyncio

import config
from database import Database
from ranks import setup_rank_handlers, check_auto_promotions
from social import setup_social_handlers
from admin import setup_admin_handlers

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация
app = Flask(__name__)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()
db = Database()

# Регистрируем обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Я бот для чата \"Святые\". Вот мои команды:\n"
        f"/profile - мой профиль\n"
        f"/top - топ чата\n"
        f"/help - все команды"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 **Все команды бота:**\n\n"
        "👤 **Профиль:**\n"
        "/profile - твой профиль\n"
        "/profile @user - профиль друга\n"
        "/top - топ чата\n"
        "/nextrank - до следующего ранга\n\n"
        "🎮 **Социальные:**\n"
        "/obn @user - обнять\n"
        "/slap @user - шлепнуть\n"
        "/givebeer @user - угостить пивом 🍺\n"
        "/respect @user - выразить уважение 👑\n"
        "/random - случайное число\n\n"
        "🛡 **Модерация:**\n"
        "/warn @user - предупредить\n"
        "/mute @user 10min - замутить\n"
        "/kick @user - выгнать\n"
        "/ban @user - забанить\n"
        "/unban @user - разбанить\n"
        "/votekick @user - голосование за кик"
    )

# Flask маршруты
@app.route('/')
def home():
    return "Святой бот работает! 🤖"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Получение обновлений от Telegram"""
    update = Update.model_validate(request.get_json(), context={"bot": bot})
    asyncio.run_coroutine_threadsafe(dp.feed_update(bot, update), loop)
    return "OK", 200

# Функции запуска
async def on_startup():
    """Действия при запуске"""
    # Устанавливаем вебхук
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_URL', '').replace('https://', '')}/webhook"
    if not webhook_url.startswith('https://'):
        webhook_url = 'https://' + webhook_url
    
    await bot.set_webhook(url=webhook_url)
    logging.info(f"✅ Webhook установлен на {webhook_url}")
    
    # Проверяем повышения
    await check_auto_promotions(bot, db)

async def on_shutdown():
    """Действия при остановке"""
    await bot.delete_webhook()
    await bot.session.close()

def run_bot():
    """Запуск бота в отдельном цикле событий"""
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    loop.run_until_complete(on_startup())
    
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(on_shutdown())

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    import threading
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)