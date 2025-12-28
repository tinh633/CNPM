# models.py
import json
import os
import time
import secrets
import string
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Set, Any, Tuple

DATA_FILE = "quiz_data.json"
ROLES = ["Admin", "Teacher", "Student"]
ROLE_CANON = {"admin": "Admin", "teacher": "Teacher", "student": "Student"}

# -----------------------------
# Data Models
# -----------------------------
@dataclass
class User:
    username: str
    password: str
    role: str
    full_name: str = ""
    dob: str = ""         # YYYY-MM-DD
    student_id: str = ""  # for students

@dataclass
class Question:
    text: str
    options: List[str]              # 4 options
    correct_indices: List[int]      # can be multiple

@dataclass
class Template:
    template_id: str
    title: str
    created_by: str
    questions: List[Question]

@dataclass
class Exam:
    exam_id: str
    template_id: str
    title: str
    created_by: str
    access_code: str
    password: str
    duration_seconds: int
    allow_review: bool
    attempt_limit: int             # 0 means unlimited
    start_ts: int
    end_ts: int
    questions: List[Question]

@dataclass
class Attempt:
    attempt_id: str
    exam_id: str
    code: str
    title: str
    username: str
    full_name: str
    student_id: str
    score: float                   # max = total questions
    total: int
    started_at: float
    submitted_at: float
    time_taken_seconds: int
    answers: List[List[int]]

# -----------------------------
# Scoring Logic
# -----------------------------
def score_question_partial(user_sel: Set[int], correct: Set[int], points: float) -> Tuple[float, Set[int], Set[int]]:
    """
    Partial scoring:
    earned_ratio = max(0, (c - w) / k)
    """
    if not correct:
        return (0.0, set(), set())
    c = len(user_sel & correct)
    w = len(user_sel - correct)
    k = len(correct)
    earned_ratio = (c - w) / k
    earned_ratio = max(0.0, min(1.0, earned_ratio))
    earned = earned_ratio * points
    missing = correct - user_sel
    extra = user_sel - correct
    return earned, missing, extra

# -----------------------------
# Storage & Migrations
# -----------------------------
class DataStore:
    def __init__(self, path: str = DATA_FILE):
        self.path = path
        self.data: Dict[str, Any] = {"users": [], "templates": [], "exams": [], "attempts": []}
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            self._seed_default()
            self.save()
            return

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            self._seed_default()
            self.save()
            return

        self.data = raw if isinstance(raw, dict) else {}
        self.data.setdefault("users", [])
        self.data.setdefault("templates", [])
        self.data.setdefault("exams", [])
        self.data.setdefault("attempts", [])

        # Migration logic
        for u in self.data["users"]:
            u.setdefault("full_name", "")
            u.setdefault("dob", "")
            u.setdefault("student_id", "")
            role = str(u.get("role", "")).strip()
            role_norm = ROLE_CANON.get(role.lower(), role)
            if role_norm not in ROLES:
                role_norm = "Student"
            u["role"] = role_norm

        for t in self.data["templates"]:
            t.setdefault("questions", [])
            for qu in t.get("questions", []):
                if "correct_indices" not in qu and "correct_index" in qu:
                    qu["correct_indices"] = [int(qu.get("correct_index", 0))]
                qu.pop("correct_index", None)

        for e in self.data["exams"]:
            e.setdefault("attempt_limit", 0)
            e.setdefault("allow_review", False)
            e.setdefault("password", "")
            e.setdefault("duration_seconds", 0)
            e.setdefault("start_ts", 0)
            e.setdefault("end_ts", 0)
            e.setdefault("questions", [])
            for qu in e.get("questions", []):
                if "correct_indices" not in qu and "correct_index" in qu:
                    qu["correct_indices"] = [int(qu.get("correct_index", 0))]
                qu.pop("correct_index", None)

        for a in self.data["attempts"]:
            try:
                a["score"] = float(a.get("score", 0))
            except Exception:
                a["score"] = 0.0
            a.setdefault("answers", [])

        self.save()

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def _seed_default(self):
        self.data = {
            "users": [
                asdict(User(username="admin", password="admin", role="Admin")),
                asdict(User(username="teacher", password="teacher", role="Teacher",
                           full_name="Teacher One", dob="1990-01-01")),
                asdict(User(username="student", password="student", role="Student",
                           full_name="Student One", dob="2005-01-01", student_id="SV001")),
            ],
            "templates": [],
            "exams": [],
            "attempts": [],
        }

    # ---- Users ----
    def find_user(self, username: str) -> Optional[User]:
        for u in self.data["users"]:
            if u.get("username") == username:
                return User(**u)
        return None

    def list_users(self) -> List[User]:
        return [User(**u) for u in self.data["users"]]

    def add_user(self, user: User) -> bool:
        if self.find_user(user.username):
            return False
        user.role = ROLE_CANON.get(user.role.lower(), user.role)
        if user.role not in ROLES:
            user.role = "Student"
        self.data["users"].append(asdict(user))
        self.save()
        return True

    def update_password(self, username: str, new_password: str) -> bool:
        for u in self.data["users"]:
            if u.get("username") == username:
                u["password"] = new_password
                self.save()
                return True
        return False

    def update_profile(self, username: str, full_name: str, dob: str, student_id: str) -> bool:
        for u in self.data["users"]:
            if u.get("username") == username:
                u["full_name"] = full_name
                u["dob"] = dob
                u["student_id"] = student_id
                self.save()
                return True
        return False

    # ---- IDs/Codes ----
    def new_template_id(self) -> str:
        return f"TP{int(time.time() * 1000)}"

    def new_exam_id(self) -> str:
        return f"EX{int(time.time() * 1000)}"

    def new_attempt_id(self) -> str:
        return f"AT{int(time.time() * 1000)}{secrets.randbelow(1000)}"

    def _all_codes(self) -> Set[str]:
        return {(e.get("access_code") or "").upper() for e in self.data["exams"] if e.get("access_code")}

    def new_unique_code(self, length: int = 8) -> str:
        alphabet = string.ascii_uppercase + string.digits
        existing = self._all_codes()
        while True:
            code = "".join(secrets.choice(alphabet) for _ in range(length))
            if code not in existing:
                return code

    # ---- Templates ----
    def add_template(self, t: Template):
        self.data["templates"].append(self._template_to_dict(t))
        self.save()

    def update_template(self, t: Template) -> bool:
        """Update content of an existing template."""
        for i, existing in enumerate(self.data["templates"]):
            if existing.get("template_id") == t.template_id:
                self.data["templates"][i] = self._template_to_dict(t)
                self.save()
                return True
        return False

    def list_templates(self) -> List[Template]:
        return [self._dict_to_template(x) for x in self.data["templates"]]

    def list_templates_by_teacher(self, teacher: str) -> List[Template]:
        return [t for t in self.list_templates() if t.created_by == teacher]

    def get_template(self, template_id: str) -> Optional[Template]:
        for t in self.data["templates"]:
            if t.get("template_id") == template_id:
                return self._dict_to_template(t)
        return None

    def delete_template(self, template_id: str) -> bool:
        before = len(self.data["templates"])
        self.data["templates"] = [t for t in self.data["templates"] if t.get("template_id") != template_id]
        if len(self.data["templates"]) == before:
            return False
        self.save()
        return True

    def has_exam_from_template(self, template_id: str) -> bool:
        return any(e.get("template_id") == template_id for e in self.data["exams"])

    def _template_to_dict(self, t: Template) -> Dict[str, Any]:
        return {
            "template_id": t.template_id,
            "title": t.title,
            "created_by": t.created_by,
            "questions": [asdict(q) for q in t.questions],
        }

    def _dict_to_template(self, d: Dict[str, Any]) -> Template:
        qs = []
        for q in d.get("questions", []):
            qs.append(Question(text=q["text"], options=q["options"], correct_indices=q.get("correct_indices", [])))
        return Template(
            template_id=d.get("template_id", ""),
            title=d.get("title", ""),
            created_by=d.get("created_by", ""),
            questions=qs
        )

    # ---- Exams ----
    def add_exam(self, e: Exam):
        self.data["exams"].append(self._exam_to_dict(e))
        self.save()

    def list_exams(self) -> List[Exam]:
        return [self._dict_to_exam(x) for x in self.data["exams"]]

    def list_exams_by_teacher(self, teacher: str) -> List[Exam]:
        return [e for e in self.list_exams() if e.created_by == teacher]

    def get_exam_by_code(self, code: str) -> Optional[Exam]:
        code = (code or "").strip().upper()
        for e in self.data["exams"]:
            if (e.get("access_code") or "").upper() == code:
                return self._dict_to_exam(e)
        return None

    def get_exam(self, exam_id: str) -> Optional[Exam]:
        for e in self.data["exams"]:
            if e.get("exam_id") == exam_id:
                return self._dict_to_exam(e)
        return None

    def delete_exam(self, exam_id: str) -> bool:
        before = len(self.data["exams"])
        self.data["exams"] = [e for e in self.data["exams"] if e.get("exam_id") != exam_id]
        if len(self.data["exams"]) == before:
            return False
        self.save()
        return True

    def _exam_to_dict(self, e: Exam) -> Dict[str, Any]:
        return {
            "exam_id": e.exam_id,
            "template_id": e.template_id,
            "title": e.title,
            "created_by": e.created_by,
            "access_code": e.access_code,
            "password": e.password,
            "duration_seconds": e.duration_seconds,
            "allow_review": e.allow_review,
            "attempt_limit": e.attempt_limit,
            "start_ts": e.start_ts,
            "end_ts": e.end_ts,
            "questions": [asdict(q) for q in e.questions],
        }

    def _dict_to_exam(self, d: Dict[str, Any]) -> Exam:
        qs = []
        for q in d.get("questions", []):
            qs.append(Question(text=q["text"], options=q["options"], correct_indices=q.get("correct_indices", [])))
        return Exam(
            exam_id=d.get("exam_id", ""),
            template_id=d.get("template_id", ""),
            title=d.get("title", ""),
            created_by=d.get("created_by", ""),
            access_code=d.get("access_code", ""),
            password=d.get("password", "") or "",
            duration_seconds=int(d.get("duration_seconds", 0) or 0),
            allow_review=bool(d.get("allow_review", False)),
            attempt_limit=int(d.get("attempt_limit", 0) or 0),
            start_ts=int(d.get("start_ts", 0) or 0),
            end_ts=int(d.get("end_ts", 0) or 0),
            questions=qs
        )

    # ---- Attempts ----
    def add_attempt(self, a: Attempt):
        self.data["attempts"].append(asdict(a))
        self.save()

    def list_attempts_for_user(self, username: str) -> List[Attempt]:
        out = [Attempt(**x) for x in self.data["attempts"] if x.get("username") == username]
        out.sort(key=lambda z: z.submitted_at, reverse=True)
        return out

    def list_attempts_for_exam(self, exam_id: str) -> List[Attempt]:
        out = [Attempt(**x) for x in self.data["attempts"] if x.get("exam_id") == exam_id]
        out.sort(key=lambda z: z.submitted_at, reverse=True)
        return out

    def count_attempts_for_user_exam(self, username: str, exam_id: str) -> int:
        return sum(1 for x in self.data["attempts"] if x.get("username") == username and x.get("exam_id") == exam_id)

    def delete_attempts_for_exam(self, exam_id: str) -> int:
        before = len(self.data["attempts"])
        self.data["attempts"] = [a for a in self.data["attempts"] if a.get("exam_id") != exam_id]
        deleted = before - len(self.data["attempts"])
        if deleted:
            self.save()
        return deleted