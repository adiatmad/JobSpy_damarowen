import pandas as pd

from intelligence import score_jobs
from pipeline import deduplicate_jobs, normalize_job_url, validate_jobs


def test_score_jobs_prefers_title_match():
    jobs = pd.DataFrame([
        {"title": "GIS Analyst", "description": "Mapping work", "location": "Jakarta", "Work Type": "On-site", "date_posted": "2026-09-12", "posted_age_hours": 24},
        {"title": "Project Manager", "description": "GIS project", "location": "Jakarta", "Work Type": "Remote", "date_posted": "2026-09-13", "posted_age_hours": 2},
    ])
    result = score_jobs(jobs, "GIS Analyst", "Jakarta")
    assert result.iloc[0]["title"] == "GIS Analyst"
    assert result.iloc[0]["Match Score"] > result.iloc[1]["Match Score"]


def test_location_mismatch_is_penalized():
    jobs = pd.DataFrame([
        {"title": "Management Trainee", "description": "", "location": "Jakarta", "Work Type": "On-site", "date_posted": "2026-09-13", "posted_age_hours": 3},
        {"title": "Management Trainee", "description": "", "location": "Surabaya", "Work Type": "On-site", "date_posted": "2026-09-13", "posted_age_hours": 3},
    ])
    result = score_jobs(jobs, "Management Trainee", "Jakarta")
    jakarta = result[result["location"] == "Jakarta"].iloc[0]
    surabaya = result[result["location"] == "Surabaya"].iloc[0]
    assert jakarta["Match Score"] > surabaya["Match Score"]
    assert "lokasi berbeda" in surabaya["Why Match"]


def test_seen_history_reduces_score():
    jobs = pd.DataFrame([
        {"title": "GIS Analyst", "description": "", "location": "Jakarta", "Work Type": "On-site", "date_posted": "2026-09-13", "posted_age_hours": 3, "job_url": "https://x/1"},
    ])
    fresh = score_jobs(jobs, "GIS Analyst", "Jakarta")
    seen = score_jobs(jobs, "GIS Analyst", "Jakarta", history={"https://x/1": {"seen_count": 3}})
    assert seen.iloc[0]["Match Score"] < fresh.iloc[0]["Match Score"]
    assert "sudah terlihat 3x" in seen.iloc[0]["Why Match"]


def test_deduplicate_jobs_drops_same_url_and_exact_key():
    jobs = pd.DataFrame([
        {"title": "GIS Analyst", "company": "Example", "job_url": "https://x/1"},
        {"title": "GIS Analyst", "company": "Example", "job_url": "https://x/1"},
        {"title": "GIS Analyst", "company": "Example", "job_url": "https://x/2"},
        {"title": "Data Engineer", "company": "Example", "job_url": "https://x/3"},
    ])
    result = deduplicate_jobs(jobs)
    assert len(result) == 2


def test_normalize_job_url_removes_tracking_noise():
    url = "HTTPS://Example.com/jobs/123/?utm_source=linkedin&foo=bar&fbclid=abc"
    assert normalize_job_url(url) == "https://example.com/jobs/123?foo=bar"


def test_validate_jobs_enforces_freshness_and_excludes_unknown_by_default():
    jobs = pd.DataFrame([
        {"title": "Fresh", "company": "A", "job_url": "https://x/1", "date_posted": "2026-09-13"},
        {"title": "Old", "company": "B", "job_url": "https://x/2", "date_posted": "2026-09-01"},
        {"title": "Unknown", "company": "C", "job_url": "https://x/3", "date_posted": None},
    ])
    result = validate_jobs(jobs, hours_old=24 * 30)
    assert set(result["title"]) == {"Fresh", "Old"}
    assert "Unknown" not in set(result["title"])
