import os
import logging
import random
from flask import Flask, request
from aiogram import Bot, Dispatcher
from aiogram.types import Message, Update
from aiogram.filters import Command
import asyncio
import datetime

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

# ========== ОСНОВНЫЕ КОМАНДЫ ==========

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Приветственное сообщение"""
    db.get_user(message.from_user.id, message.from_user.username)
    
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Добро пожаловать в чат \"Святые\"!\n\n"
        f"🤖 Я бот-модератор и игровой компаньон.\n"
        f"Вот мои основные команды:\n"
        f"/profile - мой профиль\n"
        f"/help - все команды\n"
        f"/rules - правила чата"
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Полный список команд"""
    await message.answer(
        "📋 **ПОЛНЫЙ СПИСОК КОМАНД БОТА**\n\n"
        "👤 **ПРОФИЛЬ И СТАТИСТИКА:**\n"
        "/profile - твой профиль\n"
        "/profile @user - профиль друга\n"
        "/top - топ чата по активности\n"
        "/topbeers - топ по угощениям пивом 🍺\n"
        "/toprespects - топ по уважению 👑\n"
        "/tophugs - топ по обнимашкам 🤗\n"
        "/topslaps - топ по шлепкам 👊\n"
        "/level - твой уровень\n"
        "/achievements - твои достижения\n"
        "/nextrank - сколько до следующего ранга\n"
        "/ranks - список всех с рангами\n\n"
        
        "🎮 **ИГРЫ И РАЗВЛЕЧЕНИЯ:**\n"
        "/random [N] - случайное число от 1 до N (по умолч. 100)\n"
        "/dice - бросить кубик 🎲\n"
        "/coin - орлянка (орел/решка)\n"
        "/choose пиво|чипсы|сухарики - выбрать из вариантов\n"
        "/rps камень - камень-ножницы-бумага с ботом\n\n"
        
        "🤗 **СОЦИАЛЬНЫЕ КОМАНДЫ:**\n"
        "/obn @user - обнять друга\n"
        "/slap @user - шлепнуть друга\n"
        "/givebeer @user - угостить пивом 🍺\n"
        "/respect @user - выразить уважение 👑\n"
        "/highfive @user - дать пять\n"
        "/tea @user - пригласить на чай\n\n"
        
        "🛡 **МОДЕРАЦИЯ (для админов):**\n"
        "/warn @user [причина] - предупредить\n"
        "/mute @user [время] [причина] - замутить\n"
        "/unmute @user - снять мут\n"
        "/kick @user [причина] - выгнать\n"
        "/ban @user [причина] - забанить\n"
        "/unban @user - разбанить\n"
        "/votekick @user - голосование за кик\n\n"
        
        "👑 **УПРАВЛЕНИЕ РАНГАМИ (для админов):**\n"
        "/rank @user [1-5] - выдать ранг\n"
        "/demote @user - понизить ранг\n"
        "/admins - список руководства\n\n"
        
        "ℹ️ **ИНФО:**\n"
        "/rules - правила чата"
    )

@dp.message(Command("random"))
async def cmd_random(message: Message):
    """Случайное число"""
    try:
        args = message.text.split()
        if len(args) > 1:
            max_num = int(args[1])
            if max_num < 1:
                max_num = 100
        else:
            max_num = 100
        
        result = random.randint(1, max_num)
        await message.answer(f"🎲 Случайное число от 1 до {max_num}: **{result}**")
    except ValueError:
        await message.answer("❌ Некорректное число. Используй: `/random 100`")

@dp.message(Command("dice"))
async def cmd_dice(message: Message):
    """Бросок кубика"""
    result = random.randint(1, 6)
    dice_emoji = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"][result-1]
    await message.answer(f"{dice_emoji} Выпало: **{result}**")

@dp.message(Command("coin"))
async def cmd_coin(message: Message):
    """Орлянка"""
    result = random.choice(["Орёл", "Решка"])
    await message.answer(f"🪙 Монета показала: **{result}**")

@dp.message(Command("choose"))
async def cmd_choose(message: Message):
    """Выбрать случайный вариант"""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Напиши варианты через |. Например: `/choose пиво|чипсы|сухарики`")
        return
    
    options = [opt.strip() for opt in args[1].split('|') if opt.strip()]
    if len(options) < 2:
        await message.answer("❌ Нужно минимум 2 варианта через |")
        return
    
    result = random.choice(options)
    await message.answer(f"🤔 Я выбираю... **{result}**!")

@dp.message(Command("rps"))
async def cmd_rps(message: Message):
    """Камень-ножницы-бумага"""
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Выбери: камень, ножницы или бумага. Пример: `/rps камень`")
        return
    
    user_choice = args[1].lower()
    if user_choice not in ["камень", "ножницы", "бумага"]:
        await message.answer("❌ Можно только: камень, ножницы, бумага")
        return
    
    bot_choice = random.choice(["камень", "ножницы", "бумага"])
    
    if user_choice == bot_choice:
        result = "🤝 Ничья!"
    elif (user_choice == "камень" and bot_choice == "ножницы") or \
         (user_choice == "ножницы" and bot_choice == "бумага") or \
         (user_choice == "бумага" and bot_choice == "камень"):
        result = "🎉 Ты выиграл!"
    else:
        result = "🤖 Я выиграл!"
    
    await message.answer(
        f"🗿 Ты: {user_choice}\n"
        f"🤖 Я: {bot_choice}\n\n"
        f"**{result}**"
    )

@dp.message(Command("rules"))
async def cmd_rules(message: Message):
    """Правила чата"""
    await message.answer(
        "📜 **ПРАВИЛА ЧАТА \"СВЯТЫЕ\"**\n\n"
        "1. Уважай других участников\n"
        "2. Не матерись (бот следит!)\n"
        "3. Не спамь и не флуди\n"
        "4. Не рекламируй без спроса\n"
        "5. Соблюдай тематику чата\n\n"
        "⚠️ **Система наказаний:**\n"
        "• 1-2 предупреждения - устно\n"
        "• 3 предупреждения - мут 1 час\n"
        "• 4 предупреждения - мут 1 день\n"
        "• 5 предупреждений - кик\n"
        "• 6 предупреждений - бан\n\n"
        "Будь человеком! 🤗"
    )

# Счетчик сообщений для всех пользователей
@dp.message()
async def count_messages(message: Message):
    """Увеличиваем счетчик сообщений для всех"""
    if message.from_user and not message.text.startswith('/'):
        db.update_messages_count(message.from_user.id)

# ========== FLASK МАРШРУТЫ ==========

@app.route('/')
def home():
    return "Святой бот работает! 🤖"

@app.route('/health')
def health():
    return "OK", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Получение обновлений от Telegram"""
    try:
        update_data = request.get_json()
        logging.info(f"🔥 Получен webhook: {update_data.get('update_id') if update_data else 'None'}")
        
        if not update_data:
            return "No data", 400
        
        update = Update.model_validate(update_data)
        asyncio.run_coroutine_threadsafe(dp.feed_update(bot, update), loop)
        
        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Ошибка в webhook: {e}")
        return "Internal Server Error", 500

# ========== ЗАПУСК БОТА ==========

async def on_startup():
    """Действия при запуске"""
    try:
        print("🔄 Загрузка ранговых команд...")
        setup_rank_handlers(dp, db)
        
        print("🔄 Загрузка социальных команд...")
        await setup_social_handlers(dp, db)
        
        print("🔄 Загрузка админ-команд...")
        setup_admin_handlers(dp, db)
        
        render_url = os.environ.get('RENDER_EXTERNAL_URL', '')
        logging.info(f"🔍 RENDER_EXTERNAL_URL = {render_url}")
        
        if render_url:
            webhook_url = f"{render_url}/webhook"
            logging.info(f"🔧 Устанавливаю вебхук на: {webhook_url}")
            
            await bot.delete_webhook()
            await bot.set_webhook(url=webhook_url)
            
            webhook_info = await bot.get_webhook_info()
            logging.info(f"✅ Вебхук установлен: {webhook_info.url}")
            logging.info(f"✅ Ожидающих обновлений: {webhook_info.pending_update_count}")
        
        await check_auto_promotions(bot, db)
        logging.info("🚀 Бот запущен!")
    except Exception as e:
        logging.error(f"❌ Ошибка при запуске: {e}")

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
    import threading
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)