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

async def setup_rank_handlers(dp, db):
    """Регистрация обработчиков команд для рангов"""
    
    @dp.message(Command("profile"))
    async def cmd_profile(message: Message):
        """Просмотр профиля"""
        # Определяем, чей профиль смотрим
        args = message.text.split()
        if len(args) > 1 and args[1].startswith('@'):
            # Профиль другого пользователя
            username = args[1][1:]
            user = db.get_user_by_username(username)
            if not user:
                await message.answer(f"❌ Пользователь {args[1]} не найден")
                return
            target_name = username
            target_user = user
        else:
            # Свой профиль
            target_name = message.from_user.username
            target_user = db.get_user(message.from_user.id, target_name)
        
        # Получаем данные
        rank = target_user[2]
        rank_name = RANK_NAMES.get(rank, "Неизвестно")
        messages = target_user[5] if len(target_user) > 5 else 0
        
        # Дата присоединения
        join_date_str = target_user[3] if len(target_user) > 3 else None
        days_in_chat = 0
        if join_date_str:
            try:
                join_date = datetime.datetime.fromisoformat(join_date_str)
                days_in_chat = (datetime.datetime.now() - join_date).days
            except:
                pass
        
        profile_text = (
            f"👤 **Профиль @{target_name}**\n"
            f"────────────────\n"
            f"**Ранг:** {rank_name}\n"
            f"**Уровень:** {int(messages/100)+1 if messages else 1}\n"
            f"────────────────\n"
            f"📊 **Статистика:**\n"
            f"📝 Сообщений: {messages}\n"
            f"📅 Дней в чате: {days_in_chat}\n"
        )
        
        await message.answer(profile_text)
    
    @dp.message(Command("top"))
    async def cmd_top(message: Message):
        """Топ пользователей по сообщениям"""
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
        
        if rank >= 5:
            await message.answer("💎 Ты достиг максимального ранга!")
            return
        
        next_rank = rank + 1
        
        if next_rank not in RANK_REQUIREMENTS:
            await message.answer(f"👑 Ранг '{RANK_NAMES[next_rank]}' выдается только вручную.")
            return
        
        req = RANK_REQUIREMENTS[next_rank]
        
        # Получаем дни в чате
        join_date_str = user[3] if len(user) > 3 else None
        days_in_chat = 0
        if join_date_str:
            try:
                join_date = datetime.datetime.fromisoformat(join_date_str)
                days_in_chat = (datetime.datetime.now() - join_date).days
            except:
                pass
        
        messages_needed = max(0, req["messages"] - messages)
        days_needed = max(0, req["days"] - days_in_chat)
        
        await message.answer(
            f"🎯 **Путь к рангу {RANK_NAMES[next_rank]}**\n\n"
            f"📝 Сообщений: {messages}/{req['messages']}\n"
            f"📅 Дней: {days_in_chat}/{req['days']}\n\n"
            f"Осталось: {messages_needed} сообщ. и {days_needed} дней"
        )
    
    @dp.message(Command("level"))
    async def cmd_level(message: Message):
        """Уровень пользователя"""
        user = db.get_user(message.from_user.id, message.from_user.username)
        messages = user[5] if len(user) > 5 else 0
        level = int(messages / 100) + 1
        next_level = (level * 100) - messages
        
        await message.answer(
            f"📊 **Уровень @{message.from_user.username}**\n"
            f"Текущий уровень: **{level}**\n"
            f"Сообщений: {messages}\n"
            f"До следующего уровня: {next_level} сообщ."
        )
    
    @dp.message(Command("achievements"))
    async def cmd_achievements(message: Message):
        """Достижения пользователя"""
        user = db.get_user(message.from_user.id, message.from_user.username)
        
        messages = user[5] if len(user) > 5 else 0
        
        achievements = []
        
        if messages >= 100:
            achievements.append("• 🗣 **Болтун** - 100 сообщений")
        if messages >= 1000:
            achievements.append("• 🏆 **Говорун** - 1000 сообщений")
        if messages >= 5000:
            achievements.append("• 📢 **Легенда чата** - 5000 сообщений")
        
        if not achievements:
            achievements = ["• Пока нет достижений. Активничай!"]
        
        await message.answer(
            f"🏅 **Достижения @{message.from_user.username}**\n\n" +
            "\n".join(achievements)
        )
    
    @dp.message(Command("ranks"))
    async def cmd_ranks(message: Message):
        """Список всех пользователей с рангами"""
        users_with_ranks = db.get_users_with_ranks()
        
        if not users_with_ranks:
            await message.answer("❌ Пока нет пользователей с рангами")
            return
        
        ranks_dict = {0: [], 1: [], 2: [], 3: [], 4: [], 5: []}
        for user in users_with_ranks:
            user_id, username, rank, messages = user[:4]
            if rank in ranks_dict:
                ranks_dict[rank].append((username, messages))
        
        text = "👑 **СПИСОК РАНГОВ**\n\n"
        
        for rank in range(5, -1, -1):
            if ranks_dict[rank]:
                text += f"**{RANK_NAMES[rank]}**\n"
                for username, messages in sorted(ranks_dict[rank], key=lambda x: x[1], reverse=True):
                    text += f"  • @{username} — {messages} сообщ.\n"
                text += "\n"
        
        await message.answer(text)
    
    @dp.message(Command("rank"))
    async def cmd_rank(message: Message):
        """Выдать ранг пользователю"""
        user_rank = db.get_user_rank(message.from_user.id)
        
        if user_rank < 2:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        args = message.text.split()
        if len(args) < 3:
            await message.answer("❌ Использование: `/rank @user [1-5]`")
            return
        
        target_username = args[1].replace('@', '')
        try:
            target_rank = int(args[2])
        except ValueError:
            await message.answer("❌ Ранг должен быть числом от 1 до 5")
            return
        
        if target_rank < 1 or target_rank > 5:
            await message.answer("❌ Ранг должен быть от 1 до 5")
            return
        
        # Проверка прав
        can_promote = False
        if user_rank == 5:
            can_promote = True
        elif user_rank == 4 and target_rank <= 3:
            can_promote = True
        elif user_rank == 3 and target_rank <= 2:
            can_promote = True
        elif user_rank == 2 and target_rank == 1:
            can_promote = True
        
        if not can_promote:
            await message.answer("❌ У тебя нет прав выдавать такой ранг")
            return
        
        target_user = db.get_user_by_username(target_username)
        if not target_user:
            await message.answer(f"❌ Пользователь @{target_username} не найден")
            return
        
        db.update_user_rank(target_user[0], target_rank, message.from_user.id, "Ручная выдача")
        
        await message.answer(
            f"✅ Пользователь @{target_username} повышен до ранга **{RANK_NAMES[target_rank]}**"
        )
    
    @dp.message(Command("demote"))
    async def cmd_demote(message: Message):
        """Понизить пользователя"""
        user_rank = db.get_user_rank(message.from_user.id)
        
        if user_rank < 3:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Использование: `/demote @user`")
            return
        
        target_username = args[1].replace('@', '')
        target_user = db.get_user_by_username(target_username)
        
        if not target_user:
            await message.answer(f"❌ Пользователь @{target_username} не найден")
            return
        
        current_rank = target_user[2]
        if current_rank >= user_rank and user_rank != 5:
            await message.answer("❌ Нельзя понизить пользователя с равным или высшим рангом")
            return
        
        db.update_user_rank(target_user[0], 0, message.from_user.id, "Понижение")
        
        await message.answer(f"✅ Пользователь @{target_username} понижен до Новичка")
    
    print("✅ Ранговые команды загружены")
    return dp

async def check_auto_promotions(bot, db):
    """Автоматическая проверка повышений"""
    print("🔍 Проверка автоповышений...")
    
    users = db.get_all_users()
    promoted = 0
    
    for user in users:
        if len(user) < 6:
            continue
            
        user_id = user[0]
        username = user[1]
        rank = user[2]
        join_date_str = user[3]
        messages = user[5]
        
        if rank >= 2:
            continue
        
        # Вычисляем дни в чате
        days = 0
        if join_date_str:
            try:
                join_date = datetime.datetime.fromisoformat(join_date_str)
                days = (datetime.datetime.now() - join_date).days
            except:
                pass
        
        # Проверка на Стажера
        if rank == 0 and 1 in RANK_REQUIREMENTS:
            req = RANK_REQUIREMENTS[1]
            if messages >= req["messages"] and days >= req["days"]:
                db.update_user_rank(user_id, 1, None, "Автоматическое повышение")
                promoted += 1
                print(f"✅ @{username} повышен до Стажера")
        
        # Проверка на Святого
        elif rank == 1 and 2 in RANK_REQUIREMENTS:
            req = RANK_REQUIREMENTS[2]
            if messages >= req["messages"] and days >= req["days"]:
                db.update_user_rank(user_id, 2, None, "Автоматическое повышение")
                promoted += 1
                print(f"✅ @{username} повышен до Святого")
    
    print(f"✅ Автоповышений: {promoted}")
    return promoted