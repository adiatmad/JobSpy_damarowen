"""Framework-agnostic orchestration for multi-source job searches."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from time import perf_counter

import pandas as pd

from scraper import scrape_one_site

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


def search_sources(
    sites: list[str], *, search_term: str, location: str, country_indeed: str,
    results_wanted: int, hours_old: int, proxy: str = None,
) -> SearchRun:
    """Run selected sources sequentially and return jobs plus observability.

    Sequential execution is intentional for now: source reliability is measured
    before concurrency is introduced.
    """
    frames: list[pd.DataFrame] = []
    results: list[SourceResult] = []

    for site in sites:
        started = datetime.now(timezone.utc).isoformat()
        started_clock = perf_counter()
        df, error = scrape_one_site(
            site=site, search_term=search_term, location=location,
            country_indeed=country_indeed, results_wanted=results_wanted,
            hours_old=hours_old, proxy=proxy,
        )
        duration_ms = int((perf_counter() - started_clock) * 1000)

        if error:
            results.append(SourceResult(
                source=site, status=classify_error(error), result_count=0,
                duration_ms=duration_ms, attempts=2, error=error, started_at=started,
            ))
            continue

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
            duration_ms=duration_ms, attempts=1, started_at=started,
        ))

    jobs = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return SearchRun(jobs=jobs, sources=tuple(results))
