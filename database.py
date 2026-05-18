import sqlite3
import json
from datetime import datetime

DB_PATH = "results.db"

class Database:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    full_name TEXT,
                    region TEXT,
                    post TEXT,
                    document TEXT,
                    total INTEGER,
                    correct INTEGER,
                    wrong INTEGER,
                    percent REAL,
                    start_time TEXT,
                    end_time TEXT
                )
            """)
            conn.commit()

    def save_result(self, user_id, username, full_name, region, post,
                    document, total, correct, wrong, percent, start_time, end_time):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO results
                (user_id, username, full_name, region, post, document,
                 total, correct, wrong, percent, start_time, end_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, full_name, region, post, document,
                  total, correct, wrong, percent, start_time, end_time))
            conn.commit()

    def get_all_results(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM results ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]

    def get_user_results(self, user_id):
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM results WHERE user_id=? ORDER BY id DESC", (user_id,)
            ).fetchall()
            return [dict(r) for r in rows]
