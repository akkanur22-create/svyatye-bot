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
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    rank INTEGER DEFAULT 0,
                    join_date DATETIME,
                    last_message_date DATETIME,
                    messages INTEGER DEFAULT 0,
                    hugs_given INTEGER DEFAULT 0,
                    hugs_received INTEGER DEFAULT 0,
                    slaps_given INTEGER DEFAULT 0,
                    slaps_received INTEGER DEFAULT 0,
                    beers_given INTEGER DEFAULT 0,
                    beers_received INTEGER DEFAULT 0,
                    respects_given INTEGER DEFAULT 0,
                    respects_received INTEGER DEFAULT 0,
                    warns INTEGER DEFAULT 0,
                    is_muted BOOLEAN DEFAULT FALSE,
                    mute_end_date DATETIME,
                    is_banned BOOLEAN DEFAULT FALSE
                )
            """)
            
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
            conn.commit()
    
    def get_user(self, user_id, username=None):
        with self.get_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", 
                (user_id,)
            ).fetchone()
            
            if not user:
                now = datetime.datetime.now()
                conn.execute("""
                    INSERT INTO users (user_id, username, join_date, last_message_date)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username, now, now))
                conn.commit()
                
                user = conn.execute(
                    "SELECT * FROM users WHERE user_id = ?", 
                    (user_id,)
                ).fetchone()
            else:
                if username and (not user[1] or username != user[1]):
                    conn.execute(
                        "UPDATE users SET username = ? WHERE user_id = ?",
                        (username, user_id)
                    )
                    conn.commit()
                    user = conn.execute(
                        "SELECT * FROM users WHERE user_id = ?", 
                        (user_id,)
                    ).fetchone()
            
            return user
    
    def get_user_by_username(self, username):
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()
    
    def get_user_rank(self, user_id):
        with self.get_connection() as conn:
            result = conn.execute(
                "SELECT rank FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            return result[0] if result else 0
    
    def update_user_rank(self, user_id, new_rank, promoted_by=None, reason=None):
        with self.get_connection() as conn:
            old_rank = conn.execute(
                "SELECT rank FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            old_rank = old_rank[0] if old_rank else 0
            
            conn.execute(
                "UPDATE users SET rank = ? WHERE user_id = ?",
                (new_rank, user_id)
            )
            
            conn.execute("""
                INSERT INTO promotion_logs (user_id, old_rank, new_rank, promoted_by, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, old_rank, new_rank, promoted_by, reason))
            conn.commit()
    
    def update_messages_count(self, user_id):
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE users 
                SET messages = messages + 1,
                    last_message_date = ?
                WHERE user_id = ?
            """, (datetime.datetime.now(), user_id))
            conn.commit()
    
    def get_top_users(self, limit=10):
        with self.get_connection() as conn:
            return conn.execute("""
                SELECT user_id, username, rank, messages 
                FROM users 
                ORDER BY messages DESC 
                LIMIT ?
            """, (limit,)).fetchall()
    
    def get_users_with_ranks(self):
        with self.get_connection() as conn:
            return conn.execute("""
                SELECT user_id, username, rank, messages 
                FROM users 
                WHERE rank > 0
                ORDER BY rank DESC, messages DESC
            """).fetchall()
    
    def get_users_with_rank_above(self, min_rank):
        with self.get_connection() as conn:
            return conn.execute("""
                SELECT user_id, username, rank 
                FROM users 
                WHERE rank > ?
                ORDER BY rank DESC
            """, (min_rank,)).fetchall()
    
    def get_all_users(self):
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM users").fetchall()
    
    def add_warn(self, user_id):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET warns = warns + 1 WHERE user_id = ?",
                (user_id,)
            )
            conn.commit()
            result = conn.execute(
                "SELECT warns FROM users WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            return result[0] if result else 0