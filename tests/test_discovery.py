import pandas as pd

import discovery
import search_engine
from scraper import ScrapeResult




def test_build_career_discovery_queries_returns_bounded_variants():
    queries = discovery.build_career_discovery_queries("GIS Analyst", "Surabaya")
    assert len(queries) == 3
    assert all('"GIS Analyst"' in query for query in queries)
    assert all('"Surabaya"' in query for query in queries)
    assert any("inurl:careers" in query for query in queries)
    assert any("inurl:join-us" in query for query in queries)
    assert any('intitle:"join our team"' in query for query in queries)


def test_build_career_discovery_queries_remote_scope():
    queries = discovery.build_career_discovery_queries("GIS Analyst", "Remote worldwide")
    assert len(queries) == 3
    assert all("remote" in query for query in queries)
    assert all("work from home" in query for query in queries)


def test_build_searxng_query_targets_career_pages():
    query = discovery.build_searxng_query("GIS Analyst", "Surabaya")
    assert '"GIS Analyst"' in query
    assert '"Surabaya"' in query
    assert "inurl:careers" in query
    assert "inurl:jobs" in query
    assert "intitle:\"we're hiring\"" in query


def test_build_searxng_query_adds_remote_terms_for_remote_search():
    query = discovery.build_searxng_query("GIS Analyst", "Remote worldwide")
    assert "remote" in query
    assert "work from home" in query
    assert "distributed" in query


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
    result = discovery.search_searxng("http://searxng.local", '"GIS Analyst" "Surabaya"', max_results=5)
    assert result.error is None
    assert len(result.dataframe) == 1
    assert result.dataframe.iloc[0]["site"] == "searxng"
    assert result.dataframe.iloc[0]["job_url"] == "https://example.com/job"
    assert result.dataframe.iloc[0]["discovery_query"] == '"GIS Analyst" "Surabaya"'


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
    captured = {}

    def fake_search(*args, **kwargs):
        captured["query"] = args[1]
        return discovery.DiscoveryResult(pd.DataFrame([{
            "title": "GIS Analyst", "company": "", "location": "", "date_posted": "Unknown",
            "posted_age_hours": pd.NA, "description": "GIS role", "job_url": "https://example.com/job", "site": "searxng",
        }]))

    monkeypatch.setattr(search_engine, "search_searxng", fake_search)
    result = search_engine.search_sources(
        ["indeed"], search_term="GIS Analyst", location="Jakarta",
        country_indeed="Indonesia", results_wanted=5, hours_old=0,
    )
    assert len(result.jobs) == 1
    assert result.sources[-1].source == "searxng"
    assert result.sources[-1].status == "SUCCESS"
    assert '"GIS Analyst"' in captured["query"]
    assert '"Jakarta"' in captured["query"]
    assert "inurl:careers" in captured["query"]
