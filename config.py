"""
Cấu hình tập trung cho toàn bộ ứng dụng FaceID Attendance.
Chỉnh các giá trị ở đây để tối ưu hiệu năng theo máy của bạn,
không cần sửa code rải rác nhiều nơi.
"""
import os

# ============================================================
# ĐƯỜNG DẪN
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "faceid.db")
ANTISPOOF_MODEL_PATH = os.path.join(MODELS_DIR, "best.pt")

# ============================================================
# CAMERA
# ============================================================
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS_TARGET = 30          # FPS hiển thị UI (luồng đọc camera)
UI_REFRESH_MS = 25              # Tốc độ Tkinter pull frame mới để vẽ (ms)

# ============================================================
# INSIGHTFACE (Nhận diện khuôn mặt)
# ============================================================
# Máy CPU yếu -> giảm det_size để tăng FPS rõ rệt (640->320 nhanh gấp ~3-4 lần)
FACE_MODEL_NAME = "buffalo_l"
FACE_DET_SIZE = (320, 320)
FACE_PROVIDERS = ["CPUExecutionProvider"]   # Đổi thành CUDAExecutionProvider nếu có GPU NVIDIA
FACE_CTX_ID = 0

# Chỉ chạy detect mỗi N frame đọc được (giảm tải CPU, không giảm tải camera)
ATTENDANCE_DETECT_INTERVAL = 4
ENROLL_DETECT_INTERVAL = 3

# ============================================================
# ANTI-SPOOFING (YOLO)
# ============================================================
ANTISPOOF_CONF_THRESHOLD = 0.6
ANTISPOOF_CLASSES = ["fake", "real"]
ANTISPOOF_IMG_SIZE = 320          # Giảm từ 640 mặc định của YOLO -> nhanh hơn nhiều trên CPU
ANTISPOOF_INTERVAL = 2            # Chạy YOLO mỗi N frame có detect khuôn mặt

# ============================================================
# MATCHING (So khớp khuôn mặt)
# ============================================================
SIMILARITY_THRESHOLD = 0.45
ATTENDANCE_COOLDOWN_SEC = 8       # Sau khi chấm công, "khoá" 1 người trong N giây

# ============================================================
# ENROLL (Đăng ký khuôn mặt mới)
# ============================================================
ENROLL_MAX_SAMPLES = 12
ENROLL_MIN_CONFIDENCE = 0.55
ENROLL_MIN_SAMPLE_SIMILARITY = 0.90   # Mẫu mới phải khác mẫu trước ít nhất (1 - giá trị này)
ENROLL_MAX_OUTLIER_DISTANCE = 0.40
ENROLL_SAMPLE_COOLDOWN_FRAMES = 6
ENROLL_MIN_FACE_SIZE = 100
ENROLL_MAX_FACE_SIZE = 420

# ============================================================
# GIAO DIỆN
# ============================================================
APP_NAME = "FaceID Attendance"
APP_MIN_WIDTH = 1200
APP_MIN_HEIGHT = 720
APPEARANCE_MODE = "light"          # light mode theo yêu cầu
COLOR_THEME = "blue"