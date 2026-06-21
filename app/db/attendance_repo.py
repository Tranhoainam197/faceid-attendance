"""
Repository ghi nhận và truy vấn lịch sử điểm danh.
"""
from datetime import datetime

from app.db.session_repo import SessionRepo


class AttendanceRepo:
    def __init__(self, db):
        self.conn = db.get_connection()
        self.session_repo = SessionRepo(db)

    def mark(self, session_id: int, student_id: str, student_name: str,
             similarity: float, status: str = "present") -> bool:
        if not self.session_repo.is_open(session_id):
            print("[AttendanceRepo] Buổi học không mở hoặc đã kết thúc")
            return False

        now = datetime.now().isoformat()
        try:
            cur = self.conn.execute("""
                INSERT OR IGNORE INTO attendance
                (session_id, student_id, student_name, time, status, similarity)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (session_id, student_id, student_name, now, status, similarity))
            self.conn.commit()
            if cur.rowcount > 0:
                return True
            return self.exists(session_id, student_id)
        except Exception as e:
            print(f"[AttendanceRepo] Lỗi mark: {e}")
            return False

    def exists(self, session_id: int, student_id: str) -> bool:
        row = self.conn.execute("""
            SELECT 1 FROM attendance WHERE session_id = ? AND student_id = ?
        """, (session_id, student_id)).fetchone()
        return row is not None

    def get_by_date(self, date_str: str):
        rows = self.conn.execute("""
            SELECT student_id, student_name, time, date(time) AS date_only,
                   status, session_id, similarity
            FROM attendance
            WHERE date(time) = ?
            ORDER BY time DESC
        """, (date_str,)).fetchall()
        return [dict(r) for r in rows]

    def get_all(self):
        rows = self.conn.execute("""
            SELECT student_id, student_name, time, date(time) AS date_only,
                   status, session_id, similarity
            FROM attendance
            ORDER BY time DESC
        """).fetchall()
        return [dict(r) for r in rows]

    def get_by_session(self, session_id: int):
        rows = self.conn.execute("""
            SELECT student_id, student_name, time, status, similarity
            FROM attendance
            WHERE session_id = ?
            ORDER BY time
        """, (session_id,)).fetchall()
        return [dict(r) for r in rows]

    def count_today(self) -> int:
        today = datetime.now().strftime("%Y-%m-%d")
        return len(self.get_by_date(today))

    def count_all(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS c FROM attendance").fetchone()
        return row["c"]