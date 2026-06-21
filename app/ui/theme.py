"""
Theme tập trung cho toàn bộ giao diện: màu sắc, font, khoảng cách.
Light mode chuyên nghiệp lấy cảm hứng từ các app SaaS hiện đại
(nền trắng/xám nhạt, điểm nhấn xanh, chữ tối, bo góc mềm).
"""

# ============================================================
# MÀU SẮC
# ============================================================
COLORS = {
    # Nền
    "bg_app": "#F4F6F9",          # nền tổng thể, xám rất nhạt
    "bg_sidebar": "#FFFFFF",
    "bg_card": "#FFFFFF",
    "bg_card_hover": "#F0F4FF",
    "bg_input": "#F7F8FA",

    # Viền
    "border": "#E5E8EC",
    "border_focus": "#4F6EF7",

    # Chữ
    "text_primary": "#1A1D29",
    "text_secondary": "#6B7280",
    "text_muted": "#9CA3AF",
    "text_on_accent": "#FFFFFF",

    # Màu chủ đạo (accent) - xanh indigo chuyên nghiệp
    "accent": "#4F6EF7",
    "accent_hover": "#3D5BE0",
    "accent_light": "#EEF2FF",

    # Trạng thái
    "success": "#16A34A",
    "success_light": "#ECFDF5",
    "warning": "#F59E0B",
    "warning_light": "#FFFBEB",
    "danger": "#EF4444",
    "danger_light": "#FEF2F2",
    "info": "#3B82F6",
    "info_light": "#EFF6FF",

    # Sidebar item
    "sidebar_active_bg": "#EEF2FF",
    "sidebar_active_text": "#4F6EF7",
    "sidebar_text": "#4B5563",
    "sidebar_hover": "#F4F6F9",
}

# ============================================================
# FONT
# ============================================================
FONTS = {
    "family": "Segoe UI",
    "h1": ("Segoe UI", 26, "bold"),
    "h2": ("Segoe UI", 19, "bold"),
    "h3": ("Segoe UI", 15, "bold"),
    "body": ("Segoe UI", 13),
    "body_bold": ("Segoe UI", 13, "bold"),
    "small": ("Segoe UI", 11),
    "small_bold": ("Segoe UI", 11, "bold"),
    "mono": ("Consolas", 12),
    "sidebar_item": ("Segoe UI", 13),
    "stat_value": ("Segoe UI", 28, "bold"),
}

# ============================================================
# KÍCH THƯỚC / BO GÓC
# ============================================================
RADIUS = {
    "card": 14,
    "button": 10,
    "input": 8,
    "badge": 20,
}

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 16,
    "lg": 24,
    "xl": 32,
}

SIDEBAR_WIDTH = 230