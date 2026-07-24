import streamlit as st
import pandas as pd
from jobspy import scrape_jobs

st.set_page_config(page_title="Job Search Scraper", page_icon="🔎", layout="wide")

st.title("🔎 Job Search Scraper")
st.caption("Powered by python-jobspy-damarowen — following official repository usage")

with st.sidebar:
    st.header("Search Settings")
    
    # Site selection matching repository options
    site_options = ["indeed", "linkedin", "zip_recruiter", "glassdoor", "google", "jobstreet"]
    sites = st.multiselect(
        "Job sites to search",
        options=site_options,
        default=["indeed", "linkedin"],
        help="google requires google_search_term parameter"
    )
    
    search_term = st.text_input("Job title / keywords", value="software engineer")
    
    # Google-specific parameter (only if google is selected)
    if "google" in sites:
        st.info("🔍 Google requires special syntax - copy from Google Jobs UI")
        google_search_term = st.text_input(
            "Google search term",
            value="software engineer jobs in Jakarta since yesterday",
            help="Example: 'software engineer jobs near San Francisco, CA since yesterday'"
        )
    else:
        google_search_term = None
    
    location = st.text_input("Location", value="Jakarta", 
                           help="For JobStreet: use Indonesian city names")
    
    country_indeed = st.text_input(
        "Country (Indeed & Glassdoor only)",
        value="Indonesia",
        help="Only used by Indeed and Glassdoor. Use exact name from docs."
    )
    
    results_wanted = st.slider("Results per site", min_value=5, max_value=100, value=20, step=5)
    
    # IMPORTANT: Indeed can only use ONE filter from this list
    st.subheader("Filters (⚠️ Indeed limitations)")
    st.caption("Indeed: can only use ONE of: hours_old, remote, job_type, easy_apply")
    
    hours_old = st.number_input(
        "Posted within (hours)",
        min_value=0,
        value=0,  # Default to 0 to avoid conflicts
        step=24,
        help="Set to 0 to disable. Note: Indeed can't use with remote filter."
    )
    
    # If hours_old > 0, suggest disabling remote for Indeed
    if hours_old > 0:
        st.warning("⚠️ Since hours_old > 0, Indeed will ignore is_remote filter")
    
    is_remote = st.checkbox("Remote jobs only", value=False)
    if is_remote and hours_old > 0:
        st.warning("⚠️ Indeed can't use both hours_old and is_remote. Remote will be client-side filtered.")
    
    search_clicked = st.button("Search jobs", type="primary", use_container_width=True)

if search_clicked:
    if not sites:
        st.error("Pick at least one job site.")
        st.stop()
    
    # Validate Google
    if "google" in sites and not google_search_term:
        st.error("Google requires google_search_term. Please fill it in.")
        st.stop()
    
    with st.spinner("Scraping job boards... this can take 10-60 seconds."):
        try:
            # Build kwargs exactly like repository examples
            kwargs = {
                "site_name": sites,
                "search_term": search_term,
                "location": location,
                "results_wanted": results_wanted,
                "country_indeed": country_indeed,
                "verbose": 0,
            }
            
            # Only add google_search_term if google is in sites
            if "google" in sites and google_search_term:
                kwargs["google_search_term"] = google_search_term
            
            # Only add hours_old if > 0
            if hours_old and hours_old > 0:
                kwargs["hours_old"] = int(hours_old)
            
            # Only add is_remote if checked (but note Indeed limitation)
            if is_remote:
                kwargs["is_remote"] = True
            
            # Debug: show what we're sending
            st.caption(f"Parameters: {', '.join(kwargs.keys())}")
            
            jobs = scrape_jobs(**kwargs)
            
        except Exception as e:
            st.error(f"Scraping error: {e}")
            st.stop()
    
    if jobs is None or len(jobs) == 0:
        st.warning("No jobs found.")
        
        # Show troubleshooting based on sites selected
        st.subheader("Troubleshooting")
        if "google" in sites:
            st.info("""
            **Google Tips:**
            - Use exact syntax from Google Jobs UI
            - Search on Google Jobs first, copy the search box text
            - Example: `"software engineer jobs in Jakarta since yesterday"`
            """)
        if "jobstreet" in sites:
            st.info("""
            **JobStreet Tips:**
            - Use Indonesian city names: Jakarta, Tangerang, Bandung, Surabaya
            - Or omit location for nationwide search
            - hours_old maps to: 1, 3, 7, 14, 30 days
            """)
        if "indeed" in sites and hours_old > 0 and is_remote:
            st.warning("""
            **Indeed Limitation:**
            Indeed can't use hours_old AND is_remote together.
            Try removing one filter.
            """)
        st.stop()
    
    st.success(f"Found {len(jobs)} jobs")
    
    # Display with preferred columns
    preferred_cols = [
        "site", "title", "company", "location", "city", "state",
        "job_type", "is_remote", "date_posted", "job_url",
    ]
    existing_cols = [c for c in preferred_cols if c in jobs.columns]
    other_cols = [c for c in jobs.columns if c not in existing_cols]
    jobs = jobs[existing_cols + other_cols]
    
    st.dataframe(jobs, use_container_width=True, hide_index=True)
    
    csv = jobs.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV",
        data=csv,
        file_name=f"jobs_{search_term.replace(' ', '_')}.csv",
        mime="text/csv",
    )
    
    # Show site breakdown
    if 'site' in jobs.columns:
        st.caption(f"Jobs by site: {dict(jobs['site'].value_counts())}")

else:
    st.info("Set search options in sidebar, then click **Search jobs**.")
    
    st.markdown("""
    ---
    ### 📋 Quick Reference (from repository)
    
    | Site | Parameters | Notes |
    |------|------------|-------|
    | **Indeed** | location, country_indeed, [hours_old OR is_remote OR job_type OR easy_apply] | Best scraper, no rate limiting |
    | **LinkedIn** | location | Rate limits around 1000 jobs |
    | **JobStreet** | location (Indonesia) | Use city names: Jakarta, Bandung, etc. |
    | **Google** | google_search_term | Copy exact syntax from Google Jobs UI |
    | **Glassdoor** | location, country_indeed | |
    | **ZipRecruiter** | location | US/Canada only |
    
    ### ⚠️ Indeed Limitations
    Only **one** of these can be used in a search:
    - hours_old
    - job_type & is_remote (combined)
    - easy_apply
    """)
