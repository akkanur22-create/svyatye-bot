import os
import asyncio
import threading
from flask import Flask
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

import config
from database import Database
from ranks import setup_rank_handlers, check_auto_promotions
from social import setup_social_handlers
from admin import setup_admin_handlers

# Flask сервер для пингов (чтобы бот не засыпал)
app = Flask(__name__)

@app.route('/')
def home():
    return "Святой бот работает! 🤖"

@app.route('/health')
def health():
    return "OK", 200

# Инициализация бота
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

async def on_startup():
    print("🚀 Бот запущен!")
    # Проверяем повышения при старте
    await check_auto_promotions(bot, db)

async def main():
    await on_startup()
    await dp.start_polling(bot)

def run_bot():
    asyncio.run(main())

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Запускаем Flask сервер на порту из окружения Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)