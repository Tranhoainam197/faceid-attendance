"""
Sidebar: menu điều hướng cố định bên trái, highlight trang đang chọn.
"""
import customtkinter as ctk

from app.ui.theme import COLORS, FONTS, SIDEBAR_WIDTH

NAV_ITEMS = [
    ("dashboard", "🏠", "Tổng quan"),
    ("attendance", "📷", "Chấm công"),
    ("enroll", "➕", "Đăng ký mới"),
    ("students", "👥", "Nhân sự"),
    ("history", "🕘", "Lịch sử"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_navigate):
        super().__init__(
            parent, width=SIDEBAR_WIDTH, fg_color=COLORS["bg_sidebar"],
            corner_radius=0, border_width=0,
        )
        self.on_navigate = on_navigate
        self.buttons = {}
        self.active_key = None

        self.pack_propagate(False)

        # ===== Logo / Tên app =====
        header = ctk.CTkFrame(self, fg_color="transparent", height=84)
        header.pack(fill="x", padx=20, pady=(24, 10))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="🪪", font=("Segoe UI", 26),
        ).pack(side="left", padx=(0, 10))

        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            title_box, text="FaceID", font=FONTS["h3"],
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            title_box, text="Attendance System", font=FONTS["small"],
            text_color=COLORS["text_muted"], anchor="w",
        ).pack(fill="x")

        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1).pack(fill="x", padx=20, pady=(0, 16))

        # ===== Nav items =====
        nav_container = ctk.CTkFrame(self, fg_color="transparent")
        nav_container.pack(fill="x", padx=14)

        for key, icon, label in NAV_ITEMS:
            self._create_nav_button(nav_container, key, icon, label)

        # ===== Footer =====
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", side="bottom", padx=20, pady=20)
        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1).pack(
            fill="x", side="bottom", padx=20, pady=(0, 0)
        )
        ctk.CTkLabel(
            footer, text="© 2026 FaceID Attendance",
            font=FONTS["small"], text_color=COLORS["text_muted"],
        ).pack(anchor="w")

    def _create_nav_button(self, parent, key, icon, label):
        btn = ctk.CTkButton(
            parent,
            text=f"  {icon}   {label}",
            anchor="w",
            font=FONTS["sidebar_item"],
            fg_color="transparent",
            text_color=COLORS["sidebar_text"],
            hover_color=COLORS["sidebar_hover"],
            corner_radius=10,
            height=42,
            command=lambda k=key: self._handle_click(k),
        )
        btn.pack(fill="x", pady=3)
        self.buttons[key] = btn

    def _handle_click(self, key):
        self.set_active(key)
        self.on_navigate(key)

    def set_active(self, key):
        self.active_key = key
        for k, btn in self.buttons.items():
            if k == key:
                btn.configure(
                    fg_color=COLORS["sidebar_active_bg"],
                    text_color=COLORS["sidebar_active_text"],
                    font=FONTS["sidebar_item"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["sidebar_text"],
                )