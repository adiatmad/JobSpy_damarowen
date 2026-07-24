import streamlit as st
import pandas as pd
from jobspy import scrape_jobs

st.set_page_config(
    page_title="JobSpy - Fork Version",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 JobSpy - Python Job Scraper")
st.caption("Using python-jobspy-damarowen fork - exactly as documented")

# Display package version info
try:
    import jobspy
    st.sidebar.caption(f"⚡ Package: python-jobspy-damarowen")
except:
    pass

with st.sidebar:
    st.header("🔧 Search Settings")
    
    # Site selection - exactly as fork supports
    site_options = [
        "indeed",
        "linkedin", 
        "zip_recruiter",
        "glassdoor",
        "google",
        "bayt",
        "bdjobs",
        "jobstreet"
    ]
    
    sites = st.multiselect(
        "Job Sites",
        options=site_options,
        default=["indeed", "linkedin"],
        help="Select one or more job boards"
    )
    
    st.divider()
    
    # Main search parameters - exactly as fork expects
    search_term = st.text_input(
        "Search Term",
        value="software engineer",
        help="Job title or keywords"
    )
    
    location = st.text_input(
        "Location",
        value="Jakarta",
        help="City, state, or country"
    )
    
    # Google-specific parameter (only used when google is selected)
    if "google" in sites:
        st.warning("📌 Google requires special syntax")
        google_search_term = st.text_input(
            "Google Search Term",
            value="software engineer jobs in Jakarta since yesterday",
            help="Copy exact syntax from Google Jobs UI"
        )
    else:
        google_search_term = None
    
    # Country for Indeed & Glassdoor
    if any(s in sites for s in ["indeed", "glassdoor"]):
        country_indeed = st.text_input(
            "Country (Indeed/Glassdoor)",
            value="Indonesia",
            help="Exact country name: Indonesia, USA, Singapore, etc."
        )
    else:
        country_indeed = None
    
    st.divider()
    
    # Results and filters
    col1, col2 = st.columns(2)
    with col1:
        results_wanted = st.number_input(
            "Results per site",
            min_value=1,
            max_value=1000,
            value=20,
            step=5
        )
    
    with col2:
        hours_old = st.number_input(
            "Hours Old",
            min_value=0,
            max_value=168,
            value=24,
            step=24,
            help="0 = no filter"
        )
    
    # Additional filters
    is_remote = st.checkbox("Remote Only", value=False)
    
    job_type = st.selectbox(
        "Job Type",
        options=[None, "fulltime", "parttime", "internship", "contract"],
        format_func=lambda x: "Any" if x is None else x.title()
    )
    
    distance = st.number_input(
        "Distance (miles)",
        min_value=0,
        max_value=500,
        value=50,
        step=10,
        help="0 = no limit"
    )
    
    st.divider()
    
    # Advanced parameters
    with st.expander("⚙️ Advanced"):
        verbose = st.selectbox(
            "Verbose Level",
            options=[0, 1, 2],
            index=0,
            help="0=errors, 1=warnings, 2=all logs"
        )
        
        offset = st.number_input(
            "Offset",
            min_value=0,
            value=0,
            help="Start from offset result"
        )
        
        linkedin_fetch_description = st.checkbox(
            "Fetch LinkedIn Descriptions",
            value=False,
            help="Slower but gets full description"
        )
        
        enforce_annual_salary = st.checkbox(
            "Enforce Annual Salary",
            value=False,
            help="Convert wages to annual salary"
        )
    
    search_clicked = st.button(
        "🔍 Search Jobs",
        type="primary",
        use_container_width=True
    )

def build_kwargs():
    """Build kwargs exactly as fork expects - no modifications"""
    
    kwargs = {
        "site_name": sites,
        "search_term": search_term,
        "results_wanted": results_wanted,
        "verbose": verbose,
    }
    
    # Only add location if provided
    if location:
        kwargs["location"] = location
    
    # Only add country_indeed if provided and needed
    if country_indeed and any(s in sites for s in ["indeed", "glassdoor"]):
        kwargs["country_indeed"] = country_indeed
    
    # Only add google_search_term if google selected
    if "google" in sites and google_search_term:
        kwargs["google_search_term"] = google_search_term
    
    # Add hours_old if > 0
    if hours_old and hours_old > 0:
        kwargs["hours_old"] = hours_old
    
    # Add is_remote if True
    if is_remote:
        kwargs["is_remote"] = True
    
    # Add job_type if not None
    if job_type:
        kwargs["job_type"] = job_type
    
    # Add distance if > 0
    if distance and distance > 0:
        kwargs["distance"] = distance
    
    # Add offset if > 0
    if offset and offset > 0:
        kwargs["offset"] = offset
    
    # Add linkedin_fetch_description if True
    if linkedin_fetch_description:
        kwargs["linkedin_fetch_description"] = True
    
    # Add enforce_annual_salary if True
    if enforce_annual_salary:
        kwargs["enforce_annual_salary"] = True
    
    return kwargs

if search_clicked:
    if not sites:
        st.error("❌ Please select at least one job site.")
        st.stop()
    
    # Validate Google
    if "google" in sites and not google_search_term:
        st.error("❌ Google requires 'google_search_term'. Please fill it in.")
        st.stop()
    
    # Build kwargs
    kwargs = build_kwargs()
    
    # Show what we're sending
    with st.expander("📋 Parameters Sent to Fork", expanded=False):
        st.code(f"scrape_jobs(**{kwargs})", language="python")
    
    # Scrape
    with st.spinner("🔄 Scraping job boards..."):
        try:
            jobs = scrape_jobs(**kwargs)
        except Exception as e:
            st.error(f"❌ Error: {e}")
            
            # Show helpful error based on sites
            if "jobstreet" in sites:
                st.info("""
                **JobStreet Tips:**
                - Use location: Jakarta, Bandung, Surabaya, Tangerang
                - Or omit location for nationwide
                - hours_old maps to: 1, 3, 7, 14, 30 days
                """)
            
            if "google" in sites:
                st.info("""
                **Google Tips:**
                - Copy exact syntax from Google Jobs UI
                - Example: "software engineer jobs in Jakarta since yesterday"
                """)
            
            st.stop()
    
    # Process results
    if jobs is None or len(jobs) == 0:
        st.warning("⚠️ No jobs found")
        
        # Show site-specific notes
        st.subheader("💡 Tips")
        if "jobstreet" in sites:
            st.markdown("- **JobStreet**: Try location 'Jakarta' or leave empty")
        if "google" in sites:
            st.markdown("- **Google**: Must use exact google_search_term syntax")
        if "indeed" in sites and hours_old > 0 and is_remote:
            st.markdown("- **Indeed**: Can't use hours_old AND is_remote together")
        
        st.stop()
    
    # Success
    st.success(f"✅ Found {len(jobs)} jobs")
    
    # Show site breakdown if available
    if 'site' in jobs.columns:
        site_counts = jobs['site'].value_counts()
        cols = st.columns(min(len(site_counts), 4))
        for i, (site, count) in enumerate(site_counts.items()):
            cols[i % 4].metric(site.title(), count)
    
    # Display dataframe
    st.dataframe(jobs, use_container_width=True, hide_index=True)
    
    # Download
    csv = jobs.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download CSV",
        data=csv,
        file_name=f"jobs_{search_term.replace(' ', '_')}.csv",
        mime="text/csv"
    )
    
    # Show columns info
    with st.expander("📊 Available Columns"):
        st.write(list(jobs.columns))

else:
    st.info("👈 Configure your search in the sidebar, then click **Search Jobs**")
    
    st.markdown("""
    ---
    ### 📖 Fork Documentation
    
    **Supported Sites:**
    - `indeed`, `linkedin`, `zip_recruiter`, `glassdoor`, `google`, `bayt`, `bdjobs`, `jobstreet`
    
    **JobStreet (Indonesia):**
    - Use `site_name="jobstreet"`
    - Location: Jakarta, Tangerang, Bandung, Surabaya, Yogyakarta
    - Or omit location for nationwide
    
    **Google:**
    - Must use `google_search_term`
    - Copy exact syntax from Google Jobs UI
    
    **Indeed Limitations:**
    - Only one of: hours_old, job_type & is_remote, easy_apply
    
    **LinkedIn Limitations:**
    - Only one of: hours_old, easy_apply
    """)
