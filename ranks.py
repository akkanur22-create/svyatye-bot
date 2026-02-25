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

# Требования для автоматического повышения (дни, сообщения)
RANK_REQUIREMENTS = {
    1: {"days": 5, "messages": 500},
    2: {"days": 30, "messages": 3000},
}

# Права для каждого ранга
RANK_PERMISSIONS = {
    0: [],  # Новичок - только писать
    1: ["mute_30min", "warn", "vote"],  # Стажер
    2: ["mute", "kick", "clearwarns", "rank_1"],  # Святой
    3: ["ban", "unban", "rank_1", "rank_2", "demote_to_2"],  # Зам.Руководителя
    4: ["rank_1", "rank_2", "rank_3", "demote", "settings"],  # Руководитель
    5: ["all"]  # Директор - всё
}

async def setup_rank_handlers(dp, db):
    """Регистрация обработчиков команд для рангов"""
    
    @dp.message(Command("profile"))
    async def cmd_profile(message: Message):
        """Просмотр профиля"""
        # Определяем, чей профиль смотрим
        args = message.text.split()
        if len(args) > 1 and args[1].startswith('@'):
            # Профиль другого пользователя
            username = args[1][1:]  # убираем @
            # Ищем пользователя в БД по username
            user = db.get_user_by_username(username)
            if not user:
                await message.answer(f"❌ Пользователь {args[1]} не найден в базе")
                return
            target_id = user[0]
            target_name = username
        else:
            # Свой профиль
            target_id = message.from_user.id
            target_name = message.from_user.username
            user = db.get_user(target_id, target_name)
        
        # Получаем данные
        rank = user[2]
        rank_name = RANK_NAMES.get(rank, "Неизвестно")
        messages = user[4]
        
        # Дата присоединения
        join_date = datetime.datetime.fromisoformat(user[3]) if user[3] else datetime.datetime.now()
        days_in_chat = (datetime.datetime.now() - join_date).days
        
        # Социальная статистика
        hugs_given = user[8] if len(user) > 8 else 0
        hugs_received = user[9] if len(user) > 9 else 0
        slaps_given = user[10] if len(user) > 10 else 0
        slaps_received = user[11] if len(user) > 11 else 0
        beers_given = user[12] if len(user) > 12 else 0
        beers_received = user[13] if len(user) > 13 else 0
        respects_given = user[14] if len(user) > 14 else 0
        respects_received = user[15] if len(user) > 15 else 0
        
        # Предупреждения
        warns = user[16] if len(user) > 16 else 0
        
        profile_text = (
            f"👤 **Профиль @{target_name}**\n"
            f"────────────────\n"
            f"**Ранг:** {rank_name}\n"
            f"**Уровень:** {int(messages/100)+1}\n"
            f"────────────────\n"
            f"📊 **Статистика:**\n"
            f"📝 Сообщений: {messages}\n"
            f"📅 Дней в чате: {days_in_chat}\n"
            f"⚠️ Предупреждений: {warns}\n"
            f"────────────────\n"
            f"🤗 **Социальное:**\n"
            f"• Обнимашек: {hugs_given} дал / {hugs_received} получил\n"
            f"• Шлепков: {slaps_given} дал / {slaps_received} получил\n"
            f"• 🍺 Пива: {beers_given} угостил / {beers_received} выпил\n"
            f"• 👑 Респектов: {respects_given} выразил / {respects_received} получил\n"
        )
        
        # Добавляем информацию о следующем ранге
        if rank < 2:  # Если не Святой и выше
            next_rank = rank + 1
            if next_rank in RANK_REQUIREMENTS:
                req = RANK_REQUIREMENTS[next_rank]
                messages_needed = max(0, req["messages"] - messages)
                days_needed = max(0, req["days"] - days_in_chat)
                
                profile_text += (
                    f"────────────────\n"
                    f"🎯 **До следующего ранга:**\n"
                    f"• Осталось сообщений: {messages_needed}\n"
                    f"• Осталось дней: {days_needed}"
                )
        
        await message.answer(profile_text)
    
    @dp.message(Command("top"))
    async def cmd_top(message: Message):
        """Топ пользователей по сообщениям"""
        # Получаем топ-10 пользователей
        top_users = db.get_top_users(limit=10)
        
        if not top_users:
            await message.answer("❌ Пока нет данных для топа")
            return
        
        top_text = "🏆 **ТОП ЧАТА ПО СООБЩЕНИЯМ**\n\n"
        
        for i, user in enumerate(top_users, 1):
            user_id, username, rank, messages = user
            rank_name = RANK_NAMES.get(rank, "Новичок")
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            
            top_text += f"{medal} @{username} — {messages} сообщ. ({rank_name})\n"
        
        await message.answer(top_text)
    
    @dp.message(Command("nextrank"))
    async def cmd_nextrank(message: Message):
        """Информация о следующем ранге"""
        user = db.get_user(message.from_user.id, message.from_user.username)
        
        rank = user[2]
        messages = user[4]
        join_date = datetime.datetime.fromisoformat(user[3]) if user[3] else datetime.datetime.now()
        days_in_chat = (datetime.datetime.now() - join_date).days
        
        if rank >= 5:
            await message.answer("💎 Ты достиг максимального ранга! Ты — легенда!")
            return
        
        next_rank = rank + 1
        
        if next_rank not in RANK_REQUIREMENTS:
            await message.answer(f"👑 Ранг '{RANK_NAMES[next_rank]}' выдается только вручную администрацией.")
            return
        
        req = RANK_REQUIREMENTS[next_rank]
        messages_needed = max(0, req["messages"] - messages)
        days_needed = max(0, req["days"] - days_in_chat)
        
        progress_messages = req["messages"] - messages_needed
        progress_days = req["days"] - days_needed
        
        # Процент выполнения
        msg_percent = int((progress_messages / req["messages"]) * 100) if req["messages"] > 0 else 0
        days_percent = int((progress_days / req["days"]) * 100) if req["days"] > 0 else 0
        
        # Полоска прогресса
        def progress_bar(percent):
            filled = int(percent / 10)
            return "█" * filled + "░" * (10 - filled)
        
        await message.answer(
            f"🎯 **Путь к рангу {RANK_NAMES[next_rank]}**\n\n"
            f"📊 **Прогресс:**\n"
            f"📝 Сообщения: {progress_messages}/{req['messages']}\n"
            f"{progress_bar(msg_percent)} {msg_percent}%\n\n"
            f"📅 Дни в чате: {progress_days}/{req['days']}\n"
            f"{progress_bar(days_percent)} {days_percent}%\n\n"
            f"Осталось: {messages_needed} сообщ. и {days_needed} дней"
        )

async def check_auto_promotions(bot, db):
    """Автоматическая проверка повышений"""
    print("🔍 Проверка автоповышений...")
    
    # Получаем всех пользователей с рангом 0 или 1
    users = db.get_all_users()
    
    promoted = 0
    for user in users:
        user_id, username, rank, messages, join_date = user[:5]
        
        if rank >= 2:  # Выше Святого только ручная выдача
            continue
        
        if rank == 0 and 1 in RANK_REQUIREMENTS:
            # Проверка на Стажера
            req = RANK_REQUIREMENTS[1]
            join_dt = datetime.datetime.fromisoformat(join_date) if join_date else datetime.datetime.now()
            days = (datetime.datetime.now() - join_dt).days
            
            if messages >= req["messages"] and days >= req["days"]:
                # Повышаем до Стажера
                db.update_user_rank(user_id, 1)
                promoted += 1
                try:
                    await bot.send_message(
                        user_id,
                        f"🎉 Поздравляем! Ты повышен до ранга **{RANK_NAMES[1]}**!\n"
                        f"Теперь тебе доступны команды модерации: /mute, /warn, /vote"
                    )
                except:
                    pass
        
        elif rank == 1 and 2 in RANK_REQUIREMENTS:
            # Проверка на Святого
            req = RANK_REQUIREMENTS[2]
            join_dt = datetime.datetime.fromisoformat(join_date) if join_date else datetime.datetime.now()
            days = (datetime.datetime.now() - join_dt).days
            
            if messages >= req["messages"] and days >= req["days"]:
                # Повышаем до Святого
                db.update_user_rank(user_id, 2)
                promoted += 1
                try:
                    await bot.send_message(
                        user_id,
                        f"⚜️ Поздравляем! Ты достиг ранга **{RANK_NAMES[2]}**!\n"
                        f"Теперь ты можешь: /kick, /clearwarns, выдавать ранг Стажера"
                    )
                except:
                    pass
    
    print(f"✅ Автоповышений: {promoted}")