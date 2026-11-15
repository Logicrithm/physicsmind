"""Where feedback is kept: a local SQLite file on this computer, or a Supabase table when the app is online.

The online host wipes its own disk whenever the app restarts (after 12 quiet hours or on every update), so feedback
from testers must go to a database outside it. choose_store() picks Supabase when SUPABASE_URL and SUPABASE_KEY are
set, and the local file otherwise. Both keep the same columns, including the app version that gave the answer.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import urllib.error
import urllib.request

from .config import setting

DEFAULT_DB = Path(__file__).resolve().parent.parent / "physicsmind.db"
RATINGS = {"helpful", "not_helpful"}
# Long pasted text is cut so a single visitor cannot fill the free database.
LIMITS = {"question": 4000, "answer": 12000, "comment": 1000, "issue_category": 100, "model": 200,
          "verification_status": 200, "response_type": 50, "response_id": 100, "app_version": 100}


class FeedbackNotSaved(Exception):
    """The feedback could not be stored; the message is safe to show (it never contains a key)."""


def init_db(db_path=DEFAULT_DB):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS response_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                response_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                response_type TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                model TEXT,
                rating TEXT NOT NULL,
                issue_category TEXT,
                comment TEXT,
                verification_status TEXT,
                app_version TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_response_id ON response_feedback(response_id)")
        # Files made before 15 Nov 2026 have no app_version column. Adding it leaves every existing row as it was.
        columns = {row[1] for row in conn.execute("PRAGMA table_info(response_feedback)")}
        if "app_version" not in columns:
            conn.execute("ALTER TABLE response_feedback ADD COLUMN app_version TEXT")


def feedback_row(response_id, response_type, question, answer, rating, issue_category="", comment="",
                 model="", verification_status="", app_version=""):
    if rating not in RATINGS:
        raise ValueError("rating must be helpful or not_helpful")
    row = {"response_id": response_id, "created_at": datetime.now(timezone.utc).isoformat(),
           "response_type": response_type, "question": question, "answer": answer, "model": model,
           "rating": rating, "issue_category": issue_category, "comment": comment,
           "verification_status": verification_status, "app_version": app_version}
    for name, limit in LIMITS.items():
        row[name] = str(row[name] or "")[:limit]
    return row


def save_feedback(response_id, response_type, question, answer, rating,
                  issue_category="", comment="", model="", verification_status="", app_version="",
                  db_path=DEFAULT_DB):
    row = feedback_row(response_id, response_type, question, answer, rating, issue_category, comment,
                       model, verification_status, app_version)
    init_db(db_path)
    names = list(row)
    with sqlite3.connect(db_path) as conn:
        conn.execute(f"INSERT INTO response_feedback ({', '.join(names)}) VALUES ({', '.join('?' * len(names))})",
                     [row[name] for name in names])


def feedback_count(db_path=DEFAULT_DB):
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM response_feedback").fetchone()[0]


class LocalStore:
    where = "on this computer"

    def __init__(self, db_path=None):
        self.db_path = Path(db_path or DEFAULT_DB)
        init_db(self.db_path)

    def save(self, **fields):
        save_feedback(**fields, db_path=self.db_path)

    def count(self):
        return feedback_count(self.db_path)


class OnlineStore:
    """Adds rows to the Supabase table through its REST API. The key it is given should be the project's
    publishable (anon) key, which the setup SQL allows to add feedback and nothing else: it cannot read, change
    or delete what testers sent."""
    where = "online"
    TABLE = "response_feedback"

    def __init__(self, url, key, send=urllib.request.urlopen):
        self.url, self.key, self.send = url.rstrip("/"), key, send

    def save(self, **fields):
        row = feedback_row(**fields)
        headers = {"apikey": self.key, "Content-Type": "application/json", "Prefer": "return=minimal"}
        if self.key.startswith("eyJ"):  # an older anon key is a JWT and also goes in the Authorization header
            headers["Authorization"] = f"Bearer {self.key}"
        request = urllib.request.Request(f"{self.url}/rest/v1/{self.TABLE}", data=json.dumps(row).encode("utf-8"),
                                         headers=headers, method="POST")
        try:
            with self.send(request, timeout=10) as response:
                status = response.status
        except urllib.error.HTTPError as exc:
            raise FeedbackNotSaved(f"the feedback database refused it (HTTP {exc.code})") from None
        except (urllib.error.URLError, OSError):
            raise FeedbackNotSaved("the feedback database could not be reached") from None
        if status not in (200, 201, 204):
            raise FeedbackNotSaved(f"the feedback database answered HTTP {status}")

    def count(self):
        return None  # the app's key may only add feedback, not read it back


def choose_store(db_path=None):
    url, key = setting("SUPABASE_URL"), setting("SUPABASE_KEY")
    if url and key:
        return OnlineStore(url, key)
    return LocalStore(db_path)
