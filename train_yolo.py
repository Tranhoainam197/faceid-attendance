"""
Script train model YOLOv8 cho anti-spoofing (phân loại real/fake).

CÁCH DÙNG:
1. Đã chạy data_collect.py để thu thập ảnh
2. Đã chạy split_data.py để chia train/val/test
3. Chạy: python train_yolo.py

LƯU Ý VỀ THỜI GIAN (máy chỉ có CPU, không có GPU NVIDIA):
- Train trên CPU CHẬM hơn GPU rất nhiều (có thể 5-15 phút/epoch tùy dataset).
- Script này dùng model "yolov8n" (nano - nhẹ nhất) và epoch vừa phải để khả thi trên CPU.
- Nếu máy quá yếu, có thể giảm EPOCHS hoặc IMG_SIZE ở phần cấu hình dưới.
- Có thể train qua đêm nếu cần (script tự lưu checkpoint, không cần lo mất tiến trình
  do utralytics tự lưu lại 'last.pt' sau mỗi epoch).

KẾT QUẢ:
Sau khi train xong, model tốt nhất sẽ nằm tại:
    runs/detect/antispoof_training/weights/best.pt
Hãy copy file này vào: models/best.pt để app chính sử dụng.
"""
import os
import shutil

from ultralytics import YOLO

# ============================================================
DATA_YAML = "dataset/split/data.yaml"
BASE_MODEL = "yolov8n.pt"       # model nano, nhẹ nhất, phù hợp CPU
EPOCHS = 60
IMG_SIZE = 320                  # khớp với ANTISPOOF_IMG_SIZE trong config.py
BATCH_SIZE = 8                  # giảm xuống 4 nếu máy bị treo / hết RAM
RUN_NAME = "antispoof_training"
DEVICE = "cpu"                  # đổi thành "0" nếu sau này có GPU NVIDIA
# ============================================================


def main():
    if not os.path.exists(DATA_YAML):
        print(f"Không tìm thấy {DATA_YAML}")
        print("Hãy chạy data_collect.py rồi split_data.py trước.")
        return

    print("=" * 60)
    print("BẮT ĐẦU TRAIN MODEL ANTI-SPOOFING")
    print(f"Base model : {BASE_MODEL}")
    print(f"Epochs     : {EPOCHS}")
    print(f"Image size : {IMG_SIZE}")
    print(f"Batch size : {BATCH_SIZE}")
    print(f"Device     : {DEVICE} (CPU - sẽ chậm hơn GPU, vui lòng kiên nhẫn)")
    print("=" * 60)

    model = YOLO(BASE_MODEL)

    model.train(
        data=DATA_YAML,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        device=DEVICE,
        name=RUN_NAME,
        patience=15,          # dừng sớm nếu không cải thiện sau 15 epoch (tiết kiệm thời gian)
        save=True,
        plots=True,           # xuất biểu đồ loss/mAP để xem model học tốt không
        verbose=True,
        workers=2,            # số luồng load data - giảm nếu máy yếu
        cache=False,          # True sẽ tốn RAM hơn nhưng train nhanh hơn nếu RAM đủ (8GB+)
    )

    print("\n" + "=" * 60)
    print("TRAIN HOÀN TẤT")

    best_path = f"runs/detect/{RUN_NAME}/weights/best.pt"
    if os.path.exists(best_path):
        os.makedirs("models", exist_ok=True)
        dest = "models/best.pt"
        shutil.copy(best_path, dest)
        print(f"Đã tự động copy model tốt nhất vào: {dest}")
    else:
        print(f"Không tìm thấy {best_path}, hãy kiểm tra thư mục runs/detect/{RUN_NAME}/weights/ thủ công")

    print("Xem biểu đồ kết quả train tại: "
          f"runs/detect/{RUN_NAME}/results.png")
    print("=" * 60)


if __name__ == "__main__":
    main()