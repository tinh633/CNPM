# ui/admin.py
import tkinter as tk
from tkinter import messagebox, simpledialog
import ttkbootstrap as tb
import utils
from models import User, ROLES
from .base import Header, info, err

class AdminFrame(tb.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        Header(self, "Admin Dashboard", "User and system management.").pack(fill="x")

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
        right = tb.Labelframe(main, text=" Management ", padding=15, bootstyle="info")
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

        # --- Create User Form ---
        self.new_user = tk.StringVar()
        self.new_role = tk.StringVar(value="Student")
        f = tb.Frame(left)
        f.pack(fill="x")
        tb.Label(f, text="Username (ID):").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(f, textvariable=self.new_user, width=28).grid(row=0, column=1, padx=6, pady=6, sticky="w")
        tb.Label(f, text="Role:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        tb.Combobox(f, textvariable=self.new_role, values=ROLES, state="readonly", width=26).grid(row=2, column=1, padx=6, pady=6, sticky="w")
        tb.Button(f, text="Create User", command=self.create_user, bootstyle="success", width=20).grid(row=3, column=1, pady=20, sticky="w")

        # --- Manage Actions ---
        self.target_user = tk.StringVar()
        self.reset_pass = tk.StringVar()
        rr = tb.Frame(right); rr.pack(fill="x")
        
        tb.Label(rr, text="Target User:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(rr, textvariable=self.target_user, width=25).grid(row=0, column=1, sticky="w", padx=6, pady=6)
        tb.Button(rr, text="Delete", command=self.delete_user_action, bootstyle="danger").grid(row=0, column=2, padx=10, sticky="w")

        tb.Label(rr, text="New Password:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        tb.Entry(rr, textvariable=self.reset_pass, width=25).grid(row=1, column=1, sticky="w", padx=6, pady=6)
        tb.Button(rr, text="Reset Pass", command=self.reset_password, bootstyle="warning-outline").grid(row=1, column=2, padx=10, sticky="w")

        tb.Label(right, text="User List:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(15, 5))
        self.users_box = tk.Listbox(right, height=12, font=("Consolas", 10), selectbackground="#e1e1e1", selectforeground="black")
        self.users_box.pack(fill="both", expand=True)
        self.users_box.bind("<<ListboxSelect>>", self._on_user_select)

    def on_show(self):
        if not self.app.current_user or self.app.current_user.role != "Admin":
            self.app.logout()
            return
        self.refresh_users()

    def refresh_users(self):
        self.users_box.delete(0, tk.END)
        for u in self.app.store.list_users():
            self.users_box.insert(tk.END, f"{u.username:<15} | {u.role:<8} | {u.full_name}")

    def _on_user_select(self, event):
        selection = self.users_box.curselection()
        if selection:
            data = self.users_box.get(selection[0])
            self.target_user.set(data.split("|")[0].strip())

    def create_user(self):
        username = self.new_user.get().strip()
        role = (self.new_role.get() or "").strip()
        if not utils.is_valid_cccd_username(username):
            err("Username must be exactly 12 digits (ID).")
            return
        temp_pw = utils.generate_temp_password(8)
        ok = self.app.store.add_user(User(username=username, password=temp_pw, role=role, must_change_password=True))
        if not ok:
            err("Username already exists.")
            return
        self._show_password_once(username, temp_pw)
        self.new_user.set("")
        self.refresh_users()

    def _show_password_once(self, username, password):
        win = tb.Toplevel(self)
        win.title("Success")
        tb.Label(win, text=f"User: {username}\nTemp Password: {password}", font=("Segoe UI", 12)).pack(padx=20, pady=20)
        tb.Button(win, text="Copy & Close", command=lambda: [win.clipboard_clear(), win.clipboard_append(password), win.destroy()], bootstyle="success").pack(pady=10)

    def reset_password(self):
        username = self.target_user.get().strip()
        new_pw = self.reset_pass.get()
        if not username or not new_pw: return err("Missing information.")
        
        reason = simpledialog.askstring("Reason", "Enter password reset reason:")
        if not reason: return err("Reason required for audit log.")

        ok = self.app.store.update_password(username, new_pw)
        if ok:
            self.app.store.set_must_change_password(username, True)
            utils.audit_log("RESET_PASSWORD", self.app.current_user.username, target=username, reason=reason)
            info(f"Password reset for {username}.")
            self.reset_pass.set("")
        else:
            err("User does not exist.")

    def delete_user_action(self):
        username = self.target_user.get().strip()
        if not username: return err("No user selected.")
        if username == "admin": return err("Cannot delete root admin.")
        if not messagebox.askyesno("Confirm", f"Delete user {username}?"): return
        
        if self.app.store.delete_user(username):
            utils.audit_log("DELETE_USER", self.app.current_user.username, target=username)
            info("Deleted.")
            self.target_user.set("")
            self.refresh_users()
        else:
            err("Delete failed.")