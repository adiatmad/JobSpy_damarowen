import pandas as pd

from intelligence import score_jobs
from pipeline import deduplicate_jobs


def test_score_jobs_prefers_title_match():
    jobs = pd.DataFrame([
        {"title": "GIS Analyst", "description": "Mapping work", "location": "Jakarta", "Work Type": "On-site", "date_posted": "2026-09-12"},
        {"title": "Project Manager", "description": "GIS project", "location": "Jakarta", "Work Type": "Remote", "date_posted": "2026-09-13"},
    ])
    result = score_jobs(jobs, "GIS Analyst", "Jakarta")
    assert result.iloc[0]["title"] == "GIS Analyst"
    assert result.iloc[0]["Match Score"] > result.iloc[1]["Match Score"]


def test_deduplicate_jobs_drops_same_url_and_exact_key():
    jobs = pd.DataFrame([
        {"title": "GIS Analyst", "company": "Example", "job_url": "https://x/1"},
        {"title": "GIS Analyst", "company": "Example", "job_url": "https://x/1"},
        {"title": "GIS Analyst", "company": "Example", "job_url": "https://x/2"},
        {"title": "Data Engineer", "company": "Example", "job_url": "https://x/3"},
    ])
    result = deduplicate_jobs(jobs)
    assert len(result) == 2
