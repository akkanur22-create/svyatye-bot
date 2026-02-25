import datetime
from aiogram.types import Message
from aiogram.filters import Command

# Словарь с названиями рангов
RANK_NAMES = {
    0: "👤 Новичок",
    1: "🌟 Стажер.Святых",
    2: "⚜️ Святой",
    3: "🔰 Зам.Руководителя",
    4: "👑 Руководитель святых",
    5: "💎 Директор святых"
}

# Требования для автоматического повышения
RANK_REQUIREMENTS = {
    1: {"days": 5, "messages": 500},
    2: {"days": 30, "messages": 3000},
}

async def setup_rank_handlers(dp, db):
    """Регистрация обработчиков команд для рангов"""
    
    @dp.message(Command("profile"))
    async def cmd_profile(message: Message):
        user_id = message.from_user.id
        user = db.get_user(user_id, message.from_user.username)
        
        # Посчитаем дни в чате
        join_date = datetime.datetime.fromisoformat(user[3])
        days_in_chat = (datetime.datetime.now() - join_date).days
        
        rank = user[2]
        rank_name = RANK_NAMES.get(rank, "Неизвестно")
        messages = user[4]
        
        # Социальная статистика
        hugs_given = user[8] if len(user) > 8 else 0
        hugs_received = user[9] if len(user) > 9 else 0
        beers_given = user[12] if len(user) > 12 else 0
        beers_received = user[13] if len(user) > 13 else 0
        
        await message.answer(
            f"👤 **Профиль @{message.from_user.username}**\n"
            f"────────────────\n"
            f"**Ранг:** {rank_name}\n"
            f"**Сообщений:** {messages}\n"
            f"**Дней в чате:** {days_in_chat}\n"
            f"────────────────\n"
            f"🤗 Обнимашек: {hugs_given} дал / {hugs_received} получил\n"
            f"🍺 Пива: {beers_given} угостил / {beers_received} выпил\n"
            f"────────────────\n"
            f"Чтобы узнать больше: /help"
        )
    
    @dp.message(Command("top"))
    async def cmd_top(message: Message):
        # Заглушка для топа
        await message.answer("🏆 **Топ чата** появится soon! Следите за обновлениями!")

async def check_auto_promotions(bot, db):
    """Автоматическая проверка повышений (будет вызываться раз в день)"""
    print("🔍 Проверка автоповышений...")
    # Здесь будет логика повышения