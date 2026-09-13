"""Small local persistence layer for the personal-first JobSpy mode."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


DEFAULT_DB_PATH = Path("data") / "jobspy.sqlite3"


class JobStore:
    """SQLite-backed store with no external database service required."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_url TEXT NOT NULL UNIQUE,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    date_posted TEXT,
                    source TEXT,
                    description TEXT,
                    work_type TEXT,
                    application_status TEXT NOT NULL DEFAULT 'new',
                    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_company_title ON jobs(company, title)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_last_seen ON jobs(last_seen_at)"
            )

    def upsert_jobs(self, jobs: pd.DataFrame) -> int:
        """Insert new jobs and refresh last_seen_at for existing URLs."""
        if jobs is None or jobs.empty or "job_url" not in jobs.columns:
            return 0

        columns = [
            "job_url",
            "title",
            "company",
            "location",
            "date_posted",
            "source",
            "description",
            "Work Type",
        ]
        rows = []
        for _, row in jobs.iterrows():
            url = str(row.get("job_url", "")).strip()
            if not url:
                continue
            rows.append(
                (
                    url,
                    str(row.get("title", "")),
                    str(row.get("company", "")),
                    str(row.get("location", "")),
                    str(row.get("date_posted", "")),
                    str(row.get("site", row.get("source", ""))),
                    str(row.get("description", "")),
                    str(row.get("Work Type", "")),
                )
            )

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO jobs
                    (job_url, title, company, location, date_posted, source,
                     description, work_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(job_url) DO UPDATE SET
                    title = excluded.title,
                    company = excluded.company,
                    location = excluded.location,
                    date_posted = excluded.date_posted,
                    source = excluded.source,
                    description = excluded.description,
                    work_type = excluded.work_type,
                    last_seen_at = CURRENT_TIMESTAMP
                """,
                rows,
            )
        return len(rows)

    def update_application_status(self, job_url: str, status: str) -> None:
        allowed = {"new", "shortlisted", "applied", "interview", "rejected", "withdrawn"}
        if status not in allowed:
            raise ValueError(f"Unsupported application status: {status}")
        with self._connect() as connection:
            connection.execute(
                "UPDATE jobs SET application_status = ? WHERE job_url = ?",
                (status, job_url),
            )

    def load_jobs(self) -> pd.DataFrame:
        with self._connect() as connection:
            return pd.read_sql_query(
                "SELECT * FROM jobs ORDER BY last_seen_at DESC", connection
            )
