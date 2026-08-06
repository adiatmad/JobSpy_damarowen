import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime
import urllib.parse

import pandas as pd
import streamlit as st
from jobspy import scrape_jobs
from jobspy.model import Country

st.set_page_config(page_title="Job Search Scraper", page_icon="🔎", layout="wide")

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
ALL_SITES = ["indeed", "linkedin", "zip_recruiter", "glassdoor"]   # Google removed
DEFAULT_SITES = ["indeed", "linkedin"]
MAX_RETRIES = 2
RETRY_DELAY_SECONDS = 3
PER_SITE_TIMEOUT_SECONDS = 60

PERMANENT_BLOCK_MARKERS = ("403", "cf-waf", "forbidden", "cloudflare", "just a moment")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def is_permanent_block(error_msg: str) -> bool:
    if not error_msg:
        return False
    lowered = error_msg.lower()
    return any(marker in lowered for marker in PERMANENT_BLOCK_MARKERS)

def glassdoor_supports_country(country_str: str) -> bool:
    try:
        country = Country.from_string(country_str)
    except ValueError:
        return False
    return len(country.value) == 3

def build_google_search_term(search_term: str, location: str, hours_old: int) -> str:
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
    results_wanted: int, hours_old: int,
) -> dict:
    kwargs = dict(site_name=[site], results_wanted=results_wanted, verbose=0)

    if location and location.strip():
        kwargs["location"] = location.strip()

    if site in ("indeed", "glassdoor"):
        kwargs["country_indeed"] = country_indeed

    if hours_old and hours_old > 0:
        kwargs["hours_old"] = int(hours_old)

    # is_remote removed entirely – no longer passed

    if search_term and search_term.strip():
        kwargs["search_term"] = search_term.strip()

    return kwargs

def scrape_one_site(site: str, **kwargs_inputs) -> tuple[pd.DataFrame | None, str | None]:
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
                break

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)

    return None, last_error

def validate_jobs(jobs: pd.DataFrame, hours_old: int) -> pd.DataFrame:
    if jobs.empty:
        return jobs

    for col in ("title", "company"):
        if col in jobs.columns:
            jobs = jobs[jobs[col].notna() & (jobs[col].astype(str).str.strip() != "")]

    if "job_url" in jobs.columns:
        jobs = jobs[jobs["job_url"].notna() & (jobs["job_url"].astype(str).str.strip() != "")]

    if hours_old and hours_old > 0 and "date_posted" in jobs.columns:
        cutoff = pd.Timestamp.now().normalize() - pd.Timedelta(hours=int(hours_old))
        parsed_dates = pd.to_datetime(jobs["date_posted"], errors="coerce")
        stale_mask = parsed_dates.notna() & (parsed_dates < cutoff)
        jobs = jobs[~stale_mask]

    return jobs

def dedupe_cross_site(jobs: pd.DataFrame) -> pd.DataFrame:
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

# ----------------------------------------------------------------------
# Tab UI
# ----------------------------------------------------------------------
tab1, tab2 = st.tabs(["🔍 Search Jobs", "📖 Job Search Playbook"])

# ==================== TAB 1: SEARCH ====================
with tab1:
    st.caption(
        "Powered by python-jobspy-damarowen — searches LinkedIn, Indeed, ZipRecruiter, "
        "and Glassdoor. Keyword is optional.\n\n"
        "**Google is not scraped** — a manual search suggestion is provided after scraping if you enable it."
    )

    with st.sidebar:
        st.header("Search settings")

        location = st.text_input(
            "Location (optional)",
            value="",
            help="Leave empty for broader search (useful for remote)."
        )
        if not location:
            st.caption("💡 Location empty → will try to search broadly.")

        country_indeed = st.text_input(
            "Country (for Indeed/Glassdoor)",
            value="Indonesia",
            help="Only used by Indeed and Glassdoor. Use exact name, e.g. 'Indonesia', 'USA'."
        )
        search_term = st.text_input(
            "Job title / keywords (optional)",
            value="",
            help="Leave blank to get all postings for the location and recency filters."
        )

        st.caption("Job sites to scrape")
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
                    help=f"Glassdoor has no site for '{country_indeed}'.",
                    key="site_glassdoor",
                )
            else:
                checked = col.checkbox(site, value=(site in DEFAULT_SITES), key=f"site_{site}")
                if checked:
                    sites.append(site)

        if not glassdoor_ok:
            st.caption(f"⚠️ Glassdoor is disabled — not available for '{country_indeed}'.")
        st.caption(
            "⚠️ zip_recruiter only covers US/Canada listings — irrelevant results for other locations."
        )

        results_wanted = st.slider("Results per site", min_value=5, max_value=100, value=20, step=5)
        hours_old = st.number_input(
            "Only show jobs posted within (hours)",
            min_value=0,
            value=72,
            step=24,
            help="Set to 0 to ignore this filter.",
        )

        # Remote checkbox removed – users are directed to Playbook for remote search techniques.

        search_clicked = st.button("Search jobs", type="primary", width="stretch")

        # Google manual suggestion toggle
        google_enabled = st.checkbox(
            "✨ Show Google manual search suggestion after scraping",
            value=False,
            help="We do not scrape Google due to blocking. If enabled, we'll build a query you can use manually."
        )

    # ===== MAIN SEARCH LOGIC =====
    if search_clicked:
        if not sites:
            st.error("Pick at least one job site from the sidebar (Google is not scraped).")
            st.stop()

        common_inputs = dict(
            search_term=search_term,
            location=location,
            country_indeed=country_indeed,
            results_wanted=results_wanted,
            hours_old=hours_old,
        )

        all_dfs = []
        site_status = {}
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
                "No jobs found from any scraped site. Try a different location, fewer filters, "
                "or check the per-site errors above. (Google is not scraped.)"
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
                # Add company career column
                if "company_url" in jobs.columns:
                    jobs["company_career"] = jobs["company_url"].fillna("")
                    mask = jobs["company_career"].str.strip().eq("") | jobs["company_career"].isna()
                    jobs.loc[mask, "company_career"] = jobs.loc[mask, "company"].astype(str) + " " + jobs.loc[mask, "title"].astype(str)
                else:
                    jobs["company_career"] = jobs["company"].astype(str) + " " + jobs["title"].astype(str)

                summary = f"Found {len(jobs)} valid jobs across {len(all_dfs)} site(s)"
                if filtered_count:
                    summary += f" — {filtered_count} filtered out as incomplete, stale, or duplicate"
                st.success(summary)

                preferred_cols = [
                    "site", "title", "company", "location", "city", "state",
                    "job_type", "is_remote", "date_posted", "min_amount", "max_amount",
                    "currency", "job_url", "company_career"
                ]
                existing_preferred = [c for c in preferred_cols if c in jobs.columns]
                other_cols = [c for c in jobs.columns if c not in existing_preferred]
                jobs = jobs[existing_preferred + other_cols]

                st.dataframe(jobs, width="stretch", hide_index=True)

                # CSV download
                loc_part = location.strip().replace(" ", "_") if location and location.strip() else "anywhere"
                search_part = search_term.strip().replace(" ", "_") if search_term and search_term.strip() else "all_jobs"
                timestamp = datetime.now().strftime("%Y-%b-%d_%H%M")
                csv_filename = f"jobs_{search_part}_{loc_part}_{timestamp}.csv"

                csv = jobs.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download results as CSV",
                    data=csv,
                    file_name=csv_filename,
                    mime="text/csv",
                )

                # Google manual suggestion
                if google_enabled:
                    st.divider()
                    st.subheader("🔍 Extra: Google Jobs Manual Search")
                    google_query = build_google_search_term(search_term, location, hours_old)
                    st.caption(
                        "This is a suggested query you can use on Google Jobs. "
                        "Click the link below to open it in a new tab."
                    )
                    st.code(google_query, language="text")
                    encoded_query = urllib.parse.quote(google_query)
                    google_url = f"https://www.google.com/search?q={encoded_query}&ibp=htl;jobs"
                    st.markdown(f"[🔗 Search this on Google Jobs]({google_url})")
                    st.caption(
                        "Google Jobs often has listings that don't appear on other boards – "
                        "this helps you cast a wider net!"
                    )

# ==================== TAB 2: PLAYBOOK ====================
with tab2:
    st.title("📖 Job Search Playbook")
    st.markdown("**Practical techniques to find valid job information using Google Search.**")

    with st.expander("🚀 Quick Start – Copy‑paste these keywords", expanded=True):
        st.markdown("**1. General job search (Indonesia)**")
        st.code('("recruitment" OR "rekrutmen" OR "karir" OR "lowongan" OR "career" OR "pekerjaan" OR "job" OR "vacancy") (site:*.co.id OR site:*.ac.id OR site:*.go.id OR site:*.com OR site:*.org)', language="text")
        st.caption("💡 Add `-jobstreet` at the end to exclude JobStreet listings.")

        st.markdown("**2. Specific city (example: Temanggung, Jateng)**")
        st.code('("recruitment" OR "rekrutmen" OR "karir" OR "lowongan" OR "career" OR "pekerjaan" OR "job" OR "vacancy") AND ("Temanggung" OR "Magelang" OR "Jawa Tengah") (site:*.co.id OR site:*.ac.id OR site:*.go.id OR site:*.com OR site:*.org) -jobstreet', language="text")

        st.markdown("**3. Surabaya – Gresik area**")
        st.code('intext:(recruitment OR rekrutmen OR karir OR lowongan OR career) AND (surabaya OR gresik)', language="text")

    with st.expander("📍 Build your own location query"):
        col1, col2 = st.columns(2)
        with col1:
            city = st.text_input("City", "Temanggung")
        with col2:
            province = st.text_input("Province (optional)", "Jawa Tengah")
        exclude = st.text_input("Exclude (e.g., jobstreet)", value="jobstreet")
        if st.button("Generate Location Query"):
            base = f'("recruitment" OR "rekrutmen" OR "karir" OR "lowongan" OR "career" OR "pekerjaan" OR "job" OR "vacancy")'
            loc = f'("{city}"'
            if province:
                loc += f' OR "{province}"'
            loc += ") "
            sites_part = "(site:*.co.id OR site:*.ac.id OR site:*.go.id OR site:*.com OR site:*.org)"
            query = f"{base} AND {loc} {sites_part}"
            if exclude.strip():
                query += f" -{exclude.strip()}"
            st.code(query, language="text")
            st.markdown(f"[🔗 Search on Google](https://www.google.com/search?q={urllib.parse.quote(query)})")

    with st.expander("🏢 Scan specific job portals (including remote)"):
        st.markdown("These portals often have remote-friendly companies.")
        portals = [
            ("BambooHR", "inurl:bamboohr.com 'jobs/view' remote after:2026-05-01"),
            ("Greenhouse", "site:greenhouse.io Remote"),
            ("Lever", "site:jobs.lever.co Remote"),
            ("Workable", "site:careers.workable.com Remote"),
            ("Remote OK", "site:remoteok.com remote"),
            ("We Work Remotely", "site:weworkremotely.com"),
        ]
        for name, query in portals:
            st.markdown(f"**{name}**")
            st.code(query, language="text")
            st.markdown(f"[🔗 Search](https://www.google.com/search?q={urllib.parse.quote(query)})")

    with st.expander("🔗 LinkedIn time filter (last 24 hours)"):
        st.markdown("Use this link to see jobs posted in the last 24 hours. Change the number after `r` for different time windows (seconds).")
        linkedin_location = st.text_input("LinkedIn location (e.g., Surabaya)", "Surabaya")
        linkedin_keyword = st.text_input("LinkedIn keyword", "hiring")
        if st.button("Generate LinkedIn Link"):
            base = "https://www.linkedin.com/jobs/search/"
            params = {
                "keywords": f"{linkedin_keyword} {linkedin_location}",
                "f_TPR": "r86400",
                "origin": "JOB_SEARCH_PAGE_JOB_FILTER",
                "sortBy": "R"
            }
            query_str = urllib.parse.urlencode(params)
            url = f"{base}?{query_str}"
            st.code(url, language="text")
            st.markdown(f"[🔗 Open LinkedIn search]({url})")
            st.caption("💡 Change `r86400` to `r172800` for 48h, `r43200` for 12h, etc.")

    with st.expander("🤖 AI Helper – Generate keywords with ChatGPT / DeepSeek"):
        st.markdown("Copy this prompt and paste it into ChatGPT, DeepSeek, or Meta AI to get custom search queries.")
        prompt = """Buatkan kata kunci untuk mencari informasi pekerjaan bidang [your field] di [your location] lewat Google Search dengan teknik Google Dorking.

Contoh output: 
- site:indeed.co.id "GIS" "Indonesia" "job"
- inurl:career "GIS" "Indonesia" "vacancy"
- filetype:pdf "Lowongan Kerja GIS" "Indonesia"

Buatkan 5–10 variasi dengan operator yang berbeda."""
        st.code(prompt, language="text")
        st.caption("💡 Replace the bracketed parts with your own field and location.")

    with st.expander("🌐 Community & Free Tools"):
        st.markdown("**Join the community**")
        st.markdown("[Discord: Kabur Aja Dulu](https://discord.com/invite/KaburAjaDulu) – structured discussions about job hunting abroad and more.")

        st.markdown("**Free CV & job tracking tool**")
        st.markdown("[jobresume.rndhri.com](https://jobresume.rndhri.com/) – build CV, track applications, practice interviews (no cost).")

        st.markdown("**WEF Future of Jobs Report 2025**")
        st.markdown("[Download PDF](https://www.weforum.org/publications/the-future-of-jobs-report-2025/)")
        st.markdown("**AI prompt to summarise the report:**")
        summarise_prompt = """Ringkaskan laporan Future of Jobs Report 2025 dari World Economic Forum dalam bahasa Indonesia. Fokus pada:
- Sektor yang paling banyak menambah lapangan kerja
- Sektor yang paling banyak mengurangi lapangan kerja
- Keterampilan yang paling dibutuhkan
- Rekomendasi untuk pencari kerja
Buat ringkasan 2–3 paragraf yang mudah dipahami."""
        st.code(summarise_prompt, language="text")

        st.markdown("---")
        st.markdown("**Share your own tip**")
        tip = st.text_area("Your tip (will be displayed in community section – for now, just a note)")
        if st.button("Submit Tip"):
            st.success("Thank you! Your tip has been recorded (this is a demo).")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown(
    "Powered by [damarowen/JobSpy](https://github.com/damarowen/JobSpy) — "
    "a fork of JobSpy for job scraping. Built for job seekers who refuse to give up."
)
