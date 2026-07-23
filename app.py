import streamlit as st
import pandas as pd
from jobspy import scrape_jobs

st.set_page_config(page_title="Job Search Scraper", page_icon="🔎", layout="wide")

st.title("🔎 Job Search Scraper")
st.caption("Powered by python-jobspy-damarowen — searches LinkedIn, Indeed, ZipRecruiter, Glassdoor, and JobStreet.")

with st.sidebar:
    st.header("Search settings")

    site_options = ["indeed", "linkedin", "zip_recruiter", "glassdoor", "google", "jobstreet"]
    sites = st.multiselect(
        "Job sites to search",
        options=site_options,
        default=["indeed", "linkedin"],
    )

    search_term = st.text_input("Job title / keywords", value="software engineer")

    location = st.text_input("Location", value="Jakarta")

    country_indeed = st.text_input(
        "Country (for Indeed/Glassdoor)",
        value="Indonesia",
        help="Only used by Indeed and Glassdoor. Use the exact country name, e.g. 'Indonesia', 'USA', 'Singapore'.",
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

    with st.spinner("Scraping job boards... this can take 10-60 seconds."):
        try:
            kwargs = dict(
                site_name=sites,
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

            jobs = scrape_jobs(**kwargs)
        except Exception as e:
            st.error(f"Something went wrong while scraping: {e}")
            st.stop()

    if jobs is None or len(jobs) == 0:
        st.warning("No jobs found. Try different keywords, a different location, or fewer filters.")
    else:
        st.success(f"Found {len(jobs)} jobs")

        # Keep the most useful columns front and center if they exist
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
