"""
Script thu thập dữ liệu để train model anti-spoofing (YOLO).

CÁCH DÙNG:
1. Chạy: python data_collect.py
2. Nhấn phím:
   - 'r' : chuyển sang mode quay ảnh THẬT (real)
   - 'f' : chuyển sang mode quay ảnh GIẢ (fake) - cầm ảnh/điện thoại trước camera
   - SPACE hoặc tự động lưu liên tục khi mặt rõ nét (không bị mờ)
   - 'q' : thoát

GỢI Ý THU THẬP DATA TỐT:
- Real: quay nhiều người khác nhau, nhiều góc độ, nhiều điều kiện ánh sáng
- Fake: in ảnh ra giấy / mở ảnh trên điện thoại / màn hình laptop khác, quay lại
- Nên có tối thiểu 200-300 ảnh mỗi loại (real/fake) để model học tốt
- Giữ tỉ lệ real:fake gần bằng nhau (1:1) để tránh model bị lệch (bias)
"""
import os
import time

import cv2
from cvzone.FaceDetectionModule import FaceDetector

# ============================================================
OUTPUT_DIR = "dataset/raw"
CONFIDENCE = 0.75
CAM_WIDTH, CAM_HEIGHT = 640, 480
BLUR_THRESHOLD = 35          # giá trị Laplacian variance, cao hơn = ảnh nét hơn
OFFSET_W_PERCENT = 15        # nới rộng bbox quanh mặt để model học cả viền/khung ảnh giả
OFFSET_H_PERCENT = 20
SAVE_INTERVAL_SEC = 0.4      # giãn cách giữa 2 lần lưu, tránh data trùng lặp quá nhiều
# ============================================================

CLASS_NAMES = {"real": 1, "fake": 0}   # khớp với ANTISPOOF_CLASSES = ["fake", "real"]


def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def normalize_bbox(x, y, w, h, img_w, img_h):
    xc = (x + w / 2) / img_w
    yc = (y + h / 2) / img_h
    wn = w / img_w
    hn = h / img_h
    return (
        round(min(max(xc, 0), 1), 6),
        round(min(max(yc, 0), 1), 6),
        round(min(max(wn, 0), 1), 6),
        round(min(max(hn, 0), 1), 6),
    )


def main():
    ensure_dirs()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    detector = FaceDetector()

    mode = "real"     # mode mặc định, đổi bằng phím r/f
    last_save_time = 0
    counts = {"real": 0, "fake": 0}

    print("=" * 60)
    print("THU THẬP DỮ LIỆU ANTI-SPOOFING")
    print("Phím: [r] real | [f] fake | [q] thoát")
    print("=" * 60)

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        display = frame.copy()
        _, bboxes = detector.findFaces(frame, draw=False)

        if bboxes:
            for bbox in bboxes:
                x, y, w, h = bbox["bbox"]
                score = bbox["score"][0]

                if score < CONFIDENCE:
                    continue

                offset_w = int((OFFSET_W_PERCENT / 100) * w)
                offset_h = int((OFFSET_H_PERCENT / 100) * h)
                x1 = max(0, x - offset_w)
                y1 = max(0, y - offset_h)
                x2 = min(frame.shape[1], x + w + offset_w)
                y2 = min(frame.shape[0], y + h + offset_h)

                face_crop = frame[y1:y2, x1:x2]
                if face_crop.size == 0:
                    continue

                blur_value = cv2.Laplacian(face_crop, cv2.CV_64F).var()
                is_sharp = blur_value > BLUR_THRESHOLD

                color = (34, 197, 94) if is_sharp else (239, 68, 68)
                cv2.rectangle(display, (x1, y1), (x2, y2), color, 2)
                cv2.putText(display, f"blur={blur_value:.0f}", (x1, max(y1 - 10, 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                now = time.time()
                if is_sharp and (now - last_save_time) > SAVE_INTERVAL_SEC:
                    img_h, img_w = frame.shape[:2]
                    xc, yc, wn, hn = normalize_bbox(x1, y1, x2 - x1, y2 - y1, img_w, img_h)
                    class_id = CLASS_NAMES[mode]

                    ts = str(time.time()).replace(".", "")
                    img_path = os.path.join(OUTPUT_DIR, f"{mode}_{ts}.jpg")
                    label_path = os.path.join(OUTPUT_DIR, f"{mode}_{ts}.txt")

                    cv2.imwrite(img_path, frame)
                    with open(label_path, "w") as f:
                        f.write(f"{class_id} {xc} {yc} {wn} {hn}\n")

                    counts[mode] += 1
                    last_save_time = now

        # Header info
        cv2.rectangle(display, (0, 0), (CAM_WIDTH, 40), (30, 30, 30), -1)
        cv2.putText(display, f"MODE: {mode.upper()}  |  real={counts['real']}  fake={counts['fake']}",
                    (10, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("Data Collection - [r]eal [f]ake [q]uit", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            mode = "real"
            print(">> Chuyển sang mode: REAL")
        elif key == ord("f"):
            mode = "fake"
            print(">> Chuyển sang mode: FAKE")

    cap.release()
    cv2.destroyAllWindows()

    print("\n" + "=" * 60)
    print(f"Hoàn tất. Đã thu thập: real={counts['real']} ảnh, fake={counts['fake']} ảnh")
    print(f"Dữ liệu lưu tại: {OUTPUT_DIR}/")
    print("Bước tiếp theo: chạy split_data.py để chia train/val/test")
    print("=" * 60)


if __name__ == "__main__":
    main()