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
    "Glassdoor, and Google. Keyword is optional — you can search by location and "
    "recency alone."
)

# JobStreet removed: this fork's JobStreet scraper is consistently blocked by
# Cloudflare (WAF challenge page, HTTP 403) when run from Streamlit Community
# Cloud's shared IPs — it never returns real results here, so keeping it in the
# list just wastes a retry cycle and misleads users into thinking it's an option.
ALL_SITES = ["indeed", "linkedin", "zip_recruiter", "glassdoor", "google"]
DEFAULT_SITES = ["indeed", "linkedin"]
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3
PER_SITE_TIMEOUT_SECONDS = 60

# Substrings that indicate a permanent anti-bot block rather than a transient
# network hiccup. Retrying against these wastes time — Cloudflare doesn't care
# how many times you ask again in the next 3 seconds.
PERMANENT_BLOCK_MARKERS = ("403", "cf-waf", "forbidden", "cloudflare", "just a moment")


def is_permanent_block(error_msg: str) -> bool:
    if not error_msg:
        return False
    lowered = error_msg.lower()
    return any(marker in lowered for marker in PERMANENT_BLOCK_MARKERS)


def glassdoor_supports_country(country_str: str) -> bool:
    """Ask the library itself whether Glassdoor has a domain for this country."""
    if not country_str or not country_str.strip():
        return False
    try:
        country = Country.from_string(country_str)
    except ValueError:
        return False
    return len(country.value) == 3  # 3rd tuple element = Glassdoor domain


def build_google_search_term(search_term: str, location: str, hours_old: int) -> str:
    """Build the query Google Jobs expects: '<keyword> jobs near <location> since <recency>'.

    google_search_term is the ONLY param that actually filters Google Jobs results —
    plain search_term is ignored by the Google scraper. This builds it whether or not
    the user typed a keyword, matching the syntax Google's own search box expects.
    """
    term = search_term.strip() if search_term and search_term.strip() else ""
    if not term:
        term = "jobs"
    elif not term.lower().endswith("jobs"):
        term += " jobs"

    if location and location.strip():
        term += f" near {location.strip()}"

    if hours_old and hours_old > 0:
        if hours_old <= 24:
            term += " since yesterday"
        elif hours_old <= 24 * 7:
            term += " this week"
        elif hours_old <= 24 * 30:
            term += " this month"

    return term


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
        # google_search_term is the only param that filters Google Jobs — build it
        # whether or not the user typed a keyword.
        kwargs["google_search_term"] = build_google_search_term(search_term, location, hours_old)
    else:
        if has_keyword:
            kwargs["search_term"] = search_term.strip()

    return kwargs


def scrape_one_site(site: str, **kwargs_inputs) -> tuple[pd.DataFrame | None, str | None]:
    """Scrape a single site in isolation, with retries and a timeout. Never raises.

    Retries only on transient failures (timeouts, network errors). A detected
    permanent block (403 / cf-waf / Cloudflare challenge) exits immediately —
    retrying that within seconds never succeeds and only slows the search down.
    """
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
            if is_permanent_block(last_error):
                break  # hard block — further attempts won't help

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)

    return None, last_error


def validate_jobs(jobs: pd.DataFrame, hours_old: int) -> pd.DataFrame:
    """Drop rows that don't look like real, current postings.

    Scrapers occasionally return rows with missing fields or dates outside the
    requested window (some sites don't strictly enforce their own recency
    filter). This re-checks the basics ourselves rather than trusting the raw
    scrape as "valid" by default.
    """
    if jobs.empty:
        return jobs

    for col in ("title", "company"):
        if col in jobs.columns:
            jobs = jobs[jobs[col].notna() & (jobs[col].astype(str).str.strip() != "")]

    if "job_url" in jobs.columns:
        jobs = jobs[jobs["job_url"].notna() & (jobs["job_url"].astype(str).str.strip() != "")]

    if hours_old and hours_old > 0 and "date_posted" in jobs.columns:
        cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(hours=hours_old)
        parsed_dates = pd.to_datetime(jobs["date_posted"], errors="coerce")
        # Only drop rows we can confidently parse as stale — don't punish rows
        # where the site simply didn't supply a parseable date.
        stale_mask = parsed_dates.notna() & (parsed_dates < cutoff)
        jobs = jobs[~stale_mask]

    return jobs


def dedupe_cross_site(jobs: pd.DataFrame) -> pd.DataFrame:
    """Catch the same posting appearing on multiple boards under different URLs.

    The existing job_url dedup only catches exact-URL repeats within one run —
    it misses e.g. the same listing showing up via both Indeed and Google Jobs.
    """
    if jobs.empty:
        return jobs
    key_cols = [c for c in ("title", "company", "location") if c in jobs.columns]
    if not key_cols:
        return jobs
    normalized_key = jobs[key_cols].apply(
        lambda row: "|".join(str(v).strip().lower() for v in row), axis=1
    )
    jobs = jobs.assign(_dedupe_key=normalized_key)
    jobs = jobs.drop_duplicates(subset="_dedupe_key").drop(columns="_dedupe_key")
    return jobs


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
    st.caption(
        "⚠️ zip_recruiter only covers US/Canada listings — irrelevant results are "
        "expected for other locations."
    )

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

        raw_count = len(jobs)
        jobs = validate_jobs(jobs, hours_old)
        jobs = dedupe_cross_site(jobs)
        filtered_count = raw_count - len(jobs)

        if jobs.empty:
            st.warning(
                f"Found {raw_count} raw result(s), but none passed validation "
                "(missing title/company, no URL, or stale date_posted). Try "
                "loosening the filters."
            )
        else:
            summary = f"Found {len(jobs)} valid jobs across {len(all_dfs)} site(s)"
            if filtered_count:
                summary += f" — {filtered_count} filtered out as incomplete, stale, or duplicate"
            st.success(summary)

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
