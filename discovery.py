"""Optional discovery helpers for search-engine results and browser fallback.

The core application does not require these integrations. Set ``SEARXNG_URL``
to enable metasearch discovery, and explicitly enable Scrapling or Crawl4AI
before using page enrichment. Enrichment is deliberately bounded.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from urllib.parse import urljoin

import pandas as pd
import requests


CAREER_PATH_TERMS = (
    "inurl:careers",
    "inurl:jobs",
    "inurl:join-us",
    'intitle:"we\'re hiring"',
    'intitle:"join our team"',
)
REMOTE_TERMS = (
    "remote",
    "work from home",
    "distributed",
)


@dataclass(frozen=True)
class DiscoveryResult:
    """A discovery outcome that can be represented by the search engine."""

    dataframe: pd.DataFrame
    error: str | None = None


def _searxng_endpoint(base_url: str) -> str:
    base = base_url.rstrip("/")
    return base if base.endswith("/search") else urljoin(base + "/", "search")


def build_career_discovery_queries(search_term: str, location: str = "") -> list[str]:
    """Build a small set of focused career-page discovery queries."""
    term = search_term.strip()
    place = location.strip()
    if not term:
        return []

    base = [f'"{term}"']
    if place:
        base.append(f'"{place}"')
    prefix = " ".join(base)

    queries = [
        f"{prefix} (inurl:careers OR inurl:jobs)",
        f"{prefix} (inurl:join-us OR intitle:\"we're hiring\")",
        f"{prefix} (intitle:\"join our team\" OR \"careers\")",
    ]

    location_lower = place.casefold()
    if any(token in location_lower for token in ("remote", "worldwide", "anywhere", "global")):
        remote_scope = "(" + " OR ".join(REMOTE_TERMS) + ")"
        queries = [f"{query} {remote_scope}" for query in queries]

    return queries


def build_searxng_query(search_term: str, location: str = "") -> str:
    """Backward-compatible single-query form for callers that need one query."""
    queries = build_career_discovery_queries(search_term, location)
    return queries[0] if queries else ""


def search_searxng(
    base_url: str,
    query: str,
    *,
    max_results: int = 20,
    timeout: int = 10,
) -> DiscoveryResult:
    """Query a configured SearXNG instance using its JSON search API."""
    if not base_url or not query.strip():
        return DiscoveryResult(pd.DataFrame(), "SearXNG URL or query is empty")
    try:
        response = requests.get(
            _searxng_endpoint(base_url),
            params={"q": query.strip(), "format": "json"},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        rows = []
        for item in payload.get("results", [])[:max_results]:
            url = str(item.get("url", "")).strip()
            title = str(item.get("title", "")).strip()
            if not url or not title:
                continue
            published_date = item.get("publishedDate") or item.get("published_date") or item.get("date") or "Unknown"
            rows.append({
                "title": title,
                "company": "",
                "location": "",
                "date_posted": str(published_date).strip() or "Unknown",
                "posted_age_hours": pd.NA,
                "description": str(item.get("content", "")),
                "job_url": url,
                "site": "searxng",
                "discovery_source": str(item.get("engine", "searxng")),
                "discovery_query": query.strip(),
            })
        return DiscoveryResult(pd.DataFrame(rows))
    except (requests.RequestException, ValueError, TypeError) as exc:
        return DiscoveryResult(pd.DataFrame(), str(exc))


def scrapling_enabled() -> bool:
    """Return whether optional Scrapling enrichment was explicitly enabled."""
    return os.getenv("JOBSPY_SCRAPLING", "0").strip().lower() in {"1", "true", "yes", "on"}


def fetch_with_scrapling(url: str) -> str:
    """Fetch a discovered page with Scrapling and return main-content markdown.

    The import is lazy so the core application remains usable without the
    optional dependency. Scrapling is used as a bounded page-enrichment layer,
    not as a replacement for JobSpy's structured source adapters.
    """
    if not url.strip():
        raise ValueError("URL is empty")
    from scrapling.fetchers import Fetcher

    page = Fetcher.get(url.strip())
    markdown = page.markdown(main_content_only=True)
    return str(markdown or "")


async def _crawl4ai_markdown(url: str) -> str:
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url)
        if not result.success:
            raise RuntimeError(result.error_message or "Crawl4AI crawl failed")
        markdown = result.markdown
        return markdown.raw_markdown if hasattr(markdown, "raw_markdown") else str(markdown or "")


def fetch_with_crawl4ai(url: str) -> str:
    """Fetch rendered page content; the optional dependency is imported lazily."""
    if not url.strip():
        raise ValueError("URL is empty")
    return asyncio.run(_crawl4ai_markdown(url))


def crawl4ai_enabled() -> bool:
    """Return whether the browser fallback was explicitly enabled."""
    return os.getenv("JOBSPY_CRAWL4AI", "0").strip().lower() in {"1", "true", "yes", "on"}


def searxng_url() -> str:
    """Return the configured SearXNG endpoint, if any."""
    return os.getenv("SEARXNG_URL", "").strip()
