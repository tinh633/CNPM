# ui/teacher.py
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk 
import ttkbootstrap as tb
from ttkbootstrap.scrolled import ScrolledText
import time
from typing import Optional, List, Set

# Import từ các module khác
from models import Template, Exam, Question, Attempt, score_question_partial
import utils
from .base import Header, info, err, is_valid_date_yyyy_mm_dd
from .auth import ask_change_password

# =============================================================================
# CÁC CLASS HỖ TRỢ (PREVIEW / REVIEW)
# =============================================================================

class ReviewFrameBase(tb.Frame):
    """Class cơ sở cho các màn hình xem trước (tránh lặp code)"""
    def __init__(self, parent, app, title="Review"):
        super().__init__(parent)
        self.app = app
        self.back_to = "TeacherFrame"
        
        Header(self, title).pack(fill="x")
        
        top = tb.Frame(self)
        top.pack(fill="x", pady=10)
        tb.Button(top, text="Đóng / Quay lại", command=self.go_back, bootstyle="secondary").pack(side="right", padx=20)
        
        self.text = ScrolledText(self, font=("Segoe UI", 11), bootstyle="round")
        self.text.pack(fill="both", expand=True, padx=10, pady=10)

    def go_back(self):
        self.app.show_frame(self.back_to)

class TemplatePreviewFrame(ReviewFrameBase):
    def load_template(self, tid, back_to):
        self.back_to = back_to
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

class ExamPreviewFrame(ReviewFrameBase):
    def load_exam(self, eid, back_to):
        self.back_to = back_to
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

class TeacherAttemptFrame(ReviewFrameBase):
    def load_attempt(self, attempt, back_to):
        self.back_to = back_to
        exam = self.app.store.get_exam(attempt.exam_id)
        
        self.text.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        
        if not exam:
            self.text.insert(tk.END, "Không tìm thấy đề thi gốc (có thể đã bị xóa).")
        else:
            total_q = len(exam.questions)
            self.text.insert(tk.END, f"Học sinh: {attempt.full_name} ({attempt.student_id})\n", "h1")
            self.text.insert(tk.END, f"Điểm số: {attempt.score:.2f} / {total_q}\n", "h1")
            self.text.tag_config("h1", font=("Segoe UI", 16, "bold"), foreground="#2C3E50")
            self.text.insert(tk.END, "-"*60 + "\n\n")
            
            for i, q in enumerate(exam.questions):
                user_sel = set(attempt.answers[i]) if i < len(attempt.answers) else set()
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


# =============================================================================
# MAIN TEACHER DASHBOARD
# =============================================================================

class TeacherFrame(tb.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # State variables
        self.selected_exam_id: Optional[str] = None
        self.editing_template_id: Optional[str] = None 
        self.editing_question_index: Optional[int] = None

        # Variables for Builder
        self.tpl_title = tk.StringVar()
        self.q_text = tk.StringVar()
        self.opt_vars = [tk.StringVar() for _ in range(4)]
        self.correct_vars = [tk.BooleanVar(value=False) for _ in range(4)]
        self._temp_questions: List[Question] = []
        
        # Biến cho trang Manager (Publish)
        self.pub_start = tk.StringVar(value=time.strftime("%Y-%m-%d 08:00", time.localtime()))
        self.pub_end = tk.StringVar(value=time.strftime("%Y-%m-%d 23:00", time.localtime()))
        self.pub_duration = tk.IntVar(value=30)
        self.pub_use_pass = tk.BooleanVar(value=False)
        self.pub_pass = tk.StringVar()
        self.pub_allow_review = tk.BooleanVar(value=False)
        self.pub_attempt_limit = tk.IntVar(value=1)
        self.pub_enable_monitor = tk.BooleanVar(value=False) # <--- MỚI: Biến lưu trạng thái bật Anti-cheat

        # Biến cho Profile
        self.t_full_name = tk.StringVar()
        self.t_dob = tk.StringVar()

        # Layout
        self._build_ui()

    def _build_ui(self):
        # 1. Sidebar Panel
        self.sidebar = tb.Frame(self, bootstyle="primary", width=250)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False) 

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
        self._create_sidebar_btn("👤  Hồ sơ (Profile)", lambda: self.show_tab("Profile"))
        
        tb.Frame(self.sidebar, height=50, bootstyle="primary").pack(fill="y", expand=True) # Spacer
        
        tb.Button(self.sidebar, text="Đăng xuất", command=self.app.logout, bootstyle="light-outline", width=15).pack(pady=20)

        # 2. Main Content Area
        self.content_area = tb.Frame(self, bootstyle="bg")
        self.content_area.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # Notebook
        self.notebook = ttk.Notebook(self.content_area)
        self.notebook.pack(fill="both", expand=True)
        
        # Tabs
        self.tab_dashboard = self._init_tab_dashboard()
        self.tab_builder = self._init_tab_builder()
        self.tab_manager = self._init_tab_manager()
        self.tab_results = self._init_tab_results()
        self.tab_profile = self._init_tab_profile()

        self.notebook.add(self.tab_dashboard, text="Dashboard")
        self.notebook.add(self.tab_builder, text="Builder")
        self.notebook.add(self.tab_manager, text="Manager")
        self.notebook.add(self.tab_results, text="Results")
        self.notebook.add(self.tab_profile, text="Profile")
        
        style = ttk.Style()
        style.layout('Hidden.TNotebook.Tab', []) 
        self.notebook.config(style='Hidden.TNotebook')

    def _create_sidebar_btn(self, text, command):
        btn = tb.Button(self.sidebar, text=text, command=command, bootstyle="primary", cursor="hand2")
        btn.pack(fill="x", pady=5, padx=10)
        return btn

    def show_tab(self, name):
        tabs = {"Dashboard": 0, "Builder": 1, "Manager": 2, "Results": 3, "Profile": 4}
        self.notebook.select(tabs[name])
        
        if name == "Manager":
            self.refresh_templates()
            self.refresh_exams()
        if name == "Results":
            self.refresh_exams_in_results()

    def on_show(self):
        if not self.app.current_user or self.app.current_user.role != "Teacher":
            self.app.logout()
            return
        u = self.app.current_user
        self.lbl_user.config(text=f"GV. {u.full_name}\n({u.username})")
        self.t_full_name.set(u.full_name)
        self.t_dob.set(u.dob)
        self.show_tab("Dashboard")
        self.clear_builder()

    # --- TABS INIT ---

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
            
            for w in [lbl_icon, lbl_title]: w.bind("<Button-1>", lambda e: cmd())
            return card

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        grid.columnconfigure(2, weight=1)

        create_card(grid, "Ngân hàng câu hỏi", "📝", "#0d6efd", lambda: self.show_tab("Builder"), 0, 0)
        create_card(grid, "Quản lý đề thi", "📂", "#198754", lambda: self.show_tab("Manager"), 0, 1)
        create_card(grid, "Kết quả & Điểm", "📊", "#ffc107", lambda: self.show_tab("Results"), 0, 2)
        create_card(grid, "Hồ sơ cá nhân", "👤", "#0dcaf0", lambda: self.show_tab("Profile"), 1, 0)
        create_card(grid, "Thống kê lớp", "📈", "#6610f2", lambda: info("Tính năng đang phát triển"), 1, 1)
        create_card(grid, "Trợ giúp", "💡", "#d63384", lambda: info("Liên hệ Admin để được hỗ trợ"), 1, 2)
        return frame

    def _init_tab_builder(self):
        frame = tb.Frame(self.notebook, padding=10)
        h = tb.Frame(frame)
        h.pack(fill="x", pady=(0, 10))
        tb.Label(h, text="Soạn Ngân Hàng Câu Hỏi", font=("Segoe UI", 18, "bold"), bootstyle="primary").pack(side="left")
        tb.Button(h, text="Làm mới form", command=self.clear_builder, bootstyle="secondary-outline").pack(side="right")

        body = tb.Frame(frame)
        body.pack(fill="both", expand=True)
        
        # Left
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
        
        # Right
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

    def _init_tab_manager(self):
        frame = tb.Frame(self.notebook, padding=10)
        tb.Label(frame, text="Quản Lý Đề Thi & Xuất Bản", font=("Segoe UI", 18, "bold"), bootstyle="primary").pack(anchor="w", pady=(0, 10))

        paned = tb.Panedwindow(frame, orient="horizontal")
        paned.pack(fill="both", expand=True)

        # 1. Templates
        f_tpl = tb.Labelframe(paned, text=" 1. Ngân hàng đề (Templates) ", padding=10)
        paned.add(f_tpl, weight=1)
        
        self.tree_tpl = ttk.Treeview(f_tpl, columns=("id", "title", "qs"), show="headings")
        self.tree_tpl.heading("id", text="ID"); self.tree_tpl.heading("title", text="Tiêu đề"); self.tree_tpl.heading("qs", text="Số câu")
        self.tree_tpl.column("id", width=0, stretch=False) 
        self.tree_tpl.pack(fill="both", expand=True, pady=(0, 10))
        
        btns_tpl = tb.Frame(f_tpl)
        btns_tpl.pack(fill="x")
        tb.Button(btns_tpl, text="Sửa", command=self.edit_selected_template, bootstyle="info-outline").pack(side="left", padx=2)
        tb.Button(btns_tpl, text="Xóa", command=self.delete_selected_template, bootstyle="danger-outline").pack(side="left", padx=2)
        tb.Button(btns_tpl, text="Xuất Word", command=self.export_selected_template_word, bootstyle="secondary-outline").pack(side="left", padx=2)
        
        # 2. Publish Config
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
        
        # --- MỚI: Checkbox bật/tắt Anti-cheat ---
        tb.Checkbutton(f_pub, text="Bật giám sát (Anti-cheat)", variable=self.pub_enable_monitor, bootstyle="danger-round-toggle").pack(anchor="w", pady=5)
        # ----------------------------------------
        
        tb.Button(f_pub, text=">>> XUẤT BẢN KỲ THI >>>", command=self.publish_exam, bootstyle="warning").pack(fill="x", pady=20)

        # 3. Exams
        f_exam = tb.Labelframe(paned, text=" 3. Đề đang mở (Exams) ", padding=10)
        paned.add(f_exam, weight=1)
        
        self.tree_exam = ttk.Treeview(f_exam, columns=("id", "title", "code", "status"), show="headings")
        self.tree_exam.heading("id", text="ID"); self.tree_exam.heading("title", text="Tên kỳ thi")
        self.tree_exam.heading("code", text="Mã Code"); self.tree_exam.heading("status", text="Trạng thái")
        self.tree_exam.column("id", width=0, stretch=False)
        self.tree_exam.column("code", width=80, anchor="center")
        self.tree_exam.column("status", width=80, anchor="center")
        self.tree_exam.pack(fill="both", expand=True, pady=(0, 10))
        
        btns_ex = tb.Frame(f_exam)
        btns_ex.pack(fill="x")
        tb.Button(btns_ex, text="Hủy/Xóa", command=self.delete_selected_exam, bootstyle="danger").pack(side="right")
        tb.Button(btns_ex, text="Reset Lượt thi", command=self.delete_attempts_for_selected_exam, bootstyle="warning-outline").pack(side="right", padx=5)
        return frame

    def _init_tab_results(self):
        frame = tb.Frame(self.notebook, padding=10)
        tb.Label(frame, text="Kết Quả & Bảng Điểm", font=("Segoe UI", 18, "bold"), bootstyle="primary").pack(anchor="w", pady=(0, 10))

        top = tb.Frame(frame)
        top.pack(fill="x", pady=(0, 10))
        tb.Label(top, text="Chọn kỳ thi để xem điểm:").pack(side="left", padx=(0, 10))
        
        self.res_exam_var = tk.StringVar()
        self.res_exam_cb = tb.Combobox(top, textvariable=self.res_exam_var, state="readonly", width=50)
        self.res_exam_cb.pack(side="left")
        self.res_exam_cb.bind("<<ComboboxSelected>>", self._on_result_exam_select)
        
        tb.Button(top, text="Xuất Excel", command=self.export_selected_exam_results_excel, bootstyle="success").pack(side="right")

        self.tree_res = ttk.Treeview(frame, columns=("aid", "std_name", "sid", "score", "time"), show="headings")
        self.tree_res.heading("aid", text="ID"); self.tree_res.heading("std_name", text="Họ tên")
        self.tree_res.heading("sid", text="MSSV"); self.tree_res.heading("score", text="Điểm số")
        self.tree_res.heading("time", text="Thời gian làm")
        self.tree_res.column("aid", width=0, stretch=False)
        self.tree_res.column("score", anchor="center"); self.tree_res.column("time", anchor="center")
        self.tree_res.pack(fill="both", expand=True)
        
        sb = tb.Scrollbar(frame, orient="vertical", command=self.tree_res.yview)
        sb.place(relx=1, rely=0, relheight=1, anchor="ne")
        self.tree_res.configure(yscrollcommand=sb.set)
        
        self.tree_res.bind("<Double-Button-1>", lambda e: self.view_attempt_details_from_results())
        tb.Label(frame, text="* Nhấp đúp vào dòng để xem chi tiết bài làm", font=("Segoe UI", 9, "italic"), bootstyle="secondary").pack(anchor="w")
        return frame

    def _init_tab_profile(self):
        frame = tb.Frame(self.notebook, padding=20)
        tb.Label(frame, text="Hồ sơ cá nhân", font=("Segoe UI", 18, "bold"), bootstyle="primary").pack(anchor="w", pady=(0, 10))
        tb.Label(frame, text="Cập nhật thông tin và đổi mật khẩu của bạn.", bootstyle="secondary").pack(anchor="w", pady=(0, 20))

        form = tb.Labelframe(frame, text="Thông tin giáo viên", padding=15, bootstyle="info")
        form.pack(fill="x", pady=(0, 15))

        tb.Label(form, text="Họ tên:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(form, textvariable=self.t_full_name, width=40).grid(row=0, column=1, sticky="w", padx=6, pady=6)

        tb.Label(form, text="Ngày sinh (YYYY-MM-DD):").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(form, textvariable=self.t_dob, width=40).grid(row=1, column=1, sticky="w", padx=6, pady=6)

        btn_row = tb.Frame(form)
        btn_row.grid(row=2, column=1, sticky="e", pady=(10, 0))
        tb.Button(btn_row, text="Lưu hồ sơ", command=self.teacher_update_profile, bootstyle="success").pack(side="left", padx=6)
        tb.Button(btn_row, text="Đổi mật khẩu", command=self.teacher_change_password, bootstyle="warning").pack(side="left")
        return frame

    # --- LOGIC BUILDER ---

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
        self.clear_builder_form_only()

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

    # --- LOGIC MANAGER ---

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
            if not messagebox.askyesno("Cảnh báo", "Template này đang dùng cho Kỳ thi. Xóa sẽ mất dữ liệu. Tiếp tục?"): return
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

    def _toggle_pub_pass(self):
        if self.pub_use_pass.get():
            self.pub_pass_entry.config(state="normal")
        else:
            self.pub_pass_entry.config(state="disabled")
            self.pub_pass.set("")

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
            enable_monitoring=bool(self.pub_enable_monitor.get()), # <--- MỚI: Lưu cấu hình giám sát
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

    # --- LOGIC RESULTS ---

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

    # --- LOGIC PROFILE ---

    def teacher_update_profile(self):
        u = self.app.current_user
        if not u: return
        full_name = (self.t_full_name.get() or "").strip()
        dob = (self.t_dob.get() or "").strip()

        if dob and (not is_valid_date_yyyy_mm_dd(dob)):
            return err("Ngày sinh không hợp lệ. Định dạng đúng: YYYY-MM-DD")

        ok = self.app.store.update_profile(u.username, full_name, dob, student_id="")
        if not ok: return err("Không thể cập nhật hồ sơ.")
        
        uu = self.app.store.find_user(u.username)
        if uu:
            self.app.current_user = uu
            self.lbl_user.config(text=f"GV. {uu.full_name}\n({uu.username})")
        info("Đã cập nhật hồ sơ giáo viên.")

    def teacher_change_password(self):
        data = ask_change_password(self)
        if data is None: return
        old_pw, new_pw, confirm = data
        cur = self.app.store.find_user(self.app.current_user.username)
        if not cur or (cur.password != (old_pw or "")):
            return err("Mật khẩu hiện tại không đúng.")
        new_pw = (new_pw or "").strip()
        if not new_pw: return err("Mật khẩu mới không được để trống.")
        if new_pw != (confirm or ""): return err("Mật khẩu mới không khớp.")
        okp, msgp = utils.validate_strong_password(new_pw)
        if not okp: return err(msgp)
        ok = self.app.store.update_password(self.app.current_user.username, new_pw)
        if not ok: return err("Không thể đổi mật khẩu.")
        uu = self.app.store.find_user(self.app.current_user.username)
        if uu: self.app.current_user = uu
        info("Đổi mật khẩu thành công!")