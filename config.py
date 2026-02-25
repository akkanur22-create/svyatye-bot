import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Будет взято из переменных окружения Render

# Названия рангов
RANK_NAMES = {
    0: "Новичок",
    1: "Стажер.Святых",
    2: "Святой",
    3: "Зам.Руководителя",
    4: "Руководитель святых",
    5: "Директор святых"
}

# Требования для автоматического повышения
RANK_REQUIREMENTS = {
    1: {"days": 5, "messages": 500, "auto": True},
    2: {"days": 30, "messages": 3000, "auto": True},
    3: {"auto": False},  # Только ручная выдача
    4: {"auto": False},
    5: {"auto": False}
}