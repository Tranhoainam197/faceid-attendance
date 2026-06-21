"""
HistoryPage: tra cứu lịch sử điểm danh theo ngày hoặc toàn bộ, tìm theo mã số, export CSV.
"""
import csv
from datetime import datetime, date

import customtkinter as ctk
from tkinter import ttk, filedialog

from app.ui.theme import COLORS, FONTS
from app.ui.widgets.toast import show_toast


class HistoryPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.all_logs = []

        self._build_ui()

    # ============================================================
    # UI LAYOUT
    # ============================================================
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 12))
        ctk.CTkLabel(
            header, text="Lịch sử chấm công", font=FONTS["h1"],
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            header, text="Tra cứu và xuất báo cáo điểm danh theo ngày",
            font=FONTS["body"], text_color=COLORS["text_secondary"], anchor="w",
        ).pack(fill="x", pady=(2, 0))

        self._build_filter_bar()
        self._build_stats_strip()
        self._build_table()

    def _build_filter_bar(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 12))

        ctk.CTkLabel(
            bar, text="Ngày:", font=FONTS["body"], text_color=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 8))

        self.date_entry = ctk.CTkEntry(bar, width=140, height=38, font=FONTS["body"])
        self.date_entry.insert(0, date.today().strftime("%Y-%m-%d"))
        self.date_entry.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            bar, text="Lọc theo ngày", width=120, height=38, font=FONTS["small_bold"],
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._load_by_date,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            bar, text="Xem tất cả", width=110, height=38, font=FONTS["small_bold"],
            fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"],
            hover_color=COLORS["border"], command=self._load_all,
        ).pack(side="left", padx=(0, 20))

        self.search_entry = ctk.CTkEntry(
            bar, placeholder_text="🔍  Tìm theo mã số...", width=220, height=38, font=FONTS["body"],
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter_by_id())

        ctk.CTkButton(
            bar, text="⬇ Xuất CSV", width=110, height=38, font=FONTS["small_bold"],
            fg_color=COLORS["success"], hover_color="#15803D",
            command=self._export_csv,
        ).pack(side="right")

    def _build_stats_strip(self):
        strip = ctk.CTkFrame(
            self, fg_color=COLORS["info_light"], corner_radius=10,
            border_width=1, border_color=COLORS["info"],
        )
        strip.grid(row=2, column=0, sticky="ew", padx=32, pady=(0, 12))

        self.stats_label = ctk.CTkLabel(
            strip, text="Tổng cộng: 0  ·  Hôm nay: 0", font=FONTS["small_bold"],
            text_color=COLORS["info"],
        )
        self.stats_label.pack(padx=16, pady=10, anchor="w")

    def _build_table(self):
        table_card = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"], corner_radius=14,
            border_width=1, border_color=COLORS["border"],
        )
        table_card.grid(row=3, column=0, sticky="nsew", padx=32, pady=(0, 24))
        table_card.grid_rowconfigure(0, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        self._style_treeview()

        columns = ("id", "name", "time", "date", "status", "session", "similarity")
        self.tree = ttk.Treeview(
            table_card, columns=columns, show="headings", style="LightHistory.Treeview",
        )
        headers = {
            "id": "Mã số", "name": "Họ tên", "time": "Giờ", "date": "Ngày",
            "status": "Trạng thái", "session": "Buổi", "similarity": "Độ khớp",
        }
        widths = {
            "id": 90, "name": 200, "time": 90, "date": 110,
            "status": 100, "session": 80, "similarity": 90,
        }
        for col, text in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=widths[col], anchor="center")
        self.tree.column("name", anchor="w")

        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(16, 0), pady=16)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 16), pady=16)

        self.tree.tag_configure("oddrow", background=COLORS["bg_card"])
        self.tree.tag_configure("evenrow", background=COLORS["bg_input"])

    def _style_treeview(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "LightHistory.Treeview",
            background=COLORS["bg_card"], foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_card"], rowheight=30,
            font=FONTS["small"], borderwidth=0,
        )
        style.configure(
            "LightHistory.Treeview.Heading",
            background=COLORS["bg_input"], foreground=COLORS["text_secondary"],
            font=FONTS["small_bold"], relief="flat", borderwidth=0,
        )
        style.map(
            "LightHistory.Treeview",
            background=[("selected", COLORS["accent_light"])],
            foreground=[("selected", COLORS["text_primary"])],
        )

    # ============================================================
    # DATA
    # ============================================================
    def _render(self, logs):
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not logs:
            self.tree.insert("", "end", values=("", "", "", "Không có dữ liệu", "", "", ""))
            return

        for i, log in enumerate(logs):
            tag = "evenrow" if i % 2 else "oddrow"
            time_str = datetime.fromisoformat(log["time"]).strftime("%H:%M:%S")
            similarity = log.get("similarity")
            sim_str = f"{similarity:.0%}" if similarity is not None else "—"
            self.tree.insert(
                "", "end", tags=(tag,),
                values=(
                    log["student_id"], log["student_name"], time_str, log["date_only"],
                    "Có mặt" if log["status"] == "present" else log["status"],
                    f"#{log['session_id']}", sim_str,
                ),
            )

    def _update_stats(self):
        total = self.app.attendance_repo.count_all()
        today = self.app.attendance_repo.count_today()
        self.stats_label.configure(text=f"Tổng cộng: {total}  ·  Hôm nay: {today}")

    def _load_by_date(self):
        date_str = self.date_entry.get().strip()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            show_toast(self, "Định dạng ngày không đúng (YYYY-MM-DD)", "error")
            return

        self.all_logs = self.app.attendance_repo.get_by_date(date_str)
        self._render(self.all_logs)
        self._update_stats()

    def _load_all(self):
        self.all_logs = self.app.attendance_repo.get_all()
        self._render(self.all_logs)
        self._update_stats()

    def _filter_by_id(self):
        keyword = self.search_entry.get().strip().lower()
        if not keyword:
            self._render(self.all_logs)
            return
        filtered = [log for log in self.all_logs if keyword in str(log["student_id"]).lower()]
        self._render(filtered)

    def _export_csv(self):
        if not self.all_logs:
            show_toast(self, "Không có dữ liệu để xuất!", "warning")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"lich_su_cham_cong_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Mã số", "Họ tên", "Giờ", "Ngày", "Trạng thái", "Buổi", "Độ khớp"])
                for log in self.all_logs:
                    time_str = datetime.fromisoformat(log["time"]).strftime("%H:%M:%S")
                    similarity = log.get("similarity")
                    sim_str = f"{similarity:.0%}" if similarity is not None else ""
                    writer.writerow([
                        log["student_id"], log["student_name"], time_str, log["date_only"],
                        log["status"], log["session_id"], sim_str,
                    ])
            show_toast(self, "Đã xuất file CSV thành công!", "success")
        except Exception as e:
            show_toast(self, f"Lỗi khi xuất file: {e}", "error")

    # ============================================================
    # PAGE LIFECYCLE
    # ============================================================
    def on_show(self):
        self._load_by_date()