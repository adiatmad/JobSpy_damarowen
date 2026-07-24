import concurrent.futures
import time

import pandas as pd
import streamlit as st
from jobspy import scrape_jobs
from jobspy.model import Country

st.set_page_config(page_title="Job Search Scraper", page_icon="🔎", layout="wide")

st.title("🔎 Job Search Scraper")
st.caption(
    "Powered by python-jobspy-damarowen — searches LinkedIn, Indeed, ZipRecruiter, "
    "Glassdoor, Google, and JobStreet."
)

SITE_LABELS = {
    "indeed": "Indeed",
    "linkedin": "LinkedIn",
    "zip_recruiter": "ZipRecruiter",
    "glassdoor": "Glassdoor",
    "google": "Google",
    "jobstreet": "JobStreet",
}
DEFAULT_ON = {"indeed", "linkedin"}

MAX_RETRIES = 2
RETRY_BACKOFF_SEC = 3
SITE_TIMEOUT_SEC = 60


def glassdoor_supported(country_name: str) -> bool:
    """Glassdoor only has a domain for some countries in this library.
    We check the library's own Country enum instead of hardcoding a list,
    so this stays correct if the library adds/removes country support."""
    try:
        country = Country.from_string(country_name)
    except ValueError:
        return False
    # Country.value is (names, indeed_code) or (names, indeed_code, glassdoor_code).
    # A 3rd element means Glassdoor has a domain for this country.
    return len(country.value) == 3


def scrape_one_site(site, search_term, location, country_indeed, results_wanted, hours_old, is_remote):
    """Scrape a single site with retries + a hard timeout. Never raises —
    returns (dataframe_or_None, error_message_or_None) so one bad site
    can't take down the others."""
    kwargs = dict(
        site_name=[site],
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        country_indeed=country_indeed,
        verbose=0,
    )
    if hours_old and hours_old > 0:
        kwargs["hours_old"] = int(hours_old)
    if is_remote:
        kwargs["is_remote"] = True

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                future = ex.submit(scrape_jobs, **kwargs)
                df = future.result(timeout=SITE_TIMEOUT_SEC)
            if df is None:
                return pd.DataFrame(), None
            return df, None
        except concurrent.futures.TimeoutError:
            last_error = f"timed out after {SITE_TIMEOUT_SEC}s (site may be blocking automated requests)"
        except Exception as e:
            last_error = str(e)
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_BACKOFF_SEC * attempt)

    return None, last_error


with st.sidebar:
    st.header("Search settings")

    search_term = st.text_input("Job title / keywords", value="software engineer")
    location = st.text_input("Location", value="Jakarta")
    country_indeed = st.text_input(
        "Country (for Indeed/Glassdoor)",
        value="Indonesia",
        help="Only used by Indeed and Glassdoor. Use the exact country name, e.g. 'Indonesia', 'USA', 'Singapore'.",
    )

    gd_ok = glassdoor_supported(country_indeed)

    st.subheader("Job sites to search")
    selected_sites = []
    for site in ["indeed", "linkedin", "zip_recruiter", "glassdoor", "google", "jobstreet"]:
        if site == "glassdoor" and not gd_ok:
            st.checkbox(
                f"{SITE_LABELS[site]} (unavailable for this country)",
                value=False,
                disabled=True,
                key=f"site_{site}",
                help="Glassdoor has no site for this country in the underlying library — "
                "selecting it would crash the whole search, so it's disabled automatically.",
            )
            continue
        checked = st.checkbox(
            SITE_LABELS[site], value=(site in DEFAULT_ON), key=f"site_{site}"
        )
        if checked:
            selected_sites.append(site)

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
    if not selected_sites:
        st.error("Pick at least one job site from the sidebar.")
        st.stop()

    results = {}
    errors = {}
    progress = st.progress(0.0, text="Starting...")

    for i, site in enumerate(selected_sites):
        progress.progress(i / len(selected_sites), text=f"Searching {SITE_LABELS[site]}...")
        df, err = scrape_one_site(
            site, search_term, location, country_indeed, results_wanted, hours_old, is_remote
        )
        if err:
            errors[site] = err
        else:
            results[site] = df
    progress.progress(1.0, text="Done")
    progress.empty()

    with st.expander("Per-site results", expanded=True):
        for site in selected_sites:
            if site in results:
                st.success(f"**{SITE_LABELS[site]}**: {len(results[site])} jobs found")
            else:
                st.warning(f"**{SITE_LABELS[site]}**: failed — {errors.get(site, 'unknown error')}")

    non_empty = [df for df in results.values() if df is not None and len(df) > 0]

    if not non_empty:
        st.warning(
            "No jobs found from any site. Try different keywords, a different location, "
            "fewer filters, or check the per-site results above for errors."
        )
    else:
        jobs = pd.concat(non_empty, ignore_index=True)
        if "job_url" in jobs.columns:
            jobs = jobs.drop_duplicates(subset=["job_url"])

        st.success(f"Found {len(jobs)} jobs total across {len(non_empty)} site(s)")

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
