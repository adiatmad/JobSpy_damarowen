import pandas as pd

import search_engine
from scraper import ScrapeResult


def test_classify_error():
    assert search_engine.classify_error("waktu habis (60 detik)") == "TIMEOUT"
    assert search_engine.classify_error("HTTP 403 forbidden") == "BLOCKED"
    assert search_engine.classify_error("429 too many requests") == "RATE_LIMITED"
    assert search_engine.classify_error("connection reset by peer") == "NETWORK_ERROR"


def test_search_sources_records_success_and_empty_and_attempts(monkeypatch):
    frames = {
        "indeed": pd.DataFrame([{"title": "GIS Analyst", "job_url": "https://example.com/1"}]),
        "linkedin": pd.DataFrame(),
    }

    def fake_scrape_one_site_detailed(**kwargs):
        return ScrapeResult(frames[kwargs["site"]], None, 1)

    monkeypatch.setattr(search_engine, "scrape_one_site_detailed", fake_scrape_one_site_detailed)

    result = search_engine.search_sources(
        ["indeed", "linkedin"], search_term="GIS Analyst", location="Indonesia",
        country_indeed="Indonesia", results_wanted=10, hours_old=72,
    )

    assert len(result.jobs) == 1
    assert [item.status for item in result.sources] == ["SUCCESS", "EMPTY"]
    assert result.sources[0].result_count == 1
    assert result.sources[1].result_count == 0
    assert result.sources[0].attempts == 1


def test_job_store_round_trip_and_seen_count(tmp_path):
    from storage import JobStore

    store = JobStore(tmp_path / "jobs.sqlite3")
    jobs = pd.DataFrame([{
        "job_url": "https://example.com/1", "job_fingerprint": "gis analyst|example|jakarta",
        "title": "GIS Analyst", "company": "Example", "location": "Jakarta",
        "date_posted": "2026-09-13", "site": "indeed", "description": "Remote role", "Work Type": "Remote",
    }])

    assert store.upsert_jobs(jobs) == 1
    assert store.upsert_jobs(jobs) == 1
    loaded = store.load_jobs()
    assert len(loaded) == 1
    assert loaded.iloc[0]["application_status"] == "new"
    assert loaded.iloc[0]["seen_count"] == 2
    assert loaded.iloc[0]["job_fingerprint"] == "gis analyst|example|jakarta"

    store.update_application_status("https://example.com/1", "shortlisted")
    assert store.load_jobs().iloc[0]["application_status"] == "shortlisted"


def test_job_store_sparse_reingest_preserves_richer_fields_and_status(tmp_path):
    from storage import JobStore

    store = JobStore(tmp_path / "jobs.sqlite3")
    original = pd.DataFrame([{
        "job_url": "https://example.com/2",
        "job_fingerprint": "gis analyst|example|jakarta",
        "title": "GIS Analyst",
        "company": "Example",
        "location": "Jakarta",
        "date_posted": "2026-10-17",
        "site": "indeed",
        "description": "A detailed description",
        "Work Type": "Remote",
    }])
    sparse = pd.DataFrame([{
        "job_url": "https://example.com/2",
        "job_fingerprint": pd.NA,
        "title": pd.NA,
        "company": " ",
        "location": pd.NA,
        "date_posted": None,
        "site": "linkedin",
        "description": pd.NA,
        "Work Type": pd.NA,
    }])

    assert store.upsert_jobs(original) == 1
    store.update_application_status("https://example.com/2", "shortlisted")
    assert store.upsert_jobs(sparse) == 1

    row = store.load_jobs().iloc[0]
    assert row["title"] == "GIS Analyst"
    assert row["company"] == "Example"
    assert row["location"] == "Jakarta"
    assert row["date_posted"] == "2026-10-17"
    assert row["description"] == "A detailed description"
    assert row["Work Type"] == "Remote"
    assert row["source"] == "linkedin"
    assert row["application_status"] == "shortlisted"
    assert row["seen_count"] == 2
    assert row["job_fingerprint"] == "gis analyst|example|jakarta"
