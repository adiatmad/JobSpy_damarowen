from scraper import SOURCE_HELP, SOURCE_LABELS, SUPPORTED_SITES, build_kwargs_for_site


def test_supported_sources_match_pinned_jobspy_adapter_inventory():
    assert SUPPORTED_SITES == (
        "indeed",
        "linkedin",
        "google",
        "zip_recruiter",
        "glassdoor",
        "bayt",
        "naukri",
        "bdjobs",
    )
    assert set(SOURCE_LABELS) == set(SUPPORTED_SITES)
    assert set(SOURCE_HELP) == set(SUPPORTED_SITES)


def test_google_jobs_uses_dedicated_query_with_role_and_location():
    kwargs = build_kwargs_for_site(
        site="google",
        search_term="GIS analyst",
        location="Indonesia",
        country_indeed="Indonesia",
        results_wanted=15,
        hours_old=72,
    )

    assert kwargs["site_name"] == ["google"]
    assert kwargs["google_search_term"] == "GIS analyst jobs near Indonesia"
    assert "country_indeed" not in kwargs


def test_google_jobs_query_without_location_is_still_a_job_query():
    kwargs = build_kwargs_for_site(
        site="google",
        search_term="GIS analyst",
        location="",
        country_indeed="Indonesia",
        results_wanted=15,
        hours_old=72,
    )

    assert kwargs["google_search_term"] == "GIS analyst jobs"


def test_country_filter_is_only_sent_to_indeed_and_glassdoor():
    for site in ("indeed", "glassdoor"):
        kwargs = build_kwargs_for_site(
            site=site,
            search_term="GIS analyst",
            location="Indonesia",
            country_indeed="Indonesia",
            results_wanted=15,
            hours_old=72,
        )
        assert kwargs["country_indeed"] == "Indonesia"

    for site in ("linkedin", "google", "zip_recruiter", "bayt", "naukri", "bdjobs"):
        kwargs = build_kwargs_for_site(
            site=site,
            search_term="GIS analyst",
            location="Indonesia",
            country_indeed="Indonesia",
            results_wanted=15,
            hours_old=72,
        )
        assert "country_indeed" not in kwargs
