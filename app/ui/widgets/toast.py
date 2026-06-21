"""
Toast: thông báo nổi nhỏ ở góc màn hình, tự ẩn sau vài giây.
Thay thế messagebox xấu/lỗi thời của Tkinter, đồng bộ với theme sáng hiện đại.
"""
import customtkinter as ctk

from app.ui.theme import COLORS, FONTS, RADIUS


class Toast(ctk.CTkFrame):
    _active_toasts = []

    def __init__(self, parent, message: str, kind: str = "info", duration_ms: int = 2500):
        style_map = {
            "success": (COLORS["success"], COLORS["success_light"], "✓"),
            "error": (COLORS["danger"], COLORS["danger_light"], "✕"),
            "warning": (COLORS["warning"], COLORS["warning_light"], "⚠"),
            "info": (COLORS["info"], COLORS["info_light"], "ℹ"),
        }
        accent, bg, icon = style_map.get(kind, style_map["info"])

        super().__init__(
            parent, fg_color=bg, corner_radius=RADIUS["card"],
            border_width=1, border_color=accent,
        )

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(padx=16, pady=12, fill="x")

        ctk.CTkLabel(
            row, text=icon, text_color=accent,
            font=FONTS["body_bold"], width=20,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            row, text=message, text_color=COLORS["text_primary"],
            font=FONTS["body"], wraplength=320, justify="left",
        ).pack(side="left", fill="x", expand=True)

        self._stack_and_show(parent)
        self.after(duration_ms, self._dismiss)

    def _stack_and_show(self, parent):
        Toast._active_toasts.append(self)
        offset = 20 + (len(Toast._active_toasts) - 1) * 64
        self.place(relx=0.99, y=offset, anchor="ne")

    def _dismiss(self):
        if self in Toast._active_toasts:
            Toast._active_toasts.remove(self)
        self.destroy()
        self._reflow()

    def _reflow(self):
        for i, toast in enumerate(Toast._active_toasts):
            offset = 20 + i * 64
            toast.place(relx=0.99, y=offset, anchor="ne")


def show_toast(parent, message: str, kind: str = "info"):
    """Helper gọi nhanh: show_toast(self, 'Đã lưu!', 'success')"""
    return Toast(parent, message, kind)