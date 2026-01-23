# ui/auth.py
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from .base import info, err
import utils
from models import ROLES, ROLE_CANON

class PasswordChangeDialog(tk.Toplevel):
    """Modal dialog to change password: current, new, confirm."""
    def __init__(self, parent, title="Change Password"):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None  # (old, new, confirm) or None
        self.transient(parent)
        self.grab_set()

        frm = tb.Frame(self, padding=15)
        frm.pack(fill="both", expand=True)

        self.old_var = tk.StringVar()
        self.new_var = tk.StringVar()
        self.cf_var = tk.StringVar()

        tb.Label(frm, text="Current Password:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(frm, textvariable=self.old_var, show="*", width=28).grid(row=0, column=1, padx=6, pady=6)

        tb.Label(frm, text="New Password:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(frm, textvariable=self.new_var, show="*", width=28).grid(row=1, column=1, padx=6, pady=6)

        tb.Label(frm, text="Confirm New Password:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(frm, textvariable=self.cf_var, show="*", width=28).grid(row=2, column=1, padx=6, pady=6)

        btns = tb.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, pady=(12, 0), sticky="e")
        tb.Button(btns, text="Cancel", bootstyle="secondary", command=self._cancel).pack(side="right", padx=6)
        tb.Button(btns, text="Confirm", bootstyle="success", command=self._ok).pack(side="right")

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self._cancel())
        self.after(50, lambda: self.focus_force())

    def _ok(self):
        self.result = (self.old_var.get(), self.new_var.get(), self.cf_var.get())
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()

def ask_change_password(parent) -> tuple | None:
    dlg = PasswordChangeDialog(parent)
    parent.wait_window(dlg)
    return dlg.result

class LoginFrame(tb.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        bg_frame = tb.Frame(self)
        bg_frame.place(relx=0.5, rely=0.5, anchor="center")

        tb.Label(bg_frame, text="🎓", font=("Segoe UI Emoji", 64)).pack(pady=(0, 10))
        tb.Label(bg_frame, text="MULTIPLE CHOICE EXAM SYSTEM", font=("Segoe UI", 24, "bold"), bootstyle="primary").pack(pady=(0, 5))
        tb.Label(bg_frame, text="Login to continue", font=("Segoe UI", 12), bootstyle="secondary").pack(pady=(0, 30))

        form = tb.Labelframe(bg_frame, text=" Login Information ", padding=25, bootstyle="primary")
        form.pack(fill="x", pady=10)

        tb.Label(form, text="Role:", font=("Segoe UI", 10)).pack(anchor="w", pady=(5,0))
        self.role_var = tk.StringVar(value=ROLES[0])
        tb.Combobox(form, textvariable=self.role_var, values=ROLES, state="readonly", font=("Segoe UI", 10)).pack(fill="x", pady=(0, 15))

        tb.Label(form, text="Username:", font=("Segoe UI", 10)).pack(anchor="w", pady=(5,0))
        self.user_var = tk.StringVar()
        self.user_entry = tb.Entry(form, textvariable=self.user_var, font=("Segoe UI", 10))
        self.user_entry.pack(fill="x", pady=(0, 15))

        tb.Label(form, text="Password:", font=("Segoe UI", 10)).pack(anchor="w", pady=(5,0))
        self.pass_var = tk.StringVar()
        self.pass_entry = tb.Entry(form, textvariable=self.pass_var, show="*", font=("Segoe UI", 10))
        self.pass_entry.pack(fill="x", pady=(0, 15))

        tb.Button(form, text="LOGIN", command=self.do_login, bootstyle="primary", width=100).pack(pady=(10, 5))
        self.user_entry.focus_set()
        self.bind_all("<Return>", self._enter_login)

    def _enter_login(self, event):
        if self.winfo_ismapped():
            self.do_login()

    def do_login(self):
        role = self.role_var.get().strip()
        username = self.user_var.get().strip()
        password = self.pass_var.get()

        if role not in ROLES or not username or not password:
            err("Please enter all information.")
            return

        u = self.app.store.find_user(username)
        if not u:
            err("User does not exist.")
            return
        # NOTE: Passwords should be hashed in production
        if u.password != password:
            err("Incorrect password.")
            return

        u.role = ROLE_CANON.get(u.role.lower(), u.role)
        if u.role != role:
            messagebox.showwarning("Wrong Role", f"You selected: {role}. Actual role is: {u.role}.")
            self.role_var.set(u.role)
            role = u.role

        self.app.current_user = u
        info(f"Login successful!\nWelcome {u.full_name or u.username} ({u.role}).")

        if getattr(u, 'must_change_password', False):
            while True:
                data = ask_change_password(self)
                if data is None:
                    err("You must change your password on first login.")
                    continue
                old_pw, new_pw, confirm = data
                if (old_pw or "") != (u.password or ""):
                    err("Current password is incorrect.")
                    continue
                if new_pw != (confirm or ""):
                    err("New passwords do not match.")
                    continue
                ok2, msg2 = utils.validate_strong_password(new_pw)
                if not ok2:
                    err(msg2)
                    continue
                self.app.store.update_password(u.username, new_pw)
                self.app.store.set_must_change_password(u.username, False)
                u = self.app.store.find_user(u.username) or u
                self.app.current_user = u
                info("Password changed successfully!")
                break

        if u.role == "Admin": self.app.show_frame("AdminFrame")
        elif u.role == "Teacher": self.app.show_frame("TeacherFrame")
        else: self.app.show_frame("StudentFrame")