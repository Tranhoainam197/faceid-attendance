<div align="center">

<h1>⬡ FaceID Attendance System</h1>

<p><strong>Hệ thống Chấm Công Tự Động Sử Dụng Nhận Diện Khuôn Mặt & Chống Giả Mạo</strong></p>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.6%2B-41CD52?style=flat-square&logo=qt&logoColor=white)](https://doc.qt.io/qtforpython)
[![InsightFace](https://img.shields.io/badge/InsightFace-ArcFace-FF6B35?style=flat-square)](https://insightface.ai)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Anti--Spoof-00C7B7?style=flat-square&logo=ultralytics)](https://ultralytics.com)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square)](https://sqlalchemy.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## 📌 Giới thiệu

**FaceID Attendance** là hệ thống chấm công doanh nghiệp thế hệ mới, thay thế hoàn toàn thẻ từ và vân tay bằng công nghệ nhận diện khuôn mặt AI. Hệ thống nhận dạng nhân viên theo thời gian thực qua camera, tự động ghi nhận điểm danh và có cơ chế chống giả mạo bằng ảnh/video.

### ✨ Tính năng nổi bật

| Tính năng | Mô tả |
|-----------|-------|
| 🎯 **Nhận diện chính xác** | ArcFace (buffalo_l) — độ chính xác 99.4% trên LFW benchmark |
| 🛡️ **Chống giả mạo** | YOLOv8 phân loại real/fake theo thời gian thực |
| ⚡ **Realtime** | Xử lý 30 FPS trên CPU thông thường |
| 🖥️ **Giao diện hiện đại** | PySide6, Light mode, thiết kế Material Design |
| 🗄️ **Database chuẩn** | SQLAlchemy ORM + SQLite, hỗ trợ WAL mode |
| 📊 **Thống kê trực quan** | Dashboard tổng hợp điểm danh theo ngày/phiên |
| 🔒 **Bảo mật** | Không lưu ảnh gốc, chỉ lưu vector embedding 512-chiều |

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER (GUI)                      │
│   PySide6 │ MainWindow │ HomeView │ AttendanceView │ EnrollView  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ gọi trực tiếp
┌───────────────────────────▼─────────────────────────────────────┐
│                      CORE LAYER (AI Pipeline)                    │
│                                                                  │
│  ┌─────────────────┐    ┌──────────────────┐    ┌────────────┐  │
│  │ InsightFace     │    │  AntiSpoofing     │    │FaceMatcher │  │
│  │ Singleton       │    │  (YOLOv8)         │    │(Cosine)    │  │
│  │ ArcFace buffalo │    │  real/fake detect │    │0.45 thresh │  │
│  └────────┬────────┘    └────────┬──────────┘    └─────┬──────┘  │
│           │                      │                      │         │
│           └──────────────────────┴──────────────────────┘         │
│                          EnrollManager                            │
│                   (thu thập 15 mẫu, outlier filter)              │
└───────────────────────────┬─────────────────────────────────────┘
                            │ đọc/ghi
┌───────────────────────────▼─────────────────────────────────────┐
│                     DATA LAYER (Repository)                      │
│                                                                  │
│   SQLAlchemy ORM     SQLite (WAL)     Pickle (embeddings.pkl)   │
│   ├── Employee       ├── employees    └── 512-d L2-normalized   │
│   ├── Session        ├── sessions         ArcFace embeddings     │
│   └── Attendance     └── attendance                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔬 Pipeline AI chi tiết

```
Camera Frame (BGR)
        │
        ▼
┌───────────────────────────────────────────────┐
│         ANTI-SPOOFING (mỗi frame)             │
│   YOLOv8 → phát hiện real/fake boxes         │
│   conf_threshold = 0.80                       │
└───────────────┬───────────────────────────────┘
                │ has_real = True?
                ▼
┌───────────────────────────────────────────────┐
│     FACE DETECTION (mỗi 5 frame)              │
│   InsightFace buffalo_l → bbox + embedding    │
│   det_size = (480, 480)                       │
│   Scale ×(1/0.75) về kích thước gốc          │
└───────────────┬───────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────┐
│     OVERLAP VERIFICATION                      │
│   YOLO real_box ∩ InsightFace bbox > 0       │
│   (đảm bảo face detected = face real)        │
└───────────────┬───────────────────────────────┘
                │ verified
                ▼
┌───────────────────────────────────────────────┐
│     COSINE SIMILARITY MATCHING                │
│   query_emb · DB_matrix → argmax             │
│   similarity ≥ 0.45 → nhận dạng thành công  │
│   O(N) với N = số nhân viên                  │
└───────────────┬───────────────────────────────┘
                │ match
                ▼
┌───────────────────────────────────────────────┐
│     COOLDOWN CHECK (60 giây)                  │
│   Tránh ghi trùng trong cùng phiên           │
└───────────────┬───────────────────────────────┘
                │
                ▼
         mark_attendance()
         → SQLite (WAL mode)
```

---

## 📁 Cấu trúc thư mục

```
faceid-attendance/
│
├── main.py                     # Điểm khởi động ứng dụng
├── config.yaml                 # Cấu hình tập trung (camera, AI, DB, UI)
├── requirements.txt
├── .gitignore
│
├── src/
│   ├── core/                   # AI Pipeline
│   │   ├── insightface_singleton.py   # Thread-safe Singleton — ArcFace
│   │   ├── anti_spoofing.py           # YOLOv8 real/fake detection
│   │   ├── face_matcher.py            # Cosine similarity matching
│   │   └── enroll_manager.py          # Thu thập & lưu embedding
│   │
│   ├── database/               # Data Layer
│   │   ├── models.py                  # SQLAlchemy ORM (Employee, Session, Attendance)
│   │   └── repository.py              # Data Access Layer — mọi truy vấn DB
│   │
│   ├── gui/                    # Presentation Layer
│   │   ├── main_window.py             # Sidebar navigation + QStackedWidget
│   │   ├── styles.py                  # Stylesheet tập trung (Material Design)
│   │   └── views/
│   │       ├── home_view.py           # Dashboard thống kê
│   │       ├── attendance_view.py     # Điểm danh realtime
│   │       ├── enroll_view.py         # Đăng ký khuôn mặt
│   │       ├── employee_view.py       # Quản lý nhân viên
│   │       └── history_view.py        # Lịch sử điểm danh
│   │
│   └── utils/
│       ├── config.py                  # Config loader (YAML → dict)
│       └── logger.py                  # Rotating file logger
│
├── models/                     # Model AI (không push lên git)
│   ├── anti_spoof.pt           # YOLOv8 custom trained
│   └── (buffalo_l tự download bởi insightface)
│
├── data/                       # Dữ liệu runtime (không push lên git)
│   ├── attendance.db           # SQLite database
│   └── embeddings.pkl          # Face embeddings
│
├── logs/                       # Log files (tự tạo khi chạy)
│
├── tests/                      # Unit tests
│   └── ...
│
└── docs/                       # Tài liệu bổ sung
    └── ...
```

---

## 🛠️ Công nghệ sử dụng

| Thành phần | Công nghệ | Phiên bản | Mục đích |
|-----------|-----------|-----------|---------|
| **Giao diện** | PySide6 (Qt6) | ≥6.6 | UI hiện đại, cross-platform |
| **Nhận diện khuôn mặt** | InsightFace / ArcFace | ≥0.7.3 | Trích xuất embedding 512-d |
| **Chống giả mạo** | YOLOv8 (Ultralytics) | ≥8.0 | Phân loại real/fake |
| **Inference** | ONNX Runtime | ≥1.17 | Chạy model AI trên CPU |
| **Camera** | OpenCV | ≥4.9 | Đọc frame, vẽ annotation |
| **Database** | SQLAlchemy + SQLite | ≥2.0 | ORM, WAL mode |
| **Config** | PyYAML | ≥6.0 | Cấu hình tập trung |

---

## ⚙️ Hướng dẫn cài đặt

### Yêu cầu hệ thống

- **OS**: Windows 10/11, Ubuntu 20.04+, macOS 12+
- **Python**: 3.10 hoặc 3.11
- **RAM**: Tối thiểu 4GB (khuyến nghị 8GB)
- **Camera**: Webcam USB hoặc tích hợp (720p trở lên)

---

### Bước 1 — Clone repository

```bash
git clone https://github.com/Tranhoainam197/faceid-attendance.git
cd faceid-attendance
```

### Bước 2 — Tạo môi trường ảo

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### Bước 3 — Cài đặt dependencies

```bash
pip install -r requirements.txt
```

> **Lưu ý InsightFace trên Windows:**
> Nếu `pip install insightface` báo lỗi, dùng file wheel đã build sẵn:
> ```bash
> pip install insightface-0.7.3-cp310-cp310-win_amd64.whl
> ```

### Bước 4 — Đặt model Anti-Spoofing

Sao chép file model YOLOv8 đã train vào thư mục `models/`:
```
models/
└── anti_spoof.pt    ← file model của bạn
```

### Bước 5 — Chạy ứng dụng

```bash
python main.py
```

Lần đầu chạy, InsightFace sẽ tự động tải model `buffalo_l` (~500MB).

---

## 🚀 Hướng dẫn sử dụng

### 1. Đăng ký nhân viên mới
1. Vào **"Đăng ký NV"** trên sidebar
2. Nhập Mã NV, Họ tên, Phòng ban
3. Nhấn **"Bắt đầu"** — giữ khuôn mặt trước camera
4. Xoay mặt nhẹ để thu thập 15 mẫu đa dạng
5. Nhấn **"Lưu nhân viên"** sau khi thanh tiến độ đầy

### 2. Điểm danh
1. Vào **"Điểm danh"** → chọn hoặc tạo phiên
2. Nhấn **"Bắt đầu"**
3. Nhân viên đứng trước camera — hệ thống tự nhận dạng và ghi danh
4. Nhấn **"Dừng"** khi kết thúc ca

### 3. Xem lịch sử
1. Vào **"Lịch sử"** → chọn ngày cần xem
2. Nhấn **"Tìm kiếm"** để lọc kết quả

---

## 🧠 Giải thích kỹ thuật

### Tại sao dùng ArcFace?
ArcFace sử dụng **Additive Angular Margin Loss** để học phân biệt khuôn mặt trong không gian hypersphere. Khoảng cách giữa các embedding được tối ưu theo góc (cosine), cho phép phân biệt chính xác ngay cả với biến thể ánh sáng, góc nhìn và biểu cảm.

### Tại sao cần anti-spoofing?
Không có anti-spoofing, kẻ gian có thể dùng **ảnh chụp** hoặc **video** để đánh lừa hệ thống. YOLOv8 phát hiện khuôn mặt thật (3D, có độ sâu) khác với ảnh phẳng (2D) qua các đặc trưng texture, phản quang và chuyển động.

### Tại sao dùng Singleton cho InsightFace?
Model buffalo_l chiếm ~500MB RAM. Tạo nhiều instance gây **tràn bộ nhớ** và tốn 3–8 giây mỗi lần khởi tạo. Singleton đảm bảo chỉ load một lần, chia sẻ an toàn giữa các thread nhờ `threading.Lock`.

### Tại sao lưu embedding thay vì ảnh?
- **Bảo mật**: Không thể tái tạo khuôn mặt từ vector 512 số thực
- **Tốc độ**: So sánh vector O(N) nhanh hơn so sánh ảnh O(N×W×H)
- **Nhỏ gọn**: Mỗi nhân viên chỉ tốn ~2KB thay vì hàng MB ảnh

---

## 👥 Nhóm phát triển

| Thành viên | Vai trò |
|-----------|---------|
| **[Tên TV 1]** | AI Core — InsightFace, ArcFace embedding pipeline |
| **[Tên TV 2]** | Anti-Spoofing — YOLOv8 training & integration |
| **[Tên TV 3]** | Database — SQLAlchemy ORM, Repository pattern |
| **[Tên TV 4]** | GUI — PySide6, Material Design, UX flow |
| **[Tên TV 5]** | Architecture — Clean Architecture, Config, Logger, Docs |

---

## 📄 Giấy phép

Dự án được phân phối theo giấy phép [MIT](LICENSE).

---

<div align="center">
<sub>Xây dựng với ❤️ bởi nhóm FaceID | Đại học Công nghệ TP.HCM</sub>
</div>