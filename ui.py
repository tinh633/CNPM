# ui.py
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
from tkinter import ttk 
import time
from typing import Optional, List, Dict, Set

# Thư viện giao diện đẹp
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap.tableview import Tableview

# Import models
from models import (
    User, Exam, Template, Question, Attempt,
    ROLES, ROLE_CANON, score_question_partial
)
# Import utils
import utils

# -----------------------------
# UI helpers
# -----------------------------
def info(msg: str):
    messagebox.showinfo("Thông báo", msg)

def err(msg: str):
    messagebox.showerror("Lỗi", msg)

class Header(tb.Frame):
    def __init__(self, parent, title, subtitle=""):
        super().__init__(parent, bootstyle="primary")
        tb.Label(self, text=title, font=("Segoe UI", 18, "bold"), bootstyle="inverse-primary").pack(anchor="w", padx=20, pady=(15, 5))
        if subtitle:
            tb.Label(self, text=subtitle, font=("Segoe UI", 11), bootstyle="inverse-primary").pack(anchor="w", padx=20, pady=(0, 15))
        else:
            tb.Label(self, text="", font=("Segoe UI", 11), bootstyle="inverse-primary").pack(pady=(0, 15))

# -----------------------------
# FRAMES
# -----------------------------

class LoginFrame(tb.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # Background image or color could go here
        bg_frame = tb.Frame(self)
        bg_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Logo/Icon giả lập bằng text
        tb.Label(bg_frame, text="🎓", font=("Segoe UI Emoji", 64)).pack(pady=(0, 10))
        
        tb.Label(bg_frame, text="HỆ THỐNG THI TRẮC NGHIỆM", font=("Segoe UI", 24, "bold"), bootstyle="primary").pack(pady=(0, 5))
        tb.Label(bg_frame, text="Đăng nhập để tiếp tục", font=("Segoe UI", 12), bootstyle="secondary").pack(pady=(0, 30))

        form = tb.Labelframe(bg_frame, text=" Thông tin đăng nhập ", padding=25, bootstyle="primary")
        form.pack(fill="x", pady=10)

        # Role
        tb.Label(form, text="Vai trò:", font=("Segoe UI", 10)).pack(anchor="w", pady=(5,0))
        self.role_var = tk.StringVar(value=ROLES[0])
        tb.Combobox(form, textvariable=self.role_var, values=ROLES, state="readonly", font=("Segoe UI", 10))\
            .pack(fill="x", pady=(0, 15))

        # User
        tb.Label(form, text="Tài khoản:", font=("Segoe UI", 10)).pack(anchor="w", pady=(5,0))
        self.user_var = tk.StringVar()
        self.user_entry = tb.Entry(form, textvariable=self.user_var, font=("Segoe UI", 10))
        self.user_entry.pack(fill="x", pady=(0, 15))

        # Pass
        tb.Label(form, text="Mật khẩu:", font=("Segoe UI", 10)).pack(anchor="w", pady=(5,0))
        self.pass_var = tk.StringVar()
        self.pass_entry = tb.Entry(form, textvariable=self.pass_var, show="*", font=("Segoe UI", 10))
        self.pass_entry.pack(fill="x", pady=(0, 15))

        # Buttons
        tb.Button(form, text="ĐĂNG NHẬP", command=self.do_login, bootstyle="primary", width=100).pack(pady=(10, 5))
        
        self.user_entry.focus_set()
        self.bind_all("<Return>", self._enter_login)

    def _enter_login(self, event):
        if self.winfo_ismapped():
            self.do_login()

    def clear(self):
        self.user_var.set("")
        self.pass_var.set("")
        self.user_entry.focus_set()

    def do_login(self):
        role = self.role_var.get().strip()
        username = self.user_var.get().strip()
        password = self.pass_var.get()

        if role not in ROLES or not username or not password:
            err("Vui lòng nhập đầy đủ thông tin.")
            return

        u = self.app.store.find_user(username)
        if not u:
            err("Người dùng không tồn tại.")
            return
        if u.password != password:
            err("Sai mật khẩu.")
            return

        u.role = ROLE_CANON.get(u.role.lower(), u.role)
        if u.role != role:
            err(f"Sai vai trò.\nTài khoản này là: {u.role}")
            return

        self.app.current_user = u
        # info(f"Xin chào {u.username} ({u.role}).")
        if u.role == "Admin":
            self.app.show_frame("AdminFrame")
        elif u.role == "Teacher":
            self.app.show_frame("TeacherFrame")
        else:
            self.app.show_frame("StudentFrame")


class AdminFrame(tb.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        Header(self, "Admin Dashboard", "Manage users and system access.").pack(fill="x")

        top = tb.Frame(self)
        top.pack(fill="x", pady=10)
        tb.Button(top, text="Reload Data", command=self.app.reload_data, bootstyle="info-outline").pack(side="right", padx=6)
        tb.Button(top, text="Logout", command=self.app.logout, bootstyle="secondary").pack(side="right")

        main = tb.Frame(self)
        main.pack(fill="both", expand=True, pady=10)

        # Left: Create
        left = tb.Labelframe(main, text=" Create New User ", padding=15, bootstyle="success")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Right: Manage
        right = tb.Labelframe(main, text=" User Management ", padding=15, bootstyle="info")
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        # --- Create User Form ---
        self.new_user = tk.StringVar()
        self.new_pass = tk.StringVar()
        self.new_role = tk.StringVar(value="Student")

        f = tb.Frame(left)
        f.pack(fill="x")
        tb.Label(f, text="Username:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(f, textvariable=self.new_user, width=28).grid(row=0, column=1, padx=6, pady=6, sticky="w")
        tb.Label(f, text="Password:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(f, textvariable=self.new_pass, width=28).grid(row=1, column=1, padx=6, pady=6, sticky="w")
        tb.Label(f, text="Role:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        tb.Combobox(f, textvariable=self.new_role, values=ROLES, state="readonly", width=26)\
            .grid(row=2, column=1, padx=6, pady=6, sticky="w")
        tb.Button(f, text="Create User", command=self.create_user, bootstyle="success", width=20).grid(row=3, column=1, pady=20, sticky="w")

        # --- Manage Actions (Reset/Delete) ---
        self.target_user = tk.StringVar()
        self.reset_pass = tk.StringVar()
        
        rr = tb.Frame(right)
        rr.pack(fill="x")
        
        # Row 1: Target Username selection
        tb.Label(rr, text="Target Username:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(rr, textvariable=self.target_user, width=25).grid(row=0, column=1, sticky="w", padx=6, pady=6)
        
        # Nút Xóa nằm ngay cạnh tên User
        tb.Button(rr, text="Delete User", command=self.delete_user_action, bootstyle="danger").grid(row=0, column=2, padx=10, sticky="w")

        # Row 2: Reset Password
        tb.Label(rr, text="New Password:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(rr, textvariable=self.reset_pass, width=25).grid(row=1, column=1, sticky="w", padx=6, pady=6)
        tb.Button(rr, text="Reset Password", command=self.reset_password, bootstyle="warning-outline").grid(row=1, column=2, padx=10, sticky="w")

        # Listbox for users
        tb.Label(right, text="User List (Click to select):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(15, 5))
        self.users_box = tk.Listbox(right, height=12, font=("Consolas", 10), selectbackground="#e1e1e1", selectforeground="black")
        self.users_box.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Bind sự kiện click vào listbox
        self.users_box.bind("<<ListboxSelect>>", self._on_user_select)

    def on_show(self):
        if not self.app.current_user or self.app.current_user.role != "Admin":
            err("You need Admin role.")
            self.app.logout()
            return
        self.refresh_users()

    def refresh_users(self):
        self.users_box.delete(0, tk.END)
        for u in self.app.store.list_users():
            self.users_box.insert(tk.END, f"{u.username:<15} | {u.role:<8} | {u.full_name}")

    def _on_user_select(self, event):
        # Khi chọn user trong list, tự điền tên vào ô Target User
        selection = self.users_box.curselection()
        if selection:
            data = self.users_box.get(selection[0])
            username = data.split("|")[0].strip()
            self.target_user.set(username)

    def create_user(self):
        username = self.new_user.get().strip()
        password = self.new_pass.get()
        role = self.new_role.get().strip()
        if not username or not password or role not in ROLES:
            err("Username, password, and role are needed.")
            return
        ok = self.app.store.add_user(User(username=username, password=password, role=role))
        if not ok:
            err("Username exists.")
            return
        info("User created.")
        self.new_user.set("")
        self.new_pass.set("")
        self.new_role.set("Student")
        self.refresh_users()

    def delete_user_action(self):
        username = self.target_user.get().strip()
        if not username:
            err("Please select or enter a username to delete.")
            return
        
        if username == self.app.current_user.username:
            err("You cannot delete yourself!")
            return

        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete user '{username}'?\nThis action cannot be undone."):
            return

        success = self.app.store.delete_user(username)
        if success:
            info(f"User '{username}' has been deleted.")
            self.target_user.set("")
            self.refresh_users()
        else:
            err("Cannot delete user (User not found or is restricted 'admin').")

    def reset_password(self):
        username = self.target_user.get().strip()
        new_password = self.reset_pass.get()
        if not username or not new_password:
            err("Username and new password are needed.")
            return
        ok = self.app.store.update_password(username, new_password)
        if not ok:
            err("User not found.")
            return
        info(f"Password for '{username}' updated.")
        self.reset_pass.set("")
        self.refresh_users()


# =================================================================================
# TEACHER FRAME - REDESIGNED (DASHBOARD STYLE)
# =================================================================================
class TeacherFrame(tb.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.selected_exam_id: Optional[str] = None
        
        # State variables
        self.editing_template_id: Optional[str] = None 
        self.editing_question_index: Optional[int] = None

        # --- KHAI BÁO BIẾN TRƯỚC (QUAN TRỌNG) ---
        # Variables for Builder
        self.tpl_title = tk.StringVar()
        self.q_text = tk.StringVar()
        self.opt_vars = [tk.StringVar() for _ in range(4)]
        self.correct_vars = [tk.BooleanVar(value=False) for _ in range(4)]
        self._temp_questions: List[Question] = []
        
        # Biến cho trang Manager
        self.pub_start = tk.StringVar(value=time.strftime("%Y-%m-%d 08:00", time.localtime()))
        self.pub_end = tk.StringVar(value=time.strftime("%Y-%m-%d 23:00", time.localtime()))
        self.pub_duration = tk.IntVar(value=30)
        self.pub_use_pass = tk.BooleanVar(value=False)
        self.pub_pass = tk.StringVar()
        self.pub_allow_review = tk.BooleanVar(value=False)
        self.pub_attempt_limit = tk.IntVar(value=1)

        # --- LAYOUT CHÍNH: Sidebar (Trái) + Content (Phải) ---
        
        # 1. Sidebar Panel
        self.sidebar = tb.Frame(self, bootstyle="primary", width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False) # Giữ cố định chiều rộng

        # Logo / Info User Sidebar
        self.lbl_user = tb.Label(self.sidebar, text="Giáo viên", font=("Segoe UI", 12, "bold"), 
                                 bootstyle="inverse-primary", justify="center")
        self.lbl_user.pack(pady=(30, 5), padx=10)
        
        tb.Separator(self.sidebar, bootstyle="light").pack(fill="x", padx=20, pady=20)

        # Menu Buttons
        self._create_sidebar_btn("🏠  Màn hình chính", lambda: self.show_tab("Dashboard"))
        self._create_sidebar_btn("📝  Soạn câu hỏi", lambda: self.show_tab("Builder"))
        self._create_sidebar_btn("📂  Quản lý đề thi", lambda: self.show_tab("Manager"))
        self._create_sidebar_btn("📊  Kết quả thi", lambda: self.show_tab("Results"))
        
        tb.Frame(self.sidebar, height=50, bootstyle="primary").pack(fill="y", expand=True) # Spacer
        
        tb.Button(self.sidebar, text="Đăng xuất", command=self.app.logout, bootstyle="light-outline", width=15).pack(pady=20)

        # 2. Main Content Area
        self.content_area = tb.Frame(self, bootstyle="bg")
        self.content_area.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # Notebook
        self.notebook = ttk.Notebook(self.content_area)
        self.notebook.pack(fill="both", expand=True)
        
        # --- CÁC TRANG CON (TABS) ---
        # Gọi hàm init
        self.tab_dashboard = self._init_tab_dashboard()
        self.tab_builder = self._init_tab_builder()
        self.tab_manager = self._init_tab_manager()
        self.tab_results = self._init_tab_results()

        self.notebook.add(self.tab_dashboard, text="Dashboard")
        self.notebook.add(self.tab_builder, text="Builder")
        self.notebook.add(self.tab_manager, text="Manager")
        self.notebook.add(self.tab_results, text="Results")
        
        # Ẩn thanh tab mặc định
        style = ttk.Style()
        style.layout('Hidden.TNotebook.Tab', []) 
        self.notebook.config(style='Hidden.TNotebook')

    def _create_sidebar_btn(self, text, command):
        btn = tb.Button(
            self.sidebar, 
            text=text, 
            command=command, 
            bootstyle="primary", 
            cursor="hand2"
        )
        btn.pack(fill="x", pady=5, padx=10)
        return btn

    def show_tab(self, name):
        tabs = {"Dashboard": 0, "Builder": 1, "Manager": 2, "Results": 3}
        self.notebook.select(tabs[name])
        
        if name == "Manager":
            self.refresh_templates()
            self.refresh_exams()
        if name == "Results":
            self.refresh_exams_in_results()

    def on_show(self):
        if not self.app.current_user or self.app.current_user.role != "Teacher":
            err("Cần quyền Giáo viên.")
            self.app.logout()
            return
        self.lbl_user.config(text=f"GV. {self.app.current_user.full_name}\n({self.app.current_user.username})")
        self.show_tab("Dashboard")
        self.clear_builder()

    # -------------------------------------------------------------------------
    # TAB 1: DASHBOARD
    # -------------------------------------------------------------------------
    def _init_tab_dashboard(self):
        frame = tb.Frame(self.notebook, padding=20)
        
        tb.Label(frame, text="Màn hình chính", font=("Segoe UI", 20, "bold"), bootstyle="primary").pack(anchor="w", pady=(0, 20))

        grid = tb.Frame(frame)
        grid.pack(fill="both", expand=True)

        def create_card(parent, title, icon, color, cmd, row, col):
            card = tb.Frame(parent, bootstyle="light", padding=2)
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            
            btn = tb.Button(card, bootstyle="light", command=cmd)
            btn.pack(fill="both", expand=True)
            
            lbl_icon = tb.Label(btn, text=icon, font=("Segoe UI Emoji", 40), foreground=color, background="#f8f9fa")
            lbl_icon.pack(pady=(30, 10))
            
            lbl_title = tb.Label(btn, text=title, font=("Segoe UI", 12, "bold"), foreground="#333", background="#f8f9fa")
            lbl_title.pack(pady=(0, 30))
            
            for w in [lbl_icon, lbl_title]:
                w.bind("<Button-1>", lambda e: cmd())
            
            return card

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)

        create_card(grid, "Ngân hàng câu hỏi", "📝", "#0d6efd", lambda: self.show_tab("Builder"), 0, 0)
        create_card(grid, "Quản lý đề thi", "📂", "#198754", lambda: self.show_tab("Manager"), 0, 1)
        create_card(grid, "Kết quả & Điểm", "📊", "#ffc107", lambda: self.show_tab("Results"), 0, 2)
        
        create_card(grid, "Hồ sơ cá nhân", "👤", "#0dcaf0", lambda: info("Tính năng đang phát triển"), 1, 0)
        create_card(grid, "Thống kê lớp", "📈", "#6610f2", lambda: info("Tính năng đang phát triển"), 1, 1)
        create_card(grid, "Trợ giúp", "💡", "#d63384", lambda: info("Liên hệ Admin để được hỗ trợ"), 1, 2)

        return frame

    # -------------------------------------------------------------------------
    # TAB 2: BUILDER
    # -------------------------------------------------------------------------
    def _init_tab_builder(self):
        frame = tb.Frame(self.notebook, padding=10)
        
        h = tb.Frame(frame)
        h.pack(fill="x", pady=(0, 10))
        tb.Label(h, text="Soạn Ngân Hàng Câu Hỏi", font=("Segoe UI", 18, "bold"), bootstyle="primary").pack(side="left")
        tb.Button(h, text="Làm mới form", command=self.clear_builder, bootstyle="secondary-outline").pack(side="right")

        body = tb.Frame(frame)
        body.pack(fill="both", expand=True)
        
        # --- Form (Left) ---
        left = tb.Labelframe(body, text=" Nhập nội dung ", padding=15, bootstyle="success")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tb.Label(left, text="Tiêu đề Bộ câu hỏi (Template):", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tb.Entry(left, textvariable=self.tpl_title).pack(fill="x", pady=(5, 15))
        
        tb.Separator(left).pack(fill="x", pady=5)
        
        tb.Label(left, text="Nội dung câu hỏi:", font=("Segoe UI", 10)).pack(anchor="w")
        tb.Entry(left, textvariable=self.q_text).pack(fill="x", pady=(5, 10))
        
        opts_frame = tb.Frame(left)
        opts_frame.pack(fill="x")
        
        for i in range(4):
            row = tb.Frame(opts_frame)
            row.pack(fill="x", pady=2)
            tb.Label(row, text=f"Đáp án {i+1}:", width=10).pack(side="left")
            tb.Entry(row, textvariable=self.opt_vars[i]).pack(side="left", fill="x", expand=True, padx=5)
            tb.Checkbutton(row, text="Đúng", variable=self.correct_vars[i], bootstyle="round-toggle").pack(side="right")

        btn_row = tb.Frame(left, padding=(0, 15, 0, 0))
        btn_row.pack(fill="x")
        self.btn_add_q = tb.Button(btn_row, text="Thêm câu hỏi", command=self.add_or_update_question, bootstyle="success")
        self.btn_add_q.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # --- List (Right) ---
        right = tb.Labelframe(body, text=" Danh sách câu hỏi tạm ", padding=15, bootstyle="info")
        right.pack(side="right", fill="both", expand=True)
        
        self.builder_tree = ttk.Treeview(right, columns=("no", "content", "ans"), show="headings", height=10)
        self.builder_tree.heading("no", text="#")
        self.builder_tree.heading("content", text="Nội dung")
        self.builder_tree.heading("ans", text="Đáp án đúng")
        self.builder_tree.column("no", width=40, anchor="center")
        self.builder_tree.column("content", width=300)
        self.builder_tree.column("ans", width=80, anchor="center")
        self.builder_tree.pack(fill="both", expand=True)
        
        self.builder_tree.bind("<Double-Button-1>", lambda e: self.load_question_for_editing())

        actions = tb.Frame(right, padding=(0, 10, 0, 0))
        actions.pack(fill="x")
        tb.Button(actions, text="Xóa câu chọn", command=self.remove_question_from_builder, bootstyle="danger-outline").pack(side="left")
        self.btn_save = tb.Button(actions, text="LƯU BỘ CÂU HỎI (TEMPLATE)", command=self.save_template, bootstyle="primary")
        self.btn_save.pack(side="right")

        return frame

    # -------------------------------------------------------------------------
    # TAB 3: MANAGER
    # -------------------------------------------------------------------------
    def _init_tab_manager(self):
        frame = tb.Frame(self.notebook, padding=10)
        
        tb.Label(frame, text="Quản Lý Đề Thi & Xuất Bản", font=("Segoe UI", 18, "bold"), bootstyle="primary").pack(anchor="w", pady=(0, 10))

        # ĐÃ SỬA LỖI Ở DÒNG NÀY: Panedwindow (chữ w thường)
        paned = tb.Panedwindow(frame, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # --- LEFT: Templates ---
        f_tpl = tb.Labelframe(paned, text=" 1. Ngân hàng đề (Templates) ", padding=10)
        paned.add(f_tpl, weight=1)
        
        self.tree_tpl = ttk.Treeview(f_tpl, columns=("id", "title", "qs"), show="headings")
        self.tree_tpl.heading("id", text="ID")
        self.tree_tpl.heading("title", text="Tiêu đề")
        self.tree_tpl.heading("qs", text="Số câu")
        self.tree_tpl.column("id", width=0, stretch=False) 
        self.tree_tpl.pack(fill="both", expand=True, pady=(0, 10))
        
        btns_tpl = tb.Frame(f_tpl)
        btns_tpl.pack(fill="x")
        tb.Button(btns_tpl, text="Sửa", command=self.edit_selected_template, bootstyle="info-outline").pack(side="left", padx=2)
        tb.Button(btns_tpl, text="Xóa", command=self.delete_selected_template, bootstyle="danger-outline").pack(side="left", padx=2)
        tb.Button(btns_tpl, text="Xuất Word", command=self.export_selected_template_word, bootstyle="secondary-outline").pack(side="left", padx=2)
        
        # --- MIDDLE: Publish Config ---
        f_pub = tb.Labelframe(paned, text=" 2. Cấu hình thi ", padding=10, bootstyle="warning")
        paned.add(f_pub, weight=1)
        
        tb.Label(f_pub, text="Thời gian mở:").pack(anchor="w")
        tb.Entry(f_pub, textvariable=self.pub_start).pack(fill="x", pady=2)
        tb.Label(f_pub, text="Thời gian đóng:").pack(anchor="w")
        tb.Entry(f_pub, textvariable=self.pub_end).pack(fill="x", pady=2)
        
        row1 = tb.Frame(f_pub); row1.pack(fill="x", pady=5)
        tb.Label(row1, text="Phút:").pack(side="left")
        tb.Spinbox(row1, from_=1, to=180, textvariable=self.pub_duration, width=5).pack(side="left", padx=5)
        
        tb.Label(row1, text="Lượt thi:").pack(side="left", padx=(10,0))
        tb.Spinbox(row1, from_=0, to=10, textvariable=self.pub_attempt_limit, width=5).pack(side="left", padx=5)
        
        tb.Checkbutton(f_pub, text="Đặt mật khẩu", variable=self.pub_use_pass, command=self._toggle_pub_pass).pack(anchor="w", pady=(10,0))
        self.pub_pass_entry = tb.Entry(f_pub, textvariable=self.pub_pass, state="disabled")
        self.pub_pass_entry.pack(fill="x")
        
        tb.Checkbutton(f_pub, text="Cho xem lại bài", variable=self.pub_allow_review).pack(anchor="w", pady=5)
        
        tb.Button(f_pub, text=">>> XUẤT BẢN KỲ THI >>>", command=self.publish_exam, bootstyle="warning").pack(fill="x", pady=20)

        # --- RIGHT: Exams ---
        f_exam = tb.Labelframe(paned, text=" 3. Đề đang mở (Exams) ", padding=10)
        paned.add(f_exam, weight=1)
        
        self.tree_exam = ttk.Treeview(f_exam, columns=("id", "title", "code", "status"), show="headings")
        self.tree_exam.heading("id", text="ID")
        self.tree_exam.heading("title", text="Tên kỳ thi")
        self.tree_exam.heading("code", text="Mã Code")
        self.tree_exam.heading("status", text="Trạng thái")
        self.tree_exam.column("id", width=0, stretch=False)
        self.tree_exam.column("code", width=80, anchor="center")
        self.tree_exam.column("status", width=80, anchor="center")
        self.tree_exam.pack(fill="both", expand=True, pady=(0, 10))
        
        btns_ex = tb.Frame(f_exam)
        btns_ex.pack(fill="x")
        tb.Button(btns_ex, text="Hủy/Xóa", command=self.delete_selected_exam, bootstyle="danger").pack(side="right")
        tb.Button(btns_ex, text="Reset Lượt thi", command=self.delete_attempts_for_selected_exam, bootstyle="warning-outline").pack(side="right", padx=5)

        return frame

    # -------------------------------------------------------------------------
    # TAB 4: RESULTS
    # -------------------------------------------------------------------------
    def _init_tab_results(self):
        frame = tb.Frame(self.notebook, padding=10)
        tb.Label(frame, text="Kết Quả & Bảng Điểm", font=("Segoe UI", 18, "bold"), bootstyle="primary").pack(anchor="w", pady=(0, 10))

        # Top: Chọn kỳ thi
        top = tb.Frame(frame)
        top.pack(fill="x", pady=(0, 10))
        tb.Label(top, text="Chọn kỳ thi để xem điểm:").pack(side="left", padx=(0, 10))
        
        self.res_exam_var = tk.StringVar()
        self.res_exam_cb = tb.Combobox(top, textvariable=self.res_exam_var, state="readonly", width=50)
        self.res_exam_cb.pack(side="left")
        self.res_exam_cb.bind("<<ComboboxSelected>>", self._on_result_exam_select)
        
        tb.Button(top, text="Xuất Excel", command=self.export_selected_exam_results_excel, bootstyle="success").pack(side="right")

        # Table
        self.tree_res = ttk.Treeview(frame, columns=("aid", "std_name", "sid", "score", "time"), show="headings")
        self.tree_res.heading("aid", text="ID")
        self.tree_res.heading("std_name", text="Họ tên")
        self.tree_res.heading("sid", text="MSSV")
        self.tree_res.heading("score", text="Điểm số")
        self.tree_res.heading("time", text="Thời gian làm")
        
        self.tree_res.column("aid", width=0, stretch=False)
        self.tree_res.column("score", anchor="center")
        self.tree_res.column("time", anchor="center")
        
        self.tree_res.pack(fill="both", expand=True)
        
        # Scrollbar
        sb = tb.Scrollbar(frame, orient="vertical", command=self.tree_res.yview)
        sb.place(relx=1, rely=0, relheight=1, anchor="ne")
        self.tree_res.configure(yscrollcommand=sb.set)
        
        self.tree_res.bind("<Double-Button-1>", lambda e: self.view_attempt_details_from_results())
        
        tb.Label(frame, text="* Nhấp đúp vào dòng để xem chi tiết bài làm", font=("Segoe UI", 9, "italic"), bootstyle="secondary").pack(anchor="w")
        
        return frame

    # =========================================================================
    # LOGIC FUNCTIONS
    # =========================================================================

    def _toggle_pub_pass(self):
        if self.pub_use_pass.get():
            self.pub_pass_entry.config(state="normal")
        else:
            self.pub_pass_entry.config(state="disabled")
            self.pub_pass.set("")

    # --- Builder Logic ---
    def refresh_builder_list(self):
        for item in self.builder_tree.get_children():
            self.builder_tree.delete(item)
        for i, q in enumerate(self._temp_questions):
            ans_str = ",".join(str(x+1) for x in q.correct_indices)
            self.builder_tree.insert("", "end", iid=str(i), values=(i+1, q.text, ans_str))

    def add_or_update_question(self):
        text = self.q_text.get().strip()
        options = [v.get().strip() for v in self.opt_vars]
        correct_indices = [i for i, b in enumerate(self.correct_vars) if b.get()]
        
        if not text: return err("Thiếu nội dung câu hỏi.")
        if any(not o for o in options): return err("Cần nhập đủ 4 đáp án.")
        if len(correct_indices) == 0: return err("Chọn ít nhất 1 đáp án đúng.")
        
        q = Question(text=text, options=options, correct_indices=correct_indices)
        
        if self.editing_question_index is not None:
            if 0 <= self.editing_question_index < len(self._temp_questions):
                self._temp_questions[self.editing_question_index] = q
            else:
                self._temp_questions.append(q)
        else:
            self._temp_questions.append(q)

        self.refresh_builder_list()
        
        self.q_text.set("")
        for v in self.opt_vars: v.set("")
        for b in self.correct_vars: b.set(False)
        self.editing_question_index = None
        self.btn_add_q.config(text="Thêm câu hỏi", bootstyle="success")

    def load_question_for_editing(self):
        sel = self.builder_tree.selection()
        if not sel: return
        idx = int(sel[0]) 
        
        if idx >= len(self._temp_questions): return
        q = self._temp_questions[idx]
        
        self.q_text.set(q.text)
        for i, opt in enumerate(q.options):
            if i < 4: self.opt_vars[i].set(opt)
        for i in range(4):
            self.correct_vars[i].set(i in q.correct_indices)
            
        self.editing_question_index = idx
        self.btn_add_q.config(text=f"Cập nhật câu #{idx+1}", bootstyle="info")

    def remove_question_from_builder(self):
        sel = self.builder_tree.selection()
        if not sel: return
        idx = int(sel[0])
        self._temp_questions.pop(idx)
        self.refresh_builder_list()
        self.clear_builder_form_only()

    def clear_builder_form_only(self):
        self.editing_question_index = None
        self.btn_add_q.config(text="Thêm câu hỏi", bootstyle="success")
        self.q_text.set("")
        for v in self.opt_vars: v.set("")
        for b in self.correct_vars: b.set(False)

    def clear_builder(self):
        self.editing_template_id = None
        self.tpl_title.set("")
        self._temp_questions.clear()
        self.refresh_builder_list()
        self.clear_builder_form_only()
        self.btn_save.config(text="LƯU BỘ CÂU HỎI", bootstyle="primary")

    def save_template(self):
        title = self.tpl_title.get().strip()
        if not title: return err("Thiếu tiêu đề bộ câu hỏi.")
        if len(self._temp_questions) == 0: return err("Cần ít nhất 1 câu hỏi.")
        
        if self.editing_template_id:
            if not messagebox.askyesno("Xác nhận", "Ghi đè bộ câu hỏi này?"): return
            t = Template(
                template_id=self.editing_template_id,
                title=title,
                created_by=self.app.current_user.username,
                questions=list(self._temp_questions)
            )
            self.app.store.update_template(t)
            info("Đã cập nhật bộ câu hỏi.")
        else:
            t = Template(
                template_id=self.app.store.new_template_id(),
                title=title,
                created_by=self.app.current_user.username,
                questions=list(self._temp_questions)
            )
            self.app.store.add_template(t)
            info("Đã lưu bộ câu hỏi mới.")

        self.clear_builder()
        self.refresh_templates()

    # --- Manager Logic ---
    def refresh_templates(self):
        for item in self.tree_tpl.get_children():
            self.tree_tpl.delete(item)
            
        teacher = self.app.current_user.username
        for t in self.app.store.list_templates_by_teacher(teacher):
            self.tree_tpl.insert("", "end", iid=t.template_id, values=(t.template_id, t.title, len(t.questions)))

    def refresh_exams(self):
        for item in self.tree_exam.get_children():
            self.tree_exam.delete(item)
            
        teacher = self.app.current_user.username
        now = int(time.time())
        for e in self.app.store.list_exams_by_teacher(teacher):
            status = "ĐANG MỞ" if (e.start_ts <= now <= e.end_ts) else ("CHỜ" if now < e.start_ts else "ĐÓNG")
            self.tree_exam.insert("", "end", iid=e.exam_id, values=(e.exam_id, e.title, e.access_code, status))

    def edit_selected_template(self):
        sel = self.tree_tpl.selection()
        if not sel: return err("Chọn một template.")
        tid = sel[0]
        
        t = self.app.store.get_template(tid)
        if not t: return

        self.editing_template_id = t.template_id
        self.tpl_title.set(t.title)
        self._temp_questions = list(t.questions) 
        self.refresh_builder_list()
        self.btn_save.config(text=f"Cập nhật ({t.template_id})", bootstyle="info")
        
        self.show_tab("Builder")
        info(f"Đã tải '{t.title}'.")

    def delete_selected_template(self):
        sel = self.tree_tpl.selection()
        if not sel: return err("Chọn template.")
        tid = sel[0]
        
        if self.app.store.has_exam_from_template(tid):
            if not messagebox.askyesno("Cảnh báo", "Template này đang được dùng cho Kỳ thi.\nXóa sẽ mất dữ liệu liên quan. Tiếp tục?"): return
        
        if self.app.store.delete_template(tid):
            info("Đã xóa.")
            self.refresh_templates()

    def export_selected_template_word(self):
        sel = self.tree_tpl.selection()
        if not sel: return err("Chọn template.")
        tid = sel[0]
        tpl = self.app.store.get_template(tid)
        filepath = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word", "*.docx")])
        if filepath:
            utils.export_template_to_word(tpl, filepath)
            info("Đã xuất file Word.")

    def preview_selected_template(self):
        self.edit_selected_template()

    def publish_exam(self):
        sel = self.tree_tpl.selection()
        if not sel: return err("Vui lòng chọn Template ở bảng bên trái.")
        tid = sel[0]
        tpl = self.app.store.get_template(tid)
        
        start_ts = utils.parse_dt(self.pub_start.get())
        end_ts = utils.parse_dt(self.pub_end.get())
        if not start_ts or not end_ts: return err("Ngày giờ không hợp lệ (YYYY-MM-DD HH:MM)")
        if end_ts <= start_ts: return err("Thời gian đóng phải sau thời gian mở.")
        
        dur_min = int(self.pub_duration.get())
        code = self.app.store.new_unique_code(8)
        
        e = Exam(
            exam_id=self.app.store.new_exam_id(),
            template_id=tpl.template_id,
            title=tpl.title,
            created_by=self.app.current_user.username,
            access_code=code,
            password=self.pub_pass.get() if self.pub_use_pass.get() else "",
            duration_seconds=dur_min * 60,
            allow_review=bool(self.pub_allow_review.get()),
            attempt_limit=int(self.pub_attempt_limit.get()),
            start_ts=int(start_ts),
            end_ts=int(end_ts),
            questions=list(tpl.questions)
        )
        self.app.store.add_exam(e)
        info(f"Đã xuất bản kỳ thi!\nMÃ CODE: {code}")
        self.refresh_exams()

    def delete_selected_exam(self):
        sel = self.tree_exam.selection()
        if not sel: return
        eid = sel[0]
        if messagebox.askyesno("Xóa", "Xóa kỳ thi này?"):
            self.app.store.delete_exam(eid)
            self.refresh_exams()

    def delete_attempts_for_selected_exam(self):
        sel = self.tree_exam.selection()
        if not sel: return
        eid = sel[0]
        if messagebox.askyesno("Reset", "Xóa hết bài làm của học sinh cho đề này?"):
            n = self.app.store.delete_attempts_for_exam(eid)
            info(f"Đã xóa {n} lượt thi.")

    # --- Results Logic ---
    def refresh_exams_in_results(self):
        teacher = self.app.current_user.username
        exams = self.app.store.list_exams_by_teacher(teacher)
        values = [f"{e.exam_id} | {e.title}" for e in exams]
        self.res_exam_cb['values'] = values
        if values:
            self.res_exam_cb.current(0)
            self._on_result_exam_select(None)

    def _on_result_exam_select(self, event):
        val = self.res_exam_cb.get()
        if not val: return
        eid = val.split("|")[0].strip()
        
        for item in self.tree_res.get_children():
            self.tree_res.delete(item)
            
        attempts = self.app.store.list_attempts_for_exam(eid)
        for a in attempts:
            score10 = (a.score / max(1, a.total)) * 10.0
            took = f"{a.time_taken_seconds // 60}p {a.time_taken_seconds % 60}s"
            self.tree_res.insert("", "end", iid=a.attempt_id, 
                                 values=(a.attempt_id, a.full_name, a.student_id, f"{score10:.2f}/10", took))

    def view_attempt_details_from_results(self):
        sel = self.tree_res.selection()
        if not sel: return
        aid = sel[0] 
        
        val = self.res_exam_cb.get()
        eid = val.split("|")[0].strip()
        attempts = self.app.store.list_attempts_for_exam(eid)
        
        target = next((x for x in attempts if x.attempt_id == aid), None)
        if target:
            self.app.frames["TeacherAttemptFrame"].load_attempt(target, back_to="TeacherFrame")
            self.app.show_frame("TeacherAttemptFrame")

    def export_selected_exam_results_excel(self):
        val = self.res_exam_cb.get()
        if not val: return err("Chưa chọn kỳ thi.")
        eid = val.split("|")[0].strip()
        
        e = self.app.store.get_exam(eid)
        attempts = self.app.store.list_attempts_for_exam(eid)
        
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if filepath:
            utils.export_exam_results_to_excel(e, attempts, filepath)
            info("Đã xuất Excel.")
    
    def preview_selected_exam(self):
        sel = self.tree_exam.selection()
        if not sel: return err("Chọn đề thi.")
        eid = sel[0]
        self.app.frames["ExamPreviewFrame"].load_exam(eid, back_to="TeacherFrame")
        self.app.show_frame("ExamPreviewFrame")
class StudentFrame(tb.Frame):
    # (Dùng lại code StudentFrame cũ của bạn - không cần sửa)
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.full_name = tk.StringVar()
        self.dob = tk.StringVar()
        self.sid = tk.StringVar()
        self._build_ui()
        
    def _build_ui(self):
        Header(self, "Cổng Thông Tin Học Sinh", "Nhập mã đề thi để làm bài.").pack(fill="x")
        top = tb.Frame(self); top.pack(fill="x", pady=5)
        tb.Button(top, text="Tải lại", command=self.app.reload_data, bootstyle="info-outline").pack(side="right", padx=6)
        tb.Button(top, text="Đăng xuất", command=self.app.logout, bootstyle="secondary").pack(side="right")
        main = tb.Frame(self); main.pack(fill="both", expand=True, pady=10)
        left = tb.Labelframe(main, text=" Vào thi ", padding=15, bootstyle="success")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = tb.Labelframe(main, text=" Hồ sơ & Lịch sử ", padding=15, bootstyle="info")
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        lf = tb.Frame(left); lf.pack(fill="x", pady=20)
        tb.Label(lf, text="MÃ ĐỀ THI (CODE):", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.code_var = tk.StringVar()
        tb.Entry(lf, textvariable=self.code_var, width=25, font=("Consolas", 14)).pack(fill="x", pady=10)
        tb.Button(lf, text="VÀO THI NGAY", command=self.open_by_code, bootstyle="success", width=100).pack(pady=10)

        pf = tb.Frame(right); pf.pack(fill="x")
        tb.Label(pf, text="Họ tên:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(pf, textvariable=self.full_name, width=30).grid(row=0, column=1, sticky="w", padx=6, pady=6)
        tb.Label(pf, text="Ngày sinh:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(pf, textvariable=self.dob, width=30).grid(row=1, column=1, sticky="w", padx=6, pady=6)
        tb.Label(pf, text="MSSV:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(pf, textvariable=self.sid, width=30).grid(row=2, column=1, sticky="w", padx=6, pady=6)
        tb.Button(pf, text="Cập nhật hồ sơ", command=self.update_profile, bootstyle="primary-outline").grid(row=3, column=1, sticky="e", pady=10)

        tb.Separator(right).pack(fill="x", padx=10, pady=6)
        tb.Label(right, text="Lịch sử thi:", bootstyle="inverse-light").pack(anchor="w", padx=10)
        self.attempt_list = tk.Listbox(right, height=10, font=("Segoe UI", 9))
        self.attempt_list.pack(fill="both", expand=True, padx=10, pady=(6, 10))
        tb.Button(right, text="Xem lại bài đã chọn", command=self.review_selected, bootstyle="info").pack(pady=(0, 10))

    def on_show(self):
        if not self.app.current_user or self.app.current_user.role != "Student":
            err("Cần quyền Học sinh.")
            self.app.logout()
            return
        u = self.app.store.find_user(self.app.current_user.username)
        if u: self.app.current_user = u
        self.full_name.set(self.app.current_user.full_name)
        self.dob.set(self.app.current_user.dob)
        self.sid.set(self.app.current_user.student_id)
        self.refresh_attempts()

    def update_profile(self):
        self.app.store.update_profile(
            self.app.current_user.username,
            self.full_name.get().strip(),
            self.dob.get().strip(),
            self.sid.get().strip()
        )
        info("Đã cập nhật hồ sơ.")
        self.refresh_attempts()

    def refresh_attempts(self):
        self.attempt_list.delete(0, tk.END)
        attempts = self.app.store.list_attempts_for_user(self.app.current_user.username)
        if not attempts:
            self.attempt_list.insert(tk.END, "Chưa có bài thi nào.")
            return
        for a in attempts:
            score10 = (a.score / max(1, a.total)) * 10.0
            self.attempt_list.insert(tk.END, f"{utils.fmt_dt_full(a.submitted_at)} | {a.title} | {score10:.2f}/10")

    def open_by_code(self):
        code = self.code_var.get().strip().upper()
        if not code: return err("Vui lòng nhập mã đề.")
        exam = self.app.store.get_exam_by_code(code)
        if not exam: return err("Không tìm thấy đề thi.")

        now = int(time.time())
        if now < exam.start_ts: return err(f"Đề thi chưa mở.\nBắt đầu: {utils.fmt_dt(exam.start_ts)}")
        if now > exam.end_ts: return err(f"Đề thi đã đóng.\nKết thúc: {utils.fmt_dt(exam.end_ts)}")
        
        if exam.attempt_limit > 0:
            used = self.app.store.count_attempts_for_user_exam(self.app.current_user.username, exam.exam_id)
            if used >= exam.attempt_limit: return err("Bạn đã hết lượt làm bài.")

        if exam.password:
            pw = simpledialog.askstring("Mật khẩu", "Đề thi yêu cầu mật khẩu:", show="*")
            if pw != exam.password: return err("Sai mật khẩu.")

        self.app.frames["ExamTakeFrame"].load_exam(exam)
        self.app.show_frame("ExamTakeFrame")

    def review_selected(self):
        sel = self.attempt_list.curselection()
        if not sel: return err("Chọn một bài thi để xem lại.")
        attempts = self.app.store.list_attempts_for_user(self.app.current_user.username)
        attempt = attempts[sel[0]]
        exam = self.app.store.get_exam(attempt.exam_id)
        if not exam: return err("Dữ liệu đề thi gốc đã bị xóa.")
        if not exam.allow_review: return err("Giáo viên không cho phép xem lại bài.")
        self.app.frames["ReviewFrame"].load_review(exam, attempt, back_to="StudentFrame")
        self.app.show_frame("ReviewFrame")


class ExamTakeFrame(tb.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.exam: Optional[Exam] = None
        self.index = 0
        self.answers: List[Set[int]] = []
        self.marked_questions: Set[int] = set()
        self.started_at: float = 0.0
        self.end_time: float = 0.0
        self._timer_job = None
        self._auto_submitted = False

        # Top bar
        top = tb.Frame(self, bootstyle="light")
        top.pack(fill="x", side="top", pady=(0, 10))
        self.timer_label = tb.Label(top, text="Thời gian còn: --:--", font=("Segoe UI", 16, "bold"), bootstyle="danger")
        self.timer_label.pack(side="left", padx=20, pady=10)
        tb.Button(top, text="THOÁT", command=self.back, bootstyle="secondary").pack(side="right", padx=20)

        # Main Container
        container = tb.Frame(self)
        container.pack(fill="both", expand=True)

        # Sidebar (Right)
        self.sidebar = tb.Labelframe(container, text=" Bản đồ câu hỏi ", padding=10)
        self.sidebar.pack(side="right", fill="y", padx=10, pady=5)
        self.grid_frame = tb.Frame(self.sidebar)
        self.grid_frame.pack(fill="both", expand=True)
        
        legend = tb.Frame(self.sidebar)
        legend.pack(fill="x", pady=20)
        tb.Label(legend, text="■ Đang chọn", bootstyle="primary").pack(anchor="w")
        tb.Label(legend, text="■ Đã trả lời", bootstyle="success").pack(anchor="w")
        tb.Label(legend, text="■ Đánh dấu", bootstyle="warning").pack(anchor="w")
        tb.Label(legend, text="□ Chưa làm", bootstyle="secondary").pack(anchor="w")

        # Content (Left)
        self.main_area = tb.Frame(container, padding=20)
        self.main_area.pack(side="left", fill="both", expand=True)
        self.title_label = tb.Label(self.main_area, text="", font=("Segoe UI", 18, "bold"), bootstyle="primary")
        self.title_label.pack(anchor="w", pady=(0, 15))
        
        self.q_label = tb.Label(self.main_area, text="", wraplength=700, justify="left", font=("Segoe UI", 14))
        self.q_label.pack(anchor="w", pady=(0, 20))

        self.opt_vars = [tk.IntVar(value=0) for _ in range(4)]
        self.check_buttons = []
        for i in range(4):
            cb = tb.Checkbutton(self.main_area, text="", variable=self.opt_vars[i], bootstyle="round-toggle")
            cb.pack(anchor="w", pady=5)
            self.check_buttons.append(cb)

        # Bottom Nav
        nav = tb.Frame(self.main_area) 
        nav.pack(fill="x", side="bottom", pady=20)
        self.progress_label = tb.Label(nav, text="", font=("Segoe UI", 10, "italic"))
        self.progress_label.pack(side="left")

        tb.Button(nav, text="NỘP BÀI", command=self.submit, bootstyle="success").pack(side="right", padx=6)
        tb.Button(nav, text="Tiếp >", command=self.next_q, bootstyle="primary-outline").pack(side="right", padx=6)
        tb.Button(nav, text="< Trước", command=self.prev_q, bootstyle="secondary-outline").pack(side="right", padx=6)
        self.btn_mark = tb.Button(nav, text="Đánh dấu xem lại", command=self.toggle_mark, bootstyle="warning-outline")
        self.btn_mark.pack(side="right", padx=20)
        self.nav_buttons = []

    def load_exam(self, exam: Exam):
        self.stop_timer()
        self.exam = exam
        self.index = 0
        self.answers = [set() for _ in range(len(exam.questions))]
        self.marked_questions = set()
        self.started_at = time.time()
        self.end_time = self.started_at + exam.duration_seconds
        self._auto_submitted = False
        self.create_nav_grid()
        self.render()
        self._tick()

    def create_nav_grid(self):
        for w in self.grid_frame.winfo_children(): w.destroy()
        self.nav_buttons = []
        if not self.exam: return
        cols = 5
        for i in range(len(self.exam.questions)):
            btn = tb.Button(self.grid_frame, text=str(i + 1), width=3, 
                            command=lambda idx=i: self.jump_to(idx),
                            bootstyle="secondary-outline")
            btn.grid(row=i//cols, column=i%cols, padx=3, pady=3)
            self.nav_buttons.append(btn)

    def jump_to(self, target):
        self._save_current()
        self.index = target
        self.render()

    def toggle_mark(self):
        if self.index in self.marked_questions: self.marked_questions.remove(self.index)
        else: self.marked_questions.add(self.index)
        self.render()

    def stop_timer(self):
        if self._timer_job:
            self.after_cancel(self._timer_job)
            self._timer_job = None

    def _tick(self):
        if not self.exam: return
        left = int(self.end_time - time.time())
        mm, ss = max(0, left) // 60, max(0, left) % 60
        self.timer_label.config(text=f"Thời gian còn: {mm:02d}:{ss:02d}")
        if left < 300: 
            self.timer_label.configure(bootstyle="danger")
        else:
            self.timer_label.configure(bootstyle="success")

        if left <= 0 and not self._auto_submitted:
            self._auto_submitted = True
            self._save_current()
            self._submit_internal(auto=True)
            return
        self._timer_job = self.after(1000, self._tick)

    def _current_selection(self) -> Set[int]:
        return {i for i in range(4) if int(self.opt_vars[i].get()) == 1}

    def _save_current(self):
        if self.exam: self.answers[self.index] = self._current_selection()

    def render(self):
        if not self.exam: return
        q = self.exam.questions[self.index]
        self.title_label.config(text=f"{self.exam.title}")
        self.q_label.config(text=f"Câu {self.index+1}: {q.text}")
        
        for i in range(4): self.check_buttons[i].config(text=q.options[i])
        saved = self.answers[self.index]
        for i in range(4): self.opt_vars[i].set(1 if i in saved else 0)
            
        self.progress_label.config(text=f"Tiến độ: {self.index+1} / {len(self.exam.questions)}")
        
        if self.index in self.marked_questions:
            self.btn_mark.configure(bootstyle="warning", text="Bỏ đánh dấu")
        else:
            self.btn_mark.configure(bootstyle="warning-outline", text="Đánh dấu")

        for i, btn in enumerate(self.nav_buttons):
            style = "secondary-outline"
            if len(self.answers[i]) > 0: style = "success"
            if i in self.marked_questions: style = "warning"
            if i == self.index: style = "primary" 
            btn.configure(bootstyle=style)

    def next_q(self):
        self._save_current()
        if self.index < len(self.exam.questions) - 1:
            self.index += 1
            self.render()

    def prev_q(self):
        self._save_current()
        if self.index > 0:
            self.index -= 1
            self.render()

    def submit(self):
        self._save_current()
        done = sum(1 for a in self.answers if len(a) > 0)
        if not messagebox.askyesno("Nộp bài", f"Bạn đã làm: {done}/{len(self.exam.questions)}\nNộp bài ngay?"): return
        self._submit_internal(False)

    def _submit_internal(self, auto):
        total_score = 0.0
        for ans, q in zip(self.answers, self.exam.questions):
            earned, _, _ = score_question_partial(ans, set(q.correct_indices), 1.0)
            total_score += earned
        
        u = self.app.current_user
        a = Attempt(
            self.app.store.new_attempt_id(), self.exam.exam_id, self.exam.access_code, self.exam.title,
            u.username, u.full_name, u.student_id,
            total_score, len(self.exam.questions), self.started_at, time.time(),
            int(time.time() - self.started_at), [sorted(list(s)) for s in self.answers]
        )
        self.app.store.add_attempt(a)
        self.stop_timer()
        msg = f"Hết giờ. Hệ thống tự nộp.\nĐiểm: {total_score:.2f}" if auto else f"Đã nộp bài thành công!\nĐiểm: {total_score:.2f}"
        messagebox.showinfo("Hoàn thành", msg)
        self.back()

    def back(self):
        self.stop_timer()
        self.app.show_frame("StudentFrame")


class ReviewFrame(tb.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.exam = None; self.attempt = None
        Header(self, "Xem Lại Bài Thi").pack(fill="x")
        
        top = tb.Frame(self); top.pack(fill="x", pady=10)
        tb.Button(top, text="< Quay lại", command=self.go_back, bootstyle="secondary").pack(side="right")
        
        self.text = ScrolledText(self, wrap="word", height=20, font=("Segoe UI", 11), bootstyle="round")
        self.text.pack(fill="both", expand=True, padx=10, pady=10)

    def load_review(self, exam, attempt, back_to):
        self.exam = exam; self.attempt = attempt; self.back_to = back_to
        self.render()

    def render(self):
        self.text.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        
        total_q = len(self.exam.questions)
        self.text.insert(tk.END, f"Điểm số: {self.attempt.score:.2f} / {total_q}\n", "h1")
        self.text.tag_config("h1", font=("Segoe UI", 16, "bold"), foreground="#2C3E50")
        self.text.insert(tk.END, "-"*60 + "\n\n")
        
        for i, q in enumerate(self.exam.questions):
            user_sel = set(self.attempt.answers[i]) if i < len(self.attempt.answers) else set()
            correct = set(q.correct_indices)
            earned, _, _ = score_question_partial(user_sel, correct, 1.0)
            
            self.text.insert(tk.END, f"Câu {i+1}: {q.text} ", "q_title")
            self.text.insert(tk.END, f"(Điểm: {earned:.2f})\n", "points")
            
            for oi, opt in enumerate(q.options):
                mu = "[x]" if oi in user_sel else "[ ]"
                mc = "  <-- ĐÚNG" if oi in correct else ""
                
                line = f"   {mu} {oi+1}. {opt}{mc}\n"
                
                tag = "normal"
                if oi in user_sel: tag = "user_selected"
                if oi in correct: tag = "correct_ans"
                
                self.text.insert(tk.END, line, tag)
            self.text.insert(tk.END, "\n")
            
        self.text.tag_config("q_title", font=("Segoe UI", 11, "bold"))
        self.text.tag_config("points", font=("Segoe UI", 10, "italic"), foreground="gray")
        self.text.tag_config("correct_ans", foreground="green")
        self.text.tag_config("user_selected", foreground="blue")
        
        self.text.text.config(state="disabled")

    def go_back(self):
        self.app.show_frame(self.back_to)


class TeacherAttemptFrame(ReviewFrame):
    def load_attempt(self, attempt, back_to):
        self.attempt = attempt; self.back_to = back_to
        self.exam = self.app.store.get_exam(attempt.exam_id)
        self.render()


class TemplatePreviewFrame(tb.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.template_id = None
        Header(self, "Xem trước Template").pack(fill="x")
        tb.Button(self, text="Đóng", command=self.go_back, bootstyle="secondary").pack(anchor="e", pady=10, padx=10)
        self.text = ScrolledText(self, font=("Segoe UI", 11)); self.text.pack(fill="both", expand=True)

    def load_template(self, tid, back_to):
        self.template_id = tid; self.back_to = back_to
        t = self.app.store.get_template(tid)
        self.text.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        if t:
            self.text.insert(tk.END, f"Template: {t.title}\nSố câu: {len(t.questions)}\n\n")
            for i, q in enumerate(t.questions):
                self.text.insert(tk.END, f"Câu {i+1}: {q.text}\n")
                for oi, opt in enumerate(q.options):
                    mark = " (đúng)" if oi in q.correct_indices else ""
                    self.text.insert(tk.END, f"  {oi+1}. {opt}{mark}\n")
        self.text.text.config(state="disabled")

    def go_back(self): self.app.show_frame(self.back_to)


class ExamPreviewFrame(tb.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.exam_id = None
        Header(self, "Xem trước Đề thi").pack(fill="x")
        tb.Button(self, text="Đóng", command=self.go_back, bootstyle="secondary").pack(anchor="e", pady=10, padx=10)
        self.text = ScrolledText(self, font=("Segoe UI", 11)); self.text.pack(fill="both", expand=True)

    def load_exam(self, eid, back_to):
        self.exam_id = eid; self.back_to = back_to
        e = self.app.store.get_exam(eid)
        self.text.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        if e:
            self.text.insert(tk.END, f"Exam: {e.title}\nCode: {e.access_code}\n\n")
            for i, q in enumerate(e.questions):
                self.text.insert(tk.END, f"Câu {i+1}: {q.text}\n")
                for oi, opt in enumerate(q.options):
                    mark = " (đúng)" if oi in q.correct_indices else ""
                    self.text.insert(tk.END, f"  {oi+1}. {opt}{mark}\n")
        self.text.text.config(state="disabled")

    def go_back(self): self.app.show_frame(self.back_to)