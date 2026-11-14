"""SQLite persistence for response feedback and later evaluation."""
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DEFAULT_DB = Path(__file__).resolve().parent.parent / "physicsmind.db"

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
                verification_status TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_response_id ON response_feedback(response_id)")

def save_feedback(response_id, response_type, question, answer, rating,
                  issue_category="", comment="", model="", verification_status="",
                  db_path=DEFAULT_DB):
    if rating not in {"helpful", "not_helpful"}:
        raise ValueError("rating must be helpful or not_helpful")
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            INSERT INTO response_feedback
            (response_id, created_at, response_type, question, answer, model,
             rating, issue_category, comment, verification_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            response_id,
            datetime.now(timezone.utc).isoformat(),
            response_type,
            question,
            answer,
            model,
            rating,
            issue_category,
            comment,
            verification_status
        ))

def feedback_count(db_path=DEFAULT_DB):
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        return conn.execute("SELECT COUNT(*) FROM response_feedback").fetchone()[0]
