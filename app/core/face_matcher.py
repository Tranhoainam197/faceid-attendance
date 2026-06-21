"""
FaceMatcher: so khớp embedding khuôn mặt với database bằng cosine similarity.
Đọc dữ liệu trực tiếp từ SQLite (qua StudentRepo), không còn phụ thuộc file .pkl.
"""
import numpy as np


class FaceMatcher:
    def __init__(self, student_repo, threshold: float):
        self.student_repo = student_repo
        self.threshold = threshold
        self.embeddings = None   # ma trận (N, 512) đã normalize
        self.ids = []
        self.names = []
        self.reload()

    def reload(self):
        """Nạp lại toàn bộ embedding từ DB. Gọi sau khi enroll mới hoặc xoá sinh viên."""
        data = self.student_repo.get_all_with_embeddings()

        if not data:
            self.embeddings = None
            self.ids, self.names = [], []
            print("[FaceMatcher] Database rỗng, chưa có sinh viên nào.")
            return

        self.ids = [d[0] for d in data]
        self.names = [d[1] for d in data]
        embs = np.array([d[2] for d in data], dtype=np.float32)

        norms = np.linalg.norm(embs, axis=1, keepdims=True)
        self.embeddings = embs / np.maximum(norms, 1e-10)

        print(f"[FaceMatcher] Đã nạp {len(self.ids)} khuôn mặt từ database.")

    def match(self, query_embedding: np.ndarray):
        """
        Trả về (student_id, name, similarity) nếu vượt threshold,
        ngược lại trả về (None, None, best_similarity).
        """
        if self.embeddings is None or len(self.embeddings) == 0:
            return None, None, 0.0

        query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
        similarities = self.embeddings @ query_norm

        idx = int(np.argmax(similarities))
        best_sim = float(similarities[idx])

        if best_sim >= self.threshold:
            return self.ids[idx], self.names[idx], best_sim
        return None, None, best_sim