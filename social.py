import random
from aiogram.types import Message
from aiogram.filters import Command

# Словарь с реакциями
HUG_MESSAGES = [
    "🤗 {giver} тепло обнял {receiver}!",
    "🫂 {giver} и {receiver} обнялись, как старые друзья!",
    "💞 {giver} подарил {receiver} обнимашку!",
    "🌟 {giver} обнял {receiver} так крепко, что тот засветился!",
]

SLAP_MESSAGES = [
    "👋 {giver} шлепнул {receiver}!",
    "🤚 {giver} дал {receiver} подзатыльник!",
    "😲 {giver} шлепнул {receiver} так, что искры из глаз!",
]

BEER_MESSAGES = [
    "🍺 {giver} угостил пивом {receiver}! Буль-буль-буль!",
    "🍻 {giver} наливает кружечку {receiver}! За здоровье!",
    "🍺 {giver} и {receiver} теперь пивные друзья!",
]

RESPECT_MESSAGES = [
    "👑 {giver} выражает глубокое уважение {receiver}!",
    "🎩 {giver} снимает шляпу перед {receiver}!",
    "🏆 {giver} ставит {receiver} на пьедестал почёта!",
]

HIGHFIVE_MESSAGES = [
    "🖐️ {giver} даёт пять {receiver}!",
    "✋ {giver} и {receiver} обмениваются хай-файвом!",
    "🤚 Есть контакт! {giver} и {receiver}!"
]

TEA_MESSAGES = [
    "🍵 {giver} приглашает {receiver} на чашечку чая!",
    "☕ {giver} наливает чай {receiver}! С плюшками!",
    "🫖 {giver} и {receiver} пьют чай и обсуждают жизнь!"
]

def setup_social_handlers(dp, db):
    """Регистрация социальных команд"""
    
    async def social_action(message: Message, action_type: str, messages_dict: list, update_db_func):
        """Общая функция для социальных действий"""
        # Проверяем, есть ли упоминание
        if not message.reply_to_message and len(message.text.split()) < 2:
            await message.answer(f"❌ Нужно указать пользователя. Например: `/{action_type} @user` или ответь на сообщение")
            return
        
        # Определяем получателя
        if message.reply_to_message:
            receiver = message.reply_to_message.from_user
        else:
            username = message.text.split()[1]
            if username.startswith('@'):
                username = username[1:]
            # Ищем пользователя в чате
            receiver = None
            # В реальном боте тут нужно получать информацию о пользователе по username
            # Для простоты будем считать, что пользователь есть
            receiver = message.from_user  # заглушка
        
        giver = message.from_user
        
        # Обновляем статистику в БД
        update_db_func(giver.id, receiver.id)
        
        # Выбираем случайное сообщение
        msg_template = random.choice(messages_dict)
        response = msg_template.format(giver=f"@{giver.username or giver.first_name}", 
                                        receiver=f"@{receiver.username or receiver.first_name}")
        
        await message.answer(response)
        
        # Проверяем на особые достижения
        await check_social_achievements(giver.id, receiver.id, action_type, db)
    
    @dp.message(Command("obn"))
    async def cmd_hug(message: Message):
        await social_action(
            message, 
            "obn", 
            HUG_MESSAGES, 
            lambda g, r: db.add_social_interaction(g, r, "hugs")
        )
    
    @dp.message(Command("slap"))
    async def cmd_slap(message: Message):
        await social_action(
            message, 
            "slap", 
            SLAP_MESSAGES, 
            lambda g, r: db.add_social_interaction(g, r, "slaps")
        )
    
    @dp.message(Command("givebeer"))
    async def cmd_givebeer(message: Message):
        await social_action(
            message, 
            "givebeer", 
            BEER_MESSAGES, 
            lambda g, r: db.add_social_interaction(g, r, "beers")
        )
        
        # Проверяем пивную дружбу
        if message.reply_to_message:
            giver = message.from_user.id
            receiver = message.reply_to_message.from_user.id
            
            beers_giver_to_receiver = db.get_beers_between(giver, receiver)
            beers_receiver_to_giver = db.get_beers_between(receiver, giver)
            
            if beers_giver_to_receiver >= 5 and beers_receiver_to_giver >= 5:
                await message.answer(
                    f"🍻🍻 **ПИВНАЯ ДРУЖБА!** 🍻🍻\n"
                    f"@{message.from_user.username} и @{message.reply_to_message.from_user.username} "
                    f"обменялись 5+ кружками! Они теперь пивные братья навек!"
                )
    
    @dp.message(Command("respect"))
    async def cmd_respect(message: Message):
        await social_action(
            message, 
            "respect", 
            RESPECT_MESSAGES, 
            lambda g, r: db.add_social_interaction(g, r, "respects")
        )
    
    @dp.message(Command("highfive"))
    async def cmd_highfive(message: Message):
        await social_action(
            message, 
            "highfive", 
            HIGHFIVE_MESSAGES, 
            lambda g, r: None  # пока без статистики
        )
    
    @dp.message(Command("tea"))
    async def cmd_tea(message: Message):
        await social_action(
            message, 
            "tea", 
            TEA_MESSAGES, 
            lambda g, r: None  # пока без статистики
        )
    
    # Команды для топов
    @dp.message(Command("topbeers"))
    async def cmd_topbeers(message: Message):
        """Топ по угощениям пивом"""
        top_users = db.get_top_by_stat("beers_given", limit=5)
        if not top_users:
            await message.answer("❌ Пока нет данных")
            return
        
        text = "🍺 **ТОП ПО УГОЩЕНИЯМ ПИВОМ**\n\n"
        for i, user in enumerate(top_users, 1):
            user_id, username, stat = user
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            text += f"{medal} @{username} — {stat} 🍺\n"
        
        await message.answer(text)
    
    @dp.message(Command("toprespects"))
    async def cmd_toprespects(message: Message):
        """Топ по уважению"""
        top_users = db.get_top_by_stat("respects_given", limit=5)
        if not top_users:
            await message.answer("❌ Пока нет данных")
            return
        
        text = "👑 **ТОП ПО ВЫРАЖЕНИЮ УВАЖЕНИЯ**\n\n"
        for i, user in enumerate(top_users, 1):
            user_id, username, stat = user
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            text += f"{medal} @{username} — {stat} 👑\n"
        
        await message.answer(text)
    
    @dp.message(Command("tophugs"))
    async def cmd_tophugs(message: Message):
        """Топ по обнимашкам"""
        top_users = db.get_top_by_stat("hugs_given", limit=5)
        if not top_users:
            await message.answer("❌ Пока нет данных")
            return
        
        text = "🤗 **ТОП ПО ОБНИМАШКАМ**\n\n"
        for i, user in enumerate(top_users, 1):
            user_id, username, stat = user
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            text += f"{medal} @{username} — {stat} 🤗\n"
        
        await message.answer(text)
    
    @dp.message(Command("topslaps"))
    async def cmd_topslaps(message: Message):
        """Топ по шлепкам"""
        top_users = db.get_top_by_stat("slaps_given", limit=5)
        if not top_users:
            await message.answer("❌ Пока нет данных")
            return
        
        text = "👊 **ТОП ПО ШЛЕПКАМ**\n\n"
        for i, user in enumerate(top_users, 1):
            user_id, username, stat = user
            medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
            text += f"{medal} @{username} — {stat} 👊\n"
        
        await message.answer(text)

async def check_social_achievements(giver_id, receiver_id, action, db):
    """Проверка социальных достижений"""
    # Здесь будет логика для ачивок
    pass