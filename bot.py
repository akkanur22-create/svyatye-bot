import os
import logging
import random
from flask import Flask, request
from aiogram import Bot, Dispatcher
from aiogram.types import Message,  Update 
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
    # Регистрируем пользователя в базе
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
        "👤 **ПроФИЛЬ И СТАТИСТИКА:**\n"
        "/profile - твой профиль\n"
        "/profile @user - профиль друга\n"
        "/top - топ чата по активности\n"
        "/topbeers - топ по угощениям пивом 🍺\n"
        "/toprespects - топ по уважению 👑\n"
        "/tophugs - топ по обнимашкам 🤗\n"
        "/topslaps - топ по шлепкам 👊\n"
        "/level - твой уровень\n"
        "/achievements - твои достижения\n\n"
        
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
        "/ranks - список всех с рангами\n\n"
        
        "ℹ️ **ИНФО:**\n"
        "/rules - правила чата\n"
        "/nextrank - сколько до следующего ранга"
    )

@dp.message(Command("random"))
async def cmd_random(message: Message):
    """Случайное число"""
    try:
        # Парсим аргумент (максимальное число)
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
    
    # Определяем победителя
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

@dp.message(Command("level"))
async def cmd_level(message: Message):
    """Уровень пользователя"""
    user = db.get_user(message.from_user.id, message.from_user.username)
    messages = user[4]
    
    # Простая система уровней
    level = int(messages / 100) + 1
    next_level = (level * 100) - messages
    
    await message.answer(
        f"📊 **Уровень @{message.from_user.username}**\n"
        f"Текущий уровень: **{level}**\n"
        f"Сообщений: {messages}\n"
        f"До следующего уровня: {next_level} сообщений"
    )

@dp.message(Command("achievements"))
async def cmd_achievements(message: Message):
    """Достижения пользователя"""
    user = db.get_user(message.from_user.id, message.from_user.username)
    
    # Получаем статистику
    messages = user[4]
    hugs_given = user[8] if len(user) > 8 else 0
    beers_given = user[12] if len(user) > 12 else 0
    respects_given = user[14] if len(user) > 14 else 0
    
    achievements = []
    
    # Проверяем достижения
    if messages >= 100:
        achievements.append("• 🗣 **Болтун** - 100 сообщений")
    if messages >= 1000:
        achievements.append("• 🏆 **Говорун** - 1000 сообщений")
    if hugs_given >= 10:
        achievements.append("• 🤗 **Душа компании** - 10 объятий")
    if beers_given >= 10:
        achievements.append("• 🍺 **Пивной брат** - 10 угощений")
    if respects_given >= 10:
        achievements.append("• 👑 **Уважаемый** - 10 респектов")
    
    if not achievements:
        achievements = ["• Пока нет достижений. Активничай!"]
    
    await message.answer(
        f"🏅 **Достижения @{message.from_user.username}**\n\n" +
        "\n".join(achievements)
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
    try:
        # Получаем данные от Telegram
        update_data = request.get_json()
        print(f"🔥 Получен webhook: {update_data.get('update_id')}")
        
        # Создаем объект Update
        update = Update.model_validate(update_data)
        
        # Запускаем обработку в отдельном потоке asyncio
        asyncio.run_coroutine_threadsafe(dp.feed_update(bot, update), loop)
        
        return "OK", 200
    except Exception as e:
        print(f"❌ Ошибка в webhook: {e}")
        return "Internal Server Error", 500

# Регистрируем обработчики из других модулей
setup_rank_handlers(dp, db)
setup_social_handlers(dp, db)
setup_admin_handlers(dp, db)

async def on_startup():
    """Действия при запуске"""
    try:
        render_url = os.environ.get('RENDER_EXTERNAL_URL', '')
        print(f"🔍 RENDER_EXTERNAL_URL = {render_url}")
        
        if render_url:
            webhook_url = f"{render_url}/webhook"
            print(f"🔧 Устанавливаю вебхук на: {webhook_url}")
            
            # Сначала удаляем старый вебхук
            await bot.delete_webhook()
            
            # Устанавливаем новый
            await bot.set_webhook(url=webhook_url)
            
            # Проверяем информацию о вебхуке
            webhook_info = await bot.get_webhook_info()
            print(f"✅ Вебхук установлен: {webhook_info.url}")
            print(f"✅ Ожидающих обновлений: {webhook_info.pending_update_count}")
        
        logging.info("🚀 Бот запущен!")
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")

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