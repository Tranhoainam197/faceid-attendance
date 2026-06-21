"""
Repository quản lý sinh viên/nhân viên trong SQLite.
Embedding lưu/đọc qua numpy.tobytes() <-> numpy.frombuffer().
"""
import sqlite3
from datetime import datetime

import numpy as np


class StudentRepo:
    def __init__(self, db):
        self.conn = db.get_connection()

    def upsert(self, student_id: str, name: str, embedding: np.ndarray,
               num_samples: int, quality_score: float, model_name: str = "buffalo_l") -> bool:
        """Thêm mới hoặc cập nhật sinh viên (giữ created_at cũ nếu đã tồn tại)."""
        now = datetime.now().isoformat()
        emb_bytes = embedding.astype(np.float32).tobytes()

        existing = self.get_by_id(student_id)
        try:
            if existing:
                self.conn.execute("""
                    UPDATE students
                    SET name = ?, embedding = ?, num_samples = ?,
                        quality_score = ?, model_name = ?, updated_at = ?
                    WHERE id = ?
                """, (name, emb_bytes, num_samples, quality_score, model_name, now, student_id))
            else:
                self.conn.execute("""
                    INSERT INTO students
                    (id, name, embedding, num_samples, quality_score, model_name, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (student_id, name, emb_bytes, num_samples, quality_score, model_name, now, now))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[StudentRepo] Lỗi upsert: {e}")
            return False

    def get_by_id(self, student_id: str):
        row = self.conn.execute(
            "SELECT * FROM students WHERE id = ?", (student_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_all(self):
        rows = self.conn.execute(
            "SELECT * FROM students ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_with_embeddings(self):
        """Trả về list (id, name, embedding_ndarray) để FaceMatcher dùng trực tiếp."""
        rows = self.conn.execute(
            "SELECT id, name, embedding FROM students"
        ).fetchall()
        result = []
        for r in rows:
            emb = np.frombuffer(r["embedding"], dtype=np.float32)
            result.append((r["id"], r["name"], emb))
        return result

    def has_attendance_records(self, student_id: str) -> int:
        """Trả về số lượng bản ghi điểm danh đang tham chiếu đến sinh viên này."""
        row = self.conn.execute(
            "SELECT COUNT(*) AS c FROM attendance WHERE student_id = ?", (student_id,)
        ).fetchone()
        return row["c"]

    def delete(self, student_id: str, cascade: bool = False) -> bool:
        """
        Xóa sinh viên. Nếu cascade=False và sinh viên có lịch sử điểm danh,
        việc xóa sẽ bị từ chối (do ràng buộc FOREIGN KEY) để bảo toàn dữ liệu.
        Nếu cascade=True, xóa luôn toàn bộ lịch sử điểm danh liên quan trước.
        """
        try:
            if cascade:
                self.conn.execute("DELETE FROM attendance WHERE student_id = ?", (student_id,))

            cur = self.conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"[StudentRepo] Lỗi xoá: {e}")
            self.conn.rollback()
            return False

    def count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS c FROM students").fetchone()
        return row["c"]

    def search(self, keyword: str):
        keyword = f"%{keyword.lower()}%"
        rows = self.conn.execute("""
            SELECT * FROM students
            WHERE LOWER(id) LIKE ? OR LOWER(name) LIKE ?
            ORDER BY created_at DESC
        """, (keyword, keyword)).fetchall()
        return [dict(r) for r in rows]