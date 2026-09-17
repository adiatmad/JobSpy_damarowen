import pandas as pd

import discovery
import search_engine
from scraper import ScrapeResult


def test_search_searxng_normalizes_results(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"results": [
                {"title": "GIS Analyst", "url": "https://example.com/job", "content": "GIS role", "engine": "google"},
                {"title": "", "url": "https://example.com/no-title", "content": "skip"},
            ]}

    monkeypatch.setattr(discovery.requests, "get", lambda *args, **kwargs: Response())
    result = discovery.search_searxng("http://searxng.local", "GIS Analyst Jakarta", max_results=5)
    assert result.error is None
    assert len(result.dataframe) == 1
    assert result.dataframe.iloc[0]["site"] == "searxng"
    assert result.dataframe.iloc[0]["job_url"] == "https://example.com/job"


def test_search_searxng_requires_configured_endpoint():
    result = discovery.search_searxng("", "GIS Analyst")
    assert result.dataframe.empty
    assert result.error


def test_search_sources_does_not_call_searxng_when_unconfigured(monkeypatch):
    monkeypatch.setattr(search_engine, "searxng_url", lambda: "")
    monkeypatch.setattr(
        search_engine,
        "scrape_one_site_detailed",
        lambda **kwargs: ScrapeResult(pd.DataFrame([{"title": "GIS Analyst", "job_url": "https://example.com/1"}]), None, 1),
    )
    result = search_engine.search_sources(
        ["indeed"], search_term="GIS Analyst", location="Jakarta",
        country_indeed="Indonesia", results_wanted=5, hours_old=72,
    )
    assert [item.source for item in result.sources] == ["indeed"]
    assert len(result.jobs) == 1


def test_search_sources_adds_configured_searxng(monkeypatch):
    monkeypatch.setattr(search_engine, "searxng_url", lambda: "http://searxng.local")
    monkeypatch.setattr(
        search_engine,
        "scrape_one_site_detailed",
        lambda **kwargs: ScrapeResult(pd.DataFrame(), None, 1),
    )
    monkeypatch.setattr(
        search_engine,
        "search_searxng",
        lambda *args, **kwargs: discovery.DiscoveryResult(pd.DataFrame([{
            "title": "GIS Analyst", "company": "", "location": "", "date_posted": "Unknown",
            "posted_age_hours": pd.NA, "description": "GIS role", "job_url": "https://example.com/job", "site": "searxng",
        }])),
    )
    result = search_engine.search_sources(
        ["indeed"], search_term="GIS Analyst", location="Jakarta",
        country_indeed="Indonesia", results_wanted=5, hours_old=0,
    )
    assert len(result.jobs) == 1
    assert result.sources[-1].source == "searxng"
    assert result.sources[-1].status == "SUCCESS"
