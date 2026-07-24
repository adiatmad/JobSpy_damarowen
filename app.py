import streamlit as st
import pandas as pd
import sys
from jobspy import scrape_jobs

st.set_page_config(page_title="Job Search Scraper", page_icon="🔎", layout="wide")

st.title("🔎 Job Search Scraper")
st.caption("Powered by python-jobspy-damarowen — following README exactly")

# Display package info
try:
    import jobspy
    st.sidebar.caption(f"Package: python-jobspy-damarowen")
except:
    pass

with st.sidebar:
    st.header("Search Settings")
    
    # Site selection with clear labels and warnings
    site_options = {
        "indeed": "✅ Indeed (most reliable)",
        "linkedin": "✅ LinkedIn", 
        "zip_recruiter": "ZipRecruiter (US/Canada)",
        "glassdoor": "Glassdoor",
        "jobstreet": "⚠️ JobStreet (Indonesia - may be blocked)",
        "google": "⚠️ Google (requires exact syntax)"
    }
    
    selected_sites = st.multiselect(
        "Job sites to search",
        options=list(site_options.keys()),
        default=["indeed", "linkedin"],
        format_func=lambda x: site_options[x]
    )
    
    st.divider()
    
    # Main parameters - exactly as README shows
    search_term = st.text_input(
        "Job title / keywords", 
        value="software engineer",
        help="For Indeed: use - to exclude, \"\" for exact match"
    )
    
    location = st.text_input(
        "Location", 
        value="Jakarta",
        help="JobStreet: use Indonesian cities (Jakarta, Bandung, Surabaya)"
    )
    
    # Google-specific (only show if selected)
    if "google" in selected_sites:
        st.warning("🔍 Google requires copying exact syntax from Google Jobs UI")
        google_search_term = st.text_input(
            "Google search term",
            value="software engineer jobs in Jakarta since yesterday",
            help="Copy from Google Jobs search box after applying filters"
        )
    else:
        google_search_term = None
    
    # Country for Indeed/Glassdoor (only show if selected)
    if any(site in selected_sites for site in ["indeed", "glassdoor"]):
        country_indeed = st.selectbox(
            "Country (Indeed/Glassdoor)",
            options=["Indonesia", "USA", "Singapore", "Malaysia", "Australia", "UK", "India"],
            index=0,
            help="Required for Indeed and Glassdoor"
        )
    else:
        country_indeed = "Indonesia"
    
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
            index=4,  # Default 24h
            help="JobStreet maps to: 1, 3, 7, 14, 30 days"
        )
    
    # Remote filter - with warning about Indeed limitation
    is_remote = st.checkbox("Remote jobs only", value=False)
    if is_remote and "indeed" in selected_sites and hours_old > 0:
        st.warning("⚠️ Indeed can't use both hours_old and remote. Remote will be client-side filtered.")
    
    st.divider()
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        verbose_level = st.selectbox(
            "Verbose (for debugging)",
            options=[0, 1, 2],
            index=0,
            help="0=errors only, 1=warnings, 2=all logs"
        )
        
        show_debug = st.checkbox("Show debug info", value=False)
    
    search_clicked = st.button("🔍 Search Jobs", type="primary", use_container_width=True)

def build_kwargs(sites, search_term, location, country_indeed, results_wanted, hours_old, is_remote, google_search_term):
    """Build kwargs exactly as README examples"""
    
    kwargs = {
        "site_name": sites,
        "search_term": search_term,
        "results_wanted": results_wanted,
        "verbose": verbose_level,
    }
    
    # Only add location if provided
    if location:
        kwargs["location"] = location
    
    # Only add country_indeed if Indeed or Glassdoor selected
    if any(site in sites for site in ["indeed", "glassdoor"]):
        kwargs["country_indeed"] = country_indeed
    
    # Only add hours_old if > 0
    if hours_old and hours_old > 0:
        kwargs["hours_old"] = hours_old
    
    # Only add is_remote if True (and warn if conflicting)
    if is_remote:
        # If Indeed is selected and hours_old > 0, we'll still pass it
        # but warn the user that Indeed might ignore it
        kwargs["is_remote"] = True
    
    # Only add google_search_term if Google selected and provided
    if "google" in sites and google_search_term:
        kwargs["google_search_term"] = google_search_term
    
    return kwargs

def test_jobstreet_only():
    """Quick test for JobStreet"""
    st.subheader("🔧 Testing JobStreet Only")
    st.info("Running a minimal JobStreet test as shown in README")
    
    try:
        test_kwargs = {
            "site_name": "jobstreet",
            "search_term": "software engineer",
            "location": "Jakarta",
            "results_wanted": 5,
            "hours_old": 24,
            "verbose": 2,  # Show all logs for debugging
        }
        
        st.code(f"scrape_jobs(**{test_kwargs})", language="python")
        
        with st.spinner("Testing JobStreet..."):
            jobs = scrape_jobs(**test_kwargs)
        
        if jobs is not None and len(jobs) > 0:
            st.success(f"✅ JobStreet works! Found {len(jobs)} jobs")
            st.dataframe(jobs[['title', 'company', 'location']].head())
            return True
        else:
            st.warning("⚠️ JobStreet returned 0 jobs")
            st.markdown("""
            ### Troubleshooting JobStreet:
            
            1. **Check your network** - Can you access https://www.jobstreet.co.id/ ?
            2. **Try a VPN** - Some regions block scrapers
            3. **Different location** - Try 'Bandung' or 'Surabaya'
            4. **Different search term** - Try 'engineer' or 'developer'
            5. **No location** - Try without location parameter
            6. **Update package** - `pip install --upgrade python-jobspy-damarowen`
            """)
            return False
            
    except Exception as e:
        st.error(f"❌ JobStreet error: {e}")
        st.markdown("""
        ### Common Fixes:
        - Update package: `pip install --upgrade python-jobspy-damarowen`
        - Check internet connection
        - Try with proxies if you have them
        - Open an issue on GitHub with the error message
        """)
        return False

if search_clicked:
    if not selected_sites:
        st.error("❌ Pick at least one job site.")
        st.stop()
    
    # Validate Google
    if "google" in selected_sites and not google_search_term:
        st.error("❌ Google requires google_search_term. Fill it in or deselect Google.")
        st.stop()
    
    # Show what we're about to do
    with st.expander("📋 Search Configuration", expanded=True):
        st.markdown(f"**Sites:** {', '.join(selected_sites)}")
        st.markdown(f"**Search:** {search_term}")
        st.markdown(f"**Location:** {location if location else 'None'}")
        st.markdown(f"**Results:** {results_wanted} per site")
        st.markdown(f"**Hours:** {hours_old if hours_old > 0 else 'Any'}")
        st.markdown(f"**Remote:** {is_remote}")
        if "google" in selected_sites:
            st.markdown(f"**Google term:** {google_search_term}")
    
    # Build kwargs
    kwargs = build_kwargs(
        selected_sites, search_term, location, country_indeed,
        results_wanted, hours_old, is_remote, google_search_term
    )
    
    if show_debug:
        st.subheader("🔍 Debug: Parameters being sent")
        st.code(f"scrape_jobs(**{kwargs})", language="python")
    
    # If JobStreet is selected but not working, offer to test it
    if "jobstreet" in selected_sites:
        with st.expander("🔧 JobStreet Troubleshooting"):
            if st.button("Test JobStreet with README example"):
                test_jobstreet_only()
    
    # Main scraping
    st.subheader("🔄 Scraping...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Show which sites we're scraping
        for i, site in enumerate(selected_sites):
            progress_bar.progress((i + 1) / len(selected_sites))
            status_text.text(f"Scraping {site.title()}...")
        
        # Actually scrape
        status_text.text("Fetching jobs...")
        jobs = scrape_jobs(**kwargs)
        progress_bar.progress(1.0)
        status_text.text("✅ Done!")
        
    except Exception as e:
        st.error(f"❌ Scraping error: {e}")
        
        # Show helpful error message
        if "429" in str(e):
            st.warning("⚠️ Rate limited (429). Try:")
            st.markdown("""
            - Wait a few minutes and try again
            - Use fewer sites
            - Reduce results_wanted
            - Try with proxies
            """)
        elif "timeout" in str(e).lower():
            st.warning("⚠️ Timeout. Try:")
            st.markdown("""
            - Reduce results_wanted
            - Use fewer sites
            - Check internet connection
            """)
        st.stop()
    
    # Check results
    if jobs is None or len(jobs) == 0:
        st.warning("⚠️ No jobs found")
        
        # Show site-specific troubleshooting
        st.subheader("📊 Troubleshooting")
        
        if "jobstreet" in selected_sites:
            with st.expander("🔧 JobStreet Specific", expanded=True):
                st.markdown("""
                **JobStreet Tips:**
                - Location must be Indonesian city: Jakarta, Bandung, Surabaya, Tangerang
                - Or omit location for nationwide search
                - hours_old maps to: 1, 3, 7, 14, 30 days
                - Try the "Test JobStreet" button above
                - May be blocked by JobStreet - try VPN
                """)
        
        if "google" in selected_sites:
            with st.expander("🔧 Google Specific", expanded=True):
                st.markdown("""
                **Google Tips:**
                - Must use google_search_term with exact syntax
                - Copy from Google Jobs UI search box
                - Example: `"software engineer jobs in Jakarta since yesterday"`
                - Search on Google Jobs first to see what works
                """)
        
        if "indeed" in selected_sites and hours_old > 0 and is_remote:
            with st.expander("🔧 Indeed Limitation", expanded=True):
                st.markdown("""
                **Indeed can't use both:**
                - hours_old
                - is_remote
                
                Try removing one of these filters.
                """)
        
        # General tips
        with st.expander("💡 General Tips"):
            st.markdown("""
            - Try simpler search terms
            - Remove location (let it search nationwide)
            - Remove hours_old filter
            - Reduce results_wanted
            - Try different sites
            - Check internet connection
            """)
        
        st.stop()
    
    # Success!
    st.success(f"✅ Found {len(jobs)} jobs")
    
    # Show per-site breakdown
    if 'site' in jobs.columns:
        site_counts = jobs['site'].value_counts()
        cols = st.columns(min(len(site_counts), 4))
        for i, (site, count) in enumerate(site_counts.items()):
            cols[i % 4].metric(f"{site.title()}", count)
    
    # Display data
    preferred_cols = ['site', 'title', 'company', 'location', 'job_type', 'is_remote', 'date_posted', 'job_url']
    available_cols = [c for c in preferred_cols if c in jobs.columns]
    if not available_cols:
        available_cols = jobs.columns.tolist()
    
    st.dataframe(jobs[available_cols], use_container_width=True, hide_index=True)
    
    # Download
    csv = jobs.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download CSV",
        data=csv,
        file_name=f"jobs_{search_term.replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )
    
    # Show raw data if debug
    if show_debug:
        with st.expander("🔍 Raw Data"):
            st.dataframe(jobs)

else:
    st.info("🔍 Set search options in the sidebar, then click **Search Jobs**")
    
    st.markdown("""
    ---
    ### 📋 Quick Guide (from README)
    
    | Site | Parameters | Notes |
    |------|------------|-------|
    | **Indeed** | location, country_indeed | Most reliable |
    | **LinkedIn** | location | Rate limits after ~1000 jobs |
    | **JobStreet** | location (Indonesia) | Use city names |
    | **Google** | google_search_term | Exact syntax required |
    | **Glassdoor** | location, country_indeed | |
    | **ZipRecruiter** | location | US/Canada only |
    
    ### ⚠️ Known Limitations
    
    - **Indeed**: Can't use hours_old + remote + job_type + easy_apply together
    - **LinkedIn**: Rate limits after ~10 pages
    - **Google**: Requires exact syntax from Google Jobs UI
    - **JobStreet**: May be blocked outside Indonesia
    """)
    
    # JobStreet test button
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧪 Test JobStreet (README example)", use_container_width=True):
            test_jobstreet_only()
