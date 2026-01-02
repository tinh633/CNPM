# utils.py
import time
from tkinter import messagebox
from typing import List, Optional, Set, Tuple

from models import Template, Exam, Attempt, score_question_partial

try:
    from docx import Document
    from openpyxl import Workbook
except ImportError:
    pass

# -----------------------------
# Time helpers
# -----------------------------
def parse_dt(s: str) -> Optional[int]:
    """Parse 'YYYY-MM-DD HH:MM' to unix timestamp (local)."""
    s = (s or "").strip()
    try:
        return int(time.mktime(time.strptime(s, "%Y-%m-%d %H:%M")))
    except Exception:
        return None

def fmt_dt(ts: int) -> str:
    try:
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(int(ts)))
    except Exception:
        return "N/A"

def fmt_dt_full(ts: float) -> str:
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ts)))
    except Exception:
        return "N/A"

# -----------------------------
# Export helpers
# -----------------------------
def export_template_to_word(t: Template, filepath: str, include_answers: bool = True):
    try:
        doc = Document()
        doc.add_heading(f"Template: {t.title}", level=1)
        doc.add_paragraph(f"Template ID: {t.template_id}")
        doc.add_paragraph(f"Created by: {t.created_by}")
        doc.add_paragraph(f"Questions: {len(t.questions)}")

        for i, q in enumerate(t.questions, start=1):
            doc.add_heading(f"Q{i}: {q.text}", level=2)
            for oi, opt in enumerate(q.options, start=1):
                doc.add_paragraph(f"{oi}. {opt}", style="List Bullet")
            if include_answers:
                correct = ", ".join(str(x + 1) for x in sorted(q.correct_indices))
                doc.add_paragraph(f"Correct: {correct}")
        doc.save(filepath)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export docx: {e}")

def export_exam_results_to_excel(e: Exam, attempts: List[Attempt], filepath: str):
    try:
        wb = Workbook()
        ws = wb.active
        ws.title = "Results"

        ws.append([
            "Exam Title", "Exam ID", "Code",
            "Username", "Full Name", "Student ID",
            "Score (/10)", "Raw Score", "Total Questions",
            "Time Taken (sec)", "Submitted At"
        ])

        for a in attempts:
            score10 = (a.score / max(1, a.total)) * 10.0
            ws.append([
                e.title, e.exam_id, e.access_code,
                a.username, a.full_name, a.student_id,
                round(score10, 2), round(a.score, 4), a.total,
                a.time_taken_seconds, fmt_dt_full(a.submitted_at)
            ])
        wb.save(filepath)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export xlsx: {e}")

# -----------------------------
# Audit / Security helpers
# -----------------------------
def audit_log(action: str, performed_by: str, target: str = "", reason: str = ""):
    """
    Security audit log (non-functional requirement).
    """
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    line = f"[{ts}] action={action} by={performed_by}"
    if target:
        line += f" target={target}"
    if reason:
        line += f" reason={reason.replace(chr(10), ' ')}"
    line += "\n"

    try:
        with open("audit.log", "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass

# -----------------------------
# Password policy helpers
# -----------------------------
import secrets
import string

def validate_password_policy(pw: str) -> tuple[bool, str]:
    """Policy: >=8 chars, includes uppercase, lowercase, digit, special."""
    pw = pw or ""
    if len(pw) < 8:
        return False, "Password must be at least 8 characters."
    if not any(c.islower() for c in pw):
        return False, "Password must include a lowercase letter."
    if not any(c.isupper() for c in pw):
        return False, "Password must include an uppercase letter."
    if not any(c.isdigit() for c in pw):
        return False, "Password must include a digit."
    specials = set("!@#$%^&*()-_=+[]{};:'\",.<>/?|`~")
    if not any(c in specials for c in pw):
        return False, "Password must include a special character."
    return True, ""

def generate_strong_password(length: int = 12) -> str:
    """Generate a strong password that satisfies the policy."""
    length = max(8, int(length or 12))
    lowers = string.ascii_lowercase
    uppers = string.ascii_uppercase
    digits = string.digits
    specials = "!@#$%^&*()-_=+[]{};:'\",.<>/?|`~"
    # ensure at least 1 from each
    pw = [
        secrets.choice(lowers),
        secrets.choice(uppers),
        secrets.choice(digits),
        secrets.choice(specials),
    ]
    alphabet = lowers + uppers + digits + specials
    while len(pw) < length:
        pw.append(secrets.choice(alphabet))
    secrets.SystemRandom().shuffle(pw)
    return "".join(pw)

