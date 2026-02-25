from aiogram.types import Message
from aiogram.filters import Command
import datetime
import re

def setup_admin_handlers(dp, db):
    """Регистрация админ-команд"""
    print("🛡 Настройка админ-команд...")
    
    def parse_time(time_str):
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
            return value * 30 * 86400
        return None
    
    @dp.message(Command("warn"))
    async def cmd_warn(message: Message):
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 1:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        if not message.reply_to_message:
            await message.answer("❌ Нужно ответить на сообщение пользователя")
            return
        
        target = message.reply_to_message.from_user
        reason = message.text.replace('/warn', '').strip() or "Без причины"
        
        warns = db.add_warn(target.id)
        
        await message.answer(
            f"⚠️ **Предупреждение**\n"
            f"Пользователь: @{target.username or target.first_name}\n"
            f"Модератор: @{message.from_user.username}\n"
            f"Причина: {reason}\n"
            f"Всего предупреждений: {warns}/6"
        )
    
    @dp.message(Command("mute"))
    async def cmd_mute(message: Message):
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 1:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        await message.answer("🔇 Команда /mute в разработке")
    
    @dp.message(Command("unmute"))
    async def cmd_unmute(message: Message):
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 2:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        await message.answer("🔊 Команда /unmute в разработке")
    
    @dp.message(Command("kick"))
    async def cmd_kick(message: Message):
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 2:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        await message.answer("👢 Команда /kick в разработке")
    
    @dp.message(Command("ban"))
    async def cmd_ban(message: Message):
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 3:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        await message.answer("🚫 Команда /ban в разработке")
    
    @dp.message(Command("unban"))
    async def cmd_unban(message: Message):
        user_rank = db.get_user_rank(message.from_user.id)
        if user_rank < 3:
            await message.answer("❌ У тебя нет прав для этой команды")
            return
        
        await message.answer("✅ Команда /unban в разработке")
    
    @dp.message(Command("votekick"))
    async def cmd_votekick(message: Message):
        await message.answer("🗳 Команда /votekick в разработке")
    
    @dp.message(Command("admins"))
    async def cmd_admins(message: Message):
        admins = db.get_users_with_rank_above(2)
        
        if not admins:
            await message.answer("👑 Список руководства пока пуст")
            return
        
        text = "👑 **РУКОВОДСТВО ЧАТА**\n\n"
        
        for admin in admins:
            user_id, username, rank = admin[:3]
            rank_name = {
                3: "🔰 Зам.Руководителя",
                4: "👑 Руководитель святых",
                5: "💎 Директор святых"
            }.get(rank, "Неизвестно")
            
            text += f"• @{username} — {rank_name}\n"
        
        await message.answer(text)
    
    print("✅ Админ-команды загружены")
    return dp