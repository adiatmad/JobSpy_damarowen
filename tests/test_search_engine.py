import pandas as pd

import search_engine


def test_classify_error():
    assert search_engine.classify_error("waktu habis (60 detik)") == "TIMEOUT"
    assert search_engine.classify_error("HTTP 403 forbidden") == "BLOCKED"
    assert search_engine.classify_error("429 too many requests") == "RATE_LIMITED"
    assert search_engine.classify_error("connection reset by peer") == "NETWORK_ERROR"


def test_search_sources_records_success_and_empty(monkeypatch):
    frames = {
        "indeed": pd.DataFrame([{"title": "GIS Analyst", "job_url": "https://example.com/1"}]),
        "linkedin": pd.DataFrame(),
    }

    def fake_scrape_one_site(**kwargs):
        return frames[kwargs["site"]], None

    monkeypatch.setattr(search_engine, "scrape_one_site", fake_scrape_one_site)

    result = search_engine.search_sources(
        ["indeed", "linkedin"],
        search_term="GIS Analyst",
        location="Indonesia",
        country_indeed="Indonesia",
        results_wanted=10,
        hours_old=72,
    )

    assert len(result.jobs) == 1
    assert [item.status for item in result.sources] == ["SUCCESS", "EMPTY"]
    assert result.sources[0].result_count == 1
    assert result.sources[1].result_count == 0


def test_job_store_round_trip(tmp_path):
    from storage import JobStore

    store = JobStore(tmp_path / "jobs.sqlite3")
    jobs = pd.DataFrame(
        [
            {
                "job_url": "https://example.com/1",
                "title": "GIS Analyst",
                "company": "Example",
                "location": "Jakarta",
                "date_posted": "2026-09-13",
                "site": "indeed",
                "description": "Remote role",
                "Work Type": "Remote",
            }
        ]
    )

    assert store.upsert_jobs(jobs) == 1
    loaded = store.load_jobs()
    assert len(loaded) == 1
    assert loaded.iloc[0]["application_status"] == "new"

    store.update_application_status("https://example.com/1", "shortlisted")
    assert store.load_jobs().iloc[0]["application_status"] == "shortlisted"
