# utils.py
import time
from tkinter import messagebox
from typing import List, Optional, Set, Tuple

# Import từ models để dùng type hints và logic tính điểm
from models import Template, Exam, Attempt, score_question_partial

try:
    from docx import Document
    from openpyxl import Workbook
except ImportError:
    print("Warning: python-docx or openpyxl not installed. Export features will fail.")

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

def export_exam_to_word(e: Exam, filepath: str, include_answers: bool = True):
    try:
        doc = Document()
        doc.add_heading(f"Exam: {e.title}", level=1)
        doc.add_paragraph(f"Exam ID: {e.exam_id}")
        doc.add_paragraph(f"Code: {e.access_code}")
        doc.add_paragraph(f"Window: {fmt_dt(e.start_ts)} -> {fmt_dt(e.end_ts)}")
        doc.add_paragraph(f"Duration: {max(1, e.duration_seconds // 60)} minutes")
        doc.add_paragraph(f"Password: {'set' if e.password else 'none'}")
        doc.add_paragraph(f"Allow review: {'yes' if e.allow_review else 'no'}")
        doc.add_paragraph(f"Attempt limit: {e.attempt_limit} (0=unlimited)")
        doc.add_paragraph(f"From template: {e.template_id}")

        for i, q in enumerate(e.questions, start=1):
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

def export_attempt_to_word(e: Exam, a: Attempt, filepath: str):
    try:
        doc = Document()
        doc.add_heading("Attempt Report", level=1)
        doc.add_paragraph(f"Exam: {e.title}")
        doc.add_paragraph(f"Exam ID: {e.exam_id} | Code: {e.access_code}")
        doc.add_paragraph(f"Student: {a.full_name} | Username: {a.username} | Student ID: {a.student_id}")
        doc.add_paragraph(f"Started: {fmt_dt_full(a.started_at)}")
        doc.add_paragraph(f"Submitted: {fmt_dt_full(a.submitted_at)}")
        doc.add_paragraph(f"Time taken: {a.time_taken_seconds} sec")

        total_q = max(1, len(e.questions))
        score10 = (a.score / total_q) * 10.0
        doc.add_paragraph(f"Score: {score10:.2f}/10 (raw {a.score:.4f}/{total_q})")

        answers = a.answers or []
        points_per_q = 10.0 / total_q

        for i, q in enumerate(e.questions):
            user_sel = set(answers[i]) if i < len(answers) else set()
            correct = set(q.correct_indices)
            earned, missing, extra = score_question_partial(user_sel, correct, points=points_per_q)

            doc.add_heading(f"Q{i+1}: {q.text}", level=2)
            doc.add_paragraph(f"Earned: {earned:.2f}/{points_per_q:.2f}")
            for oi, opt in enumerate(q.options, start=1):
                mu = "[x]" if (oi - 1) in user_sel else "[ ]"
                mc = "(correct)" if (oi - 1) in correct else ""
                doc.add_paragraph(f"{mu} {oi}. {opt} {mc}")
            doc.add_paragraph("Missing correct: " + (", ".join(str(x+1) for x in sorted(missing)) if missing else "none"))
            doc.add_paragraph("Extra wrong: " + (", ".join(str(x+1) for x in sorted(extra)) if extra else "none"))

        doc.save(filepath)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export docx: {e}")