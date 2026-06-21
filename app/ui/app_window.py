"""
AppWindow: cửa sổ chính của ứng dụng, chứa Sidebar + khu vực nội dung (pages).
Là "controller" trung tâm: khởi tạo các service dùng chung (DB, FaceEngine,
FaceMatcher...) và truyền xuống cho từng page sử dụng.
"""
import customtkinter as ctk

from config import (
    APP_NAME, APP_MIN_WIDTH, APP_MIN_HEIGHT,
    APPEARANCE_MODE, COLOR_THEME, SIMILARITY_THRESHOLD,
)
from app.ui.theme import COLORS
from app.ui.widgets.sidebar import Sidebar

from app.db.database import Database
from app.db.student_repo import StudentRepo
from app.db.session_repo import SessionRepo
from app.db.attendance_repo import AttendanceRepo

from app.core.face_engine import FaceEngine
from app.core.face_matcher import FaceMatcher

from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.attendance_page import AttendancePage
from app.ui.pages.enroll_page import EnrollPage
from app.ui.pages.students_page import StudentsPage
from app.ui.pages.history_page import HistoryPage


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode(APPEARANCE_MODE)
        ctk.set_default_color_theme(COLOR_THEME)

        self.title(APP_NAME)
        self.geometry(f"{APP_MIN_WIDTH}x{APP_MIN_HEIGHT}")
        self.minsize(APP_MIN_WIDTH, APP_MIN_HEIGHT)
        self.configure(fg_color=COLORS["bg_app"])

        # ===== Services dùng chung (khởi tạo 1 lần) =====
        print("[AppWindow] Đang khởi tạo hệ thống...")
        self.db = Database()
        self.student_repo = StudentRepo(self.db)
        self.session_repo = SessionRepo(self.db)
        self.attendance_repo = AttendanceRepo(self.db)

        self.face_app = FaceEngine.get_instance()
        self.face_matcher = FaceMatcher(self.student_repo, threshold=SIMILARITY_THRESHOLD)
        print("[AppWindow] Khởi tạo hoàn tất.")

        # ===== Layout: Sidebar + Content =====
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self, on_navigate=self.navigate)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content_area = ctk.CTkFrame(self, fg_color=COLORS["bg_app"], corner_radius=0)
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)

        self.pages = {}
        self._register_pages()

        self.sidebar.set_active("dashboard")
        self.navigate("dashboard")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _register_pages(self):
        page_classes = {
            "dashboard": DashboardPage,
            "attendance": AttendancePage,
            "enroll": EnrollPage,
            "students": StudentsPage,
            "history": HistoryPage,
        }
        for key, cls in page_classes.items():
            page = cls(self.content_area, app=self)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = page

    def navigate(self, key: str):
        """Chuyển trang. Gọi on_show()/on_hide() để page tự quản lý camera/resource."""
        for k, page in self.pages.items():
            if k == key:
                page.grid()
                if hasattr(page, "on_show"):
                    page.on_show()
            else:
                if hasattr(page, "on_hide"):
                    page.on_hide()
                page.grid_remove()
        self.sidebar.set_active(key)

    def on_close(self):
        for page in self.pages.values():
            if hasattr(page, "on_hide"):
                page.on_hide()
        self.db.close()
        self.destroy()