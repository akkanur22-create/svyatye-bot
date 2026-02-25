import random
from aiogram.types import Message
from aiogram.filters import Command

HUG_MESSAGES = [
    "🤗 {giver} тепло обнял {receiver}!",
    "🫂 {giver} и {receiver} обнялись, как старые друзья!",
    "💞 {giver} подарил {receiver} обнимашку!",
]

SLAP_MESSAGES = [
    "👋 {giver} шлепнул {receiver}!",
    "🤚 {giver} дал {receiver} подзатыльник!",
]

BEER_MESSAGES = [
    "🍺 {giver} угостил пивом {receiver}! Буль-буль-буль!",
    "🍻 {giver} наливает кружечку {receiver}! За здоровье!",
]

RESPECT_MESSAGES = [
    "👑 {giver} выражает глубокое уважение {receiver}!",
    "🎩 {giver} снимает шляпу перед {receiver}!",
]

HIGHFIVE_MESSAGES = [
    "🖐️ {giver} даёт пять {receiver}!",
    "✋ {giver} и {receiver} обмениваются хай-файвом!",
]

TEA_MESSAGES = [
    "🍵 {giver} приглашает {receiver} на чашечку чая!",
    "☕ {giver} наливает чай {receiver}! С плюшками!",
]

async def setup_social_handlers(dp, db):
    """Регистрация социальных команд"""
    print("📱 Настройка социальных команд...")
    
    @dp.message(Command("obn"))
    async def cmd_hug(message: Message):
        if not message.reply_to_message:
            await message.answer("❌ Нужно ответить на сообщение пользователя, которого хочешь обнять")
            return
        
        giver = message.from_user
        receiver = message.reply_to_message.from_user
        
        msg = random.choice(HUG_MESSAGES)
        await message.answer(msg.format(
            giver=f"@{giver.username or giver.first_name}",
            receiver=f"@{receiver.username or receiver.first_name}"
        ))
    
    @dp.message(Command("slap"))
    async def cmd_slap(message: Message):
        if not message.reply_to_message:
            await message.answer("❌ Нужно ответить на сообщение пользователя, которого хочешь шлепнуть")
            return
        
        giver = message.from_user
        receiver = message.reply_to_message.from_user
        
        msg = random.choice(SLAP_MESSAGES)
        await message.answer(msg.format(
            giver=f"@{giver.username or giver.first_name}",
            receiver=f"@{receiver.username or receiver.first_name}"
        ))
    
    @dp.message(Command("givebeer"))
    async def cmd_givebeer(message: Message):
        if not message.reply_to_message:
            await message.answer("❌ Нужно ответить на сообщение пользователя, которого хочешь угостить пивом")
            return
        
        giver = message.from_user
        receiver = message.reply_to_message.from_user
        
        msg = random.choice(BEER_MESSAGES)
        await message.answer(msg.format(
            giver=f"@{giver.username or giver.first_name}",
            receiver=f"@{receiver.username or receiver.first_name}"
        ))
    
    @dp.message(Command("respect"))
    async def cmd_respect(message: Message):
        if not message.reply_to_message:
            await message.answer("❌ Нужно ответить на сообщение пользователя, которому хочешь выразить уважение")
            return
        
        giver = message.from_user
        receiver = message.reply_to_message.from_user
        
        msg = random.choice(RESPECT_MESSAGES)
        await message.answer(msg.format(
            giver=f"@{giver.username or giver.first_name}",
            receiver=f"@{receiver.username or receiver.first_name}"
        ))
    
    @dp.message(Command("highfive"))
    async def cmd_highfive(message: Message):
        if not message.reply_to_message:
            await message.answer("❌ Нужно ответить на сообщение пользователя")
            return
        
        giver = message.from_user
        receiver = message.reply_to_message.from_user
        
        msg = random.choice(HIGHFIVE_MESSAGES)
        await message.answer(msg.format(
            giver=f"@{giver.username or giver.first_name}",
            receiver=f"@{receiver.username or receiver.first_name}"
        ))
    
    @dp.message(Command("tea"))
    async def cmd_tea(message: Message):
        if not message.reply_to_message:
            await message.answer("❌ Нужно ответить на сообщение пользователя")
            return
        
        giver = message.from_user
        receiver = message.reply_to_message.from_user
        
        msg = random.choice(TEA_MESSAGES)
        await message.answer(msg.format(
            giver=f"@{giver.username or giver.first_name}",
            receiver=f"@{receiver.username or receiver.first_name}"
        ))
    
    @dp.message(Command("topbeers"))
    async def cmd_topbeers(message: Message):
        await message.answer("🍺 Топ по пиву скоро появится!")
    
    @dp.message(Command("toprespects"))
    async def cmd_toprespects(message: Message):
        await message.answer("👑 Топ по уважению скоро появится!")
    
    @dp.message(Command("tophugs"))
    async def cmd_tophugs(message: Message):
        await message.answer("🤗 Топ по обнимашкам скоро появится!")
    
    @dp.message(Command("topslaps"))
    async def cmd_topslaps(message: Message):
        await message.answer("👊 Топ по шлепкам скоро появится!")
    
    print("✅ Социальные команды загружены")
    return dp