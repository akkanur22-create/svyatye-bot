import sqlite3
import datetime
import os

class Database:
    def __init__(self):
        db_path = os.path.join(os.path.dirname(__file__), "bot_database.db")
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        """Создание таблиц"""
        with self.get_connection() as conn:
            # Таблица пользователей
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    rank INTEGER DEFAULT 0,
                    join_date DATETIME,
                    last_message_date DATETIME,
                    messages INTEGER DEFAULT 0,
                    
                    -- Социальная статистика
                    hugs_given INTEGER DEFAULT 0,
                    hugs_received INTEGER DEFAULT 0,
                    slaps_given INTEGER DEFAULT 0,
                    slaps_received INTEGER DEFAULT 0,
                    beers_given INTEGER DEFAULT 0,
                    beers_received INTEGER DEFAULT 0,
                    respects_given INTEGER DEFAULT 0,
                    respects_received INTEGER DEFAULT 0,
                    
                    -- Модерация
                    warns INTEGER DEFAULT 0,
                    is_muted BOOLEAN DEFAULT FALSE,
                    mute_end_date DATETIME,
                    is_banned BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Таблица отношений между пользователями
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relations (
                    user1_id INTEGER,
                    user2_id INTEGER,
                    beers_count INTEGER DEFAULT 0,
                    hugs_count INTEGER DEFAULT 0,
                    slaps_count INTEGER DEFAULT 0,
                    respects_count INTEGER DEFAULT 0,
                    last_interaction DATETIME,
                    PRIMARY KEY (user1_id, user2_id)
                )
            """)
            
            # Таблица логов повышений
            conn.execute("""
                CREATE TABLE IF NOT EXISTS promotion_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    old_rank INTEGER,
                    new_rank INTEGER,
                    promoted_by INTEGER,
                    reason TEXT,
                    date DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица голосований
            conn.execute("""
                CREATE TABLE IF NOT EXISTS votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    target_user_id INTEGER,
                    vote_type TEXT,
                    created_by INTEGER,
                    yes_votes INTEGER DEFAULT 0,
                    no_votes INTEGER DEFAULT 0,
                    end_date DATETIME,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Таблица голосов пользователей
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vote_votes (
                    vote_id INTEGER,
                    user_id INTEGER,
                    vote BOOLEAN,  -- TRUE = за, FALSE = против
                    PRIMARY KEY (vote_id, user_id)
                )
            """)
    
    def get_user(self, user_id, username=None):
        """Получить или создать пользователя"""
        with self.get_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", 
                (user_id,)
            ).fetchone()
            
            if not user:
                # Создаём нового пользователя
                now = datetime.datetime.now()
                conn.execute("""
                    INSERT INTO users (user_id, username, join_date, last_message_date)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username, now, now))
                
                user = conn.execute(
                    "SELECT * FROM users WHERE user_id = ?", 
                    (user_id,)
                ).fetchone()
            else:
                # Обновляем username если изменился
                if username and (not user[1] or username != user[1]):
                    conn.execute(
                        "UPDATE users SET username = ? WHERE user_id = ?",
                        (username, user_id)
                    )
                    user = list(user)
                    user[1] = username
            
            return user
    
    def get_user_by_username(self, username):
        """Найти пользователя по username"""
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()
    
    def get_user_rank(self, user_id):
        """Получить ранг пользователя"""
        with self.get_connection() as conn:
            result = conn.execute(
                "SELECT rank FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            return result[0] if result else 0
    
    def update_user_rank(self, user_id, new_rank, promoted_by=None, reason=None):
        """Обновить ранг пользователя"""
        with self.get_connection() as conn:
            # Получаем старый ранг
            old_rank = conn.execute(
                "SELECT rank FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            old_rank = old_rank[0] if old_rank else 0
            
            # Обновляем ранг
            conn.execute(
                "UPDATE users SET rank = ? WHERE user_id = ?",
                (new_rank, user_id)
            )
            
            # Логируем
            conn.execute("""
                INSERT INTO promotion_logs (user_id, old_rank, new_rank, promoted_by, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, old_rank, new_rank, promoted_by, reason))
    
    def add_social_interaction(self, from_id, to_id, action_type):
        """Добавить социальное взаимодействие"""
        with self.get_connection() as conn:
            # Обновляем счётчики дающего
            conn.execute(f"""
                UPDATE users 
                SET {action_type}_given = {action_type}_given + 1,
                    last_message_date = ?
                WHERE user_id = ?
            """, (datetime.datetime.now(), from_id))
            
            # Обновляем счётчики получающего
            conn.execute(f"""
                UPDATE users 
                SET {action_type}_received = {action_type}_received + 1
                WHERE user_id = ?
            """, (to_id,))
            
            # Обновляем отношения
            now = datetime.datetime.now()
            conn.execute(f"""
                INSERT INTO relations (user1_id, user2_id, {action_type}_count, last_interaction)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(user1_id, user2_id) DO UPDATE SET
                    {action_type}_count = {action_type}_count + 1,
                    last_interaction = ?
            """, (from_id, to_id, now, now))
    
    def get_beers_between(self, user1_id, user2_id):
        """Получить количество пивных угощений между пользователями"""
        with self.get_connection() as conn:
            result = conn.execute(
                "SELECT beers_count FROM relations WHERE user1_id = ? AND user2_id = ?",
                (user1_id, user2_id)
            ).fetchone()
            return result[0] if result else 0
    
    def add_warn(self, user_id):
        """Добавить предупреждение"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET warns = warns + 1 WHERE user_id = ?",
                (user_id,)
            )
            result = conn.execute(
                "SELECT warns FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            return result[0] if result else 0
    
    def get_top_users(self, limit=10):
        """Топ пользователей по сообщениям"""
        with self.get_connection() as conn:
            return conn.execute("""
                SELECT user_id, username, rank, messages 
                FROM users 
                ORDER BY messages DESC 
                LIMIT ?
            """, (limit,)).fetchall()
    
    def get_top_by_stat(self, stat_name, limit=5):
        """Топ по определенной статистике"""
        with self.get_connection() as conn:
            return conn.execute(f"""
                SELECT user_id, username, {stat_name}
                FROM users 
                WHERE {stat_name} > 0
                ORDER BY {stat_name} DESC 
                LIMIT ?
            """, (limit,)).fetchall()
    
    def get_all_users(self):
        """Получить всех пользователей"""
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM users").fetchall()
    
    def update_messages_count(self, user_id):
        """Обновить счётчик сообщений"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE users 
                SET messages = messages + 1,
                    last_message_date = ?
                WHERE user_id = ?
            """, (datetime.datetime.now(), user_id))