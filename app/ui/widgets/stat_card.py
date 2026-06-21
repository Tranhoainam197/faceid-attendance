"""
StatCard: thẻ hiển thị 1 số liệu thống kê (dùng cho Dashboard).
"""
import customtkinter as ctk

from app.ui.theme import COLORS, FONTS, RADIUS


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, icon: str, label: str, value: str, accent: str = None):
        accent = accent or COLORS["accent"]

        super().__init__(
            parent, fg_color=COLORS["bg_card"], corner_radius=RADIUS["card"],
            border_width=1, border_color=COLORS["border"],
        )

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=18)

        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x")

        icon_box = ctk.CTkFrame(
            top_row, fg_color=accent, corner_radius=10, width=42, height=42,
        )
        icon_box.pack(side="left")
        icon_box.pack_propagate(False)
        ctk.CTkLabel(
            icon_box, text=icon, font=("Segoe UI", 18), text_color="white",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner, text=label, font=FONTS["small"],
            text_color=COLORS["text_secondary"], anchor="w",
        ).pack(fill="x", pady=(14, 2))

        self.value_label = ctk.CTkLabel(
            inner, text=value, font=FONTS["stat_value"],
            text_color=COLORS["text_primary"], anchor="w",
        )
        self.value_label.pack(fill="x")

    def set_value(self, value: str):
        self.value_label.configure(text=value)