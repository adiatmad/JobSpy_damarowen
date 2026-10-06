import sqlite3

import pandas as pd

from storage import JobStore


def _jobs():
    return pd.DataFrame([
        {
            "job_url": "https://example.com/gis-analyst",
            "job_fingerprint": "gis-analyst-example-jakarta",
            "title": "GIS Analyst",
            "company": "Example Geo",
            "location": "Jakarta",
            "date_posted": "2026-10-01",
            "site": "linkedin",
            "description": "Geospatial analysis, QGIS, Python and field mapping.",
            "Work Type": "Remote",
        },
        {
            "job_url": "https://example.com/python-engineer",
            "job_fingerprint": "python-engineer-acme",
            "title": "Python Engineer",
            "company": "Acme Data",
            "location": "Surabaya",
            "date_posted": "2026-10-02",
            "site": "indeed",
            "description": "Build data pipelines with Python.",
            "Work Type": "On-site",
        },
        {
            "job_url": "https://example.com/gis-manager",
            "job_fingerprint": "gis-manager-example-jakarta",
            "title": "GIS Manager",
            "company": "Example Geo",
            "location": "Bandung",
            "date_posted": "2026-10-03",
            "site": "linkedin",
            "description": "Manage GIS delivery and geospatial operations.",
            "Work Type": "Hybrid",
        },
    ])


def test_memory_indexes_upserts_and_reports_total_count(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite3")
    assert store.upsert_jobs(_jobs()) == 3

    result = store.search_memory("GIS", limit=1)

    assert result["shown_count"] == 1
    assert result["total_count"] == 2
    assert result["results"].iloc[0]["retrieval_rank"] == 1
    assert "Match Score" not in result["results"].columns


def test_memory_filters_are_explicit_and_combined(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.upsert_jobs(_jobs())

    result = store.search_memory("GIS", company="Example Geo", source="linkedin", work_type="Hybrid")

    assert result["total_count"] == 1
    assert result["results"].iloc[0]["title"] == "GIS Manager"


def test_reupsert_refreshes_index_without_duplicate_records(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite3")
    jobs = _jobs().iloc[[0]].copy()
    store.upsert_jobs(jobs)

    updated = jobs.copy()
    updated.loc[updated.index[0], "title"] = "Senior GIS Analyst"
    updated.loc[updated.index[0], "description"] = "Senior geospatial analysis with QGIS and Python."
    store.upsert_jobs(updated)

    old = store.search_memory("GIS Analyst")
    new = store.search_memory("Senior GIS Analyst")

    assert old["total_count"] == 0
    assert new["total_count"] == 1
    assert new["results"].iloc[0]["seen_count"] == 2


def test_application_status_stays_searchable_after_update(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.upsert_jobs(_jobs().iloc[[0]])

    store.update_application_status("https://example.com/gis-analyst", "shortlisted")
    result = store.search_memory("GIS", application_status="shortlisted")

    assert result["total_count"] == 1
    assert result["results"].iloc[0]["application_status"] == "shortlisted"


def test_company_history_is_exact_not_fuzzy(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.upsert_jobs(_jobs())

    exact = store.get_company_history("Example Geo", limit=1)
    typo = store.get_company_history("Example Ge", limit=10)

    assert exact["total_count"] == 2
    assert exact["shown_count"] == 1
    assert typo["total_count"] == 0


def test_describe_memory_exposes_index_state(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.upsert_jobs(_jobs())

    description = store.describe_memory()

    assert description["records"] == 3
    assert description["indexed_records"] == 3
    assert description["index_in_sync"] is True
    assert "title" in description["searchable_fields"]
    assert description["identity_field"] == "job_url"


def test_existing_jobs_are_migrated_into_fts_index(tmp_path):
    db_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """CREATE TABLE jobs (
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
                seen_count INTEGER NOT NULL DEFAULT 1,
                first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        connection.execute(
            """INSERT INTO jobs
               (job_url, title, company, location, date_posted, source, description, work_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("https://legacy.example/job", "Legacy GIS Role", "Legacy Co", "Jakarta",
             "2026-09-30", "linkedin", "Legacy geospatial mapping role.", "Remote"),
        )

    store = JobStore(db_path)
    result = store.search_memory("Legacy GIS")

    assert result["total_count"] == 1
    assert store.describe_memory()["index_in_sync"] is True


def test_empty_query_is_explicitly_empty(tmp_path):
    store = JobStore(tmp_path / "jobs.sqlite3")
    store.upsert_jobs(_jobs())

    result = store.search_memory("")

    assert result["shown_count"] == 0
    assert result["total_count"] == 0
    assert result["results"].empty
