"""Framework-agnostic orchestration for multi-source job searches."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from time import perf_counter

import pandas as pd

from discovery import search_searxng, searxng_url
from scraper import scrape_one_site_detailed

SOURCE_STATUSES = {
    "SUCCESS", "EMPTY", "BLOCKED", "RATE_LIMITED", "TIMEOUT",
    "PARSER_ERROR", "NETWORK_ERROR", "ERROR",
}


@dataclass(frozen=True)
class SourceResult:
    """Observable outcome of one source attempt."""
    source: str
    status: str
    result_count: int
    duration_ms: int
    attempts: int
    error: str | None = None
    started_at: str = ""

    def __post_init__(self):
        if self.status not in SOURCE_STATUSES:
            raise ValueError(f"Unsupported source status: {self.status}")

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SearchRun:
    """Complete, auditable result of a search across selected sources."""
    jobs: pd.DataFrame
    sources: tuple[SourceResult, ...]

    @property
    def source_health(self) -> list[dict]:
        return [result.to_dict() for result in self.sources]


def classify_error(error: str | None) -> str:
    if not error:
        return "ERROR"
    text = error.lower()
    if "waktu habis" in text or "timeout" in text:
        return "TIMEOUT"
    if any(token in text for token in ("blocked", "captcha", "forbidden", "403")):
        return "BLOCKED"
    if any(token in text for token in ("rate limit", "429", "too many requests")):
        return "RATE_LIMITED"
    if any(token in text for token in ("parse", "parser", "jsondecode", "keyerror")):
        return "PARSER_ERROR"
    if any(token in text for token in ("connection", "connect", "dns", "network")):
        return "NETWORK_ERROR"
    return "ERROR"


def _discover_with_searxng(search_term: str, location: str, results_wanted: int) -> tuple[pd.DataFrame, SourceResult]:
    endpoint = searxng_url()
    started = datetime.now(timezone.utc).isoformat()
    started_clock = perf_counter()
    if not endpoint:
        return pd.DataFrame(), SourceResult("searxng", "EMPTY", 0, 0, 0, "SEARXNG_URL not configured", started)

    query = " ".join(part for part in (search_term.strip(), location.strip()) if part)
    outcome = search_searxng(endpoint, query, max_results=results_wanted)
    duration_ms = int((perf_counter() - started_clock) * 1000)
    if outcome.error:
        return pd.DataFrame(), SourceResult(
            "searxng", classify_error(outcome.error), 0, duration_ms, 1, outcome.error, started
        )
    count = len(outcome.dataframe)
    if count:
        return outcome.dataframe, SourceResult("searxng", "SUCCESS", count, duration_ms, 1, None, started)
    return pd.DataFrame(), SourceResult("searxng", "EMPTY", 0, duration_ms, 1, None, started)


def search_sources(
    sites: list[str], *, search_term: str, location: str, country_indeed: str,
    results_wanted: int, hours_old: int, proxy: str = None,
) -> SearchRun:
    """Run selected JobSpy sources plus optional configured SearXNG discovery."""
    frames: list[pd.DataFrame] = []
    results: list[SourceResult] = []

    for site in sites:
        started = datetime.now(timezone.utc).isoformat()
        started_clock = perf_counter()
        outcome = scrape_one_site_detailed(
            site=site, search_term=search_term, location=location,
            country_indeed=country_indeed, results_wanted=results_wanted,
            hours_old=hours_old, proxy=proxy,
        )
        duration_ms = int((perf_counter() - started_clock) * 1000)

        if outcome.error:
            results.append(SourceResult(
                source=site, status=classify_error(outcome.error), result_count=0,
                duration_ms=duration_ms, attempts=outcome.attempts,
                error=outcome.error, started_at=started,
            ))
            continue

        df = outcome.dataframe
        count = 0 if df is None else len(df)
        if count:
            df = df.copy()
            if "site" not in df.columns:
                df["site"] = site
            frames.append(df)
            status = "SUCCESS"
        else:
            status = "EMPTY"

        results.append(SourceResult(
            source=site, status=status, result_count=count,
            duration_ms=duration_ms, attempts=outcome.attempts,
            started_at=started,
        ))

    discovered, discovery_status = _discover_with_searxng(search_term, location, results_wanted)
    if not discovered.empty:
        frames.append(discovered)
    results.append(discovery_status)

    jobs = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return SearchRun(jobs=jobs, sources=tuple(results))
