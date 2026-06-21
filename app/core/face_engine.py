"""
Singleton quản lý model InsightFace (nhận diện + trích xuất embedding khuôn mặt).
Chỉ load model 1 lần duy nhất trong toàn bộ ứng dụng (load model rất tốn thời gian).
"""
import threading

from insightface.app import FaceAnalysis

from config import FACE_MODEL_NAME, FACE_DET_SIZE, FACE_PROVIDERS, FACE_CTX_ID


class FaceEngine:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> FaceAnalysis:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    print("[FaceEngine] Đang load InsightFace (lần đầu, có thể mất 5-10s)...")
                    app = FaceAnalysis(name=FACE_MODEL_NAME, providers=FACE_PROVIDERS)
                    app.prepare(ctx_id=FACE_CTX_ID, det_size=FACE_DET_SIZE)
                    cls._instance = app
                    print("[FaceEngine] Sẵn sàng.")
        return cls._instance

    @classmethod
    def reset(cls):
        """Dùng khi cần reload model với cấu hình khác (hiếm khi cần)."""
        cls._instance = None