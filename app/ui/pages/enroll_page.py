"""
EnrollPage: trang đăng ký khuôn mặt mới.
Quy trình: nhập thông tin -> mở camera -> thu thập N mẫu khuôn mặt
(qua EnrollService, có check chất lượng/đa dạng/outlier) -> lưu vào DB.
"""
import cv2
import customtkinter as ctk
from PIL import Image, ImageTk

from config import (
    CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS_TARGET, UI_REFRESH_MS,
    ENROLL_DETECT_INTERVAL, ENROLL_MAX_SAMPLES, ENROLL_MIN_FACE_SIZE, ENROLL_MAX_FACE_SIZE,
    ENROLL_MIN_CONFIDENCE, ENROLL_SAMPLE_COOLDOWN_FRAMES, ENROLL_CONSECUTIVE_REAL_REQUIRED,
)
from app.ui.theme import COLORS, FONTS
from app.ui.widgets.toast import show_toast
from app.core.camera_stream import CameraStream
from app.core.anti_spoof import AntiSpoof
from app.core.enroll_service import EnrollService

FACE_DETECT_SCALE = 0.75

QUALITY_LABELS = [
    ("face", "👤 Khuôn mặt"),
    ("distance", "📏 Khoảng cách"),
    ("confidence", "✨ Độ rõ"),
    ("diversity", "🔄 Đa dạng"),
]

QUALITY_COLORS = {
    "good": (COLORS["success"], COLORS["success_light"]),
    "warning": (COLORS["warning"], COLORS["warning_light"]),
    "bad": (COLORS["danger"], COLORS["danger_light"]),
    "inactive": (COLORS["text_muted"], COLORS["bg_input"]),
}

INSTRUCTIONS = [
    "Nhìn thẳng vào camera",
    "Giữ khoảng cách 50–70cm",
    "Đảm bảo ánh sáng đủ sáng",
    "Xoay nhẹ đầu khi được yêu cầu",
    "Giữ khuôn mặt trong khung hình",
]


class EnrollPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        self.camera: CameraStream | None = None
        self.anti_spoof: AntiSpoof | None = None
        self.enroll_service: EnrollService | None = None

        self.running = False
        self.frame_count = 0
        self.sample_cooldown = 0
        self.consecutive_real_count = 0   # đếm số frame liên tiếp xác thực "real"
        self.photo_image = None
        self.quality_widgets = {}

        self._build_ui()

    # ============================================================
    # UI LAYOUT
    # ============================================================
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 12))
        ctk.CTkLabel(
            header, text="Đăng ký nhân sự mới", font=FONTS["h1"],
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            header, text="Nhập thông tin và thu thập mẫu khuôn mặt qua camera",
            font=FONTS["body"], text_color=COLORS["text_secondary"], anchor="w",
        ).pack(fill="x", pady=(2, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 24))
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_camera_panel(body)
        self._build_side_panel(body)

    def _build_camera_panel(self, parent):
        panel = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_card"], corner_radius=14,
            border_width=1, border_color=COLORS["border"],
        )
        panel.grid(row=0, column=0, sticky="ns", padx=(0, 16))

        inner = ctk.CTkFrame(panel, fg_color="transparent")
        inner.pack(padx=20, pady=20)
        preview_w, preview_h = 480, 360
        video_box = ctk.CTkFrame(
            inner, fg_color="#111317", corner_radius=12, width=preview_w, height=preview_h,
        )
        video_box.pack(pady=(0, 14))
        video_box.pack_propagate(False)

        self.video_label = ctk.CTkLabel(
            video_box, text="📷  Nhập thông tin và nhấn Bắt đầu", text_color="#9CA3AF",
            font=FONTS["body"],
        )
        self.video_label.place(relx=0.5, rely=0.5, anchor="center")

        self.status_label = ctk.CTkLabel(
            inner, text="Nhập thông tin bên phải để bắt đầu", font=FONTS["small_bold"],
            text_color=COLORS["text_secondary"], fg_color=COLORS["bg_input"],
            corner_radius=20, height=34,
        )
        self.status_label.pack(fill="x", pady=(0, 10))

        # Quality indicators
        quality_row = ctk.CTkFrame(inner, fg_color="transparent")
        quality_row.pack(fill="x", pady=(0, 14))
        for key, label in QUALITY_LABELS:
            chip = ctk.CTkLabel(
                quality_row, text=label, font=FONTS["small_bold"],
                text_color=COLORS["text_muted"], fg_color=COLORS["bg_input"],
                corner_radius=8, height=30, width=120,
            )
            chip.pack(side="left", padx=4)
            self.quality_widgets[key] = chip

        # Progress
        self.progress_bar = ctk.CTkProgressBar(inner, height=10, corner_radius=5)
        self.progress_bar.pack(fill="x", pady=(0, 4))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            inner, text=f"0 / {ENROLL_MAX_SAMPLES} mẫu", font=FONTS["small"],
            text_color=COLORS["text_secondary"],
        )
        self.progress_label.pack(anchor="w", pady=(0, 14))

        # Controls
        controls = ctk.CTkFrame(inner, fg_color="transparent")
        controls.pack(fill="x")

        self.btn_start = ctk.CTkButton(
            controls, text="▶  Bắt đầu thu thập", font=FONTS["body_bold"], height=42,
            fg_color=COLORS["success"], hover_color="#15803D",
            command=self.start_camera,
        )
        self.btn_start.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.btn_cancel = ctk.CTkButton(
            controls, text="✕  Hủy", font=FONTS["body_bold"], height=42,
            fg_color=COLORS["danger"], hover_color="#B91C1C",
            state="disabled", command=self.cancel_enrollment,
        )
        self.btn_cancel.pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _build_side_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)

        # Form card
        form_card = ctk.CTkFrame(
            panel, fg_color=COLORS["bg_card"], corner_radius=14,
            border_width=1, border_color=COLORS["border"],
        )
        form_card.pack(fill="x", pady=(0, 16))

        form_inner = ctk.CTkFrame(form_card, fg_color="transparent")
        form_inner.pack(fill="x", padx=20, pady=18)

        ctk.CTkLabel(
            form_inner, text="Thông tin nhân sự", font=FONTS["body_bold"],
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            form_inner, text="Mã số", font=FONTS["small"],
            text_color=COLORS["text_secondary"], anchor="w",
        ).pack(fill="x")
        self.entry_id = ctk.CTkEntry(
            form_inner, placeholder_text="VD: NV001", height=38, font=FONTS["body"],
        )
        self.entry_id.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(
            form_inner, text="Họ và tên", font=FONTS["small"],
            text_color=COLORS["text_secondary"], anchor="w",
        ).pack(fill="x")
        self.entry_name = ctk.CTkEntry(
            form_inner, placeholder_text="VD: Nguyễn Văn A", height=38, font=FONTS["body"],
        )
        self.entry_name.pack(fill="x", pady=(4, 0))

        # Instructions card
        instr_card = ctk.CTkFrame(
            panel, fg_color=COLORS["bg_card"], corner_radius=14,
            border_width=1, border_color=COLORS["border"],
        )
        instr_card.pack(fill="x")

        instr_inner = ctk.CTkFrame(instr_card, fg_color="transparent")
        instr_inner.pack(fill="x", padx=20, pady=18)

        ctk.CTkLabel(
            instr_inner, text="Hướng dẫn", font=FONTS["body_bold"],
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(fill="x", pady=(0, 10))

        for i, text in enumerate(INSTRUCTIONS, start=1):
            row = ctk.CTkFrame(instr_inner, fg_color="transparent")
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(
                row, text=str(i), font=FONTS["small_bold"], text_color="white",
                fg_color=COLORS["accent"], corner_radius=10, width=20, height=20,
            ).pack(side="left", padx=(0, 10))
            ctk.CTkLabel(
                row, text=text, font=FONTS["small"], text_color=COLORS["text_secondary"],
                anchor="w", wraplength=240, justify="left",
            ).pack(side="left", fill="x", expand=True)

        # Success panel (ẩn ban đầu)
        self.success_card = ctk.CTkFrame(
            panel, fg_color=COLORS["success_light"], corner_radius=14,
            border_width=1, border_color=COLORS["success"],
        )
        self._build_success_panel()

    def _build_success_panel(self):
        inner = ctk.CTkFrame(self.success_card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(
            inner, text="🎉 Đăng ký thành công!", font=FONTS["h3"],
            text_color=COLORS["success"], anchor="w",
        ).pack(fill="x", pady=(0, 4))

        self.success_detail_label = ctk.CTkLabel(
            inner, text="", font=FONTS["body"], text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.success_detail_label.pack(fill="x", pady=(0, 14))

        btn_row = ctk.CTkFrame(inner, fg_color="transparent")
        btn_row.pack(fill="x")

        ctk.CTkButton(
            btn_row, text="➕ Đăng ký người khác", font=FONTS["small_bold"], height=38,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self.reset_form,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_row, text="🏠 Về tổng quan", font=FONTS["small_bold"], height=38,
            fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"],
            hover_color=COLORS["border"],
            command=lambda: self.app.navigate("dashboard"),
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

    # ============================================================
    # CAMERA LIFECYCLE
    # ============================================================
    def start_camera(self):
        student_id = self.entry_id.get().strip()
        name = self.entry_name.get().strip()

        if not student_id or not name:
            show_toast(self, "Vui lòng nhập đầy đủ Mã số và Họ tên!", "warning")
            return

        if self.app.student_repo.get_by_id(student_id):
            show_toast(self, f"Mã số '{student_id}' đã tồn tại trong hệ thống!", "error")
            return

        self.current_student_id = student_id
        self.current_student_name = name

        self.camera = CameraStream(
            src=CAMERA_INDEX, width=CAMERA_WIDTH, height=CAMERA_HEIGHT,
            fps_target=CAMERA_FPS_TARGET,
        )
        if not self.camera.start():
            show_toast(self, "Không mở được camera. Kiểm tra lại thiết bị.", "error")
            self.camera = None
            return

        if self.anti_spoof is None:
            self.anti_spoof = AntiSpoof()

        self.enroll_service = EnrollService(
            face_app=self.app.face_app,
            student_repo=self.app.student_repo,
            max_samples=ENROLL_MAX_SAMPLES,
        )

        self.running = True
        self.frame_count = 0
        self.sample_cooldown = 0
        self.consecutive_real_count = 0

        self.entry_id.configure(state="disabled")
        self.entry_name.configure(state="disabled")
        self.btn_start.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.progress_bar.set(0)
        self.progress_label.configure(text=f"0 / {ENROLL_MAX_SAMPLES} mẫu")

        self._update_loop()

    def cancel_enrollment(self):
        self._stop_camera_internal()
        if self.enroll_service:
            self.enroll_service.reset()

        self.entry_id.configure(state="normal")
        self.entry_name.configure(state="normal")

        self.video_label.configure(image="", text="📷  Nhập thông tin và nhấn Bắt đầu", font=FONTS["body"])
        self.progress_bar.set(0)
        self.progress_label.configure(text=f"0 / {ENROLL_MAX_SAMPLES} mẫu")
        self._reset_quality_indicators()
        self._set_status("Nhập thông tin bên phải để bắt đầu", COLORS["text_secondary"])

        self.btn_start.configure(state="normal")
        self.btn_cancel.configure(state="disabled")

    def _stop_camera_internal(self):
        self.running = False
        if self.camera:
            self.camera.stop()
            self.camera = None
        self.photo_image = None

    # ============================================================
    # MAIN LOOP
    # ============================================================
    def _update_loop(self):
        if not self.running or self.camera is None:
            return

        frame_bgr = self.camera.get_frame()
        if frame_bgr is None:
            self.after(UI_REFRESH_MS, self._update_loop)
            return

        self.frame_count += 1
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        display_frame = frame_bgr.copy()

        faces = []
        if self.frame_count % ENROLL_DETECT_INTERVAL == 0:
            small = cv2.resize(frame_rgb, None, fx=FACE_DETECT_SCALE, fy=FACE_DETECT_SCALE)
            faces = self.app.face_app.get(small)

        spoof_info = self.anti_spoof.detect(frame_bgr)
        display_frame = AntiSpoof.draw(display_frame, spoof_info)

        self._reset_quality_indicators()

        if faces:
            self._process_single_face(faces[0], frame_rgb, spoof_info, display_frame)
        else:
            self._set_quality("face", "bad")
            self._set_status("👤 Không phát hiện khuôn mặt", COLORS["danger"])

        if self.sample_cooldown > 0:
            self.sample_cooldown -= 1

        self._render_frame(display_frame)
        self.after(UI_REFRESH_MS, self._update_loop)

    def _process_single_face(self, face, frame_rgb, spoof_info, display_frame):
        # Scale bbox ngược lại theo đúng tỉ lệ đã downscale trước khi detect
        l, t, r, b = (face.bbox / FACE_DETECT_SCALE).astype(int)
        w, h = r - l, b - t

        verified_real = any(
            AntiSpoof.boxes_overlap((l, t, r, b), real_box)
            for real_box in spoof_info["real_boxes"]
        )

        if not verified_real:
            # Bất kỳ frame nào không xác thực được "real" sẽ RESET bộ đếm liên tiếp,
            # buộc phải xác thực lại từ đầu - tránh trường hợp 1 frame dao động sai
            # lọt qua giữa nhiều frame "fake" liên tục (vd: ảnh điện thoại di chuyển).
            self.consecutive_real_count = 0
            self._set_quality("face", "bad")
            self._set_status("🚨 Phát hiện khả năng giả mạo hoặc không rõ ràng", COLORS["danger"])
            cv2.rectangle(display_frame, (l, t), (r, b), (0, 0, 239), 3)
            cv2.putText(display_frame, "SPOOF?", (l, max(t - 10, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 239), 2)
            return

        self.consecutive_real_count += 1
        self._set_quality("face", "good")

        if self.consecutive_real_count < ENROLL_CONSECUTIVE_REAL_REQUIRED:
            remaining = ENROLL_CONSECUTIVE_REAL_REQUIRED - self.consecutive_real_count
            self._set_status(f"🔍 Đang xác thực khuôn mặt thật... ({remaining} frame nữa)", COLORS["info"])
            cv2.rectangle(display_frame, (l, t), (r, b), (255, 165, 0), 2)
            return

        distance_ok = ENROLL_MIN_FACE_SIZE <= w <= ENROLL_MAX_FACE_SIZE and \
            ENROLL_MIN_FACE_SIZE <= h <= ENROLL_MAX_FACE_SIZE

        if w < ENROLL_MIN_FACE_SIZE or h < ENROLL_MIN_FACE_SIZE:
            self._set_quality("distance", "bad")
            self._set_status("📏 Đưa khuôn mặt lại GẦN camera hơn", COLORS["warning"])
        elif w > ENROLL_MAX_FACE_SIZE or h > ENROLL_MAX_FACE_SIZE:
            self._set_quality("distance", "bad")
            self._set_status("📏 Lùi ra XA camera một chút", COLORS["warning"])
        else:
            self._set_quality("distance", "good")

        confidence_ok = face.det_score >= ENROLL_MIN_CONFIDENCE
        if confidence_ok:
            self._set_quality("confidence", "good")
        else:
            self._set_quality("confidence", "bad")
            self._set_status(f"✨ Ánh sáng chưa đủ ({face.det_score * 100:.0f}%)", COLORS["warning"])

        box_color = (34, 197, 94) if (distance_ok and confidence_ok) else (0, 165, 255)
        cv2.rectangle(display_frame, (l, t), (r, b), box_color, 3)
        cv2.putText(display_frame, f"{face.det_score * 100:.0f}%", (l, max(t - 10, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

        if distance_ok and confidence_ok:
            self._try_collect_sample(frame_rgb)

    def _try_collect_sample(self, frame_rgb):
        if self.sample_cooldown > 0:
            self._set_quality("diversity", "warning")
            self._set_status(f"⏱ Giữ yên ({self.sample_cooldown} frame)...", COLORS["info"])
            return

        ok, reason = self.enroll_service.try_add_sample(frame_rgb)

        if ok:
            self.sample_cooldown = ENROLL_SAMPLE_COOLDOWN_FRAMES
            count = self.enroll_service.sample_count()

            self.progress_bar.set(self.enroll_service.progress())
            self.progress_label.configure(text=f"{count} / {ENROLL_MAX_SAMPLES} mẫu")
            self._set_quality("diversity", "good")
            self._set_status(f"✅ Thu thập mẫu {count}/{ENROLL_MAX_SAMPLES}", COLORS["success"])

            if self.enroll_service.is_complete():
                self._finish_enrollment()
        elif reason == "too_similar":
            self._set_quality("diversity", "warning")
            self._set_status("🔄 Xoay nhẹ đầu sang trái/phải/lên/xuống", COLORS["warning"])
        elif reason == "multiple_faces":
            self._set_quality("diversity", "warning")
            self._set_status("⚠ Phát hiện nhiều khuôn mặt, chỉ giữ 1 người trong khung", COLORS["warning"])

    def _finish_enrollment(self):
        # Kiểm tra khuôn mặt vừa thu thập có trùng với người ĐÃ ĐĂNG KÝ khác không
        # (tránh 1 khuôn mặt được gắn nhiều mã số/tên khác nhau).
        is_dup, dup_id, dup_name, similarity = self.enroll_service.check_duplicate_face(
            self.app.face_matcher
        )

        if is_dup:
            self._stop_camera_internal()
            show_toast(
                self,
                f"Khuôn mặt này đã được đăng ký với mã '{dup_id}' ({dup_name}), "
                f"độ giống {similarity:.0%}. Không thể đăng ký trùng!",
                "error",
            )
            self.enroll_service.reset()
            self.cancel_enrollment()
            return

        success = self.enroll_service.save(self.current_student_id, self.current_student_name)
        self._stop_camera_internal()

        if not success:
            show_toast(self, "Lỗi khi lưu dữ liệu, vui lòng thử lại!", "error")
            self.reset_form()
            return

        self.app.face_matcher.reload()

        self.video_label.configure(image="", text="✅", font=("Segoe UI", 64))
        self.success_detail_label.configure(
            text=f"{self.current_student_name}  ·  Mã: {self.current_student_id}"
        )
        self.success_card.pack(fill="x", pady=(16, 0))
        self.btn_start.configure(state="disabled")
        self.btn_cancel.configure(state="disabled")
        self._set_status("Hoàn tất đăng ký", COLORS["success"])

    # ============================================================
    # HELPERS
    # ============================================================
    def _render_frame(self, frame_bgr):
        img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        img = img.resize((480, 360), Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(img)
        self.video_label.configure(image=self.photo_image, text="")

    def _set_status(self, text, color):
        self.status_label.configure(text=text, text_color=color)

    def _set_quality(self, key, status):
        text_color, bg_color = QUALITY_COLORS.get(status, QUALITY_COLORS["inactive"])
        widget = self.quality_widgets.get(key)
        if widget:
            widget.configure(text_color=text_color, fg_color=bg_color)

    def _reset_quality_indicators(self):
        for key in self.quality_widgets:
            self._set_quality(key, "inactive")

    def reset_form(self):
        self.success_card.pack_forget()

        self.entry_id.configure(state="normal")
        self.entry_name.configure(state="normal")
        self.entry_id.delete(0, "end")
        self.entry_name.delete(0, "end")

        self.video_label.configure(image="", text="📷  Nhập thông tin và nhấn Bắt đầu", font=FONTS["body"])
        self.progress_bar.set(0)
        self.progress_label.configure(text=f"0 / {ENROLL_MAX_SAMPLES} mẫu")
        self._reset_quality_indicators()
        self._set_status("Nhập thông tin bên phải để bắt đầu", COLORS["text_secondary"])

        self.btn_start.configure(state="normal")
        self.btn_cancel.configure(state="disabled")

    # ============================================================
    # PAGE LIFECYCLE
    # ============================================================
    def on_show(self):
        pass

    def on_hide(self):
        if self.running:
            self._stop_camera_internal()
            self.reset_form()