from aiogram.types import Message
from aiogram.filters import Command
import datetime
import re

async def setup_admin_handlers(dp, db):
    """Регистрация админ-команд"""
    
    def parse_time(time_str):
        """Парсит время из строки (10min, 1h, 2d)"""
        match = re.match(r'(\d+)(min|h|d|m)', time_str.lower())
        if not match:
            return None
        
        value, unit = int(match.group(1)), match.group(2)
        if unit == 'min':
            return value * 60
        elif unit == 'h':
            return value * 3600
        elif unit == 'd':
            return value * 86400
        elif unit == 'm':
            return value * 30 * 86400  # месяц примерно
        return None
    
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
            target_user = db.get_user_by_username(username)
            if not target_user:
                await message.answer(f"❌ Пользователь @{username} не найден")
                return
            # Создаем объект пользователя для ответа
            target = type('User', (), {'id': target_user[0], 'username': username, 'first_name': username})()
        
        # Получаем причину
        reason = "Без причины"
        parts = message.text.split(maxsplit=2)
        if len(parts) >= 3:
            reason = parts[2]
        elif message.reply_to_message and len(message.text.split()) > 1:
            reason = message.text.split(maxsplit=1)[1]
        
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
        
        # Проверяем аргументы
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Использование: `/mute @user [время] [причина]`\nПример: `/mute @user 10min флуд`")
            return
        
        username = args[1].replace('@', '')
        target_user = db.get_user_by_username(username)
        if not target_user:
            await message.answer(f"❌ Пользователь @{username} не найден")
            return
        
        # Парсим время
        mute_duration = 3600  # 1 час по умолчанию
        reason = "Без причины"
        
        if len(args) >= 3:
            # Проверяем, является ли второй аргумент временем
            parsed_time = parse_time(args[2])
            if parsed_time:
                mute_duration = parsed_time
                if len(args) >= 4:
                    reason = ' '.join(args[3:])
            else:
                reason = ' '.join(args[2:])
        
        # Мьютим
        db.mute_user(target_user[0], mute_duration)
        
        # Форматируем время для вывода
        if mute_duration < 3600:
            time_str = f"{mute_duration//60} мин"
        elif mute_duration < 86400:
            time_str = f"{mute_duration//3600} ч"
        else:
            time_str = f"{mute_duration//86400} дн"
        
        await message.answer(
            f"🔇 **Мут**\n"
            f"Пользователь: @{username}\n"
            f"Модератор: @{message.from_user.username}\n"
            f"Длительность: {time_str}\n"
            f"Причина: {reason}"
        )
    
    @dp.message(Command("unmute"))
    async def cmd_unmute(message: Message):
        """Снять мут"""
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 2:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Использование: `/unmute @user`")
            return
        
        username = args[1].replace('@', '')
        target_user = db.get_user_by_username(username)
        if not target_user:
            await message.answer(f"❌ Пользователь @{username} не найден")
            return
        
        db.unmute_user(target_user[0])
        await message.answer(f"🔊 С пользователя @{username} снят мут")
    
    @dp.message(Command("kick"))
    async def cmd_kick(message: Message):
        """Выгнать пользователя"""
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 2:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        args = message.text.split()
        if len(args) < 2 and not message.reply_to_message:
            await message.answer("❌ Использование: `/kick @user [причина]`")
            return
        
        # Определяем цель
        if message.reply_to_message:
            target = message.reply_to_message.from_user
            username = target.username or target.first_name
            reason = ' '.join(args[1:]) if len(args) > 1 else "Без причины"
        else:
            username = args[1].replace('@', '')
            target_user = db.get_user_by_username(username)
            if not target_user:
                await message.answer(f"❌ Пользователь @{username} не найден")
                return
            target = type('User', (), {'id': target_user[0], 'username': username})()
            reason = ' '.join(args[2:]) if len(args) > 2 else "Без причины"
        
        # Здесь должен быть вызов API Telegram для кика
        # await message.bot.kick_chat_member(message.chat.id, target.id)
        
        await message.answer(
            f"👢 **Кик**\n"
            f"Пользователь: @{username}\n"
            f"Модератор: @{message.from_user.username}\n"
            f"Причина: {reason}"
        )
    
    @dp.message(Command("ban"))
    async def cmd_ban(message: Message):
        """Забанить пользователя"""
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 3:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        args = message.text.split()
        if len(args) < 2 and not message.reply_to_message:
            await message.answer("❌ Использование: `/ban @user [причина]`")
            return
        
        if message.reply_to_message:
            target = message.reply_to_message.from_user
            username = target.username or target.first_name
            reason = ' '.join(args[1:]) if len(args) > 1 else "Без причины"
        else:
            username = args[1].replace('@', '')
            reason = ' '.join(args[2:]) if len(args) > 2 else "Без причины"
        
        db.ban_user(target.id if 'target' in locals() else target_user[0])
        
        await message.answer(
            f"🚫 **Бан**\n"
            f"Пользователь: @{username}\n"
            f"Модератор: @{message.from_user.username}\n"
            f"Причина: {reason}"
        )
    
    @dp.message(Command("unban"))
    async def cmd_unban(message: Message):
        """Разбанить пользователя"""
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 3:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        args = message.text.split()
        if len(args) < 2:
            await message.answer("❌ Использование: `/unban @user`")
            return
        
        username = args[1].replace('@', '')
        target_user = db.get_user_by_username(username)
        if not target_user:
            await message.answer(f"❌ Пользователь @{username} не найден")
            return
        
        db.unban_user(target_user[0])
        await message.answer(f"✅ Пользователь @{username} разбанен")
    
    @dp.message(Command("votekick"))
    async def cmd_votekick(message: Message):
        """Голосование за кик"""
        if len(message.text.split()) < 2 and not message.reply_to_message:
            await message.answer("❌ Использование: `/votekick @user [причина]`")
            return
        
        if message.reply_to_message:
            target = message.reply_to_message.from_user
            username = target.username or target.first_name
            reason = ' '.join(message.text.split()[1:]) if len(message.text.split()) > 1 else "Без причины"
        else:
            username = message.text.split()[1].replace('@', '')
            reason = ' '.join(message.text.split()[2:]) if len(message.text.split()) > 2 else "Без причины"
        
        # Создаем голосование
        vote_id = db.create_vote(message.chat.id, target.id, message.from_user.id, "kick")
        
        await message.answer(
            f"🗳 **Голосование за кик**\n"
            f"Пользователь: @{username}\n"
            f"Инициатор: @{message.from_user.username}\n"
            f"Причина: {reason}\n\n"
            f"Голосуйте: /yes {vote_id} или /no {vote_id}\n"
            f"Голосование продлится 5 минут"
        )