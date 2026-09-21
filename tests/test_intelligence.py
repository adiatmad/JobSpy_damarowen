import pandas as pd

from intelligence import score_jobs
from pipeline import deduplicate_jobs, job_fingerprint, normalize_job_url, process_job_data, validate_jobs


def test_score_jobs_prefers_title_match():
    jobs = pd.DataFrame([
        {"title": "GIS Analyst", "description": "Mapping work", "location": "Jakarta", "Work Type": "On-site", "date_posted": "2026-09-12", "posted_age_hours": 24},
        {"title": "Project Manager", "description": "GIS project", "location": "Jakarta", "Work Type": "Remote", "date_posted": "2026-09-13", "posted_age_hours": 2},
    ])
    result = score_jobs(jobs, "GIS Analyst", "Jakarta")
    assert result.iloc[0]["title"] == "GIS Analyst"
    assert result.iloc[0]["Match Score"] > result.iloc[1]["Match Score"]
    assert result.iloc[0]["Relevance"] == "Strong"
    assert "Novelty" not in result.columns


def test_unrelated_title_cannot_look_like_strong_keyword_match():
    jobs = pd.DataFrame([
        {"title": "Management Trainee", "description": "", "location": "Jakarta", "posted_age_hours": 3},
        {"title": "Sales Strategy Intern", "description": "Management support", "location": "Jakarta", "posted_age_hours": 3},
    ])
    result = score_jobs(jobs, "Management Trainee", "Jakarta")
    strong = result[result["title"] == "Management Trainee"].iloc[0]
    weak = result[result["title"] == "Sales Strategy Intern"].iloc[0]
    assert strong["Relevance"] == "Strong"
    assert weak["Relevance"] == "Weak"
    assert strong["Match Score"] > weak["Match Score"]


def test_location_mismatch_is_penalized():
    jobs = pd.DataFrame([
        {"title": "Management Trainee", "description": "", "location": "Jakarta", "Work Type": "On-site", "date_posted": "2026-09-13", "posted_age_hours": 3},
        {"title": "Management Trainee", "description": "", "location": "Surabaya", "Work Type": "On-site", "date_posted": "2026-09-13", "posted_age_hours": 3},
    ])
    result = score_jobs(jobs, "Management Trainee", "Jakarta")
    jakarta = result[result["location"] == "Jakarta"].iloc[0]
    surabaya = result[result["location"] == "Surabaya"].iloc[0]
    assert jakarta["Match Score"] > surabaya["Match Score"]
    assert surabaya["Location Match"] == "Mismatch"
    assert "lokasi berbeda" in surabaya["Why Match"]


def test_location_match_accepts_city_variants():
    jobs = pd.DataFrame([
        {"title": "GIS Analyst", "description": "", "location": "West Jakarta, Jakarta, Indonesia", "posted_age_hours": 3},
    ])
    result = score_jobs(jobs, "GIS Analyst", "Jakarta")
    assert result.iloc[0]["Location Match"] == "Match"
    assert "lokasi cocok" in result.iloc[0]["Why Match"]


def test_location_does_not_match_different_known_city_with_shared_region_words():
    jobs = pd.DataFrame([
        {"title": "GIS Analyst", "description": "", "location": "Surabaya, East Java, Indonesia", "posted_age_hours": 3},
    ])
    result = score_jobs(jobs, "GIS Analyst", "Jakarta")
    assert result.iloc[0]["Location Match"] == "Mismatch"
    assert "lokasi berbeda" in result.iloc[0]["Why Match"]


def test_location_does_not_partially_match_different_city():
    jobs = pd.DataFrame([
        {"title": "GIS Analyst", "description": "", "location": "Jakarta Barat, Indonesia", "posted_age_hours": 3},
        {"title": "GIS Analyst", "description": "", "location": "Jakarta Selatan, Indonesia", "posted_age_hours": 3},
    ])
    result = score_jobs(jobs, "GIS Analyst", "Jakarta Selatan")
    south = result[result["location"].str.contains("Selatan")].iloc[0]
    west = result[result["location"].str.contains("Barat")].iloc[0]
    assert south["Location Match"] == "Match"
    assert west["Location Match"] == "Match"


def test_broad_indonesia_location_does_not_penalize_regional_jobs():
    jobs = pd.DataFrame([
        {"title": "GIS Analyst", "description": "", "location": "Jakarta", "posted_age_hours": 3},
        {"title": "GIS Analyst", "description": "", "location": "Surabaya", "posted_age_hours": 3},
    ])
    result = score_jobs(jobs, "GIS Analyst", "Indonesia")
    assert all("lokasi berbeda" not in reason for reason in result["Why Match"])
    assert all(result["Location Match"] == "Match")


def test_score_is_independent_of_job_history():
    jobs = pd.DataFrame([
        {"title": "GIS Analyst", "description": "", "location": "Jakarta", "posted_age_hours": 3, "job_url": "https://x/1"},
    ])
    first = score_jobs(jobs, "GIS Analyst", "Jakarta")
    second = score_jobs(jobs, "GIS Analyst", "Jakarta")
    assert first.iloc[0]["Match Score"] == second.iloc[0]["Match Score"]


def test_deduplicate_jobs_keeps_same_title_company_in_different_locations():
    jobs = pd.DataFrame([
        {"title": "Management Trainee", "company": "Example", "location": "Jakarta", "job_url": "https://x/jkt"},
        {"title": "Management Trainee", "company": "Example", "location": "Surabaya", "job_url": "https://x/sby"},
    ])
    assert len(deduplicate_jobs(jobs)) == 2


def test_deduplicate_jobs_drops_same_url_and_exact_key():
    jobs = pd.DataFrame([
        {"title": "GIS Analyst", "company": "Example", "location": "Jakarta", "job_url": "https://x/1"},
        {"title": "GIS Analyst", "company": "Example", "location": "Jakarta", "job_url": "https://x/1"},
        {"title": "GIS Analyst", "company": "Example", "location": "Jakarta", "job_url": "https://x/2"},
        {"title": "Data Engineer", "company": "Example", "location": "Jakarta", "job_url": "https://x/3"},
    ])
    assert len(deduplicate_jobs(jobs)) == 2


def test_normalize_job_url_removes_tracking_noise():
    url = "HTTPS://Example.com/jobs/123/?utm_source=linkedin&foo=bar&fbclid=abc"
    assert normalize_job_url(url) == "https://example.com/jobs/123?foo=bar"


def test_job_fingerprint_canonicalizes_location_variants():
    a = {"title": "Management Trainee", "company": "PT Example TBK", "location": "West Jakarta, Jakarta, Indonesia"}
    b = {"title": "Management Trainee", "company": "Example", "location": "Jakarta, JW, ID"}
    assert job_fingerprint(a) == job_fingerprint(b)


def test_validate_jobs_enforces_freshness_and_excludes_unknown_by_default():
    jobs = pd.DataFrame([
        {"title": "Fresh", "company": "A", "job_url": "https://x/1", "date_posted": "2026-09-13"},
        {"title": "Old", "company": "B", "job_url": "https://x/2", "date_posted": "2026-09-01"},
        {"title": "Unknown", "company": "C", "job_url": "https://x/3", "date_posted": None},
    ])
    result = validate_jobs(jobs, hours_old=24 * 30)
    assert set(result["title"]) == {"Fresh", "Old"}
    assert "Unknown" not in set(result["title"])


def test_financial_signal_is_conservative_when_salary_is_missing():
    jobs = pd.DataFrame([{"title": "GIS Analyst", "company": "Example", "location": "Jakarta", "description": "Salary undisclosed"}])
    result = process_job_data(jobs)
    assert result.iloc[0]["Financial Signal"] == "⚪ Gaji tidak diketahui"
    assert "UMR Rp 5.07M" in result.iloc[0]["Acuan Finansial"]


def test_evidence_coverage_exposes_missing_listing_fields_without_changing_match_score():
    jobs = pd.DataFrame([
        {"title": "GIS Analyst", "company": "Example", "location": "Jakarta", "date_posted": "2026-09-20", "description": "A " * 100, "posted_age_hours": 3},
        {"title": "GIS Analyst", "company": "Example", "location": "", "date_posted": "Unknown", "description": "", "posted_age_hours": pd.NA},
    ])
    result = score_jobs(jobs, "GIS Analyst", "Jakarta")
    complete = result[result["Evidence Coverage"] == 83].iloc[0]
    incomplete = result[result["Evidence Coverage"] == 33].iloc[0]
    assert "location" not in complete["Evidence Gaps"]
    assert "date" not in complete["Evidence Gaps"]
    assert "description" not in complete["Evidence Gaps"]
    assert "salary" in complete["Evidence Gaps"]
    assert "location" in incomplete["Evidence Gaps"]
    assert "date" in incomplete["Evidence Gaps"]
    assert "description" in incomplete["Evidence Gaps"]
    assert "salary" in incomplete["Evidence Gaps"]
