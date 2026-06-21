"""
StudentsPage: danh sách nhân sự đã đăng ký - tìm kiếm, xem chi tiết, xóa, export CSV.
"""
import csv
from datetime import datetime

import customtkinter as ctk
from tkinter import ttk, filedialog

from app.ui.theme import COLORS, FONTS
from app.ui.widgets.toast import show_toast


class StudentsPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.all_students = []
        self.selected_id = None

        self._build_ui()

    # ============================================================
    # UI LAYOUT
    # ============================================================
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=(28, 12))
        ctk.CTkLabel(
            header, text="Nhân sự", font=FONTS["h1"],
            text_color=COLORS["text_primary"], anchor="w",
        ).pack(fill="x")
        self.subtitle_label = ctk.CTkLabel(
            header, text="0 người đã đăng ký", font=FONTS["body"],
            text_color=COLORS["text_secondary"], anchor="w",
        )
        self.subtitle_label.pack(fill="x", pady=(2, 0))

        self._build_toolbar()
        self._build_table()

    def _build_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", padx=32, pady=(0, 12))

        self.search_entry = ctk.CTkEntry(
            toolbar, placeholder_text="🔍  Tìm theo mã số hoặc họ tên...",
            width=320, height=38, font=FONTS["body"],
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self._filter())

        ctk.CTkButton(
            toolbar, text="🔄 Làm mới", width=110, height=38, font=FONTS["small_bold"],
            fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"],
            hover_color=COLORS["border"], command=self.refresh,
        ).pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            toolbar, text="🗑 Xóa đã chọn", width=130, height=38, font=FONTS["small_bold"],
            fg_color=COLORS["danger_light"], text_color=COLORS["danger"],
            hover_color="#FEE2E2", command=self._delete_selected,
        ).pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            toolbar, text="⬇ Xuất CSV", width=120, height=38, font=FONTS["small_bold"],
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._export_csv,
        ).pack(side="right")

    def _build_table(self):
        table_card = ctk.CTkFrame(
            self, fg_color=COLORS["bg_card"], corner_radius=14,
            border_width=1, border_color=COLORS["border"],
        )
        table_card.grid(row=2, column=0, sticky="nsew", padx=32, pady=(0, 24))
        table_card.grid_rowconfigure(0, weight=1)
        table_card.grid_columnconfigure(0, weight=1)

        self._style_treeview()

        columns = ("id", "name", "samples", "quality", "created")
        self.tree = ttk.Treeview(
            table_card, columns=columns, show="headings", style="Light.Treeview",
        )
        self.tree.heading("id", text="Mã số")
        self.tree.heading("name", text="Họ tên")
        self.tree.heading("samples", text="Số mẫu")
        self.tree.heading("quality", text="Chất lượng")
        self.tree.heading("created", text="Ngày đăng ký")

        self.tree.column("id", width=120, anchor="center")
        self.tree.column("name", width=260, anchor="w")
        self.tree.column("samples", width=100, anchor="center")
        self.tree.column("quality", width=130, anchor="center")
        self.tree.column("created", width=180, anchor="center")

        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew", padx=(16, 0), pady=16)
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(0, 16), pady=16)

        self.tree.tag_configure("oddrow", background=COLORS["bg_card"])
        self.tree.tag_configure("evenrow", background=COLORS["bg_input"])

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _style_treeview(self):
        """Đồng bộ style Treeview (ttk, không thuộc customtkinter) với theme sáng."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Light.Treeview",
            background=COLORS["bg_card"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_card"],
            rowheight=32,
            font=FONTS["body"],
            borderwidth=0,
        )
        style.configure(
            "Light.Treeview.Heading",
            background=COLORS["bg_input"],
            foreground=COLORS["text_secondary"],
            font=FONTS["small_bold"],
            relief="flat",
            borderwidth=0,
        )
        style.map(
            "Light.Treeview",
            background=[("selected", COLORS["accent_light"])],
            foreground=[("selected", COLORS["text_primary"])],
        )

    # ============================================================
    # DATA
    # ============================================================
    def refresh(self):
        self.all_students = self.app.student_repo.get_all()
        self._render(self.all_students)
        self.subtitle_label.configure(text=f"{len(self.all_students)} người đã đăng ký")

    def _render(self, students):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, s in enumerate(students):
            tag = "evenrow" if i % 2 else "oddrow"
            quality = s.get("quality_score") or 0
            created = s.get("created_at", "")[:10] if s.get("created_at") else "N/A"
            self.tree.insert(
                "", "end", iid=s["id"], tags=(tag,),
                values=(s["id"], s["name"], s["num_samples"], f"{quality:.0%}", created),
            )

    def _filter(self):
        keyword = self.search_entry.get().strip().lower()
        if not keyword:
            self._render(self.all_students)
            return
        filtered = [
            s for s in self.all_students
            if keyword in s["id"].lower() or keyword in s["name"].lower()
        ]
        self._render(filtered)

    def _on_select(self, event):
        selection = self.tree.selection()
        self.selected_id = selection[0] if selection else None

    def _delete_selected(self):
        if not self.selected_id:
            show_toast(self, "Vui lòng chọn một người trong danh sách!", "warning")
            return

        student = self.app.student_repo.get_by_id(self.selected_id)
        if not student:
            return

        confirm = ConfirmDialog(
            self, title="Xác nhận xóa",
            message=f"Bạn có chắc muốn xóa:\n\n{student['name']} (Mã: {student['id']})\n\n"
                     "Hành động này không thể hoàn tác.",
        )
        if confirm.result:
            success = self.app.student_repo.delete(self.selected_id)
            if success:
                self.app.face_matcher.reload()
                show_toast(self, f"Đã xóa {student['name']}", "success")
                self.refresh()
            else:
                show_toast(self, "Không thể xóa, vui lòng thử lại!", "error")

    def _export_csv(self):
        if not self.all_students:
            show_toast(self, "Không có dữ liệu để xuất!", "warning")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"nhan_su_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["Mã số", "Họ tên", "Số mẫu", "Chất lượng", "Ngày đăng ký"])
                for s in self.all_students:
                    quality = s.get("quality_score") or 0
                    writer.writerow([
                        s["id"], s["name"], s["num_samples"],
                        f"{quality:.0%}", s.get("created_at", "")[:10],
                    ])
            show_toast(self, "Đã xuất file CSV thành công!", "success")
        except Exception as e:
            show_toast(self, f"Lỗi khi xuất file: {e}", "error")

    # ============================================================
    # PAGE LIFECYCLE
    # ============================================================
    def on_show(self):
        self.refresh()


class ConfirmDialog(ctk.CTkToplevel):
    """Hộp thoại xác nhận đồng bộ theme, thay cho messagebox.askyesno xấu/lỗi thời."""

    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.title(title)
        self.geometry("420x220")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_card"])
        self.result = False

        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(
            self, text=message, font=FONTS["body"], text_color=COLORS["text_primary"],
            justify="left", wraplength=360,
        ).pack(padx=24, pady=(24, 16), fill="both", expand=True)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(0, 20))

        ctk.CTkButton(
            btn_row, text="Hủy", height=38, fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"], hover_color=COLORS["border"],
            command=self._cancel,
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_row, text="Xóa", height=38, fg_color=COLORS["danger"],
            hover_color="#B91C1C", command=self._confirm,
        ).pack(side="left", expand=True, fill="x", padx=(6, 0))

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self._center_on_parent(parent)
        self.wait_window(self)

    def _center_on_parent(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - 420) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - 220) // 2
        self.geometry(f"+{x}+{y}")

    def _confirm(self):
        self.result = True
        self.destroy()

    def _cancel(self):
        self.result = False
        self.destroy()