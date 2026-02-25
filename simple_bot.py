import os
import logging
import random
import datetime
import sqlite3
import asyncio
import threading
from flask import Flask, request
from aiogram import Bot, Dispatcher
from aiogram.types import Message, Update
from aiogram.filters import Command

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Конфиг
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден!")

# Инициализация
app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== ПРОСТАЯ БАЗА ДАННЫХ ==========
class SimpleDB:
    def __init__(self):
        self.conn = sqlite3.connect("bot.db", check_same_thread=False)
        self.init_db()
    
    def init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                rank INTEGER DEFAULT 0,
                messages INTEGER DEFAULT 0,
                join_date DATETIME
            )
        """)
        self.conn.commit()
    
    def get_user(self, user_id, username=None):
        cur = self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cur.fetchone()
        
        if not user:
            now = datetime.datetime.now()
            self.conn.execute(
                "INSERT INTO users (user_id, username, join_date) VALUES (?, ?, ?)",
                (user_id, username, now)
            )
            self.conn.commit()
            cur = self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cur.fetchone()
        return user
    
    def add_message(self, user_id):
        self.conn.execute(
            "UPDATE users SET messages = messages + 1 WHERE user_id = ?",
            (user_id,)
        )
        self.conn.commit()

db = SimpleDB()

# ========== ВСЕ КОМАНДЫ В ОДНОМ МЕСТЕ ==========

@dp.message(Command("start"))
async def cmd_start(message: Message):
    db.get_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Я бот для чата. Доступные команды:\n"
        f"/help - все команды"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📋 **КОМАНДЫ БОТА**\n\n"
        "/profile - мой профиль\n"
        "/top - топ чата\n"
        "/level - мой уровень\n"
        "/random - случайное число\n"
        "/dice - бросить кубик\n"
        "/coin - орлянка"
    )

@dp.message(Command("profile"))
async def cmd_profile(message: Message):
    user = db.get_user(message.from_user.id, message.from_user.username)
    rank_names = {0: "Новичок", 1: "Стажер", 2: "Святой"}
    rank = rank_names.get(user[2], "Новичок")
    
    await message.answer(
        f"👤 **Профиль**\n"
        f"Имя: @{message.from_user.username}\n"
        f"Ранг: {rank}\n"
        f"Сообщений: {user[3]}"
    )

@dp.message(Command("top"))
async def cmd_top(message: Message):
    cur = db.conn.execute(
        "SELECT username, messages FROM users ORDER BY messages DESC LIMIT 5"
    )
    top = cur.fetchall()
    
    text = "🏆 **ТОП ЧАТА**\n\n"
    for i, (username, msgs) in enumerate(top, 1):
        text += f"{i}. @{username} — {msgs} сообщ.\n"
    
    await message.answer(text)

@dp.message(Command("level"))
async def cmd_level(message: Message):
    user = db.get_user(message.from_user.id, message.from_user.username)
    level = user[3] // 10 + 1
    await message.answer(f"📊 Твой уровень: **{level}** (сообщений: {user[3]})")

@dp.message(Command("random"))
async def cmd_random(message: Message):
    num = random.randint(1, 100)
    await message.answer(f"🎲 Случайное число: **{num}**")

@dp.message(Command("dice"))
async def cmd_dice(message: Message):
    num = random.randint(1, 6)
    dice = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"][num-1]
    await message.answer(f"{dice} **{num}**")

@dp.message(Command("coin"))
async def cmd_coin(message: Message):
    result = random.choice(["Орёл", "Решка"])
    await message.answer(f"🪙 **{result}**")

# Счетчик сообщений для всех пользователей
@dp.message()
async def count_messages(message: Message):
    if message.from_user:
        db.add_message(message.from_user.id)

# ========== FLASK ДЛЯ RENDER ==========
@app.route('/')
def home():
    return "Бот работает!"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = Update.model_validate(request.get_json())
        asyncio.run_coroutine_threadsafe(dp.feed_update(bot, update), loop)
        return "OK", 200
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return "Error", 500

async def on_startup():
    render_url = os.environ.get('RENDER_EXTERNAL_URL', '')
    if render_url:
        webhook_url = f"{render_url}/webhook"
        await bot.set_webhook(url=webhook_url)
        logging.info(f"Webhook set to {webhook_url}")

def run_bot():
    global loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(on_startup())
    loop.run_forever()

if __name__ == '__main__':
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)