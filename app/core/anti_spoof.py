"""
AntiSpoof: wrapper quanh model YOLO phát hiện khuôn mặt giả mạo (ảnh/video phát lại)
so với khuôn mặt thật (real).
"""
import os
import threading

import cv2
from ultralytics import YOLO

from config import (
    ANTISPOOF_MODEL_PATH,
    ANTISPOOF_CONF_THRESHOLD,
    ANTISPOOF_CLASSES,
    ANTISPOOF_IMG_SIZE,
)


class AntiSpoof:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path: str = None, conf_threshold: float = ANTISPOOF_CONF_THRESHOLD):
        if self._initialized:
            return
        self._initialized = True

        model_path = model_path or ANTISPOOF_MODEL_PATH
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Không tìm thấy model anti-spoofing tại: {model_path}\n"
                f"Hãy train model bằng train_yolo.py hoặc đặt file best.pt vào thư mục models/"
            )

        self.conf_threshold = conf_threshold
        self.classes = ANTISPOOF_CLASSES
        self.model = YOLO(model_path)
        print(f"[AntiSpoof] Đã load model: {model_path}")

    def detect(self, img_bgr):
        """
        Chạy YOLO trên ảnh, trả về dict:
        {
            'has_real': bool,
            'max_real_conf': float,
            'real_boxes': [(x1,y1,x2,y2,conf), ...],
            'fake_boxes': [(x1,y1,x2,y2,conf), ...],
        }
        """
        results = self.model(
            img_bgr, imgsz=ANTISPOOF_IMG_SIZE, stream=True, verbose=False
        )

        real_boxes, fake_boxes = [], []
        max_real_conf = 0.0

        for r in results:
            for box in r.boxes:
                conf = float(box.conf[0])
                if conf < self.conf_threshold:
                    continue
                cls_id = int(box.cls[0])
                label = self.classes[cls_id]
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                if label == "real":
                    real_boxes.append((x1, y1, x2, y2, conf))
                    max_real_conf = max(max_real_conf, conf)
                else:
                    fake_boxes.append((x1, y1, x2, y2, conf))

        return {
            "has_real": len(real_boxes) > 0,
            "max_real_conf": max_real_conf,
            "real_boxes": real_boxes,
            "fake_boxes": fake_boxes,
        }

    @staticmethod
    def draw(img_bgr, spoof_info, thickness=2):
        """Vẽ các box real (xanh)/fake (đỏ) lên ảnh, trả về ảnh đã copy + vẽ."""
        img = img_bgr.copy()
        for x1, y1, x2, y2, conf in spoof_info["real_boxes"]:
            cv2.rectangle(img, (x1, y1), (x2, y2), (34, 197, 94), thickness)
            cv2.putText(img, f"REAL {conf:.2f}", (x1, max(y1 - 8, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (34, 197, 94), 2)
        for x1, y1, x2, y2, conf in spoof_info["fake_boxes"]:
            cv2.rectangle(img, (x1, y1), (x2, y2), (239, 68, 68), thickness)
            cv2.putText(img, f"FAKE {conf:.2f}", (x1, max(y1 - 8, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (239, 68, 68), 2)
        return img

    @staticmethod
    def boxes_overlap(box_a, box_b) -> bool:
        """Kiểm tra 2 bounding box (x1,y1,x2,y2,...) có giao nhau không."""
        ax1, ay1, ax2, ay2 = box_a[:4]
        bx1, by1, bx2, by2 = box_b[:4]
        return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1