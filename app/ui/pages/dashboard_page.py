"""
DashboardPage: trang tổng quan, hiển thị số liệu thống kê nhanh
và truy cập nhanh đến các tác vụ chính.
"""
import customtkinter as ctk

from app.ui.theme import COLORS, FONTS
from app.ui.widgets.stat_card import StatCard


class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_stats()
        self._build_quick_actions()

    # ----------------------------------------------------------
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=32, pady=(28, 8))

        ctk.CTkLabel(
            header, text="Tổng quan", font=FONTS["h1"],
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            header, text="Theo dõi nhanh tình trạng điểm danh hệ thống",
            font=FONTS["body"], text_color=COLORS["text_secondary"], anchor="w",
        ).pack(fill="x", pady=(2, 0))

    # ----------------------------------------------------------
    def _build_stats(self):
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.pack(fill="x", padx=32, pady=(12, 8))
        for i in range(4):
            stats_row.grid_columnconfigure(i, weight=1, uniform="stat")

        self.card_students = StatCard(
            stats_row, icon="👥", label="Tổng nhân sự", value="0",
            accent=COLORS["accent"],
        )
        self.card_students.grid(row=0, column=0, padx=(0, 12), sticky="ew")

        self.card_today = StatCard(
            stats_row, icon="📅", label="Điểm danh hôm nay", value="0",
            accent=COLORS["success"],
        )
        self.card_today.grid(row=0, column=1, padx=12, sticky="ew")

        self.card_total = StatCard(
            stats_row, icon="📊", label="Tổng lượt điểm danh", value="0",
            accent=COLORS["info"],
        )
        self.card_total.grid(row=0, column=2, padx=12, sticky="ew")

        self.card_session = StatCard(
            stats_row, icon="🟢", label="Buổi đang mở", value="Không có",
            accent=COLORS["warning"],
        )
        self.card_session.grid(row=0, column=3, padx=(12, 0), sticky="ew")

    # ----------------------------------------------------------
    def _build_quick_actions(self):
        section = ctk.CTkFrame(self, fg_color="transparent")
        section.pack(fill="x", padx=32, pady=(20, 8))

        ctk.CTkLabel(
            section, text="Tác vụ nhanh", font=FONTS["h3"],
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(fill="x", pady=(0, 12))

        actions_row = ctk.CTkFrame(section, fg_color="transparent")
        actions_row.pack(fill="x")
        for i in range(3):
            actions_row.grid_columnconfigure(i, weight=1, uniform="action")

        self._action_card(
            actions_row, 0, "📷", "Bắt đầu chấm công",
            "Mở camera và điểm danh theo buổi học",
            COLORS["accent"], lambda: self.app.navigate("attendance"),
        )
        self._action_card(
            actions_row, 1, "➕", "Đăng ký nhân sự mới",
            "Thu thập khuôn mặt cho người mới",
            COLORS["success"], lambda: self.app.navigate("enroll"),
        )
        self._action_card(
            actions_row, 2, "🕘", "Xem lịch sử",
            "Tra cứu và xuất báo cáo điểm danh",
            COLORS["info"], lambda: self.app.navigate("history"),
        )

    def _action_card(self, parent, col, icon, title, desc, accent, command):
        card = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_card"], corner_radius=14,
            border_width=1, border_color=COLORS["border"], cursor="hand2",
        )
        card.grid(row=0, column=col, padx=8, pady=4, sticky="nsew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=20)

        icon_box = ctk.CTkFrame(inner, fg_color=accent, corner_radius=10, width=44, height=44)
        icon_box.pack(anchor="w")
        icon_box.pack_propagate(False)
        ctk.CTkLabel(icon_box, text=icon, font=("Segoe UI", 19), text_color="white").place(
            relx=0.5, rely=0.5, anchor="center"
        )

        ctk.CTkLabel(
            inner, text=title, font=FONTS["body_bold"],
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(fill="x", pady=(14, 2))
        ctk.CTkLabel(
            inner, text=desc, font=FONTS["small"],
            text_color=COLORS["text_secondary"], anchor="w", justify="left", wraplength=220,
        ).pack(fill="x")

        # Bind click cho toàn bộ card (frame + label con)
        for widget in (card, inner, icon_box):
            widget.bind("<Button-1>", lambda e: command())
        for child in inner.winfo_children():
            child.bind("<Button-1>", lambda e: command())

    # ----------------------------------------------------------
    def on_show(self):
        """Refresh số liệu mỗi khi quay lại trang Dashboard."""
        total_students = self.app.student_repo.count()
        today_count = self.app.attendance_repo.count_today()
        total_count = self.app.attendance_repo.count_all()
        open_session = self.app.session_repo.get_open_session()

        self.card_students.set_value(str(total_students))
        self.card_today.set_value(str(today_count))
        self.card_total.set_value(str(total_count))
        self.card_session.set_value(open_session["course"] if open_session else "Không có")