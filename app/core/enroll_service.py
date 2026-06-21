"""
EnrollService: thu thập mẫu khuôn mặt, lọc outlier, tính quality score,
và lưu kết quả cuối cùng vào database (qua StudentRepo).
Tách hoàn toàn khỏi UI để dễ test và tái sử dụng.
"""
import numpy as np

from config import (
    ENROLL_MAX_SAMPLES,
    ENROLL_MIN_CONFIDENCE,
    ENROLL_MIN_SAMPLE_SIMILARITY,
    ENROLL_MAX_OUTLIER_DISTANCE,
)


class EnrollService:
    def __init__(self, face_app, student_repo, max_samples: int = ENROLL_MAX_SAMPLES):
        self.face_app = face_app
        self.student_repo = student_repo
        self.max_samples = max_samples
        self.samples = []
        self.last_embedding = None

    def reset(self):
        self.samples.clear()
        self.last_embedding = None

    def progress(self) -> float:
        return len(self.samples) / self.max_samples

    def sample_count(self) -> int:
        return len(self.samples)

    def is_complete(self) -> bool:
        return len(self.samples) >= self.max_samples

    def try_add_sample(self, rgb_frame) -> tuple[bool, str]:
        """
        Thử thêm 1 mẫu từ frame hiện tại.
        Trả về (thành_công, lý_do) để UI hiển thị thông báo phù hợp.
        """
        faces = self.face_app.get(rgb_frame)

        if len(faces) == 0:
            return False, "no_face"
        if len(faces) > 1:
            return False, "multiple_faces"

        face = faces[0]
        if face.det_score < ENROLL_MIN_CONFIDENCE:
            return False, "low_confidence"

        emb = face.normed_embedding
        if emb is None:
            return False, "no_embedding"

        if self.last_embedding is not None:
            sim = float(np.dot(emb, self.last_embedding))
            if sim > ENROLL_MIN_SAMPLE_SIMILARITY:
                return False, "too_similar"

        self.samples.append(emb)
        self.last_embedding = emb
        return True, "ok"

    def _remove_outliers(self, embeddings):
        if len(embeddings) < 5:
            return embeddings

        mean = np.mean(embeddings, axis=0)
        mean /= (np.linalg.norm(mean) + 1e-10)

        filtered = [e for e in embeddings if (1.0 - float(np.dot(e, mean))) <= ENROLL_MAX_OUTLIER_DISTANCE]

        if len(filtered) < 5:
            return embeddings
        return filtered

    def _quality_score(self, embeddings) -> float:
        if len(embeddings) < 2:
            return 0.0
        mean = np.mean(embeddings, axis=0)
        variances = [1.0 - float(np.dot(e, mean)) for e in embeddings]
        avg_variance = float(np.mean(variances))
        return min(1.0, avg_variance / 0.2)

    def save(self, student_id: str, name: str) -> bool:
        if not self.samples:
            return False

        clean_embeddings = self._remove_outliers(self.samples)
        quality = self._quality_score(clean_embeddings)

        mean_emb = np.mean(clean_embeddings, axis=0)
        mean_emb /= (np.linalg.norm(mean_emb) + 1e-10)

        success = self.student_repo.upsert(
            student_id=student_id,
            name=name,
            embedding=mean_emb,
            num_samples=len(clean_embeddings),
            quality_score=quality,
        )

        if success:
            self.reset()
        return success