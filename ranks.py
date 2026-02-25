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

def has_permission(user_rank, permission):
    """Проверка наличия права у пользователя"""
    if user_rank == 5:  # Директор может всё
        return True
    if permission in RANK_PERMISSIONS.get(user_rank, []):
        return True
    return False

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
            target_user = user
        else:
            # Свой профиль
            target_id = message.from_user.id
            target_name = message.from_user.username
            target_user = db.get_user(target_id, target_name)
        
        # Получаем данные
        rank = target_user[2]
        rank_name = RANK_NAMES.get(rank, "Неизвестно")
        messages = target_user[5] if len(target_user) > 5 else 0  # Индекс может отличаться
        
        # Дата присоединения
        join_date_str = target_user[3] if len(target_user) > 3 else None
        if join_date_str:
            try:
                join_date = datetime.datetime.fromisoformat(join_date_str)
                days_in_chat = (datetime.datetime.now() - join_date).days
            except:
                days_in_chat = 0
        else:
            days_in_chat = 0
        
        # Социальная статистика (индексы могут отличаться в зависимости от структуры БД)
        hugs_given = target_user[6] if len(target_user) > 6 else 0
        hugs_received = target_user[7] if len(target_user) > 7 else 0
        slaps_given = target_user[8] if len(target_user) > 8 else 0
        slaps_received = target_user[9] if len(target_user) > 9 else 0
        beers_given = target_user[10] if len(target_user) > 10 else 0
        beers_received = target_user[11] if len(target_user) > 11 else 0
        respects_given = target_user[12] if len(target_user) > 12 else 0
        respects_received = target_user[13] if len(target_user) > 13 else 0
        
        # Предупреждения
        warns = target_user[14] if len(target_user) > 14 else 0
        
        profile_text = (
            f"👤 **Профиль @{target_name}**\n"
            f"────────────────\n"
            f"**Ранг:** {rank_name}\n"
            f"**Уровень:** {int(messages/100)+1 if messages else 1}\n"
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
            user_id, username, rank, messages = user[:4]
            rank_name = RANK_NAMES.get(rank, "Новичок")
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            
            top_text += f"{medal} @{username} — {messages} сообщ. ({rank_name})\n"
        
        await message.answer(top_text)
    
    @dp.message(Command("nextrank"))
    async def cmd_nextrank(message: Message):
        """Информация о следующем ранге"""
        user = db.get_user(message.from_user.id, message.from_user.username)
        
        rank = user[2]
        messages = user[5] if len(user) > 5 else 0
        
        # Дата присоединения
        join_date_str = user[3] if len(user) > 3 else None
        if join_date_str:
            try:
                join_date = datetime.datetime.fromisoformat(join_date_str)
                days_in_chat = (datetime.datetime.now() - join_date).days
            except:
                days_in_chat = 0
        else:
            days_in_chat = 0
        
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
    
    @dp.message(Command("level"))
    async def cmd_level(message: Message):
        """Уровень пользователя"""
        user = db.get_user(message.from_user.id, message.from_user.username)
        messages = user[5] if len(user) > 5 else 0
        
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
        messages = user[5] if len(user) > 5 else 0
        hugs_given = user[6] if len(user) > 6 else 0
        beers_given = user[10] if len(user) > 10 else 0
        respects_given = user[12] if len(user) > 12 else 0
        
        achievements = []
        
        # Проверяем достижения
        if messages >= 100:
            achievements.append("• 🗣 **Болтун** - 100 сообщений")
        if messages >= 1000:
            achievements.append("• 🏆 **Говорун** - 1000 сообщений")
        if messages >= 5000:
            achievements.append("• 📢 **Легенда чата** - 5000 сообщений")
        if hugs_given >= 10:
            achievements.append("• 🤗 **Душа компании** - 10 объятий")
        if hugs_given >= 50:
            achievements.append("• 🤗 **Обнимашка** - 50 объятий")
        if beers_given >= 10:
            achievements.append("• 🍺 **Пивной брат** - 10 угощений")
        if beers_given >= 50:
            achievements.append("• 🍻 **Алкобарон** - 50 угощений")
        if respects_given >= 10:
            achievements.append("• 👑 **Уважаемый** - 10 респектов")
        if respects_given >= 50:
            achievements.append("• 👑 **Авторитет** - 50 респектов")
        
        # Проверка на пивную дружбу
        relations = db.get_user_relations(message.from_user.id)
        if relations:
            for rel in relations:
                if rel[2] >= 10:  # beers_count
                    achievements.append(f"• 🍻 **Пивная дружба** с @{rel[1]} - 10+ пива")
                    break
        
        if not achievements:
            achievements = ["• Пока нет достижений. Активничай!"]
        
        await message.answer(
            f"🏅 **Достижения @{message.from_user.username}**\n\n" +
            "\n".join(achievements)
        )
    
    @dp.message(Command("ranks"))
    async def cmd_ranks(message: Message):
        """Список всех пользователей с рангами"""
        # Получаем всех пользователей с рангами
        users_with_ranks = db.get_users_with_ranks()
        
        if not users_with_ranks:
            await message.answer("❌ Пока нет пользователей с рангами")
            return
        
        # Группируем по рангам
        ranks_dict = {0: [], 1: [], 2: [], 3: [], 4: [], 5: []}
        for user in users_with_ranks:
            user_id, username, rank, messages = user[:4]
            if rank in ranks_dict:
                ranks_dict[rank].append((username, messages))
        
        text = "👑 **СПИСОК РАНГОВ**\n\n"
        
        for rank in range(5, -1, -1):  # от высшего к низшему
            if ranks_dict[rank]:
                text += f"**{RANK_NAMES[rank]}**\n"
                for username, messages in sorted(ranks_dict[rank], key=lambda x: x[1], reverse=True):
                    text += f"  • @{username} — {messages} сообщ.\n"
                text += "\n"
        
        await message.answer(text)
    
    @dp.message(Command("rank"))
    async def cmd_rank(message: Message):
        """Выдать ранг пользователю"""
        # Проверка прав
        user_rank = db.get_user_rank(message.from_user.id)
        
        args = message.text.split()
        if len(args) < 3:
            await message.answer("❌ Использование: `/rank @user [1-5]`")
            return
        
        # Получаем цель
        target_username = args[1].replace('@', '')
        try:
            target_rank = int(args[2])
        except ValueError:
            await message.answer("❌ Ранг должен быть числом от 1 до 5")
            return
        
        # Проверка ранга
        if target_rank < 1 or target_rank > 5:
            await message.answer("❌ Ранг должен быть от 1 до 5")
            return
        
        # Проверка прав на выдачу
        can_promote = False
        if user_rank == 5:  # Директор может всё
            can_promote = True
        elif user_rank == 4 and target_rank <= 3:  # Руководитель до 3
            can_promote = True
        elif user_rank == 3 and target_rank <= 2:  # Зам до 2
            can_promote = True
        elif user_rank == 2 and target_rank == 1:  # Святой только 1
            can_promote = True
        
        if not can_promote:
            await message.answer("❌ У тебя нет прав выдавать такой ранг")
            return
        
        # Ищем пользователя
        target_user = db.get_user_by_username(target_username)
        if not target_user:
            await message.answer(f"❌ Пользователь @{target_username} не найден")
            return
        
        # Выдаем ранг
        db.update_user_rank(target_user[0], target_rank, message.from_user.id, "Ручная выдача")
        
        await message.answer(
            f"✅ Пользователь @{target_username} повышен до ранга **{RANK_NAMES[target_rank]}**\n"
            f"Модератор: @{message.from_user.username}"
        )
        
        # Пробуем уведомить пользователя
        try:
            await message.bot.send_message(
                target_user[0],
                f"👑 Поздравляем! Ты повышен до ранга **{RANK_NAMES[target_rank]}**!"
            )
        except:
            pass
    
    @dp.message(Command("demote"))
    async def cmd_demote(message: Message):
        """Понизить пользователя"""
        # Проверка прав
        user_rank = db.get_user_rank(message.from_user.id)
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Использование: `/demote @user` или `/demote @user [ранг]`")
            return
        
        target_username = args[1].replace('@', '')
        
        # Определяем целевой ранг для понижения
        target_new_rank = 0  # по умолчанию до Новичка
        if len(args) >= 3:
            try:
                target_new_rank = int(args[2])
            except ValueError:
                await message.answer("❌ Ранг должен быть числом")
                return
        
        # Проверка прав
        if user_rank < 3:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        # Ищем пользователя
        target_user = db.get_user_by_username(target_username)
        if not target_user:
            await message.answer(f"❌ Пользователь @{target_username} не найден")
            return
        
        current_rank = target_user[2]
        
        # Проверка, что нельзя понизить вышестоящих
        if current_rank >= user_rank and user_rank != 5:
            await message.answer("❌ Нельзя понизить пользователя с равным или высшим рангом")
            return
        
        # Проверка целевого ранга
        if target_new_rank >= current_rank:
            await message.answer("❌ Целевой ранг должен быть меньше текущего")
            return
        
        # Понижаем
        db.update_user_rank(target_user[0], target_new_rank, message.from_user.id, "Понижение")
        
        await message.answer(
            f"✅ Пользователь @{target_username} понижен до ранга **{RANK_NAMES[target_new_rank]}**\n"
            f"Модератор: @{message.from_user.username}"
        )