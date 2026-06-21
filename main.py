"""
FaceID Attendance System - Entry point.

Chạy: python main.py
(Đảm bảo đã cài đủ thư viện trong requirements.txt và đặt model
anti-spoofing tại models/best.pt trước khi chạy)
"""
import os
import sys

from config import MODELS_DIR, ANTISPOOF_MODEL_PATH


def check_prerequisites() -> bool:
    """Kiểm tra các điều kiện cần thiết trước khi khởi động, báo lỗi rõ ràng
    thay vì để app crash với traceback khó hiểu."""
    ok = True

    if not os.path.exists(ANTISPOOF_MODEL_PATH):
        print("=" * 60)
        print("⚠ THIẾU MODEL ANTI-SPOOFING")
        print(f"Không tìm thấy: {ANTISPOOF_MODEL_PATH}")
        print()
        print("Cách khắc phục:")
        print("  1. Copy file best.pt đã train sẵn vào thư mục models/")
        print("  2. Hoặc tự train: xem hướng dẫn trong README.md")
        print("     (data_collect.py -> split_data.py -> train_yolo.py)")
        print("=" * 60)
        ok = False

    return ok


def main():
    if not check_prerequisites():
        sys.exit(1)

    # Import muộn (sau khi check file) để tránh load các thư viện nặng
    # (insightface, ultralytics...) nếu điều kiện chưa đủ
    from app.ui.app_window import AppWindow

    app = AppWindow()
    app.mainloop()


if __name__ == "__main__":
    main()