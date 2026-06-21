# 🪪 FaceID Attendance System

Hệ thống điểm danh bằng nhận diện khuôn mặt, có chống giả mạo (liveness detection),
giao diện desktop hiện đại, chạy tốt trên máy chỉ có CPU.

---

## ✨ Tính năng

- **Chấm công real-time** qua camera, kết hợp nhận diện khuôn mặt (InsightFace) và
  chống giả mạo bằng ảnh/màn hình điện thoại (YOLOv8 anti-spoofing)
- **Đăng ký nhân sự mới** với kiểm tra chất lượng mẫu trực tiếp (khoảng cách, độ sáng,
  đa dạng góc mặt), tự loại bỏ outlier khi lưu
- **Quản lý buổi học (session)** — mỗi buổi có thời điểm bắt đầu/kết thúc riêng
- **Lịch sử điểm danh** — tra cứu theo ngày, tìm theo mã số, xuất CSV
- **Danh sách nhân sự** — tìm kiếm, xóa, xuất CSV
- **1 file database SQLite duy nhất** (`data/faceid.db`), embedding lưu dạng BLOB
- **Camera chạy trên thread riêng** — giao diện không bị giật/đứng dù model AI xử lý chậm
- Giao diện **light mode** chuyên nghiệp bằng CustomTkinter

---

## 💻 Yêu cầu hệ thống

| Thành phần | Yêu cầu |
|---|---|
| OS | Windows 10/11 (đã thiết kế và tối ưu cho Windows) |
| Python | 3.10 – 3.11 |
| CPU | Intel i5 hoặc tương đương trở lên |
| RAM | 8GB+ khuyến nghị |
| GPU | Không bắt buộc — chạy tốt trên CPU thuần (AMD/Intel iGPU không cần dùng) |
| Camera | Webcam ≥ 720p |

---

## 🚀 Cài đặt

### 1. Tạo virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Cài thư viện

```bash
pip install -r requirements.txt
```

> Nếu `insightface` cài lỗi trên Windows, cài thêm
> [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
> rồi chạy lại lệnh trên.

### 3. Chuẩn bị model anti-spoofing

Bạn cần file `models/best.pt`. Có 2 cách:

**Cách A — Dùng model có sẵn:** copy file `best.pt` từ dự án cũ vào thư mục `models/`.

**Cách B — Tự train model mới** (khuyến nghị nếu model cũ nhận diện chưa chính xác):

```bash
# Bước 1: Thu thập dữ liệu (mở camera, nhấn 'r'/'f' để đổi mode real/fake, 'q' để thoát)
python data_collect.py

# Bước 2: Chia train/val/test
python split_data.py

# Bước 3: Train model (chạy trên CPU, có thể mất 1-3 giờ tùy dataset và máy)
python train_yolo.py
```

Xem chi tiết hướng dẫn train ở mục [Train model anti-spoofing](#-train-model-anti-spoofing) dưới đây.

### 4. Chạy ứng dụng

```bash
python main.py
```

Database `data/faceid.db` sẽ tự động được tạo ở lần chạy đầu tiên.

---

## 📁 Cấu trúc dự án
faceid-attendance/
├── main.py                       # Entry point
├── config.py                     # Cấu hình tập trung (threshold, đường dẫn, kích thước...)
├── requirements.txt
├── README.md
│
├── data_collect.py                # Thu thập dữ liệu train anti-spoofing
├── split_data.py                  # Chia train/val/test
├── train_yolo.py                  # Train model YOLO anti-spoofing
│
├── app/
│   ├── core/                      # Business logic (không phụ thuộc UI)
│   │   ├── camera_stream.py       # Camera đọc trên thread riêng
│   │   ├── face_engine.py         # Singleton InsightFace
│   │   ├── anti_spoof.py          # Wrapper YOLO chống giả mạo
│   │   ├── face_matcher.py        # So khớp embedding (cosine similarity)
│   │   ├── enroll_service.py      # Logic thu mẫu khi đăng ký
│   │   └── attendance_service.py  # Logic xác thực + ghi nhận điểm danh
│   │
│   ├── db/                        # Tầng dữ liệu (SQLite)
│   │   ├── database.py            # Kết nối + schema
│   │   ├── student_repo.py
│   │   ├── session_repo.py
│   │   └── attendance_repo.py
│   │
│   ├── ui/
│   │   ├── theme.py                # Màu sắc, font tập trung
│   │   ├── app_window.py           # Cửa sổ chính + sidebar
│   │   ├── widgets/                # Component dùng chung (toast, stat card, sidebar)
│   │   └── pages/                  # 5 trang: dashboard, attendance, enroll, students, history
│   │
│   └── utils/
│       └── image_utils.py
│
├── models/
│   └── best.pt                     # Model YOLO anti-spoofing (tự train hoặc copy vào)
│
└── data/
└── faceid.db                   # Tự tạo khi chạy lần đầu (KHÔNG commit lên git)

---

## 🔧 Công nghệ sử dụng

| Công nghệ | Vai trò |
|---|---|
| **InsightFace** (buffalo_l) | Nhận diện khuôn mặt, trích xuất embedding 512-D |
| **YOLOv8** (ultralytics) | Phát hiện khuôn mặt giả mạo (ảnh/màn hình điện thoại) |
| **OpenCV** | Xử lý camera, vẽ kết quả |
| **CustomTkinter** | Giao diện desktop hiện đại |
| **SQLite** | Lưu trữ toàn bộ dữ liệu (1 file duy nhất) |
| **NumPy** | Tính toán embedding, cosine similarity |

---

## ⚙️ Cách hoạt động (tóm tắt kỹ thuật)

1. **Camera** chạy trên 1 thread riêng (`CameraStream`), liên tục đọc và giữ frame mới
   nhất. Giao diện chỉ lấy frame có sẵn, không bao giờ phải đợi camera → không giật/lag
   dù model AI xử lý chậm.
2. Mỗi vài frame (cấu hình ở `config.py`), **InsightFace** chạy detect + trích embedding
   trên ảnh đã giảm độ phân giải để tăng tốc.
3. **YOLO anti-spoofing** chạy trên toàn bộ frame (không phải ảnh khuôn mặt đã crop) vì
   cho độ chính xác cao hơn — quan sát từ quá trình thử nghiệm thực tế.
4. Một khuôn mặt chỉ được coi là **"thật"** nếu vùng bounding box của nó **giao nhau**
   với một box "real" mà YOLO phát hiện được trên toàn frame.
5. Khuôn mặt đã xác thực "thật" mới được đưa qua **FaceMatcher** (cosine similarity với
   embedding đã lưu trong SQLite) để xác định danh tính và ghi nhận điểm danh.

---

## 🐢 Xử lý vấn đề hiệu năng

Nếu máy bạn vẫn giật/lag, chỉnh các giá trị sau trong `config.py`:

| Tham số | Mặc định | Tăng lên để | Giảm xuống để |
|---|---|---|---|
| `FACE_DET_SIZE` | (320, 320) | Nhận diện chính xác hơn | Tăng FPS, giảm tải CPU |
| `ATTENDANCE_DETECT_INTERVAL` | 4 | — | Tăng FPS (giảm số lần detect/giây) |
| `ANTISPOOF_IMG_SIZE` | 320 | Anti-spoof chính xác hơn | Tăng FPS |
| `ANTISPOOF_INTERVAL` | 2 | — | Tăng FPS |
| `CAMERA_WIDTH/HEIGHT` | 640×480 | Hình ảnh rõ hơn | Tăng FPS đáng kể |

Thứ tự ưu tiên giảm tải khi máy quá yếu: giảm `CAMERA_WIDTH/HEIGHT` trước → giảm
`FACE_DET_SIZE` → tăng các giá trị `*_INTERVAL`.

---

## 🎯 Train model anti-spoofing

Model quyết định độ chính xác phân biệt khuôn mặt thật/giả. Nếu nhận diện sai nhiều
(luôn báo "giả mạo" hoặc ngược lại), nguyên nhân thường là **dataset chưa đủ đa dạng**,
không phải do code.

### Quy trình

```bash
python data_collect.py    # Thu thập ảnh real + fake
python split_data.py      # Chia 70/20/10 train/val/test
python train_yolo.py      # Train (CPU, ~1-3 giờ tùy dataset)
```

Sau khi train xong, copy model tốt nhất (`train_yolo.py` tự copy sẵn) vào `models/best.pt`.

### Gợi ý để model học tốt

- Thu thập **tối thiểu 200-300 ảnh** mỗi loại (real/fake), tỉ lệ gần 1:1
- **Real**: nhiều người khác nhau (nếu có thể), nhiều góc độ, nhiều điều kiện ánh sáng
  (sáng/tối/ngược sáng)
- **Fake**: in ảnh ra giấy, hoặc mở ảnh/video trên điện thoại/màn hình laptop khác rồi
  quay lại — đa dạng loại màn hình/giấy in để model không học "tắt" theo viền khung
  hình mà học đặc trưng thật/giả
- Xem `runs/detect/antispoof_training/results.png` sau khi train để kiểm tra model có
  học tốt không (mAP tăng dần, loss giảm dần, không có dấu hiệu overfit)

---

## 📌 Lưu ý

- Database (`data/faceid.db`) và model (`models/best.pt`) **không nên commit lên Git**
  nếu chia sẻ mã nguồn — đã được thêm vào `.gitignore`.
- Ứng dụng dùng `CPUExecutionProvider` cho InsightFace mặc định, phù hợp với máy không
  có GPU NVIDIA (AMD/Intel GPU không hỗ trợ CUDA nên không tăng tốc được qua onnxruntime).

---

**FaceID Attendance System** — xây dựng cho mục đích học tập, môn Trí tuệ nhân tạo.