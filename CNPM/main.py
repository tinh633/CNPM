# main.py
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict

from models import DataStore, User
# Import toàn bộ các Frame từ ui
from ui import (
    LoginFrame, AdminFrame, TeacherFrame, StudentFrame,
    ExamTakeFrame, ReviewFrame, TeacherAttemptFrame,
    TemplatePreviewFrame, ExamPreviewFrame
)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quiz Examination System")
        self.geometry("1180x760")
        self.minsize(1180, 760)

        self.store = DataStore()
        self.current_user: Optional[User] = None
        self.current_frame_name: str = "LoginFrame"

        self.container = ttk.Frame(self, padding=12)
        self.container.pack(fill="both", expand=True)
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

        self.frames: Dict[str, ttk.Frame] = {}
        self._init_frames()
        self.show_frame("LoginFrame")

    def _init_frames(self):
        # Đăng ký tất cả các Frame
        for F in (
            LoginFrame, AdminFrame, TeacherFrame, StudentFrame,
            ExamTakeFrame, ReviewFrame, TeacherAttemptFrame,
            TemplatePreviewFrame, ExamPreviewFrame
        ):
            # Truyền self (app) vào Frame để các Frame truy cập store
            frame = F(self.container, self)
            self.frames[F.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show_frame(self, name: str):
        self.current_frame_name = name
        frame = self.frames[name]
        if hasattr(frame, "on_show"):
            frame.on_show()
        frame.tkraise()

    def reload_data(self):
        self.store.load()
        if self.current_user:
            u = self.store.find_user(self.current_user.username)
            if u:
                self.current_user = u
        cur = self.frames.get(self.current_frame_name)
        if cur and hasattr(cur, "on_show"):
            cur.on_show()

    def logout(self):
        # Dừng timer nếu đang thi
        tf = self.frames.get("ExamTakeFrame")
        if tf and hasattr(tf, "stop_timer"):
            tf.stop_timer()
            
        self.current_user = None
        self.show_frame("LoginFrame")

if __name__ == "__main__":
    app = App()

    app.mainloop()
