"""
Repository quản lý buổi học/ca làm (sessions).
status chỉ nhận 2 giá trị: 'open' (đang diễn ra) hoặc 'closed' (đã kết thúc).
"""
from datetime import datetime


class SessionRepo:
    def __init__(self, db):
        self.conn = db.get_connection()

    def create(self, course: str) -> int:
        now = datetime.now().isoformat()
        cur = self.conn.execute("""
            INSERT INTO sessions (course, start_time, status)
            VALUES (?, ?, 'open')
        """, (course, now))
        self.conn.commit()
        return cur.lastrowid

    def close(self, session_id: int) -> bool:
        now = datetime.now().isoformat()
        cur = self.conn.execute("""
            UPDATE sessions SET end_time = ?, status = 'closed' WHERE id = ?
        """, (now, session_id))
        self.conn.commit()
        return cur.rowcount > 0

    def is_open(self, session_id: int) -> bool:
        row = self.conn.execute(
            "SELECT status FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return bool(row) and row["status"] == "open"

    def get_by_id(self, session_id: int):
        row = self.conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_recent(self, limit: int = 30):
        rows = self.conn.execute("""
            SELECT * FROM sessions
            ORDER BY CASE WHEN status = 'open' THEN 0 ELSE 1 END, start_time DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def get_open_session(self):
        row = self.conn.execute("""
            SELECT * FROM sessions WHERE status = 'open'
            ORDER BY start_time DESC LIMIT 1
        """).fetchone()
        return dict(row) if row else None