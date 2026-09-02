import time
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from jobspy import scrape_jobs
from utils import is_permanent_block

MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3
PER_SITE_TIMEOUT_SECONDS = 60

def build_kwargs_for_site(site: str, search_term: str, location: str, country_indeed: str, results_wanted: int, hours_old: int) -> dict:
    kwargs = dict(site_name=[site], results_wanted=results_wanted, verbose=0)
    if location and location.strip():
        kwargs["location"] = location.strip()
    if site in ("indeed", "glassdoor"):
        kwargs["country_indeed"] = country_indeed
    if hours_old and hours_old > 0:
        kwargs["hours_old"] = int(hours_old)
    if search_term and search_term.strip():
        kwargs["search_term"] = search_term.strip()
    return kwargs

def scrape_one_site(site: str, **kwargs_inputs) -> tuple[pd.DataFrame | None, str | None]:
    """Scrape 1 situs dengan batas waktu dan proteksi retry aman."""
    last_error = None
    kwargs = build_kwargs_for_site(site, **kwargs_inputs)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(scrape_jobs, **kwargs)
                df = future.result(timeout=PER_SITE_TIMEOUT_SECONDS)
            return df, None
        except FutureTimeoutError:
            last_error = f"waktu habis ({PER_SITE_TIMEOUT_SECONDS} detik)"
        except Exception as e:
            last_error = str(e)
            if is_permanent_block(last_error):
                break

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)

    return None, last_error