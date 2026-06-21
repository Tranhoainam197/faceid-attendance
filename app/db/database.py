"""
Quản lý kết nối SQLite duy nhất cho toàn ứng dụng (Singleton).
Schema gồm 3 bảng: students, sessions, attendance.
Embedding khuôn mặt được lưu dạng BLOB (numpy.tobytes()).
"""
import os
import sqlite3
import threading

from config import DB_PATH, DATA_DIR


class Database:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_connection()
        return cls._instance

    def _init_connection(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_schema()

    def _create_schema(self):
        cur = self.conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                embedding BLOB NOT NULL,
                num_samples INTEGER DEFAULT 0,
                quality_score REAL DEFAULT 0,
                model_name TEXT DEFAULT 'buffalo_l',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                status TEXT NOT NULL DEFAULT 'open'
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                student_id TEXT NOT NULL,
                student_name TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'present',
                similarity REAL,
                UNIQUE(session_id, student_id),
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        """)

        self.conn.commit()

    def get_connection(self):
        return self.conn

    def close(self):
        if self.conn:
            self.conn.close()