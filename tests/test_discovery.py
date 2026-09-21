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


def test_search_searxng_preserves_published_date(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"results": [{
                "title": "GIS Analyst",
                "url": "https://example.com/job",
                "content": "GIS role",
                "engine": "google",
                "publishedDate": "2026-09-20T10:00:00+00:00",
            }]}

    monkeypatch.setattr(discovery.requests, "get", lambda *args, **kwargs: Response())
    result = discovery.search_searxng("http://searxng.local", "GIS Analyst", max_results=5)
    assert result.dataframe.iloc[0]["date_posted"] == "2026-09-20T10:00:00+00:00"


def test_search_searxng_requires_configured_endpoint():
    result = discovery.search_searxng("", "GIS Analyst")
    assert result.dataframe.empty
    assert result.error


def test_scrapling_is_opt_in(monkeypatch):
    monkeypatch.delenv("JOBSPY_SCRAPLING", raising=False)
    assert discovery.scrapling_enabled() is False
    monkeypatch.setenv("JOBSPY_SCRAPLING", "1")
    assert discovery.scrapling_enabled() is True


def test_fetch_with_scrapling_uses_main_content_markdown(monkeypatch):
    class FakePage:
        def markdown(self, main_content_only=False):
            assert main_content_only is True
            return "# GIS Analyst\n\nApply here"

    class FakeFetcher:
        @staticmethod
        def get(url):
            assert url == "https://example.com/job"
            return FakePage()

    import types
    monkeypatch.setitem(__import__("sys").modules, "scrapling", types.ModuleType("scrapling"))
    fetchers = types.ModuleType("scrapling.fetchers")
    fetchers.Fetcher = FakeFetcher
    monkeypatch.setitem(__import__("sys").modules, "scrapling.fetchers", fetchers)
    assert discovery.fetch_with_scrapling("https://example.com/job") == "# GIS Analyst\n\nApply here"


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
    captured = {"queries": [], "limits": []}

    def fake_search(*args, **kwargs):
        captured["queries"].append(args[1])
        captured["limits"].append(kwargs["max_results"])
        return discovery.DiscoveryResult(pd.DataFrame([{
            "title": "GIS Analyst", "company": "", "location": "", "date_posted": "Unknown",
            "posted_age_hours": pd.NA, "description": "GIS role", "job_url": "https://example.com/job", "site": "searxng",
        }]))

    monkeypatch.setattr(search_engine, "search_searxng", fake_search)
    monkeypatch.setattr(search_engine, "scrapling_enabled", lambda: False)
    monkeypatch.setattr(search_engine, "crawl4ai_enabled", lambda: False)
    result = search_engine.search_sources(
        ["indeed"], search_term="GIS Analyst", location="Jakarta",
        country_indeed="Indonesia", results_wanted=5, hours_old=0,
    )
    assert len(result.jobs) == 1
    assert result.sources[-1].source == "searxng"
    assert result.sources[-1].status == "SUCCESS"
    assert len(captured["queries"]) == 3
    assert captured["limits"] == [2, 2, 2]
    assert len(result.jobs) == 1
    assert all('"GIS Analyst"' in query for query in captured["queries"])
    assert all('"Jakarta"' in query for query in captured["queries"])
    assert any("inurl:careers" in query for query in captured["queries"])
    assert any("inurl:join-us" in query for query in captured["queries"])
    assert any('intitle:"join our team"' in query for query in captured["queries"])


def test_search_sources_uses_scrapling_before_crawl4ai(monkeypatch):
    monkeypatch.setattr(search_engine, "searxng_url", lambda: "http://searxng.local")
    monkeypatch.setattr(search_engine, "scrapling_enabled", lambda: True)
    monkeypatch.setattr(search_engine, "crawl4ai_enabled", lambda: True)
    monkeypatch.setattr(search_engine, "fetch_with_scrapling", lambda url: "# Full job page")
    monkeypatch.setattr(search_engine, "fetch_with_crawl4ai", lambda url: (_ for _ in ()).throw(AssertionError("Crawl4AI should not run when Scrapling succeeds")))
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
            "posted_age_hours": pd.NA, "description": "short", "job_url": "https://example.com/job", "site": "searxng",
        }])),
    )

    result = search_engine.search_sources(
        ["indeed"], search_term="GIS Analyst", location="Jakarta",
        country_indeed="Indonesia", results_wanted=5, hours_old=0,
    )
    assert result.jobs.iloc[0]["description"] == "# Full job page"
    assert result.jobs.iloc[0]["discovery_method"] == "searxng+scrapling"


def test_build_google_career_search_term():
    from utils import build_google_career_search_term

    query = build_google_career_search_term("GIS Analyst", "Surabaya")
    assert '"GIS Analyst"' in query
    assert '"Surabaya"' in query
    assert "inurl:careers" in query
    assert "inurl:jobs" in query
    assert 'intitle:"we\'re hiring"' in query
    assert 'intitle:"join our team"' in query
    assert "remote" not in query

    remote_query = build_google_career_search_term("GIS Analyst", "Remote worldwide", remote=True)
    assert "remote" in remote_query
    assert "work from home" in remote_query
    assert "distributed" in remote_query
