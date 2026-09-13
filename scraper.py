"""Framework-agnostic JobSpy source adapter with bounded retries."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass

import pandas as pd
from jobspy import scrape_jobs

from utils import is_permanent_block

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3
PER_SITE_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class ScrapeResult:
    dataframe: pd.DataFrame | None
    error: str | None
    attempts: int


def build_kwargs_for_site(
    site: str,
    search_term: str,
    location: str,
    country_indeed: str,
    results_wanted: int,
    hours_old: int,
    proxy: str = None,
) -> dict:
    """Build JobSpy arguments without any UI/framework dependency."""
    kwargs = dict(site_name=[site], results_wanted=results_wanted, verbose=0)
    if location and location.strip():
        kwargs["location"] = location.strip()
    if site in ("indeed", "glassdoor"):
        kwargs["country_indeed"] = country_indeed
    if hours_old and hours_old > 0:
        kwargs["hours_old"] = int(hours_old)
    if search_term and search_term.strip():
        kwargs["search_term"] = search_term.strip()
    if proxy and proxy.strip():
        kwargs["proxies"] = [proxy.strip()]
    return kwargs


def scrape_one_site_detailed(
    site: str,
    search_term: str,
    location: str,
    country_indeed: str,
    results_wanted: int,
    hours_old: int,
    proxy: str = None,
) -> ScrapeResult:
    """Scrape one source and return the real number of attempts.

    A timed-out thread cannot be force-killed safely in CPython. Therefore a
    timeout is treated as a terminal attempt rather than starting another
    potentially overlapping network request. Ordinary transient errors may retry.
    """
    last_error = None
    kwargs = build_kwargs_for_site(
        site, search_term, location, country_indeed, results_wanted, hours_old, proxy
    )

    for attempt in range(1, MAX_RETRIES + 1):
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(scrape_jobs, **kwargs)
        try:
            df = future.result(timeout=PER_SITE_TIMEOUT_SECONDS)
            executor.shutdown(wait=False, cancel_futures=False)
            return ScrapeResult(df, None, attempt)
        except FutureTimeoutError:
            last_error = f"waktu habis ({PER_SITE_TIMEOUT_SECONDS} detik)"
            executor.shutdown(wait=False, cancel_futures=True)
            return ScrapeResult(None, last_error, attempt)
        except Exception as exc:
            last_error = str(exc)
            executor.shutdown(wait=False, cancel_futures=True)
            if is_permanent_block(last_error):
                break

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)

    return ScrapeResult(None, last_error, MAX_RETRIES if last_error else 0)


def scrape_one_site(
    site: str,
    search_term: str,
    location: str,
    country_indeed: str,
    results_wanted: int,
    hours_old: int,
    proxy: str = None,
) -> tuple[pd.DataFrame | None, str | None]:
    """Backward-compatible two-value adapter."""
    result = scrape_one_site_detailed(
        site=site,
        search_term=search_term,
        location=location,
        country_indeed=country_indeed,
        results_wanted=results_wanted,
        hours_old=hours_old,
        proxy=proxy,
    )
    return result.dataframe, result.error


def scrape_one_site_cached(*args, **kwargs):
    """Backward-compatible entry point for older callers."""
    return scrape_one_site(*args, **kwargs)
