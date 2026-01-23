# ui/base.py
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
import time

def info(msg: str):
    messagebox.showinfo("Information", msg)

def err(msg: str):
    messagebox.showerror("Error", msg)

def is_valid_date_yyyy_mm_dd(s: str) -> bool:
    s = (s or "").strip()
    try:
        time.strptime(s, "%Y-%m-%d")
        return True
    except Exception:
        return False

class Header(tb.Frame):
    def __init__(self, parent, title, subtitle=""):
        super().__init__(parent, bootstyle="primary")
        tb.Label(self, text=title, font=("Segoe UI", 18, "bold"), bootstyle="inverse-primary").pack(anchor="w", padx=20, pady=(15, 5))
        if subtitle:
            tb.Label(self, text=subtitle, font=("Segoe UI", 11), bootstyle="inverse-primary").pack(anchor="w", padx=20, pady=(0, 15))
        else:
            tb.Label(self, text="", font=("Segoe UI", 11), bootstyle="inverse-primary").pack(pady=(0, 15))