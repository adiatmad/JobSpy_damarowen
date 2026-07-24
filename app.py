import streamlit as st
import pandas as pd
import time
from jobspy import scrape_jobs

st.set_page_config(page_title="Job Search Scraper", page_icon="🔎", layout="wide")

st.title("🔎 Job Search Scraper")
st.caption("Powered by python-jobspy-damarowen 1.2.2 — Optimized for Indonesia")

# Initialize session state
if 'progress' not in st.session_state:
    st.session_state.progress = {}

with st.sidebar:
    st.header("Search Settings")
    
    # Site selection with clear labels
    site_options = {
        "indeed": "Indeed",
        "linkedin": "LinkedIn", 
        "zip_recruiter": "ZipRecruiter",
        "glassdoor": "Glassdoor",
        "jobstreet": "JobStreet (Indonesia)",
        "google": "Google (requires special syntax)"
    }
    
    selected_sites = st.multiselect(
        "Job sites to search",
        options=list(site_options.keys()),
        default=["indeed", "linkedin", "jobstreet"],
        format_func=lambda x: site_options[x]
    )
    
    st.divider()
    
    # Main search parameters
    search_term = st.text_input("Job title / keywords", value="software engineer")
    location = st.text_input("Location", value="Jakarta", 
                           help="For JobStreet: use Indonesian city names (Jakarta, Bandung, Surabaya)")
    
    # Google-specific parameter (only shown if Google is selected)
    if "google" in selected_sites:
        st.subheader("Google Search Settings")
        google_search_term = st.text_input(
            "Google Jobs search term",
            value="software engineer jobs in Jakarta since yesterday",
            help="Copy exact query from Google Jobs UI. Format: 'job title jobs in location since [time]'"
        )
    else:
        google_search_term = None
    
    # Country for Indeed/Glassdoor
    country_indeed = st.selectbox(
        "Country (for Indeed & Glassdoor)",
        options=["Indonesia", "USA", "Singapore", "Malaysia", "Australia", "UK", "India"],
        index=0,
        help="Only used by Indeed and Glassdoor"
    )
    
    st.divider()
    
    # Results and filters
    col1, col2 = st.columns(2)
    with col1:
        results_wanted = st.slider("Results per site", min_value=5, max_value=50, value=20, step=5)
    with col2:
        hours_old = st.selectbox(
            "Posted within (hours)",
            options=[0, 1, 3, 7, 14, 24, 48, 72, 168],
            format_func=lambda x: "Any time" if x == 0 else f"{x}h",
            index=4,
            help="JobStreet maps to: 1, 3, 7, 14, 30 days"
        )
    
    # Remote filter - handled client-side for performance
    is_remote = st.checkbox("Remote jobs only", value=False)
    if is_remote:
        st.info("⚡ Remote filter applied after scraping for better performance")
    
    st.divider()
    
    # Diagnostic mode
    run_diagnostic = st.checkbox("🔧 Diagnostic mode (test each site first)", value=False)
    
    search_clicked = st.button("🔍 Search Jobs", type="primary", use_container_width=True)

def test_site(site_name, **kwargs):
    """Test a single site with minimal results"""
    try:
        test_kwargs = kwargs.copy()
        test_kwargs["site_name"] = [site_name]
        test_kwargs["results_wanted"] = 3
        test_kwargs["verbose"] = 0
        
        # Remove incompatible parameters
        if site_name == "jobstreet":
            test_kwargs.pop("country_indeed", None)
        if site_name == "google":
            test_kwargs.pop("country_indeed", None)
            if "google_search_term" not in test_kwargs or not test_kwargs["google_search_term"]:
                return {"site": site_name, "status": "error", "error": "Google requires google_search_term"}
        
        result = scrape_jobs(**test_kwargs)
        
        if result is not None and len(result) > 0:
            return {"site": site_name, "status": "working", "count": len(result)}
        else:
            return {"site": site_name, "status": "no_results", "count": 0}
    except Exception as e:
        return {"site": site_name, "status": "error", "error": str(e)}

def scrape_with_progress(sites_to_scrape, base_kwargs, progress_bar, status_text):
    """Scrape multiple sites with progress tracking"""
    all_jobs = []
    site_results = {}
    
    for idx, site in enumerate(sites_to_scrape):
        progress = (idx + 1) / len(sites_to_scrape)
        progress_bar.progress(progress)
        status_text.text(f"🔄 Scraping {site.title()}...")
        
        try:
            # Build site-specific kwargs
            site_kwargs = base_kwargs.copy()
            site_kwargs["site_name"] = [site]
            site_kwargs["verbose"] = 0
            
            # Site-specific adjustments
            if site == "jobstreet":
                site_kwargs.pop("country_indeed", None)  # Not needed for JobStreet
                # JobStreet works with simple location
                
            if site == "google":
                site_kwargs.pop("country_indeed", None)  # Not needed for Google
                if "google_search_term" in site_kwargs and site_kwargs["google_search_term"]:
                    # Google uses its own search term
                    pass
                else:
                    site_results[site] = {"status": "error", "error": "Missing google_search_term"}
                    continue
            
            start_time = time.time()
            jobs = scrape_jobs(**site_kwargs)
            elapsed = time.time() - start_time
            
            if jobs is not None and len(jobs) > 0:
                jobs['source_site'] = site
                all_jobs.append(jobs)
                site_results[site] = {"status": "success", "count": len(jobs), "time": f"{elapsed:.1f}s"}
            else:
                site_results[site] = {"status": "no_results", "count": 0, "time": f"{elapsed:.1f}s"}
                
        except Exception as e:
            site_results[site] = {"status": "error", "error": str(e)}
    
    return all_jobs, site_results

if search_clicked:
    if not selected_sites:
        st.error("❌ Pick at least one job site from the sidebar.")
        st.stop()
    
    # Check Google requirements
    if "google" in selected_sites and not google_search_term:
        st.error("❌ Google requires a search term. Please fill in the Google Search Settings section.")
        st.stop()
    
    # === DIAGNOSTIC MODE ===
    if run_diagnostic:
        st.subheader("🔧 Running Diagnostic Tests")
        st.info("Testing each site with 3 results...")
        
        test_results = []
        test_progress = st.progress(0)
        test_status = st.empty()
        
        # Prepare test kwargs
        test_kwargs = {
            "search_term": search_term,
            "location": location,
            "country_indeed": country_indeed,
            "hours_old": hours_old if hours_old > 0 else None,
        }
        if google_search_term:
            test_kwargs["google_search_term"] = google_search_term
        
        for i, site in enumerate(selected_sites):
            test_status.text(f"Testing {site.title()}...")
            result = test_site(site, **test_kwargs)
            test_results.append(result)
            test_progress.progress((i + 1) / len(selected_sites))
        
        test_status.text("✅ Diagnostic complete!")
        
        # Show results with clear status
        st.subheader("📊 Diagnostic Results")
        working_sites = []
        for result in test_results:
            if result["status"] == "working":
                working_sites.append(result["site"])
                st.success(f"✅ **{result['site'].title()}**: Working! ({result['count']} jobs found)")
            elif result["status"] == "no_results":
                st.warning(f"⚠️ **{result['site'].title()}**: No results (try different keywords/location)")
            else:
                st.error(f"❌ **{result['site'].title()}**: Failed - {result.get('error', 'Unknown error')}")
        
        if working_sites:
            st.info(f"✅ Working sites: {', '.join([s.title() for s in working_sites])}")
            if not st.button("Continue with working sites →"):
                st.stop()
        else:
            st.error("❌ No sites are working. Try different search terms or check your internet connection.")
            st.stop()
    
    # === MAIN SEARCH ===
    # Use working sites if diagnostic ran, otherwise use all selected
    if run_diagnostic and 'working_sites' in locals() and working_sites:
        sites_to_use = working_sites
        st.success(f"🔍 Searching only working sites: {', '.join([s.title() for s in sites_to_use])}")
    else:
        sites_to_use = selected_sites
    
    # Build base kwargs
    base_kwargs = {
        "search_term": search_term,
        "location": location,
        "results_wanted": results_wanted if not is_remote else results_wanted * 2,  # Extra for filtering
        "country_indeed": country_indeed,
        "verbose": 0,
    }
    
    # Add optional parameters
    if hours_old and hours_old > 0:
        base_kwargs["hours_old"] = hours_old
    
    if google_search_term:
        base_kwargs["google_search_term"] = google_search_term
    
    # Show progress
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Scrape
    with st.spinner("🔍 Scraping job boards..."):
        try:
            all_jobs_list, site_results = scrape_with_progress(
                sites_to_use, base_kwargs, progress_bar, status_text
            )
        except Exception as e:
            st.error(f"❌ Something went wrong: {e}")
            st.stop()
    
    # Combine all jobs
    if all_jobs_list:
        jobs = pd.concat(all_jobs_list, ignore_index=True)
    else:
        jobs = pd.DataFrame()
    
    # === APPLY REMOTE FILTER (CLIENT-SIDE) ===
    if is_remote and not jobs.empty:
        status_text.text("🔄 Filtering for remote jobs...")
        original_count = len(jobs)
        
        # Check for remote column
        if 'is_remote' in jobs.columns:
            jobs = jobs[jobs['is_remote'] == True]
        elif 'remote' in jobs.columns:
            jobs = jobs[jobs['remote'] == True]
        else:
            # Fallback: keyword matching
            remote_keywords = ['remote', 'work from home', 'wfh', 'virtual', 'home based', 'telecommute']
            mask = pd.Series([False] * len(jobs))
            
            # Check title and location fields
            for col in ['title', 'location', 'description']:
                if col in jobs.columns:
                    # Convert to string and check for keywords
                    col_str = jobs[col].astype(str).str.lower()
                    mask = mask | col_str.str.contains('|'.join(remote_keywords), na=False)
            
            jobs = jobs[mask]
        
        filtered_count = len(jobs)
        status_text.text(f"✅ Remote filter applied: {filtered_count} of {original_count} jobs remain")
    
    # === DISPLAY RESULTS ===
    if jobs.empty:
        st.warning("⚠️ No jobs found")
        
        # Show detailed site status
        st.subheader("📊 Site Status Summary")
        for site, status in site_results.items():
            if status["status"] == "success":
                st.success(f"✅ **{site.title()}**: {status['count']} jobs in {status['time']}")
            elif status["status"] == "no_results":
                st.warning(f"⚠️ **{site.title()}**: No results found")
            else:
                st.error(f"❌ **{site.title()}**: {status.get('error', 'Failed')}")
        
        # Show troubleshooting tips
        with st.expander("💡 Troubleshooting Tips"):
            st.markdown("""
            **For Google:**
            - Use exact syntax from Google Jobs UI
            - Example: `"software engineer jobs in Jakarta since yesterday"`
            
            **For JobStreet:**
            - Use Indonesian city names: Jakarta, Bandung, Surabaya, Tangerang
            - Leave location empty for nationwide search
            
            **For all sites:**
            - Try simpler search terms first
            - Check your internet connection
            - Reduce filters (hours_old, remote, etc.)
            """)
        
        st.stop()
    
    # === SUCCESS! ===
    st.success(f"✅ Found {len(jobs)} jobs")
    
    # Show per-site breakdown
    if 'source_site' in jobs.columns:
        site_counts = jobs['source_site'].value_counts()
        cols = st.columns(min(len(site_counts), 4))
        for i, (site, count) in enumerate(site_counts.items()):
            cols[i % 4].metric(f"{site.title()}", count)
    
    # Display dataframe with relevant columns
    display_cols = ['source_site', 'title', 'company', 'location', 'job_type', 'is_remote', 'date_posted', 'job_url']
    available_cols = [c for c in display_cols if c in jobs.columns]
    if not available_cols:
        available_cols = jobs.columns.tolist()
    
    # Show dataframe
    st.dataframe(jobs[available_cols], use_container_width=True, hide_index=True)
    
    # Download button
    csv = jobs.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download CSV",
        data=csv,
        file_name=f"jobs_{search_term.replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )
    
    # Show full results expander
    with st.expander("📋 Full Results (all columns)"):
        st.dataframe(jobs, use_container_width=True)

else:
    st.info("🔍 Set your search options in the sidebar, then click **Search Jobs**")
    
    st.markdown("""
    ---
    ### 📌 Quick Guide
    
    | Site | Requirements | Tips |
    |------|--------------|------|
    | **Indeed** | `country_indeed` | Most reliable, no rate limiting |
    | **LinkedIn** | Location | Rate limits after ~1000 jobs |
    | **JobStreet** | Location (Indonesia) | Use city names: Jakarta, Bandung, etc. |
    | **Google** | `google_search_term` | Copy exact query from Google Jobs UI |
    | **ZipRecruiter** | Location | US/Canada only |
    | **Glassdoor** | `country_indeed` | Needs exact country name |
    
    ### 🚀 Recommended Settings for Indonesia
    - **Sites**: Indeed + LinkedIn + JobStreet
    - **Location**: Jakarta (or your city)
    - **Hours**: 24-72h
    - **Use Diagnostic Mode** to test first
    """)
