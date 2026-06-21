"""
Chia dataset thô (ảnh + label .txt cùng tên) thành 3 tập train/val/test
theo tỉ lệ 70/20/10, đồng thời tự sinh file data.yaml cho YOLO.

CÁCH DÙNG:
    python split_data.py
(Chạy sau khi đã thu thập đủ dữ liệu bằng data_collect.py)
"""
import os
import random
import shutil

INPUT_DIR = "dataset/raw"
OUTPUT_DIR = "dataset/split"
SPLIT_RATIO = {"train": 0.7, "val": 0.2, "test": 0.1}
CLASS_NAMES = ["fake", "real"]   # thứ tự PHẢI khớp config.py: ANTISPOOF_CLASSES


def main():
    if not os.path.isdir(INPUT_DIR):
        print(f"Không tìm thấy thư mục dữ liệu: {INPUT_DIR}")
        print("Hãy chạy data_collect.py trước.")
        return

    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)

    for split in ("train", "val", "test"):
        os.makedirs(f"{OUTPUT_DIR}/{split}/images", exist_ok=True)
        os.makedirs(f"{OUTPUT_DIR}/{split}/labels", exist_ok=True)

    # Lấy tên file (không đuôi) của các ảnh có cả .jpg và .txt đi kèm
    all_files = os.listdir(INPUT_DIR)
    stems = sorted(set(f.rsplit(".", 1)[0] for f in all_files if f.endswith(".jpg")))
    valid_stems = [s for s in stems if os.path.exists(f"{INPUT_DIR}/{s}.txt")]

    skipped = len(stems) - len(valid_stems)
    if skipped > 0:
        print(f"⚠ Bỏ qua {skipped} ảnh không có file label .txt tương ứng")

    if len(valid_stems) < 10:
        print(f"⚠ Chỉ có {len(valid_stems)} mẫu hợp lệ - quá ít để train hiệu quả.")
        print("  Khuyến nghị: thu thập tối thiểu 200-300 ảnh mỗi class (real/fake).")

    random.shuffle(valid_stems)

    n_total = len(valid_stems)
    n_train = int(n_total * SPLIT_RATIO["train"])
    n_val = int(n_total * SPLIT_RATIO["val"])
    # Phần dư (do làm tròn) dồn hết vào train
    n_test = n_total - n_train - n_val

    splits = {
        "train": valid_stems[:n_train],
        "val": valid_stems[n_train:n_train + n_val],
        "test": valid_stems[n_train + n_val:],
    }

    for split_name, file_stems in splits.items():
        for stem in file_stems:
            shutil.copy(f"{INPUT_DIR}/{stem}.jpg", f"{OUTPUT_DIR}/{split_name}/images/{stem}.jpg")
            shutil.copy(f"{INPUT_DIR}/{stem}.txt", f"{OUTPUT_DIR}/{split_name}/labels/{stem}.txt")

    print(f"Tổng: {n_total} mẫu -> train={len(splits['train'])}, "
          f"val={len(splits['val'])}, test={len(splits['test'])}")

    # Sinh data.yaml - đường dẫn tuyệt đối để YOLO chạy được từ bất kỳ đâu
    abs_output = os.path.abspath(OUTPUT_DIR)
    yaml_content = (
        f"train: {abs_output}/train/images\n"
        f"val: {abs_output}/val/images\n"
        f"test: {abs_output}/test/images\n"
        f"\n"
        f"nc: {len(CLASS_NAMES)}\n"
        f"names: {CLASS_NAMES}\n"
    )

    yaml_path = f"{OUTPUT_DIR}/data.yaml"
    with open(yaml_path, "w") as f:
        f.write(yaml_content)

    print(f"Đã tạo {yaml_path}")
    print("\nBước tiếp theo: chạy train_yolo.py để bắt đầu train model")


if __name__ == "__main__":
    main()