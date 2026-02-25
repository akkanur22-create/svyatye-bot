import sqlite3
import datetime
import os

class Database:
    def __init__(self):
        # Используем абсолютный путь для SQLite
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
                    messages INTEGER DEFAULT 0,
                    join_date DATETIME,
                    last_message_date DATETIME,
                    hugs_given INTEGER DEFAULT 0,
                    hugs_received INTEGER DEFAULT 0,
                    slaps_given INTEGER DEFAULT 0,
                    slaps_received INTEGER DEFAULT 0,
                    beers_given INTEGER DEFAULT 0,
                    beers_received INTEGER DEFAULT 0,
                    respects_given INTEGER DEFAULT 0,
                    respects_received INTEGER DEFAULT 0,
                    warns INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS relations (
                    user1_id INTEGER,
                    user2_id INTEGER,
                    beers_count INTEGER DEFAULT 0,
                    PRIMARY KEY (user1_id, user2_id)
                )
            """)
    
    def get_user(self, user_id, username=None):
        with self.get_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", 
                (user_id,)
            ).fetchone()
            
            if not user:
                conn.execute("""
                    INSERT INTO users (user_id, username, join_date, last_message_date)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username, datetime.datetime.now(), datetime.datetime.now()))
                
                user = conn.execute(
                    "SELECT * FROM users WHERE user_id = ?", 
                    (user_id,)
                ).fetchone()
            
            return user