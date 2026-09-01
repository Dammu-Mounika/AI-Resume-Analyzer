"""
Lightweight SQLite storage for analysis history.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Database path in project root or data directory
DB_PATH = Path(__file__).resolve().parent.parent / "analysis_history.db"


def get_db_connection() -> sqlite3.Connection:
    """Creates a connection to the SQLite database with dict-like row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initializes the database schema if tables do not exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                job_title TEXT,
                overall_score REAL NOT NULL,
                keyword_score REAL NOT NULL,
                semantic_score REAL NOT NULL,
                matched_skills TEXT,
                missing_skills TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()


def save_analysis(
    filename: str,
    job_title: Optional[str],
    overall_score: float,
    keyword_score: float,
    semantic_score: float,
    matched_skills: List[str],
    missing_skills: List[str],
) -> int:
    """Saves a new resume analysis record to the database."""
    init_db()  # Ensure table exists

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO analysis_history (
                filename, job_title, overall_score, keyword_score,
                semantic_score, matched_skills, missing_skills, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                job_title or "Unspecified Job",
                overall_score,
                keyword_score,
                semantic_score,
                json.dumps(matched_skills),
                json.dumps(missing_skills),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_recent_analyses(limit: int = 10) -> List[Dict[str, Any]]:
    """Retrieves the most recent analysis records."""
    init_db()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, filename, job_title, overall_score, keyword_score,
                   semantic_score, matched_skills, missing_skills, created_at
            FROM analysis_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()

    history = []
    for row in rows:
        item = dict(row)
        item["matched_skills"] = json.loads(item["matched_skills"] or "[]")
        item["missing_skills"] = json.loads(item["missing_skills"] or "[]")
        history.append(item)

    return history


# Automatically ensure DB setup on import
init_db()
