"""SQLite persistence for personal-first JobSpy mode."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pandas as pd

DEFAULT_DB_PATH = Path("data") / "jobspy.sqlite3"
ALLOWED_STATUSES = {"new", "shortlisted", "applied", "interview", "rejected", "withdrawn"}


class JobStore:
    """SQLite-backed store for job history and application tracking."""

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
            connection.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_url TEXT NOT NULL UNIQUE,
                    job_fingerprint TEXT,
                    title TEXT,
                    company TEXT,
                    location TEXT,
                    date_posted TEXT,
                    source TEXT,
                    description TEXT,
                    work_type TEXT,
                    application_status TEXT NOT NULL DEFAULT 'new',
                    seen_count INTEGER NOT NULL DEFAULT 1,
                    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(jobs)").fetchall()}
            if "seen_count" not in columns:
                connection.execute("ALTER TABLE jobs ADD COLUMN seen_count INTEGER NOT NULL DEFAULT 1")
            if "job_fingerprint" not in columns:
                connection.execute("ALTER TABLE jobs ADD COLUMN job_fingerprint TEXT")

            connection.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company_title ON jobs(company, title)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_jobs_last_seen ON jobs(last_seen_at)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_jobs_fingerprint ON jobs(job_fingerprint)")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS search_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_term TEXT NOT NULL,
                    location TEXT,
                    started_at TEXT NOT NULL,
                    total_jobs INTEGER NOT NULL DEFAULT 0
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS source_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_run_id INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_count INTEGER NOT NULL DEFAULT 0,
                    duration_ms INTEGER NOT NULL DEFAULT 0,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    error TEXT,
                    started_at TEXT,
                    FOREIGN KEY(search_run_id) REFERENCES search_runs(id)
                )
            """)
            self._ensure_memory_index(connection)

    @staticmethod
    def _memory_query(query: str) -> str:
        """Turn free text into safe FTS5 terms without exposing raw MATCH syntax."""
        tokens = re.findall(r"[a-zA-Z0-9+#.-]+", str(query or "").lower())
        unique = list(dict.fromkeys(token for token in tokens if token))
        return " AND ".join(f'"{token.replace(chr(34), chr(34) + chr(34))}"' for token in unique)

    def _ensure_memory_index(self, connection: sqlite3.Connection) -> None:
        """Create the lexical memory index and migrate existing jobs into it."""
        connection.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS job_memory_fts USING fts5(
                job_url UNINDEXED,
                title,
                company,
                location,
                source,
                description,
                work_type,
                application_status
            )
        """)
        job_count = int(connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0])
        index_count = int(connection.execute("SELECT COUNT(*) FROM job_memory_fts").fetchone()[0])
        if job_count != index_count:
            self._rebuild_memory_index(connection)

    def _rebuild_memory_index(self, connection: sqlite3.Connection) -> None:
        connection.execute("DELETE FROM job_memory_fts")
        connection.execute("""
            INSERT INTO job_memory_fts
                (job_url, title, company, location, source, description, work_type, application_status)
            SELECT job_url, COALESCE(title, ''), COALESCE(company, ''), COALESCE(location, ''),
                   COALESCE(source, ''), COALESCE(description, ''), COALESCE(work_type, ''),
                   COALESCE(application_status, 'new')
            FROM jobs
        """)

    def rebuild_memory_index(self) -> None:
        """Rebuild the FTS index from the canonical jobs table."""
        with self._connect() as connection:
            self._rebuild_memory_index(connection)

    def describe_memory(self) -> dict[str, object]:
        """Return inspectable metadata about the local memory index."""
        with self._connect() as connection:
            count = int(connection.execute("SELECT COUNT(*) FROM jobs").fetchone()[0])
            indexed = int(connection.execute("SELECT COUNT(*) FROM job_memory_fts").fetchone()[0])
            date_range = connection.execute(
                "SELECT MIN(first_seen_at), MAX(last_seen_at) FROM jobs"
            ).fetchone()
        return {
            "records": count,
            "indexed_records": indexed,
            "index_in_sync": count == indexed,
            "first_seen": date_range[0],
            "last_seen": date_range[1],
            "searchable_fields": [
                "title", "company", "location", "source",
                "description", "work_type", "application_status",
            ],
            "identity_field": "job_url",
        }

    def search_memory(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        company: str | None = None,
        source: str | None = None,
        work_type: str | None = None,
        application_status: str | None = None,
    ) -> dict[str, object]:
        """Search historical Job Memory with lexical FTS5 relevance and explicit filters."""
        fts_query = self._memory_query(query)
        limit = max(1, min(int(limit), 100))
        offset = max(0, int(offset))
        if not fts_query:
            return {"query": query, "shown_count": 0, "total_count": 0, "results": pd.DataFrame()}

        where = ["job_memory_fts MATCH ?"]
        params: list[object] = [fts_query]
        for column, value in (
            ("company", company),
            ("source", source),
            ("work_type", work_type),
            ("application_status", application_status),
        ):
            if value and str(value).strip():
                where.append(f"LOWER(j.{column}) = LOWER(?)")
                params.append(str(value).strip())

        predicate = " AND ".join(where)
        with self._connect() as connection:
            total = int(connection.execute(
                f"""SELECT COUNT(*) FROM job_memory_fts
                    JOIN jobs AS j ON j.job_url = job_memory_fts.job_url
                    WHERE {predicate}""",
                params,
            ).fetchone()[0])
            rows = pd.read_sql_query(
                f"""SELECT j.*, bm25(job_memory_fts) AS retrieval_bm25
                    FROM job_memory_fts
                    JOIN jobs AS j ON j.job_url = job_memory_fts.job_url
                    WHERE {predicate}
                    ORDER BY retrieval_bm25 ASC, j.last_seen_at DESC
                    LIMIT ? OFFSET ?""",
                connection,
                params=[*params, limit, offset],
            )

        if not rows.empty:
            rows["retrieval_rank"] = range(offset + 1, offset + 1 + len(rows))
        return {
            "query": query,
            "shown_count": int(len(rows)),
            "total_count": total,
            "results": rows,
        }

    def get_company_history(self, company: str, limit: int = 50) -> dict[str, object]:
        """Retrieve one explicitly selected company's history; never fuzzy-match names."""
        company = str(company or "").strip()
        limit = max(1, min(int(limit), 100))
        if not company:
            return {"company": "", "shown_count": 0, "total_count": 0, "results": pd.DataFrame()}

        with self._connect() as connection:
            total = int(connection.execute(
                "SELECT COUNT(*) FROM jobs WHERE LOWER(company) = LOWER(?)", (company,)
            ).fetchone()[0])
            rows = pd.read_sql_query(
                """SELECT * FROM jobs
                   WHERE LOWER(company) = LOWER(?)
                   ORDER BY last_seen_at DESC
                   LIMIT ?""",
                connection,
                params=(company, limit),
            )
        return {
            "company": company,
            "shown_count": int(len(rows)),
            "total_count": total,
            "results": rows,
        }


    def upsert_jobs(self, jobs: pd.DataFrame) -> int:
        """Insert jobs or refresh their historical sighting count by URL."""
        if jobs is None or jobs.empty or "job_url" not in jobs.columns:
            return 0
        rows = []
        for _, row in jobs.iterrows():
            url = str(row.get("job_url", "")).strip()
            if not url:
                continue
            rows.append((
                url, str(row.get("job_fingerprint", "")), str(row.get("title", "")),
                str(row.get("company", "")), str(row.get("location", "")),
                str(row.get("date_posted", "")), str(row.get("site", row.get("source", ""))),
                str(row.get("description", "")), str(row.get("Work Type", "")),
            ))
        with self._connect() as connection:
            connection.executemany("""
                INSERT INTO jobs
                    (job_url, job_fingerprint, title, company, location, date_posted, source, description, work_type, seen_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(job_url) DO UPDATE SET
                    job_fingerprint=excluded.job_fingerprint,
                    title=excluded.title, company=excluded.company, location=excluded.location,
                    date_posted=excluded.date_posted, source=excluded.source,
                    description=excluded.description, work_type=excluded.work_type,
                    seen_count=jobs.seen_count + 1,
                    last_seen_at=CURRENT_TIMESTAMP
            """, rows)
            for row in rows:
                connection.execute("DELETE FROM job_memory_fts WHERE job_url=?", (row[0],))
                connection.execute(
                    """INSERT INTO job_memory_fts
                       (job_url, title, company, location, source, description, work_type, application_status)
                       SELECT job_url, COALESCE(title, ''), COALESCE(company, ''), COALESCE(location, ''),
                              COALESCE(source, ''), COALESCE(description, ''), COALESCE(work_type, ''),
                              COALESCE(application_status, 'new')
                       FROM jobs WHERE job_url=?""",
                    (row[0],),
                )
        return len(rows)

    def update_application_status(self, job_url: str, status: str) -> None:
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Unsupported application status: {status}")
        with self._connect() as connection:
            connection.execute("UPDATE jobs SET application_status=? WHERE job_url=?", (status, job_url))
            connection.execute(
                "UPDATE job_memory_fts SET application_status=? WHERE job_url=?",
                (status, job_url),
            )

    def get_application_statuses(self, urls: list[str]) -> dict[str, str]:
        if not urls:
            return {}
        placeholders = ",".join("?" for _ in urls)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT job_url, application_status FROM jobs WHERE job_url IN ({placeholders})", urls
            ).fetchall()
        return {row["job_url"]: row["application_status"] for row in rows}

    def record_search(self, search_term: str, location: str, jobs: pd.DataFrame, source_results) -> int:
        """Persist one auditable search and all source outcomes."""
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO search_runs(search_term, location, started_at, total_jobs) VALUES (?, ?, CURRENT_TIMESTAMP, ?)",
                (search_term, location, 0 if jobs is None else len(jobs)),
            )
            run_id = cursor.lastrowid
            connection.executemany(
                """INSERT INTO source_runs
                (search_run_id, source, status, result_count, duration_ms, attempts, error, started_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (run_id, item.source, item.status, item.result_count, item.duration_ms, item.attempts, item.error, item.started_at)
                    for item in source_results
                ],
            )
            return int(run_id)

    def load_source_health(self, limit: int = 50) -> pd.DataFrame:
        with self._connect() as connection:
            return pd.read_sql_query(
                """SELECT source, status, result_count, duration_ms, attempts, error, started_at
                   FROM source_runs ORDER BY id DESC LIMIT ?""", connection, params=(limit,)
            )

    def load_jobs(self) -> pd.DataFrame:
        with self._connect() as connection:
            return pd.read_sql_query("SELECT * FROM jobs ORDER BY last_seen_at DESC", connection)


    def delete_job(self, job_url: str) -> None:
        """Delete one canonical job and its retrieval index entry."""
        with self._connect() as connection:
            connection.execute("DELETE FROM job_memory_fts WHERE job_url=?", (job_url,))
            connection.execute("DELETE FROM jobs WHERE job_url=?", (job_url,))
