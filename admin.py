from aiogram.types import Message
from aiogram.filters import Command

async def setup_admin_handlers(dp, db):
    """Регистрация админ-команд"""
    
    @dp.message(Command("warn"))
    async def cmd_warn(message: Message):
        """Выдать предупреждение"""
        # Проверка прав пользователя
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 1:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        # Проверяем, указан ли пользователь
        if not message.reply_to_message and len(message.text.split()) < 2:
            await message.answer("❌ Нужно указать пользователя. Например: `/warn @user` или ответь на сообщение")
            return
        
        # Определяем нарушителя
        if message.reply_to_message:
            target = message.reply_to_message.from_user
        else:
            username = message.text.split()[1]
            if username.startswith('@'):
                username = username[1:]
            # Ищем пользователя по username
            target = None  # заглушка
            await message.answer("❌ Пользователь не найден")
            return
        
        # Получаем причину
        reason = "Без причины"
        parts = message.text.split(maxsplit=2)
        if len(parts) >= 3:
            reason = parts[2]
        
        # Добавляем предупреждение
        warns = db.add_warn(target.id)
        
        # Ответ в чат
        await message.answer(
            f"⚠️ **Предупреждение**\n"
            f"Пользователь: @{target.username or target.first_name}\n"
            f"Модератор: @{message.from_user.username}\n"
            f"Причина: {reason}\n"
            f"Всего предупреждений: {warns}/6"
        )
        
        # Проверяем на автоматическое наказание
        if warns >= 6:
            # Бан
            db.ban_user(target.id)
            await message.answer(f"🚫 @{target.username} забанен (6/6 предупреждений)")
        elif warns >= 5:
            # Кик
            await message.answer(f"👢 @{target.username} будет кикнут (5/6 предупреждений)")
        elif warns >= 3:
            # Мут
            mute_time = 3600 if warns == 3 else 86400  # 1 час или 1 день
            db.mute_user(target.id, mute_time)
            await message.answer(f"🔇 @{target.username} замучен на {'1 час' if warns==3 else '1 день'} (3/6 предупреждений)")
    
    @dp.message(Command("mute"))
    async def cmd_mute(message: Message):
        """Замутить пользователя"""
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 1:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        await message.answer("⚙️ Команда в разработке")
    
    @dp.message(Command("kick"))
    async def cmd_kick(message: Message):
        """Выгнать пользователя"""
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 2:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        await message.answer("⚙️ Команда в разработке")
    
    @dp.message(Command("ban"))
    async def cmd_ban(message: Message):
        """Забанить пользователя"""
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 3:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        await message.answer("⚙️ Команда в разработке")
    
    @dp.message(Command("rank"))
    async def cmd_rank(message: Message):
        """Выдать ранг пользователю"""
        user_rank = db.get_user_rank(message.from_user.id)
        
        # Проверяем права
        args = message.text.split()
        if len(args) < 3:
            await message.answer("❌ Использование: `/rank @user [1-5]`")
            return
        
        try:
            target_rank = int(args[2])
        except ValueError:
            await message.answer("❌ Ранг должен быть числом от 1 до 5")
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
        
        # В реальном коде тут выдача ранга
        await message.answer(f"✅ Ранг {target_rank} выдан пользователю {args[1]}")
    
    @dp.message(Command("demote"))
    async def cmd_demote(message: Message):
        """Понизить пользователя"""
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 3:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        await message.answer("⚙️ Команда в разработке")
    
    @dp.message(Command("votekick"))
    async def cmd_votekick(message: Message):
        """Голосование за кик"""
        await message.answer("⚙️ Команда в разработке")