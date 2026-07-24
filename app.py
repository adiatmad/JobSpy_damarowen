import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

import pandas as pd
import streamlit as st
from jobspy import scrape_jobs
from jobspy.model import Country

st.set_page_config(page_title="Job Search Scraper", page_icon="🔎", layout="wide")

st.title("🔎 Job Search Scraper")
st.caption(
    "Powered by python-jobspy-damarowen — searches LinkedIn, Indeed, ZipRecruiter, "
    "Glassdoor, Google, and JobStreet. Keyword is optional — you can search by "
    "location and recency alone."
)

ALL_SITES = ["indeed", "linkedin", "zip_recruiter", "glassdoor", "google", "jobstreet"]
DEFAULT_SITES = ["indeed", "linkedin"]
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3
PER_SITE_TIMEOUT_SECONDS = 60


def glassdoor_supports_country(country_str: str) -> bool:
    """Ask the library itself whether Glassdoor has a domain for this country."""
    if not country_str or not country_str.strip():
        return False
    try:
        country = Country.from_string(country_str)
    except ValueError:
        return False
    return len(country.value) == 3  # 3rd tuple element = Glassdoor domain


def build_google_fallback_query(location: str, hours_old: int) -> str:
    """Build a valid Google Jobs query from location + recency when no keyword is given."""
    query = "jobs"
    if location and location.strip():
        query += f" in {location.strip()}"
    if hours_old and hours_old > 0:
        if hours_old <= 24:
            query += " since yesterday"
        elif hours_old <= 24 * 7:
            query += " this week"
        elif hours_old <= 24 * 30:
            query += " this month"
    return query


def build_kwargs_for_site(
    site: str, search_term: str, location: str, country_indeed: str,
    results_wanted: int, hours_old: int, is_remote: bool,
) -> dict:
    kwargs = dict(site_name=[site], results_wanted=results_wanted, verbose=0)
    if location and location.strip():
        kwargs["location"] = location.strip()
    if site in ("indeed", "glassdoor"):
        kwargs["country_indeed"] = country_indeed
    if hours_old and hours_old > 0:
        kwargs["hours_old"] = int(hours_old)
    if is_remote:
        kwargs["is_remote"] = True

    has_keyword = bool(search_term and search_term.strip())
    if site == "google":
        if has_keyword:
            kwargs["search_term"] = search_term.strip()
        else:
            # Google's scraper builds "{search_term} jobs" and breaks if search_term
            # is empty, so we always give it something usable.
            kwargs["google_search_term"] = build_google_fallback_query(location, hours_old)
    else:
        if has_keyword:
            kwargs["search_term"] = search_term.strip()

    return kwargs


def scrape_one_site(site: str, **kwargs_inputs) -> tuple[pd.DataFrame | None, str | None]:
    """Scrape a single site in isolation, with retries and a timeout. Never raises."""
    last_error = None
    kwargs = build_kwargs_for_site(site, **kwargs_inputs)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(scrape_jobs, **kwargs)
                df = future.result(timeout=PER_SITE_TIMEOUT_SECONDS)
            return df, None
        except FutureTimeoutError:
            last_error = f"timed out after {PER_SITE_TIMEOUT_SECONDS}s"
        except Exception as e:
            last_error = str(e)

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)

    return None, last_error


with st.sidebar:
    st.header("Search settings")

    location = st.text_input("Location", value="Jakarta")

    country_indeed = st.text_input(
        "Country (for Indeed/Glassdoor)",
        value="Indonesia",
        help="Only used by Indeed and Glassdoor. Use the exact country name, e.g. 'Indonesia', 'USA', 'Singapore'.",
    )

    search_term = st.text_input(
        "Job title / keywords (optional)",
        value="",
        help="Leave blank to get all valid postings for the location and recency filters below.",
    )

    st.caption("Job sites to search")
    glassdoor_ok = glassdoor_supports_country(country_indeed)
    sites = []
    cols = st.columns(2)
    for i, site in enumerate(ALL_SITES):
        col = cols[i % 2]
        if site == "glassdoor" and not glassdoor_ok:
            col.checkbox(
                "glassdoor 🚫",
                value=False,
                disabled=True,
                help=f"Glassdoor has no site for '{country_indeed}' in this library.",
                key="site_glassdoor",
            )
        else:
            checked = col.checkbox(site, value=(site in DEFAULT_SITES), key=f"site_{site}")
            if checked:
                sites.append(site)
    if not glassdoor_ok:
        st.caption(f"⚠️ Glassdoor is disabled — not available for '{country_indeed}'.")

    results_wanted = st.slider("Results per site", min_value=5, max_value=100, value=20, step=5)

    hours_old = st.number_input(
        "Only show jobs posted within (hours)",
        min_value=0,
        value=72,
        step=24,
        help="Set to 0 to ignore this filter.",
    )

    is_remote = st.checkbox("Remote jobs only", value=False)

    search_clicked = st.button("Search jobs", type="primary", use_container_width=True)

if search_clicked:
    if not sites:
        st.error("Pick at least one job site from the sidebar.")
        st.stop()

    common_inputs = dict(
        search_term=search_term,
        location=location,
        country_indeed=country_indeed,
        results_wanted=results_wanted,
        hours_old=hours_old,
        is_remote=is_remote,
    )

    all_dfs = []
    site_status = {}  # site -> ("ok", count) | ("empty", 0) | ("error", message)

    status_area = st.empty()
    for site in sites:
        status_area.info(f"Searching **{site}**...")
        df, err = scrape_one_site(site, **common_inputs)
        if err:
            site_status[site] = ("error", err)
        elif df is None or len(df) == 0:
            site_status[site] = ("empty", 0)
        else:
            site_status[site] = ("ok", len(df))
            all_dfs.append(df)
    status_area.empty()

    with st.expander("Per-site results", expanded=True):
        for site in sites:
            kind, info = site_status[site]
            if kind == "ok":
                st.success(f"**{site}**: {info} jobs found")
            elif kind == "empty":
                st.warning(f"**{site}**: no jobs found")
            else:
                st.error(f"**{site}**: failed — {info}")

    if not all_dfs:
        st.warning(
            "No jobs found from any site. Try a different location, fewer filters, "
            "or check the per-site errors above."
        )
    else:
        jobs = pd.concat(all_dfs, ignore_index=True)
        if "job_url" in jobs.columns:
            jobs = jobs.drop_duplicates(subset="job_url")

        st.success(f"Found {len(jobs)} jobs total across {len(all_dfs)} site(s)")

        preferred_cols = [
            "site", "title", "company", "location", "city", "state",
            "job_type", "is_remote", "date_posted", "min_amount", "max_amount",
            "currency", "job_url",
        ]
        existing_preferred = [c for c in preferred_cols if c in jobs.columns]
        other_cols = [c for c in jobs.columns if c not in existing_preferred]
        jobs = jobs[existing_preferred + other_cols]

        st.dataframe(jobs, use_container_width=True, hide_index=True)

        csv = jobs.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download results as CSV",
            data=csv,
            file_name="jobs.csv",
            mime="text/csv",
        )
else:
    st.info("Set your search options in the sidebar, then click **Search jobs**.")
