"""
AttendancePage: trang chấm công real-time bằng camera.

Kiến trúc xử lý mỗi tick (self.after):
1. Lấy frame mới nhất từ CameraStream (không chờ đợi, luôn có sẵn)
2. Mỗi N frame: chạy InsightFace để detect khuôn mặt + embedding
3. Mỗi N frame: chạy YOLO anti-spoofing trên toàn frame
4. AttendanceService xử lý kết quả: xác thực real + match + ghi nhận DB
5. Vẽ kết quả lên frame và hiển thị

Nhờ camera chạy trên thread riêng, dù bước 2-3 chậm (CPU yếu),
hình ảnh hiển thị vẫn không bị "đứng/giật" như bản cũ.
"""
import cv2
import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import ttk
from datetime import datetime, timedelta

from config import (
    CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS_TARGET, UI_REFRESH_MS,
    ATTENDANCE_DETECT_INTERVAL, SIMILARITY_THRESHOLD, ATTENDANCE_COOLDOWN_SEC,
)
from app.ui.theme import COLORS, FONTS
from app.ui.widgets.toast import show_toast
from app.core.camera_stream import CameraStream
from app.core.anti_spoof import AntiSpoof
from app.core.attendance_service import AttendanceService

FACE_DETECT_SCALE = 0.75   # downscale ảnh trước khi đưa vào InsightFace để tăng FPS


class AttendancePage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        self.camera: CameraStream | None = None
        self.anti_spoof: AntiSpoof | None = None
        self.attendance_service: AttendanceService | None = None

        self.running = False
        self.frame_count = 0
        self.photo_image = None
        self.session_map = {}   # display_text -> session_id

        self._build_ui()

    # ============================================================
    # UI LAYOUT
    # ============================================================
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ---- Header ----
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 12))
        ctk.CTkLabel(
            header, text="Chấm công", font=FONTS["h1"],
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            header, text="Chọn buổi học và bắt đầu nhận diện khuôn mặt qua camera",
            font=FONTS["body"], text_color=COLORS["text_secondary"], anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # ---- Body: 2 columns ----
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=32, pady=(0, 24))
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_camera_panel(body)
        self._build_info_panel(body)

    def _build_camera_panel(self, parent):
        panel = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_card"], corner_radius=14,
            border_width=1, border_color=COLORS["border"],
        )
        panel.grid(row=0, column=0, sticky="ns", padx=(0, 16))

        inner = ctk.CTkFrame(panel, fg_color="transparent")
        inner.pack(padx=20, pady=20)

        # Session selector
        session_row = ctk.CTkFrame(inner, fg_color="transparent")
        session_row.pack(fill="x", pady=(0, 12))

        self.session_combo = ctk.CTkComboBox(
            session_row, values=["Chưa có buổi nào"], width=300,
            font=FONTS["body"], state="readonly",
            command=self._on_session_selected,
        )
        self.session_combo.pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            session_row, text="＋ Buổi mới", width=100, font=FONTS["small_bold"],
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._open_new_session_dialog,
        ).pack(side="left")

        # Video frame
        video_box = ctk.CTkFrame(
            inner, fg_color="#111317", corner_radius=12, width=CAMERA_WIDTH, height=CAMERA_HEIGHT,
        )
        video_box.pack(pady=(0, 14))
        video_box.pack_propagate(False)

        self.video_label = ctk.CTkLabel(
            video_box, text="📷  Camera chưa khởi động", text_color="#9CA3AF",
            font=FONTS["body"],
        )
        self.video_label.place(relx=0.5, rely=0.5, anchor="center")

        # Status pill
        self.status_label = ctk.CTkLabel(
            inner, text="Chọn buổi học để bắt đầu", font=FONTS["small_bold"],
            text_color=COLORS["text_secondary"], fg_color=COLORS["bg_input"],
            corner_radius=20, height=34,
        )
        self.status_label.pack(fill="x", pady=(0, 14))

        # Controls
        controls = ctk.CTkFrame(inner, fg_color="transparent")
        controls.pack(fill="x")

        self.btn_start = ctk.CTkButton(
            controls, text="▶  Bắt đầu", font=FONTS["body_bold"], height=42,
            fg_color=COLORS["success"], hover_color="#15803D",
            command=self.start_camera,
        )
        self.btn_start.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.btn_stop = ctk.CTkButton(
            controls, text="■  Dừng", font=FONTS["body_bold"], height=42,
            fg_color=COLORS["danger"], hover_color="#B91C1C",
            state="disabled", command=self.stop_camera,
        )
        self.btn_stop.pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _build_info_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Stat strip
        stat_row = ctk.CTkFrame(panel, fg_color="transparent")
        stat_row.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        self.marked_count_label = ctk.CTkLabel(
            stat_row, text="0 người đã chấm công", font=FONTS["h3"],
            text_color=COLORS["text_primary"], anchor="w",
        )
        self.marked_count_label.pack(side="left")

        # Log list
        log_card = ctk.CTkFrame(
            panel, fg_color=COLORS["bg_card"], corner_radius=14,
            border_width=1, border_color=COLORS["border"],
        )
        log_card.grid(row=1, column=0, sticky="nsew")
        log_card.grid_rowconfigure(1, weight=1)
        log_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_card, text="Danh sách vừa điểm danh", font=FONTS["body_bold"],
            text_color=COLORS["text_primary"], anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))

        self.log_scroll = ctk.CTkScrollableFrame(log_card, fg_color="transparent")
        self.log_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.log_scroll.grid_columnconfigure(0, weight=1)

    # ============================================================
    # SESSION HANDLING
    # ============================================================
    def _refresh_sessions(self):
        sessions = self.app.session_repo.get_recent(limit=30)
        self.session_map.clear()

        if not sessions:
            self.session_combo.configure(values=["Chưa có buổi nào"])
            self.session_combo.set("Chưa có buổi nào")
            return

        display_list = []
        for s in sessions:
            start_str = datetime.fromisoformat(s["start_time"]).strftime("%d/%m %H:%M")
            tag = " · Đang mở" if s["status"] == "open" else ""
            display = f"{s['course']} — {start_str}{tag} (#{s['id']})"
            display_list.append(display)
            self.session_map[display] = s["id"]

        self.session_combo.configure(values=display_list)
        self.session_combo.set(display_list[0])
        self._on_session_selected(display_list[0])

    def _on_session_selected(self, selected_display):
        session_id = self.session_map.get(selected_display)
        if session_id and self.attendance_service:
            self.attendance_service.start_session(session_id)
        self._current_session_display = selected_display

    def _open_new_session_dialog(self):
        dialog = ctk.CTkInputDialog(
            text="Nhập tên buổi học / lớp:", title="Tạo buổi học mới"
        )
        course_name = dialog.get_input()
        if not course_name or not course_name.strip():
            return

        session_id = self.app.session_repo.create(course_name.strip())
        show_toast(self, f"Đã tạo buổi học: {course_name.strip()}", "success")
        self._refresh_sessions()

        # Tự động chọn buổi vừa tạo
        for display, sid in self.session_map.items():
            if sid == session_id:
                self.session_combo.set(display)
                self._on_session_selected(display)
                break

    # ============================================================
    # CAMERA LIFECYCLE
    # ============================================================
    def start_camera(self):
        if not self.session_map or self.session_combo.get() not in self.session_map:
            show_toast(self, "Vui lòng chọn hoặc tạo buổi học trước!", "warning")
            return

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

        if self.attendance_service is None:
            self.attendance_service = AttendanceService(
                face_app=self.app.face_app,
                face_matcher=self.app.face_matcher,
                attendance_repo=self.app.attendance_repo,
                similarity_threshold=SIMILARITY_THRESHOLD,
                cooldown_sec=ATTENDANCE_COOLDOWN_SEC,
            )
        session_id = self.session_map[self.session_combo.get()]
        self.attendance_service.start_session(session_id)

        self.running = True
        self.frame_count = 0
        self._clear_log()

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.session_combo.configure(state="disabled")
        self._set_status("🎥 Đang chấm công...", COLORS["success"])

        self._update_loop()

    def stop_camera(self):
        self.running = False
        if self.camera:
            self.camera.stop()
            self.camera = None
        if self.attendance_service:
            self.attendance_service.stop_session()

        self.video_label.configure(image="", text="📷  Camera chưa khởi động")
        self.photo_image = None

        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.session_combo.configure(state="readonly")
        self._set_status("⏹ Đã dừng chấm công", COLORS["text_secondary"])

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
        display_frame = frame_bgr.copy()

        faces = []
        if self.frame_count % ATTENDANCE_DETECT_INTERVAL == 0:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            small = cv2.resize(frame_rgb, None, fx=FACE_DETECT_SCALE, fy=FACE_DETECT_SCALE)
            faces = self.app.face_app.get(small)

        spoof_info = self.anti_spoof.detect(frame_bgr)
        display_frame = AntiSpoof.draw(display_frame, spoof_info)

        if faces:
            results = self.attendance_service.process_faces(
                faces, spoof_info, bbox_scale=1.0 / FACE_DETECT_SCALE
            )
            for res in results:
                l, t, r, b = res["bbox"]
                cv2.rectangle(display_frame, (l, t), (r, b), res["color"], 2)
                cv2.putText(
                    display_frame, res["label"], (l, max(t - 10, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, res["color"], 2,
                )
                if res.get("matched"):
                    self._maybe_log_attendance(res["student_id"], res["student_name"])

            self._update_status_from_results(results, spoof_info)
        elif spoof_info["has_real"]:
            self._set_status("✓ Khuôn mặt thật — đang nhận diện danh tính", COLORS["info"])
        elif spoof_info["fake_boxes"]:
            self._set_status("⚠ Phát hiện khả năng giả mạo", COLORS["danger"])
        else:
            self._set_status("Đang chờ phát hiện khuôn mặt...", COLORS["text_secondary"])

        self._render_frame(display_frame)
        self.after(UI_REFRESH_MS, self._update_loop)

    def _update_status_from_results(self, results, spoof_info):
        if any(r.get("matched") for r in results):
            self._set_status("✓ Đã xác thực và chấm công", COLORS["success"])
        elif spoof_info["has_real"]:
            self._set_status("✓ Khuôn mặt thật — không khớp dữ liệu", COLORS["warning"])
        else:
            self._set_status("⚠ Chưa xác thực được khuôn mặt thật", COLORS["danger"])

    def _render_frame(self, frame_bgr):
        img = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        img = img.resize((CAMERA_WIDTH, CAMERA_HEIGHT), Image.Resampling.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(img)
        self.video_label.configure(image=self.photo_image, text="")

    def _set_status(self, text, color):
        self.status_label.configure(text=text, text_color=color)

    # ============================================================
    # ATTENDANCE LOG (UI list)
    # ============================================================
    def _maybe_log_attendance(self, student_id, student_name):
        """Chỉ thêm vào danh sách UI nếu vừa thật sự ghi nhận trong DB lần này."""
        marked_ids = self.attendance_service.marked_ids
        logged_key = f"_logged_{student_id}"
        if getattr(self, logged_key, False):
            return
        if student_id in marked_ids:
            setattr(self, logged_key, True)
            self._add_log_row(student_id, student_name)
            self.marked_count_label.configure(
                text=f"{self.attendance_service.marked_count()} người đã chấm công"
            )

    def _add_log_row(self, student_id, student_name):
        row = ctk.CTkFrame(self.log_scroll, fg_color=COLORS["success_light"], corner_radius=10)
        row.pack(fill="x", pady=4, padx=4)

        ctk.CTkLabel(
            row, text="✓", font=FONTS["body_bold"], text_color=COLORS["success"], width=24,
        ).pack(side="left", padx=(10, 4), pady=10)

        text_box = ctk.CTkFrame(row, fg_color="transparent")
        text_box.pack(side="left", fill="x", expand=True, pady=8)
        ctk.CTkLabel(
            text_box, text=student_name, font=FONTS["body_bold"],
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            text_box, text=f"Mã: {student_id}  ·  {datetime.now().strftime('%H:%M:%S')}",
            font=FONTS["small"], text_color=COLORS["text_secondary"], anchor="w",
        ).pack(fill="x")

    def _clear_log(self):
        for child in self.log_scroll.winfo_children():
            child.destroy()
        self.marked_count_label.configure(text="0 người đã chấm công")
        # reset cờ "đã log" của các lượt trước
        for attr in list(self.__dict__.keys()):
            if attr.startswith("_logged_"):
                delattr(self, attr)

    # ============================================================
    # PAGE LIFECYCLE (gọi từ AppWindow.navigate)
    # ============================================================
    def on_show(self):
        self._refresh_sessions()

    def on_hide(self):
        """Quan trọng: tự dừng camera khi rời trang để không tốn CPU ngầm."""
        if self.running:
            self.stop_camera()