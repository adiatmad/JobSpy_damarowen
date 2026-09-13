import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

import pandas as pd
from jobspy import scrape_jobs

from utils import is_permanent_block

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3
PER_SITE_TIMEOUT_SECONDS = 60


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


def scrape_one_site(
    site: str,
    search_term: str,
    location: str,
    country_indeed: str,
    results_wanted: int,
    hours_old: int,
    proxy: str = None,
) -> tuple[pd.DataFrame | None, str | None]:
    """Scrape one source with bounded retries and a real timeout.

    This is deliberately framework-agnostic so the scraper can later run from
    Streamlit, a CLI, a scheduled worker, or an API without importing Streamlit.
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
            return df, None
        except FutureTimeoutError:
            last_error = f"waktu habis ({PER_SITE_TIMEOUT_SECONDS} detik)"
            # Do not wait for a hung scraper here. The worker may still unwind in
            # the background, but the caller gets its bounded response time.
            executor.shutdown(wait=False, cancel_futures=True)
        except Exception as exc:
            last_error = str(exc)
            executor.shutdown(wait=False, cancel_futures=True)
            if is_permanent_block(last_error):
                break

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)

    return None, last_error


def scrape_one_site_cached(*args, **kwargs):
    """Backward-compatible entry point for the existing Streamlit UI.

    Caching belongs at the application/orchestration boundary, not inside the
    scraper. Keeping this alias avoids breaking the current UI while the engine
    is extracted incrementally.
    """
    return scrape_one_site(*args, **kwargs)
