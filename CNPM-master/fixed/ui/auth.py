# ui/auth.py
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from .base import info, err
import utils
from models import ROLES, ROLE_CANON

class PasswordChangeDialog(tk.Toplevel):
    """Modal dialog to change password: current, new, confirm."""
    def __init__(self, parent, title="Đổi mật khẩu"):
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

        tb.Label(frm, text="Mật khẩu hiện tại:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(frm, textvariable=self.old_var, show="*", width=28).grid(row=0, column=1, padx=6, pady=6)

        tb.Label(frm, text="Mật khẩu mới:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(frm, textvariable=self.new_var, show="*", width=28).grid(row=1, column=1, padx=6, pady=6)

        tb.Label(frm, text="Nhập lại mật khẩu mới:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(frm, textvariable=self.cf_var, show="*", width=28).grid(row=2, column=1, padx=6, pady=6)

        btns = tb.Frame(frm)
        btns.grid(row=3, column=0, columnspan=2, pady=(12, 0), sticky="e")
        tb.Button(btns, text="Hủy", bootstyle="secondary", command=self._cancel).pack(side="right", padx=6)
        tb.Button(btns, text="Xác nhận", bootstyle="success", command=self._ok).pack(side="right")

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
        tb.Label(bg_frame, text="HỆ THỐNG THI TRẮC NGHIỆM", font=("Segoe UI", 24, "bold"), bootstyle="primary").pack(pady=(0, 5))
        tb.Label(bg_frame, text="Đăng nhập để tiếp tục", font=("Segoe UI", 12), bootstyle="secondary").pack(pady=(0, 30))

        form = tb.Labelframe(bg_frame, text=" Thông tin đăng nhập ", padding=25, bootstyle="primary")
        form.pack(fill="x", pady=10)

        tb.Label(form, text="Vai trò:", font=("Segoe UI", 10)).pack(anchor="w", pady=(5,0))
        self.role_var = tk.StringVar(value=ROLES[0])
        tb.Combobox(form, textvariable=self.role_var, values=ROLES, state="readonly", font=("Segoe UI", 10)).pack(fill="x", pady=(0, 15))

        tb.Label(form, text="Tài khoản:", font=("Segoe UI", 10)).pack(anchor="w", pady=(5,0))
        self.user_var = tk.StringVar()
        self.user_entry = tb.Entry(form, textvariable=self.user_var, font=("Segoe UI", 10))
        self.user_entry.pack(fill="x", pady=(0, 15))

        tb.Label(form, text="Mật khẩu:", font=("Segoe UI", 10)).pack(anchor="w", pady=(5,0))
        self.pass_var = tk.StringVar()
        self.pass_entry = tb.Entry(form, textvariable=self.pass_var, show="*", font=("Segoe UI", 10))
        self.pass_entry.pack(fill="x", pady=(0, 15))

        tb.Button(form, text="ĐĂNG NHẬP", command=self.do_login, bootstyle="primary", width=100).pack(pady=(10, 5))
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
            err("Vui lòng nhập đầy đủ thông tin.")
            return

        u = self.app.store.find_user(username)
        if not u:
            err("Người dùng không tồn tại.")
            return
        # LƯU Ý: Ở đây bạn nên thêm mã hóa mật khẩu sau này
        if u.password != password:
            err("Sai mật khẩu.")
            return

        u.role = ROLE_CANON.get(u.role.lower(), u.role)
        if u.role != role:
            messagebox.showwarning("Sai vai trò", f"Bạn chọn: {role}. Tài khoản thực tế là: {u.role}.")
            self.role_var.set(u.role)
            role = u.role

        self.app.current_user = u
        info(f"Đăng nhập thành công!\nXin chào {u.full_name or u.username} ({u.role}).")

        if getattr(u, 'must_change_password', False):
            while True:
                data = ask_change_password(self)
                if data is None:
                    err("Bạn bắt buộc phải đổi mật khẩu lần đầu.")
                    continue
                old_pw, new_pw, confirm = data
                if (old_pw or "") != (u.password or ""):
                    err("Mật khẩu hiện tại không đúng.")
                    continue
                if new_pw != (confirm or ""):
                    err("Mật khẩu mới không khớp.")
                    continue
                ok2, msg2 = utils.validate_strong_password(new_pw)
                if not ok2:
                    err(msg2)
                    continue
                self.app.store.update_password(u.username, new_pw)
                self.app.store.set_must_change_password(u.username, False)
                u = self.app.store.find_user(u.username) or u
                self.app.current_user = u
                info("Đổi mật khẩu thành công!")
                break

        if u.role == "Admin": self.app.show_frame("AdminFrame")
        elif u.role == "Teacher": self.app.show_frame("TeacherFrame")
        else: self.app.show_frame("StudentFrame")