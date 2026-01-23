# ui/student.py
import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import List, Set, Optional
import time
import random 
import ttkbootstrap as tb
from ttkbootstrap.scrolled import ScrolledText, ScrolledFrame
from ttkbootstrap.constants import *

from models import Exam, Attempt, score_question_partial
import utils
from .base import Header, info, err, is_valid_date_yyyy_mm_dd
from .auth import ask_change_password

# =============================================================================
# 1. STUDENT DASHBOARD
# =============================================================================

class StudentFrame(tb.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.full_name = tk.StringVar()
        self.dob = tk.StringVar()
        self.sid = tk.StringVar()
        self._build_ui()
        
    def _build_ui(self):
        Header(self, "Student Portal", "Enter exam code to start.").pack(fill="x")
        
        top = tb.Frame(self)
        top.pack(fill="x", pady=5)
        tb.Button(top, text="Reload", command=self.app.reload_data, bootstyle="info-outline").pack(side="right", padx=6)
        tb.Button(top, text="Logout", command=self.app.logout, bootstyle="secondary").pack(side="right")
        
        main = tb.Frame(self)
        main.pack(fill="both", expand=True, pady=10)
        
        # Left: Take Exam
        left = tb.Labelframe(main, text=" Take Exam ", padding=15, bootstyle="success")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Right: Profile & History
        right = tb.Labelframe(main, text=" Profile & History ", padding=15, bootstyle="info")
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        # Input Code Form
        lf = tb.Frame(left); lf.pack(fill="x", pady=20)
        tb.Label(lf, text="EXAM CODE:", font=("Segoe UI", 12, "bold")).pack(anchor="w")
        self.code_var = tk.StringVar()
        tb.Entry(lf, textvariable=self.code_var, width=25, font=("Consolas", 14)).pack(fill="x", pady=10)
        tb.Button(lf, text="FIND EXAM", command=self.open_by_code, bootstyle="success", width=100).pack(pady=10)

        # Profile Form
        pf = tb.Frame(right); pf.pack(fill="x")
        tb.Label(pf, text="Full Name:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(pf, textvariable=self.full_name, width=30).grid(row=0, column=1, sticky="w", padx=6, pady=6)
        
        tb.Label(pf, text="DOB:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(pf, textvariable=self.dob, width=30).grid(row=1, column=1, sticky="w", padx=6, pady=6)
        
        tb.Label(pf, text="Student ID:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(pf, textvariable=self.sid, width=30).grid(row=2, column=1, sticky="w", padx=6, pady=6)
        
        tb.Button(pf, text="Update Profile", command=self.update_profile, bootstyle="primary-outline").grid(row=3, column=1, sticky="e", pady=(10,5))
        tb.Button(pf, text="Change Password", command=self.change_password, bootstyle="warning-outline").grid(row=4, column=1, sticky="e", pady=(0,10))

        # History List
        tb.Separator(right).pack(fill="x", padx=10, pady=6)
        tb.Label(right, text="Exam History:", bootstyle="inverse-light").pack(anchor="w", padx=10)
        self.attempt_list = tk.Listbox(right, height=10, font=("Segoe UI", 9))
        self.attempt_list.pack(fill="both", expand=True, padx=10, pady=(6, 10))
        tb.Button(right, text="Review Selected", command=self.review_selected, bootstyle="info").pack(pady=(0, 10))

    def on_show(self):
        if not self.app.current_user or self.app.current_user.role != "Student":
            self.app.logout()
            return
        u = self.app.store.find_user(self.app.current_user.username)
        if u: self.app.current_user = u
        self.full_name.set(self.app.current_user.full_name)
        self.dob.set(self.app.current_user.dob)
        self.sid.set(self.app.current_user.student_id)
        self.refresh_attempts()

    def update_profile(self):
        dob = self.dob.get().strip()
        if dob and (not is_valid_date_yyyy_mm_dd(dob)):
            return err("Invalid date format. Correct format: YYYY-MM-DD")
        self.app.store.update_profile(
            self.app.current_user.username,
            self.full_name.get().strip(),
            dob,
            self.sid.get().strip()
        )
        info("Profile updated.")
        self.refresh_attempts()

    def change_password(self):
        data = ask_change_password(self)
        if data is None: return
        old_pw, new_pw, confirm = data
        cur = self.app.store.find_user(self.app.current_user.username)
        if not cur or (cur.password != (old_pw or "")):
            return err("Current password incorrect.")
        new_pw = (new_pw or "").strip()
        if not new_pw: return err("New password cannot be empty.")
        if new_pw != (confirm or ""): return err("New passwords do not match.")
        okp, msgp = utils.validate_strong_password(new_pw)
        if not okp: return err(msgp)
        ok = self.app.store.update_password(self.app.current_user.username, new_pw)
        if not ok: return err("Cannot change password.")
        u = self.app.store.find_user(self.app.current_user.username)
        if u: self.app.current_user = u
        info("Password changed successfully!")

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
        if not code: return err("Please enter exam code.")
        exam = self.app.store.get_exam_by_code(code)
        if not exam: return err("Exam not found.")

        now = int(time.time())
        if now < exam.start_ts: return err(f"Exam not yet open.\nStarts: {utils.fmt_dt(exam.start_ts)}")
        if now > exam.end_ts: return err(f"Exam closed.\nEnded: {utils.fmt_dt(exam.end_ts)}")
        
        if exam.attempt_limit > 0:
            used = self.app.store.count_attempts_for_user_exam(self.app.current_user.username, exam.exam_id)
            if used >= exam.attempt_limit: return err("No attempts remaining.")

        if exam.password:
            pw = simpledialog.askstring("Password", "Exam requires password:", show="*")
            if pw != exam.password: return err("Incorrect password.")

        self.app.frames["ExamTakeFrame"].load_exam(exam)
        self.app.show_frame("ExamTakeFrame")

    def review_selected(self):
        sel = self.attempt_list.curselection()
        if not sel: return err("Select an attempt to review.")
        attempts = self.app.store.list_attempts_for_user(self.app.current_user.username)
        attempt = attempts[sel[0]]
        exam = self.app.store.get_exam(attempt.exam_id)
        if not exam: return err("Original exam data deleted.")
        if not exam.allow_review: return err("Teacher does not allow review.")
        self.app.frames["ReviewFrame"].load_review(exam, attempt, back_to="StudentFrame")
        self.app.show_frame("ReviewFrame")

# =============================================================================
# 2. EXAM TAKE SCREEN
# =============================================================================

class ExamTakeFrame(tb.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.exam: Optional[Exam] = None
        self.current_attempt: Optional[Attempt] = None 
        
        # State variables
        self.index = 0
        self.answers: List[Set[int]] = []
        self.marked_questions: Set[int] = set()
        self.started_at: float = 0.0
        self.end_time: float = 0.0
        self._timer_job = None
        self._auto_submitted = False
        
        # Shuffled indices list
        self.shuffled_indices: List[int] = []
        
        # --- ANTI-CHEAT VARIABLES ---
        self.violation_count = 0
        self.MAX_VIOLATIONS = 3
        self.is_monitoring = False
        self._processing_alert = False # Flag to block alert loops
        self._is_submitting = False    # Flag to block check during submit
        
        # Containers
        self.intro_view = tb.Frame(self)
        self.taking_view = tb.Frame(self)
        self.result_view = tb.Frame(self)
        
        self._build_intro_ui()
        self._build_taking_ui()
        self._build_result_ui()

    # ------------------ 1. INTRO UI ------------------
    def _build_intro_ui(self):
        top = tb.Frame(self.intro_view)
        top.pack(fill="x", pady=10, padx=20)
        tb.Button(top, text="← Back", command=self.back, bootstyle="link").pack(side="left")
        
        center = tb.Frame(self.intro_view)
        center.pack(expand=True, fill="both", padx=50, pady=20)
        
        self.intro_title = tb.Label(center, text="EXAM TITLE", font=("Segoe UI", 24, "bold"), justify="center")
        self.intro_title.pack(pady=(20, 30))
        
        card = tb.Frame(center, bootstyle="light", padding=30)
        card.pack(fill="x", padx=50)
        
        info_grid = tb.Frame(card)
        info_grid.pack(pady=20)
        
        self.lbl_time = tb.Label(info_grid, text="🕒 Time: -- min", font=("Segoe UI", 12))
        self.lbl_time.grid(row=0, column=0, padx=40, pady=10, sticky="w")
        
        self.lbl_qs = tb.Label(info_grid, text="❓ Questions: --", font=("Segoe UI", 12))
        self.lbl_qs.grid(row=0, column=1, padx=40, pady=10, sticky="w")
        
        self.lbl_attempts = tb.Label(info_grid, text="👤 Attempts: 0", font=("Segoe UI", 12))
        self.lbl_attempts.grid(row=1, column=0, padx=40, pady=10, sticky="w")
        
        self.lbl_score = tb.Label(info_grid, text="💯 Scale: 10", font=("Segoe UI", 12))
        self.lbl_score.grid(row=1, column=1, padx=40, pady=10, sticky="w")
        
        # Anti-cheat warning
        self.lbl_monitor_warning = tb.Label(card, text="⚠️ Proctoring Mode: Switching tabs/exiting fullscreen will trigger warnings!", 
                 font=("Segoe UI", 10, "italic"), foreground="red")
        self.lbl_monitor_warning.pack(pady=(10, 0))

        tb.Button(card, text="START EXAM", command=self.start_exam_now, bootstyle="warning", width=30) \
          .pack(pady=(20, 0), ipady=10)
        
        hist_frame = tb.Frame(center)
        hist_frame.pack(fill="both", expand=True, pady=40, padx=50)
        
        tb.Label(hist_frame, text="Your History:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        self.hist_tree = tb.Treeview(hist_frame, columns=("time", "score", "dur"), show="headings", height=5)
        self.hist_tree.heading("time", text="Submitted")
        self.hist_tree.heading("score", text="Score")
        self.hist_tree.heading("dur", text="Duration")
        self.hist_tree.column("time", width=200); self.hist_tree.column("score", anchor="center"); self.hist_tree.column("dur", anchor="center")
        self.hist_tree.pack(fill="both", expand=True)

    # ------------------ 2. TAKING UI ------------------
    def _build_taking_ui(self):
        top = tb.Frame(self.taking_view, bootstyle="light")
        top.pack(fill="x", side="top", pady=(0, 5))
        self.timer_label = tb.Label(top, text="--:--", font=("Segoe UI", 14, "bold"), bootstyle="danger")
        self.timer_label.pack(side="left", padx=20, pady=5)
        
        self.violation_label = tb.Label(top, text="", font=("Segoe UI", 12, "bold"), foreground="red")
        self.violation_label.pack(side="right", padx=20)

        container = tb.Frame(self.taking_view)
        container.pack(fill="both", expand=True)

        self.sidebar = tb.Labelframe(container, text=" Map ", padding=10)
        self.sidebar.pack(side="right", fill="y", padx=10, pady=5)
        self.grid_frame = tb.Frame(self.sidebar)
        self.grid_frame.pack(fill="both", expand=True)
        
        # LEGEND (FULL BOX)
        legend = tb.Frame(self.sidebar)
        legend.pack(fill="x", pady=20)
        
        def add_legend_item(label_text, boot_style):
            row = tb.Frame(legend)
            row.pack(fill="x", pady=3)
            # Small button for color box
            btn = tb.Button(row, text="", width=3, bootstyle=boot_style, state="disabled")
            btn.pack(side="left")
            lbl = tb.Label(row, text=label_text)
            lbl.pack(side="left", padx=10)

        # Update legend logic
        legend = tb.Frame(self.sidebar)
        legend.pack(fill="x", pady=20)
        tb.Label(legend, text="■ Current (Blue)", foreground="#0d6efd").pack(anchor="w")
        tb.Label(legend, text="■ Answered (Green)", foreground="#198754").pack(anchor="w")
        tb.Label(legend, text="■ Marked (Yellow)", foreground="#ffc107").pack(anchor="w")
        tb.Label(legend, text="■ Unanswered (Gray)", foreground="gray").pack(anchor="w")
        
        self.nav_frame = tb.Frame(self.taking_view)
        self.nav_frame.pack(side="bottom", fill="x", pady=10)
        
        self.progress_label = tb.Label(self.nav_frame, text="", font=("Segoe UI", 10, "italic"))
        self.progress_label.pack(side="left", padx=20)

        tb.Button(self.nav_frame, text="SUBMIT", command=self.submit, bootstyle="success").pack(side="right", padx=6)
        tb.Button(self.nav_frame, text="Next >", command=self.next_q, bootstyle="primary-outline").pack(side="right", padx=6)
        tb.Button(self.nav_frame, text="< Prev", command=self.prev_q, bootstyle="secondary-outline").pack(side="right", padx=6)
        self.btn_mark = tb.Button(self.nav_frame, text="Mark", command=self.toggle_mark, bootstyle="warning-outline")
        self.btn_mark.pack(side="right", padx=20)

        self.main_scroll = ScrolledFrame(container, autohide=True, padding=20)
        self.main_scroll.pack(side="left", fill="both", expand=True)
        
        self.title_label = tb.Label(self.main_scroll, text="", font=("Segoe UI", 16, "bold"), bootstyle="primary")
        self.title_label.pack(anchor="w", pady=(0, 10), fill="x")
        
        self.q_label = tb.Label(self.main_scroll, text="", font=("Segoe UI", 13), justify="left", anchor="w")
        self.q_label.pack(anchor="w", pady=(0, 5), fill="x")
        
        self.note_label = tb.Label(self.main_scroll, text="", font=("Segoe UI", 10, "italic"), foreground="gray")
        self.note_label.pack(anchor="w", pady=(0, 20))

        self.options_frame = tb.Frame(self.main_scroll)
        self.options_frame.pack(fill="x", expand=True)
        
        self.radio_var = tk.IntVar(value=-1)
        self.check_vars = [tk.IntVar(value=0) for _ in range(4)]
        self.nav_buttons = []
        self.main_scroll.bind("<Configure>", self._on_frame_configure)

    # ------------------ 3. RESULT UI ------------------
    def _build_result_ui(self):
        top = tb.Frame(self.result_view)
        top.pack(fill="x", pady=10, padx=20)
        tb.Button(top, text="← Home", command=self.back, bootstyle="link").pack(side="left")

        center = tb.Frame(self.result_view)
        center.pack(expand=True, fill="both", padx=50, pady=20)

        tb.Label(center, text="Your exam has been submitted", font=("Segoe UI", 18), justify="center").pack(pady=(0, 20))

        card = tb.Frame(center, bootstyle="light", padding=40)
        card.pack(padx=100, pady=10)

        row1 = tb.Frame(card)
        row1.pack(fill="x", pady=(0, 20))
        
        self.res_time_lbl = tb.Label(row1, text="🕒 Duration: --", font=("Segoe UI", 11))
        self.res_time_lbl.pack(side="left", padx=20)
        
        self.res_correct_lbl = tb.Label(row1, text="❓ Correct: --/--", font=("Segoe UI", 11))
        self.res_correct_lbl.pack(side="right", padx=20)

        tb.Label(card, text="Your Score:", font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))
        self.res_score_lbl = tb.Label(card, text="0", font=("Segoe UI", 48, "bold"), foreground="#d9534f") 
        self.res_score_lbl.pack(pady=(0, 20))

        tb.Button(card, text="VIEW DETAILED ANSWERS", command=self.view_detailed_result, bootstyle="warning", width=25) \
          .pack(ipady=8)

    # ------------------ LOGIC ------------------

    def load_exam(self, exam: Exam):
        self.stop_timer()
        self.stop_monitoring() 
        self.exam = exam
        
        self.index = 0
        self.answers = [set() for _ in range(len(exam.questions))]
        self.marked_questions = set()
        self._auto_submitted = False
        
        # Create shuffled list
        self.shuffled_indices = list(range(len(exam.questions)))
        random.shuffle(self.shuffled_indices)
        
        self.intro_title.config(text=exam.title)
        self.lbl_time.config(text=f"🕒 Time: {exam.duration_seconds // 60} min")
        self.lbl_qs.config(text=f"❓ Questions: {len(exam.questions)}")
        
        attempts = self.app.store.list_attempts_for_user(self.app.current_user.username)
        my_attempts = [a for a in attempts if a.exam_id == exam.exam_id]
        self.lbl_attempts.config(text=f"👤 Attempts: {len(my_attempts)}")

        if self.exam.enable_monitoring:
            self.lbl_monitor_warning.pack(pady=(10, 0))
        else:
            self.lbl_monitor_warning.pack_forget()
        
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)
        for a in my_attempts:
            score10 = (a.score / max(1, a.total)) * 10.0
            took = f"{a.time_taken_seconds // 60}m {a.time_taken_seconds % 60}s"
            self.hist_tree.insert("", "end", values=(utils.fmt_dt_full(a.submitted_at), f"{score10:.2f}/10", took))

        self.taking_view.pack_forget()
        self.result_view.pack_forget()
        self.intro_view.pack(fill="both", expand=True)

    def start_exam_now(self):
        self.intro_view.pack_forget()
        self.result_view.pack_forget()
        self.taking_view.pack(fill="both", expand=True)
        
        self.started_at = time.time()
        self.end_time = self.started_at + self.exam.duration_seconds
        
        self.violation_count = 0
        self._processing_alert = False
        self._is_submitting = False
        
        if self.exam.enable_monitoring:
            self.violation_label.config(text=f"Violations: 0/{self.MAX_VIOLATIONS}")
            self.violation_label.pack(side="right", padx=20)
        else:
            self.violation_label.pack_forget()
        
        self.create_nav_grid()
        self.render()
        self._tick()
        
        if self.exam.enable_monitoring:
            self.start_monitoring()

    # --- ANTI-CHEAT METHODS ---
    def start_monitoring(self):
        self.is_monitoring = True
        self.app.attributes("-fullscreen", True) 
        self.app.attributes("-topmost", True)    
        # Wait 2 seconds for UI to stabilize
        self.after(2000, lambda: self.app.bind("<FocusOut>", self.on_focus_out))

    def stop_monitoring(self):
        self.is_monitoring = False
        self.app.attributes("-fullscreen", False)
        self.app.attributes("-topmost", False)
        self.app.unbind("<FocusOut>")

    def on_focus_out(self, event):
        if str(event.widget) != str(self.app): return
        if not self.is_monitoring or not self.taking_view.winfo_ismapped(): return
        if getattr(self, "_is_submitting", False): return
        if getattr(self, "_processing_alert", False): return

        self._processing_alert = True
        self.violation_count += 1
        self.violation_label.config(text=f"Violations: {self.violation_count}/{self.MAX_VIOLATIONS}")
        
        messagebox.showwarning("CHEATING WARNING", 
                               f"You left the exam screen!\n"
                               f"Violation {self.violation_count}.\n"
                               f"If exceeding {self.MAX_VIOLATIONS} times, exam will be auto-submitted.")
        
        self.app.focus_force()
        if self.violation_count >= self.MAX_VIOLATIONS:
            self.submit(auto_cheat=True)
        
        self.after(1000, lambda: setattr(self, "_processing_alert", False))

    # ---------------------------

    def show_result_screen(self, attempt: Attempt):
        self.stop_timer()
        self.stop_monitoring() 
        self.current_attempt = attempt
        
        score10 = (attempt.score / max(1, attempt.total)) * 10.0
        correct_count = 0
        for i, q in enumerate(self.exam.questions):
            user_ans = set(attempt.answers[i]) if i < len(attempt.answers) else set()
            if user_ans == set(q.correct_indices):
                correct_count += 1

        minutes = attempt.time_taken_seconds // 60
        seconds = attempt.time_taken_seconds % 60
        
        self.res_time_lbl.config(text=f"🕒 Duration: {minutes} min {seconds} sec")
        self.res_correct_lbl.config(text=f"❓ Correct: {correct_count} / {attempt.total}")
        self.res_score_lbl.config(text=f"{score10:.2f}")

        self.taking_view.pack_forget()
        self.intro_view.pack_forget()
        self.result_view.pack(fill="both", expand=True)

    def view_detailed_result(self):
        if not self.exam or not self.current_attempt: return
        if not self.exam.allow_review:
            messagebox.showwarning("Notice", "Teacher does not allow detailed review.")
            return
        self.app.frames["ReviewFrame"].load_review(self.exam, self.current_attempt, back_to="StudentFrame")
        self.app.show_frame("ReviewFrame")

    def _on_frame_configure(self, event):
        new_wrap = event.width - 50
        if new_wrap > 100:
            self.q_label.configure(wraplength=new_wrap)

    def create_nav_grid(self):
        for w in self.grid_frame.winfo_children(): w.destroy()
        self.nav_buttons = []
        if not self.exam: return
        cols = 5
        for i in range(len(self.exam.questions)):
            # Use normal grid index, color will be updated later
            btn = tb.Button(self.grid_frame, text=str(i + 1), width=3, 
                            command=lambda idx=i: self.jump_to(idx),
                            bootstyle="secondary-outline")
            btn.grid(row=i//cols, column=i%cols, padx=3, pady=3)
            self.nav_buttons.append(btn)

    def jump_to(self, target):
        self.index = target
        self.render()

    def toggle_mark(self):
        if self.index in self.marked_questions: self.marked_questions.remove(self.index)
        else: self.marked_questions.add(self.index)
        self.render()

    def _save_multi_select(self):
        if not self.exam: return
        # Save to real index
        real_idx = self.shuffled_indices[self.index]
        selected = {i for i in range(4) if self.check_vars[i].get() == 1}
        self.answers[real_idx] = selected
        self.render_nav_buttons()

    def _save_single_select(self):
        if not self.exam: return
        # Save to real index
        real_idx = self.shuffled_indices[self.index]
        val = self.radio_var.get()
        if val != -1:
            self.answers[real_idx] = {val}
        self.render_nav_buttons()

    def stop_timer(self):
        if self._timer_job:
            self.after_cancel(self._timer_job)
            self._timer_job = None

    def _tick(self):
        if not self.exam: return
        if not self.taking_view.winfo_ismapped(): return

        left = int(self.end_time - time.time())
        mm, ss = max(0, left) // 60, max(0, left) % 60
        self.timer_label.config(text=f"Time: {mm:02d}:{ss:02d}")
        if left < 300: 
            self.timer_label.configure(bootstyle="danger")
        else:
            self.timer_label.configure(bootstyle="success")

        if left <= 0 and not self._auto_submitted:
            self._auto_submitted = True
            self._submit_internal(auto=True)
            return
        self._timer_job = self.after(1000, self._tick)

    def render(self):
        if not self.exam: return
        
        # Get real question content from shuffled list
        real_idx = self.shuffled_indices[self.index]
        q = self.exam.questions[real_idx]
        
        self.title_label.config(text=f"{self.exam.title}")
        self.q_label.config(text=f"Q {self.index+1}: {q.text}")
        
        self.update_idletasks()
        self.q_label.configure(wraplength=self.main_scroll.winfo_width() - 50)

        is_multiselect = len(q.correct_indices) > 1

        for widget in self.options_frame.winfo_children():
            widget.destroy()

        # Get answer from real index
        current_ans_set = self.answers[real_idx]

        if is_multiselect:
            self.note_label.config(text="(Select all correct answers)", foreground="#d9534f")
            for i in range(4):
                val = 1 if i in current_ans_set else 0
                self.check_vars[i].set(val)
                cb = tb.Checkbutton(
                    self.options_frame,
                    text=q.options[i],
                    variable=self.check_vars[i],
                    bootstyle="square-toggle",
                    command=self._save_multi_select
                )
                cb.pack(anchor="w", pady=8, fill="x")
        else:
            self.note_label.config(text="(Select 1 correct answer)", foreground="#0275d8")
            if current_ans_set:
                self.radio_var.set(list(current_ans_set)[0])
            else:
                self.radio_var.set(-1)

            for i in range(4):
                rb = tb.Radiobutton(
                    self.options_frame,
                    text=q.options[i],
                    variable=self.radio_var,
                    value=i,
                    bootstyle="info",
                    command=self._save_single_select
                )
                rb.pack(anchor="w", pady=8, fill="x")

        self.progress_label.config(text=f"Q: {self.index+1} / {len(self.exam.questions)}")
        
        if self.index in self.marked_questions:
            self.btn_mark.configure(bootstyle="warning", text="Unmark")
        else:
            self.btn_mark.configure(bootstyle="warning-outline", text="Mark")
            
        self.render_nav_buttons()

    def render_nav_buttons(self):
        for i, btn in enumerate(self.nav_buttons):
            # i here is display index, need real_idx to check status
            real_idx = self.shuffled_indices[i]
            
            has_answer = len(self.answers[real_idx]) > 0
            is_marked = i in self.marked_questions
            is_current = (i == self.index)
            
            # Default: Gray outline (Unanswered)
            style = "secondary-outline"

            # If current: Blue (Solid)
            if is_current:
                style = "primary"

            # Rule 1: Answered -> Green (Solid)
            if has_answer:
                style = "success"
                
            # Rule 2: Marked -> Orange (Solid) - Highest priority
            if is_marked:
                style = "warning"
            
            btn.configure(bootstyle=style)

    def next_q(self):
        if self.index < len(self.exam.questions) - 1:
            self.index += 1
            self.render()

    def prev_q(self):
        if self.index > 0:
            self.index -= 1
            self.render()

    def submit(self, auto_cheat=False):
        self._is_submitting = True
        try:
            if not auto_cheat:
                done = sum(1 for a in self.answers if len(a) > 0)
                if not messagebox.askyesno("Submit Exam", f"You answered: {done}/{len(self.exam.questions)}\nSubmit now?"):
                    self._is_submitting = False
                    return
        except Exception:
            self._is_submitting = False
            return
        
        if auto_cheat:
            messagebox.showerror("Regulation Violation", "System auto-submitted due to violations.")

        self._submit_internal(auto=False)

    def _submit_internal(self, auto):
        total_score = 0.0
        # self.answers contains answers at real index.
        # self.exam.questions also at real index.
        # zipping them works perfectly -> calculate score.
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
        
        if auto:
            messagebox.showinfo("Time's up", "System auto-submitted exam.")
        
        self.show_result_screen(a)

    def back(self):
        self.stop_timer()
        self.stop_monitoring() 
        self.app.show_frame("StudentFrame")

# =============================================================================
# 3. REVIEW SCREEN
# =============================================================================

class ReviewFrame(tb.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.exam = None; self.attempt = None; self.back_to = None
        Header(self, "Review Exam").pack(fill="x")
        
        top = tb.Frame(self); top.pack(fill="x", pady=10)
        tb.Button(top, text="< Back", command=self.go_back, bootstyle="secondary").pack(side="right", padx=20)
        
        self.text = ScrolledText(self, wrap="word", height=20, font=("Segoe UI", 11), bootstyle="round")
        self.text.pack(fill="both", expand=True, padx=10, pady=10)

    def load_review(self, exam, attempt, back_to):
        self.exam = exam; self.attempt = attempt; self.back_to = back_to
        self.render()

    def render(self):
        self.text.text.config(state="normal")
        self.text.delete("1.0", tk.END)
        
        total_q = len(self.exam.questions)
        self.text.insert(tk.END, f"Score: {self.attempt.score:.2f} / {total_q}\n", "h1")
        self.text.tag_config("h1", font=("Segoe UI", 16, "bold"), foreground="#2C3E50")
        self.text.insert(tk.END, "-"*60 + "\n\n")
        
        for i, q in enumerate(self.exam.questions):
            user_sel = set(self.attempt.answers[i]) if i < len(self.attempt.answers) else set()
            correct = set(q.correct_indices)
            earned, _, _ = score_question_partial(user_sel, correct, 1.0)
            
            self.text.insert(tk.END, f"Question {i+1}: {q.text} ", "q_title")
            self.text.insert(tk.END, f"(Points: {earned:.2f})\n", "points")
            
            for oi, opt in enumerate(q.options):
                mu = "[x]" if oi in user_sel else "[ ]"
                mc = "  <-- CORRECT" if oi in correct else ""
                
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