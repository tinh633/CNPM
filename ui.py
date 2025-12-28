# ui.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import time
from typing import Optional, List, Dict, Set

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
    messagebox.showinfo("Info", msg)

def err(msg: str):
    messagebox.showerror("Error", msg)

class Header(ttk.Frame):
    def __init__(self, parent, title: str, subtitle: str = ""):
        super().__init__(parent)
        ttk.Label(self, text=title, font=("Segoe UI", 18, "bold")).pack(anchor="w")
        if subtitle:
            ttk.Label(self, text=subtitle).pack(anchor="w", pady=(2, 0))

# -----------------------------
# FRAMES
# -----------------------------

class LoginFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        Header(
            self,
            "Quiz Examination System",
            "Login. Default: admin/admin, teacher/teacher, student/student."
        ).pack(fill="x", pady=(0, 16))

        form = ttk.Frame(self)
        form.pack(pady=26)

        ttk.Label(form, text="Role:").grid(row=0, column=0, sticky="e", padx=8, pady=8)
        self.role_var = tk.StringVar(value=ROLES[0])
        ttk.Combobox(form, textvariable=self.role_var, values=ROLES, state="readonly", width=22)\
            .grid(row=0, column=1, sticky="w", padx=8, pady=8)

        ttk.Label(form, text="Username:").grid(row=1, column=0, sticky="e", padx=8, pady=8)
        self.user_var = tk.StringVar()
        self.user_entry = ttk.Entry(form, textvariable=self.user_var, width=26)
        self.user_entry.grid(row=1, column=1, sticky="w", padx=8, pady=8)

        ttk.Label(form, text="Password:").grid(row=2, column=0, sticky="e", padx=8, pady=8)
        self.pass_var = tk.StringVar()
        self.pass_entry = ttk.Entry(form, textvariable=self.pass_var, show="*", width=26)
        self.pass_entry.grid(row=2, column=1, sticky="w", padx=8, pady=8)

        btns = ttk.Frame(self)
        btns.pack(pady=8)
        ttk.Button(btns, text="Login", command=self.do_login).pack(side="left", padx=6)
        ttk.Button(btns, text="Clear", command=self.clear).pack(side="left", padx=6)

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
            err("Role, username, and password are needed.")
            return

        u = self.app.store.find_user(username)
        if not u:
            err("User not found.")
            return
        if u.password != password:
            err("Password is not correct.")
            return

        u.role = ROLE_CANON.get(u.role.lower(), u.role)
        if u.role != role:
            err(f"Role mismatch.\nAccount role: {u.role}\nYou selected: {role}")
            return

        self.app.current_user = u
        info(f"Login ok. Welcome {u.username} ({u.role}).")
        if u.role == "Admin":
            self.app.show_frame("AdminFrame")
        elif u.role == "Teacher":
            self.app.show_frame("TeacherFrame")
        else:
            self.app.show_frame("StudentFrame")


class AdminFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        Header(self, "Admin Panel", "Admin manages users.").pack(fill="x", pady=(0, 10))

        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Button(top, text="Reload", command=self.app.reload_data).pack(side="right", padx=6)
        ttk.Button(top, text="Logout", command=self.app.logout).pack(side="right")

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, pady=10)

        left = ttk.LabelFrame(main, text="Create User")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = ttk.LabelFrame(main, text="Users / Reset password")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        self.new_user = tk.StringVar()
        self.new_pass = tk.StringVar()
        self.new_role = tk.StringVar(value="Student")

        f = ttk.Frame(left, padding=10)
        f.pack(fill="x")
        ttk.Label(f, text="Username:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(f, textvariable=self.new_user, width=28).grid(row=0, column=1, padx=6, pady=6, sticky="w")
        ttk.Label(f, text="Password:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(f, textvariable=self.new_pass, width=28).grid(row=1, column=1, padx=6, pady=6, sticky="w")
        ttk.Label(f, text="Role:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        ttk.Combobox(f, textvariable=self.new_role, values=ROLES, state="readonly", width=26)\
            .grid(row=2, column=1, padx=6, pady=6, sticky="w")
        ttk.Button(f, text="Create", command=self.create_user).grid(row=3, column=0, columnspan=2, pady=(10, 4))

        self.reset_user = tk.StringVar()
        self.reset_pass = tk.StringVar()
        rr = ttk.Frame(right, padding=10)
        rr.pack(fill="x")
        ttk.Label(rr, text="Username:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(rr, textvariable=self.reset_user, width=26).grid(row=0, column=1, sticky="w", padx=6, pady=6)
        ttk.Label(rr, text="New password:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(rr, textvariable=self.reset_pass, width=26).grid(row=1, column=1, sticky="w", padx=6, pady=6)
        ttk.Button(rr, text="Reset", command=self.reset_password).grid(row=2, column=0, columnspan=2, pady=(10, 4))

        self.users_box = tk.Listbox(right, height=18)
        self.users_box.pack(fill="both", expand=True, padx=10, pady=(6, 10))

    def on_show(self):
        if not self.app.current_user or self.app.current_user.role != "Admin":
            err("You need Admin role.")
            self.app.logout()
            return
        self.refresh_users()

    def refresh_users(self):
        self.users_box.delete(0, tk.END)
        for u in self.app.store.list_users():
            self.users_box.insert(tk.END, f"{u.username} | {u.role} | {u.full_name} | {u.dob} | {u.student_id}")

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

    def reset_password(self):
        username = self.reset_user.get().strip()
        new_password = self.reset_pass.get()
        if not username or not new_password:
            err("Username and new password are needed.")
            return
        ok = self.app.store.update_password(username, new_password)
        if not ok:
            err("User not found.")
            return
        info("Password updated.")
        self.reset_user.set("")
        self.reset_pass.set("")
        self.refresh_users()


class TeacherFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.selected_exam_id: Optional[str] = None
        
        # State variables
        self.editing_template_id: Optional[str] = None 
        self.editing_question_index: Optional[int] = None # To track which question we are editing in builder

        Header(
            self,
            "Teacher Panel",
            "Templates = Question Bank. Exams = Published for students."
        ).pack(fill="x", pady=(0, 10))

        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Button(top, text="Reload", command=self.app.reload_data).pack(side="right", padx=6)
        ttk.Button(top, text="Logout", command=self.app.logout).pack(side="right")

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, pady=10)

        # --- LEFT: BUILDER ---
        left = ttk.LabelFrame(main, text="Template Builder (Create/Edit)")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # --- RIGHT: MANAGER ---
        right = ttk.LabelFrame(main, text="Manage & Publish")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        # ================= BUILDER UI =================
        self.tpl_title = tk.StringVar()
        self.q_text = tk.StringVar()
        self.opt_vars = [tk.StringVar() for _ in range(4)]
        self.correct_vars = [tk.BooleanVar(value=False) for _ in range(4)]
        self._temp_questions: List[Question] = []

        # Template Title
        bf = ttk.Frame(left, padding=10)
        bf.pack(fill="x")
        ttk.Label(bf, text="Title:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(bf, textvariable=self.tpl_title, width=34).grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Separator(left).pack(fill="x", padx=10, pady=6)

        # Question Form
        qf = ttk.Frame(left, padding=10)
        qf.pack(fill="x")
        ttk.Label(qf, text="Question Text:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(qf, textvariable=self.q_text, width=34).grid(row=0, column=1, sticky="w", padx=6, pady=6)

        for i in range(4):
            r = 1 + i
            ttk.Label(qf, text=f"Option {i+1}:").grid(row=r, column=0, sticky="e", padx=6, pady=4)
            row = ttk.Frame(qf)
            row.grid(row=r, column=1, sticky="w", padx=6, pady=4)
            ttk.Entry(row, textvariable=self.opt_vars[i], width=28).pack(side="left")
            ttk.Checkbutton(row, text="Correct", variable=self.correct_vars[i]).pack(side="left", padx=8)

        # Controls
        br = ttk.Frame(left, padding=10)
        br.pack(fill="x")
        
        # This button changes text based on context
        self.btn_add_q = ttk.Button(br, text="Add Question", command=self.add_or_update_question)
        self.btn_add_q.pack(side="left", padx=2)
        
        self.btn_save = ttk.Button(br, text="Save Template", command=self.save_template)
        self.btn_save.pack(side="left", padx=2)

        # List Actions
        ar = ttk.Frame(left, padding=(10, 0, 10, 10))
        ar.pack(fill="x")
        ttk.Button(ar, text="Edit Selected Q", command=self.load_question_for_editing).pack(side="left", padx=2)
        ttk.Button(ar, text="Delete Selected Q", command=self.remove_question_from_builder).pack(side="left", padx=2)
        ttk.Button(ar, text="Clear/Cancel", command=self.clear_builder).pack(side="right", padx=2)

        # Questions List
        self.temp_list = tk.Listbox(left, height=10)
        self.temp_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.temp_list.bind("<Double-Button-1>", lambda e: self.load_question_for_editing())


        # ================= RIGHT PANEL UI =================
        rf = ttk.Frame(right, padding=10)
        rf.pack(fill="both", expand=True)

        ttk.Label(rf, text="My Templates (Select to Edit/Publish):").pack(anchor="w")
        self.tpl_list = tk.Listbox(rf, height=7)
        self.tpl_list.pack(fill="x", pady=(6, 8))

        # Template Actions
        tpl_btn = ttk.Frame(rf)
        tpl_btn.pack(fill="x", pady=(0, 8))
        
        ttk.Button(tpl_btn, text="Edit (Load)", command=self.edit_selected_template).pack(side="left", padx=(0, 6))
        ttk.Button(tpl_btn, text="Preview", command=self.preview_selected_template).pack(side="left")
        ttk.Button(tpl_btn, text="Delete", command=self.delete_selected_template).pack(side="left", padx=6)
        ttk.Button(tpl_btn, text="Word Export", command=self.export_selected_template_word).pack(side="right")

        # Publish Section
        pub = ttk.LabelFrame(rf, text="Publish Exam")
        pub.pack(fill="x", pady=(0, 8))

        self.pub_start = tk.StringVar(value=time.strftime("%Y-%m-%d 08:00", time.localtime()))
        self.pub_end = tk.StringVar(value=time.strftime("%Y-%m-%d 23:00", time.localtime()))
        self.pub_duration = tk.IntVar(value=30)
        self.pub_use_pass = tk.BooleanVar(value=False)
        self.pub_pass = tk.StringVar()
        self.pub_allow_review = tk.BooleanVar(value=False)
        self.pub_attempt_limit = tk.IntVar(value=1)

        pf = ttk.Frame(pub, padding=8)
        pf.pack(fill="x")

        ttk.Label(pf, text="Start:").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        ttk.Entry(pf, textvariable=self.pub_start, width=16).grid(row=0, column=1, sticky="w", padx=6, pady=4)
        ttk.Label(pf, text="End:").grid(row=0, column=2, sticky="e", padx=6, pady=4)
        ttk.Entry(pf, textvariable=self.pub_end, width=16).grid(row=0, column=3, sticky="w", padx=6, pady=4)

        ttk.Label(pf, text="Minutes:").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        ttk.Spinbox(pf, from_=1, to=240, textvariable=self.pub_duration, width=5).grid(row=1, column=1, sticky="w", padx=6, pady=4)
        ttk.Label(pf, text="Attempts:").grid(row=1, column=2, sticky="e", padx=6, pady=4)
        ttk.Spinbox(pf, from_=0, to=50, textvariable=self.pub_attempt_limit, width=5).grid(row=1, column=3, sticky="w", padx=6, pady=4)

        pr = ttk.Frame(pf)
        pr.grid(row=2, column=0, columnspan=4, sticky="w", pady=(2, 2))
        ttk.Checkbutton(pr, text="Password?", variable=self.pub_use_pass, command=self._toggle_pub_pass).pack(side="left")
        self.pub_pass_entry = ttk.Entry(pr, textvariable=self.pub_pass, width=12, show="*")
        self.pub_pass_entry.pack(side="left", padx=6)
        ttk.Checkbutton(pr, text="Allow Review?", variable=self.pub_allow_review).pack(side="left", padx=(12, 0))

        btnpub = ttk.Frame(pub, padding=(8, 0, 8, 8))
        btnpub.pack(fill="x")
        ttk.Button(btnpub, text="Publish Now", command=self.publish_exam).pack(side="left")

        ttk.Separator(rf).pack(fill="x", pady=6)

        # Exam List
        ttk.Label(rf, text="Published Exams:").pack(anchor="w")
        self.exam_list = tk.Listbox(rf, height=7, exportselection=False)
        self.exam_list.pack(fill="x", pady=(6, 8))
        self.exam_list.bind("<<ListboxSelect>>", self._on_exam_select)

        exam_btn = ttk.Frame(rf)
        exam_btn.pack(fill="x", pady=(0, 8))
        ttk.Button(exam_btn, text="Preview", command=self.preview_selected_exam).pack(side="left")
        ttk.Button(exam_btn, text="Delete Exam", command=self.delete_selected_exam).pack(side="left", padx=6)
        ttk.Button(exam_btn, text="Clear Attempts", command=self.delete_attempts_for_selected_exam).pack(side="left", padx=6)
        ttk.Button(exam_btn, text="Results (Excel)", command=self.export_selected_exam_results_excel).pack(side="right")

        # Attempts List
        ttk.Label(rf, text="Student Attempts (Double click to view):").pack(anchor="w", pady=(8, 0))
        self.attempt_list = tk.Listbox(rf, height=9, exportselection=False)
        self.attempt_list.pack(fill="both", expand=True, pady=(6, 0))
        self.attempt_list.bind("<Double-Button-1>", lambda e: self.view_attempt_details())
        
        self.selected_attempt_id: str = ""
        self.attempt_list.bind("<<ListboxSelect>>", self._on_attempt_select)
        self.attempt_list.bind("<Button-1>", self._on_attempt_click)

        self._attempt_id_by_index: Dict[int, str] = {}
        self._toggle_pub_pass()

    def _toggle_pub_pass(self):
        if self.pub_use_pass.get():
            self.pub_pass_entry.config(state="normal")
        else:
            self.pub_pass_entry.config(state="disabled")
            self.pub_pass.set("")

    def on_show(self):
        if not self.app.current_user or self.app.current_user.role != "Teacher":
            err("Teacher role required.")
            self.app.logout()
            return
        self.refresh_templates()
        self.refresh_exams()
        self.attempt_list.delete(0, tk.END)
        self._attempt_id_by_index.clear()
        self.clear_builder() 

    def refresh_templates(self):
        self.tpl_list.delete(0, tk.END)
        teacher = self.app.current_user.username
        for t in self.app.store.list_templates_by_teacher(teacher):
            self.tpl_list.insert(tk.END, f"{t.template_id} | {t.title} | {len(t.questions)} Qs")

    def refresh_exams(self):
        self.exam_list.delete(0, tk.END)
        teacher = self.app.current_user.username
        now = int(time.time())
        for e in self.app.store.list_exams_by_teacher(teacher):
            status = "OPEN" if (e.start_ts <= now <= e.end_ts) else ("WAIT" if now < e.start_ts else "CLOSED")
            self.exam_list.insert(
                tk.END,
                f"{e.exam_id} | {e.title} | Code: {e.access_code} | {status}"
            )

    # ================= LOGIC BUILDER =================

    def refresh_builder_list(self):
        self.temp_list.delete(0, tk.END)
        for i, q in enumerate(self._temp_questions):
            correct_str = ",".join(str(x+1) for x in q.correct_indices)
            self.temp_list.insert(tk.END, f"{i+1}. {q.text} (Correct: {correct_str})")

    def add_or_update_question(self):
        text = self.q_text.get().strip()
        options = [v.get().strip() for v in self.opt_vars]
        correct_indices = [i for i, b in enumerate(self.correct_vars) if b.get()]
        
        if not text: return err("Question text needed.")
        if any(not o for o in options): return err("All 4 options needed.")
        if len(correct_indices) == 0: return err("Select at least 1 correct option.")
        
        q = Question(text=text, options=options, correct_indices=correct_indices)
        
        if self.editing_question_index is not None:
            # UPDATE EXISTING
            if 0 <= self.editing_question_index < len(self._temp_questions):
                self._temp_questions[self.editing_question_index] = q
            else:
                # Fallback if index invalid
                self._temp_questions.append(q)
        else:
            # ADD NEW
            self._temp_questions.append(q)

        self.refresh_builder_list()
        
        # Clear small form but keep title
        self.q_text.set("")
        for v in self.opt_vars: v.set("")
        for b in self.correct_vars: b.set(False)
        self.editing_question_index = None
        self.btn_add_q.config(text="Add Question")

    def load_question_for_editing(self):
        """Loads selected question back into the inputs for editing"""
        sel = self.temp_list.curselection()
        if not sel: return
        idx = sel[0]
        
        if idx >= len(self._temp_questions): return
        
        q = self._temp_questions[idx]
        
        # Populate form
        self.q_text.set(q.text)
        for i, opt in enumerate(q.options):
            if i < 4: self.opt_vars[i].set(opt)
        
        for i in range(4):
            self.correct_vars[i].set(i in q.correct_indices)
            
        self.editing_question_index = idx
        self.btn_add_q.config(text=f"Update Question #{idx+1}")

    def remove_question_from_builder(self):
        sel = self.temp_list.curselection()
        if not sel: return
        idx = sel[0]
        self._temp_questions.pop(idx)
        self.refresh_builder_list()
        
        # If we were editing this specific question, cancel edit mode
        if self.editing_question_index == idx:
            self.editing_question_index = None
            self.btn_add_q.config(text="Add Question")
            self.q_text.set("")
            for v in self.opt_vars: v.set("")
            for b in self.correct_vars: b.set(False)

    def edit_selected_template(self):
        """Load template from right list to left builder"""
        tid = self._selected_template_id()
        if not tid: return err("Select a template to edit.")
        
        t = self.app.store.get_template(tid)
        if not t: return

        self.editing_template_id = t.template_id
        
        self.tpl_title.set(t.title)
        self._temp_questions = list(t.questions) 
        self.refresh_builder_list()
        
        self.btn_save.config(text=f"Update ({t.template_id})")
        info(f"Loaded '{t.title}'.\nEdit questions then click Update.")

    def clear_builder(self):
        self.editing_template_id = None
        self.editing_question_index = None
        
        self.tpl_title.set("")
        self.q_text.set("")
        for v in self.opt_vars: v.set("")
        for b in self.correct_vars: b.set(False)
        
        self._temp_questions.clear()
        self.temp_list.delete(0, tk.END)
        
        self.btn_save.config(text="Save New Template")
        self.btn_add_q.config(text="Add Question")

    def save_template(self):
        title = self.tpl_title.get().strip()
        if not title: return err("Template title needed.")
        if len(self._temp_questions) == 0: return err("Need at least 1 question.")
        
        if self.editing_template_id:
            # === UPDATE MODE ===
            if not messagebox.askyesno("Confirm", "Overwrite this template?"): return
            t = Template(
                template_id=self.editing_template_id,
                title=title,
                created_by=self.app.current_user.username,
                questions=list(self._temp_questions)
            )
            if self.app.store.update_template(t):
                info("Template updated successfully.")
            else:
                err("Error: Template ID not found.")
        else:
            # === CREATE NEW MODE ===
            t = Template(
                template_id=self.app.store.new_template_id(),
                title=title,
                created_by=self.app.current_user.username,
                questions=list(self._temp_questions)
            )
            self.app.store.add_template(t)
            info("New template saved.")

        self.clear_builder()
        self.refresh_templates()

    # ================= MANAGER LOGIC =================

    def _selected_template_id(self) -> Optional[str]:
        sel = self.tpl_list.curselection()
        if not sel: return None
        return self.tpl_list.get(sel[0]).split("|")[0].strip()

    def _selected_exam_id(self) -> Optional[str]:
        sel = self.exam_list.curselection()
        if not sel: return None
        return self.exam_list.get(sel[0]).split("|")[0].strip()

    def delete_selected_template(self):
        tid = self._selected_template_id()
        if not tid: return err("Select a template.")
        if self.app.store.has_exam_from_template(tid):
            if not messagebox.askyesno("Confirm", "This template is used by an exam.\nDelete anyway?"): return
        if not messagebox.askyesno("Confirm", "Delete this template?"): return
        if self.app.store.delete_template(tid):
            info("Deleted.")
            if self.editing_template_id == tid:
                self.clear_builder()
            self.refresh_templates()

    def preview_selected_template(self):
        tid = self._selected_template_id()
        if not tid: return err("Select a template.")
        self.app.frames["TemplatePreviewFrame"].load_template(tid, back_to="TeacherFrame")
        self.app.show_frame("TemplatePreviewFrame")

    def export_selected_template_word(self):
        tid = self._selected_template_id()
        if not tid: return err("Select a template.")
        tpl = self.app.store.get_template(tid)
        filepath = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word Document", "*.docx")])
        if filepath:
            include_ans = messagebox.askyesno("Export", "Include correct answers?")
            utils.export_template_to_word(tpl, filepath, include_answers=include_ans)
            info("Exported.")

    def publish_exam(self):
        tid = self._selected_template_id()
        if not tid: return err("Select a template to publish.")
        tpl = self.app.store.get_template(tid)
        
        start_ts = utils.parse_dt(self.pub_start.get())
        end_ts = utils.parse_dt(self.pub_end.get())
        if not start_ts or not end_ts: return err("Invalid format (YYYY-MM-DD HH:MM)")
        if end_ts <= start_ts: return err("End time must be after Start time.")
        
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
        info(f"Exam Published!\nCODE: {code}")
        self.refresh_exams()

    def preview_selected_exam(self):
        eid = self._selected_exam_id()
        if not eid: return err("Select an exam.")
        self.app.frames["ExamPreviewFrame"].load_exam(eid, back_to="TeacherFrame")
        self.app.show_frame("ExamPreviewFrame")

    def delete_selected_exam(self):
        eid = self._selected_exam_id()
        if not eid: return err("Select an exam.")
        if not messagebox.askyesno("Confirm", "Delete this exam?"): return
        if self.app.store.delete_exam(eid):
            info("Deleted.")
            self.refresh_exams()
            self.attempt_list.delete(0, tk.END)

    def delete_attempts_for_selected_exam(self):
        eid = self._selected_exam_id()
        if not eid: return err("Select an exam.")
        if not messagebox.askyesno("Confirm", "Delete ALL attempts for this exam?"): return
        deleted = self.app.store.delete_attempts_for_exam(eid)
        info(f"Deleted {deleted} attempts.")
        self._on_exam_select()

    def export_selected_exam_results_excel(self):
        eid = self._selected_exam_id()
        if not eid: return err("Select an exam.")
        e = self.app.store.get_exam(eid)
        attempts = self.app.store.list_attempts_for_exam(eid)
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if filepath:
            utils.export_exam_results_to_excel(e, attempts, filepath)
            info("Exported.")

    def _on_exam_select(self, event=None):
        eid = self._selected_exam_id()
        self.selected_exam_id = eid
        self.attempt_list.delete(0, tk.END)
        self._attempt_id_by_index.clear()
        if not eid: return

        attempts = self.app.store.list_attempts_for_exam(eid)
        if not attempts:
            self.attempt_list.insert(tk.END, "(No attempts)")
            return

        for idx, a in enumerate(attempts):
            took = f"{a.time_taken_seconds // 60:02d}:{a.time_taken_seconds % 60:02d}"
            score10 = (a.score / max(1, a.total)) * 10.0
            self.attempt_list.insert(tk.END, f"{a.full_name} | {score10:.2f}/10 | {took}")
            self._attempt_id_by_index[idx] = a.attempt_id

    def _selected_attempt_id_from_listbox(self) -> str:
        sel = self.attempt_list.curselection()
        if not sel: return ""
        return self._attempt_id_by_index.get(sel[0], "")

    def view_attempt_details(self):
        eid = self.selected_exam_id
        aid = self._selected_attempt_id_from_listbox()
        if not eid or not aid: return
        
        attempts = self.app.store.list_attempts_for_exam(eid)
        target = next((x for x in attempts if x.attempt_id == aid), None)
        if target:
            self.app.frames["TeacherAttemptFrame"].load_attempt(target, back_to="TeacherFrame")
            self.app.show_frame("TeacherAttemptFrame")

    def _on_attempt_click(self, event):
        idx = self.attempt_list.nearest(event.y)
        if idx >= 0:
            self.attempt_list.selection_clear(0, tk.END)
            self.attempt_list.selection_set(idx)
            self.selected_attempt_id = self._attempt_id_by_index.get(idx, "")

    def _on_attempt_select(self, event=None):
        self._on_attempt_click(event)


class StudentFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        Header(self, "Student Panel", "Student must enter exam by CODE only.").pack(fill="x", pady=(0, 10))

        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Button(top, text="Reload", command=self.app.reload_data).pack(side="right", padx=6)
        ttk.Button(top, text="Logout", command=self.app.logout).pack(side="right")

        main = ttk.Frame(self)
        main.pack(fill="both", expand=True, pady=10)

        left = ttk.LabelFrame(main, text="Enter exam by CODE")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = ttk.LabelFrame(main, text="Profile + My attempts")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        lf = ttk.Frame(left, padding=10)
        lf.pack(fill="x")
        ttk.Label(lf, text="CODE:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.code_var = tk.StringVar()
        ttk.Entry(lf, textvariable=self.code_var, width=18).grid(row=0, column=1, sticky="w", padx=6, pady=6)
        ttk.Button(lf, text="Open", command=self.open_by_code).grid(row=0, column=2, padx=6)

        # profile
        pf = ttk.Frame(right, padding=10)
        pf.pack(fill="x")
        ttk.Label(pf, text="Full name:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ttk.Label(pf, text="DOB:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        ttk.Label(pf, text="Student ID:").grid(row=2, column=0, sticky="e", padx=6, pady=6)

        self.full_name = tk.StringVar()
        self.dob = tk.StringVar()
        self.sid = tk.StringVar()
        ttk.Entry(pf, textvariable=self.full_name, width=28).grid(row=0, column=1, sticky="w", padx=6, pady=6)
        ttk.Entry(pf, textvariable=self.dob, width=28).grid(row=1, column=1, sticky="w", padx=6, pady=6)
        ttk.Entry(pf, textvariable=self.sid, width=28).grid(row=2, column=1, sticky="w", padx=6, pady=6)
        ttk.Button(pf, text="Update profile", command=self.update_profile).grid(row=3, column=0, columnspan=2, pady=(8, 4))

        ttk.Separator(right).pack(fill="x", padx=10, pady=6)
        ttk.Label(right, text="My attempts:").pack(anchor="w", padx=10)
        self.attempt_list = tk.Listbox(right, height=16)
        self.attempt_list.pack(fill="both", expand=True, padx=10, pady=(6, 10))
        ttk.Button(right, text="Review selected attempt", command=self.review_selected).pack(pady=(0, 10))

    def on_show(self):
        if not self.app.current_user or self.app.current_user.role != "Student":
            err("You need Student role.")
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
        info("Profile updated.")
        self.refresh_attempts()

    def refresh_attempts(self):
        self.attempt_list.delete(0, tk.END)
        attempts = self.app.store.list_attempts_for_user(self.app.current_user.username)
        if not attempts:
            self.attempt_list.insert(tk.END, "No attempts yet.")
            return
        for a in attempts:
            score10 = (a.score / max(1, a.total)) * 10.0
            self.attempt_list.insert(tk.END, f"{utils.fmt_dt_full(a.submitted_at)} | {a.title} | {score10:.2f}/10")

    def open_by_code(self):
        code = self.code_var.get().strip().upper()
        if not code: return err("Need code.")
        exam = self.app.store.get_exam_by_code(code)
        if not exam: return err("Exam not found.")

        now = int(time.time())
        if now < exam.start_ts: return err(f"Exam not open yet.\nStart: {utils.fmt_dt(exam.start_ts)}")
        if now > exam.end_ts: return err(f"Exam closed.\nEnd: {utils.fmt_dt(exam.end_ts)}")
        
        if exam.attempt_limit > 0:
            used = self.app.store.count_attempts_for_user_exam(self.app.current_user.username, exam.exam_id)
            if used >= exam.attempt_limit: return err("Attempt limit reached.")

        if exam.password:
            pw = simpledialog.askstring("Password", "This exam needs password:", show="*")
            if pw != exam.password: return err("Wrong password.")

        self.app.frames["ExamTakeFrame"].load_exam(exam)
        self.app.show_frame("ExamTakeFrame")

    def review_selected(self):
        sel = self.attempt_list.curselection()
        if not sel: return err("Select an attempt.")
        attempts = self.app.store.list_attempts_for_user(self.app.current_user.username)
        attempt = attempts[sel[0]]
        exam = self.app.store.get_exam(attempt.exam_id)
        if not exam: return err("Exam data missing.")
        if not exam.allow_review: return err("Review not allowed by teacher.")
        self.app.frames["ReviewFrame"].load_review(exam, attempt, back_to="StudentFrame")
        self.app.show_frame("ReviewFrame")


class ExamTakeFrame(ttk.Frame):
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
        top = ttk.Frame(self)
        top.pack(fill="x", side="top", pady=(0, 5))
        self.timer_label = ttk.Label(top, text="Time left: --:--", font=("Segoe UI", 12, "bold"), foreground="red")
        self.timer_label.pack(side="left", padx=10)
        ttk.Button(top, text="Exit", command=self.back).pack(side="right", padx=10)

        # Main Container
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        # Sidebar (Right)
        self.sidebar = ttk.LabelFrame(container, text="Questions", padding=5)
        self.sidebar.pack(side="right", fill="y", padx=5, pady=5)
        self.grid_frame = ttk.Frame(self.sidebar)
        self.grid_frame.pack(fill="both", expand=True)
        
        legend = ttk.Frame(self.sidebar)
        legend.pack(fill="x", pady=10)
        tk.Label(legend, text="■ Current", fg="blue").pack(anchor="w")
        tk.Label(legend, text="■ Answered", fg="green").pack(anchor="w")
        tk.Label(legend, text="■ Marked", fg="orange").pack(anchor="w")

        # Content (Left)
        self.main_area = ttk.Frame(container, padding=10)
        self.main_area.pack(side="left", fill="both", expand=True)
        self.title_label = ttk.Label(self.main_area, text="", font=("Segoe UI", 14, "bold"))
        self.title_label.pack(anchor="w", pady=(0, 8))
        self.q_label = ttk.Label(self.main_area, text="", wraplength=700, justify="left", font=("Segoe UI", 11))
        self.q_label.pack(anchor="w", pady=(0, 10))

        self.opt_vars = [tk.IntVar(value=0) for _ in range(4)]
        self.check_buttons = []
        for i in range(4):
            cb = ttk.Checkbutton(self.main_area, text="", variable=self.opt_vars[i])
            cb.pack(anchor="w", pady=3)
            self.check_buttons.append(cb)

        # Bottom Nav
        nav = ttk.Frame(self.main_area) 
        nav.pack(fill="x", side="bottom", pady=20)
        self.progress_label = ttk.Label(nav, text="")
        self.progress_label.pack(side="left")

        ttk.Button(nav, text="Submit Exam", command=self.submit).pack(side="right", padx=6)
        ttk.Button(nav, text="Next >", command=self.next_q).pack(side="right", padx=6)
        ttk.Button(nav, text="< Prev", command=self.prev_q).pack(side="right", padx=6)
        self.btn_mark = tk.Button(nav, text="Mark for Review", bg="lightyellow", command=self.toggle_mark)
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
            btn = tk.Button(self.grid_frame, text=str(i + 1), width=4, command=lambda idx=i: self.jump_to(idx))
            btn.grid(row=i//cols, column=i%cols, padx=2, pady=2)
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
        self.timer_label.config(text=f"Time left: {mm:02d}:{ss:02d}")
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
        self.q_label.config(text=f"Q{self.index+1}: {q.text}")
        
        for i in range(4): self.check_buttons[i].config(text=q.options[i])
        saved = self.answers[self.index]
        for i in range(4): self.opt_vars[i].set(1 if i in saved else 0)
            
        self.progress_label.config(text=f"Question: {self.index+1}/{len(self.exam.questions)}")
        
        if self.index in self.marked_questions:
            self.btn_mark.config(text="Unmark Flag", bg="orange", fg="white")
        else:
            self.btn_mark.config(text="Mark for Review", bg="lightyellow", fg="black")

        for i, btn in enumerate(self.nav_buttons):
            bg, fg = "#f0f0f0", "black"
            if len(self.answers[i]) > 0: bg = "#90ee90"
            if i in self.marked_questions: bg = "orange"
            if i == self.index: bg, fg = "blue", "white"
            btn.config(bg=bg, fg=fg)

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
        if not messagebox.askyesno("Submit", f"Answered: {done}/{len(self.exam.questions)}\nSubmit now?"): return
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
        msg = f"Time over. Auto submit.\nScore: {total_score:.2f}" if auto else f"Submitted!\nScore: {total_score:.2f}"
        messagebox.showinfo("Done", msg)
        self.back()

    def back(self):
        self.stop_timer()
        self.app.show_frame("StudentFrame")


class ReviewFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.exam = None; self.attempt = None
        Header(self, "Review").pack(fill="x")
        
        top = ttk.Frame(self); top.pack(fill="x")
        self.info_label = ttk.Label(top, text="")
        self.info_label.pack(side="left")
        ttk.Button(top, text="Back", command=self.go_back).pack(side="right")
        
        self.text = tk.Text(self, wrap="word", height=32); self.text.pack(fill="both", expand=True)

    def load_review(self, exam, attempt, back_to):
        self.exam = exam; self.attempt = attempt; self.back_to = back_to
        self.render()

    def render(self):
        self.text.config(state="normal"); self.text.delete("1.0", tk.END)
        total_q = len(self.exam.questions)
        self.text.insert(tk.END, f"Score: {self.attempt.score:.2f}/{total_q}\n\n")
        
        for i, q in enumerate(self.exam.questions):
            user_sel = set(self.attempt.answers[i]) if i < len(self.attempt.answers) else set()
            correct = set(q.correct_indices)
            earned, _, _ = score_question_partial(user_sel, correct, 1.0)
            
            self.text.insert(tk.END, f"Q{i+1}: {q.text} (Earned: {earned:.2f})\n")
            for oi, opt in enumerate(q.options):
                mu = "[x]" if oi in user_sel else "[ ]"
                mc = "(correct)" if oi in correct else ""
                self.text.insert(tk.END, f"  {mu} {oi+1}. {opt} {mc}\n")
            self.text.insert(tk.END, "-"*40 + "\n")
        self.text.config(state="disabled")

    def go_back(self):
        self.app.show_frame(self.back_to)


class TeacherAttemptFrame(ReviewFrame):
    def load_attempt(self, attempt, back_to):
        self.attempt = attempt; self.back_to = back_to
        self.exam = self.app.store.get_exam(attempt.exam_id)
        self.render()


class TemplatePreviewFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.template_id = None
        Header(self, "Template Preview").pack(fill="x")
        ttk.Button(self, text="Back", command=self.go_back).pack(anchor="e")
        self.text = tk.Text(self); self.text.pack(fill="both", expand=True)

    def load_template(self, tid, back_to):
        self.template_id = tid; self.back_to = back_to
        t = self.app.store.get_template(tid)
        self.text.config(state="normal"); self.text.delete("1.0", tk.END)
        if t:
            self.text.insert(tk.END, f"Template: {t.title}\nQuestions: {len(t.questions)}\n\n")
            for i, q in enumerate(t.questions):
                self.text.insert(tk.END, f"Q{i+1}: {q.text}\n")
                for oi, opt in enumerate(q.options):
                    mark = " (correct)" if oi in q.correct_indices else ""
                    self.text.insert(tk.END, f"  {oi+1}. {opt}{mark}\n")
        self.text.config(state="disabled")

    def go_back(self): self.app.show_frame(self.back_to)


class ExamPreviewFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.exam_id = None
        Header(self, "Exam Preview").pack(fill="x")
        ttk.Button(self, text="Back", command=self.go_back).pack(anchor="e")
        self.text = tk.Text(self); self.text.pack(fill="both", expand=True)

    def load_exam(self, eid, back_to):
        self.exam_id = eid; self.back_to = back_to
        e = self.app.store.get_exam(eid)
        self.text.config(state="normal"); self.text.delete("1.0", tk.END)
        if e:
            self.text.insert(tk.END, f"Exam: {e.title}\nCode: {e.access_code}\n\n")
            for i, q in enumerate(e.questions):
                self.text.insert(tk.END, f"Q{i+1}: {q.text}\n")
                for oi, opt in enumerate(q.options):
                    mark = " (correct)" if oi in q.correct_indices else ""
                    self.text.insert(tk.END, f"  {oi+1}. {opt}{mark}\n")
        self.text.config(state="disabled")

    def go_back(self): self.app.show_frame(self.back_to)