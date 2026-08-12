import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime
import urllib.parse

import pandas as pd
import streamlit as st
from jobspy import scrape_jobs
from jobspy.model import Country

# ----------------------------------------------------------------------
# Page Config
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Cari Kerja",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------------------------------------------------
# Custom CSS for Mobile-Friendly & Polished UI
# ----------------------------------------------------------------------
st.markdown("""
<style>
    /* ===== WARMER THEME ===== */
    .stApp {
        background-color: #fefcf7;
    }
    .main > div {
        background-color: #fefcf7;
    }
    
    /* ===== LARGER TOUCH TARGETS (Mobile) ===== */
    @media (max-width: 768px) {
        .stButton button {
            font-size: 18px !important;
            padding: 0.75rem 1.5rem !important;
            min-height: 50px !important;
            border-radius: 12px !important;
            background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
            color: white !important;
            font-weight: 600 !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        }
        .stButton button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4) !important;
        }
        .stCheckbox label {
            font-size: 16px !important;
        }
        .stTextInput input {
            font-size: 16px !important;
            min-height: 44px !important;
            border-radius: 10px !important;
            border: 1px solid #e5e7eb !important;
        }
        .stTextInput input:focus {
            border-color: #2563eb !important;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
        }
        .stSelectbox select {
            font-size: 16px !important;
            min-height: 44px !important;
            border-radius: 10px !important;
        }
        .stNumberInput input {
            font-size: 16px !important;
            min-height: 44px !important;
            border-radius: 10px !important;
        }
        .stExpander {
            margin-bottom: 8px !important;
            border-radius: 12px !important;
            border: 1px solid #f0eee9 !important;
        }
        .stCodeBlock {
            max-height: 300px !important;
            overflow-y: auto !important;
            border-radius: 10px !important;
        }
        /* Sticky search bar */
        .sticky-search-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(254, 252, 247, 0.95);
            backdrop-filter: blur(8px);
            padding: 12px 16px 20px 16px;
            z-index: 1000;
            box-shadow: 0 -4px 20px rgba(0,0,0,0.06);
            border-top: 1px solid rgba(229, 231, 235, 0.5);
        }
        .sticky-search-bar .stButton button {
            width: 100% !important;
            font-size: 18px !important;
            padding: 14px !important;
        }
        /* Filter chips */
        .filter-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 12px 0 16px 0;
        }
        .filter-chip {
            background: #eef2ff;
            color: #1e40af;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border: 1px solid #c7d2fe;
        }
        .filter-chip-remove {
            background: #dbeafe;
            color: #1e40af;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border: 1px solid #93c5fd;
        }
        /* Dua card */
        .dua-card {
            background: linear-gradient(135deg, #f0f7ff, #e8f0fe);
            border-radius: 16px;
            padding: 20px;
            margin: 16px 0;
            border-right: 4px solid #2563eb;
            border-left: 1px solid rgba(37, 99, 235, 0.1);
        }
        .dua-card p {
            font-size: 18px;
            line-height: 1.8;
            color: #1a1a1a;
            font-style: italic;
        }
        .dua-card .attribution {
            font-size: 14px;
            color: #4b5563;
            font-style: normal;
            margin-top: 8px;
        }
        /* Language toggle */
        .lang-toggle {
            display: flex;
            justify-content: flex-end;
            margin-bottom: 8px;
        }
        .lang-toggle button {
            background: transparent !important;
            border: 1px solid #d1d5db !important;
            border-radius: 20px !important;
            padding: 4px 16px !important;
            font-size: 14px !important;
            min-height: 32px !important;
            color: #374151 !important;
            box-shadow: none !important;
        }
        .lang-toggle button:hover {
            background: #f3f4f6 !important;
            transform: none !important;
        }
        .lang-toggle .active-lang {
            background: #2563eb !important;
            color: white !important;
            border-color: #2563eb !important;
        }
        /* Empty state */
        .empty-state {
            text-align: center;
            padding: 40px 20px;
        }
        .empty-state .emoji {
            font-size: 64px;
            margin-bottom: 16px;
        }
        .empty-state h3 {
            color: #1f2937;
            margin-bottom: 8px;
        }
        .empty-state p {
            color: #6b7280;
            max-width: 400px;
            margin: 0 auto 16px auto;
        }
        .empty-state .suggestions {
            text-align: left;
            max-width: 320px;
            margin: 0 auto;
            background: #f9fafb;
            padding: 16px 20px;
            border-radius: 12px;
        }
        .empty-state .suggestions li {
            color: #374151;
            margin-bottom: 6px;
            list-style-type: none;
        }
        .empty-state .suggestions li::before {
            content: "• ";
            color: #2563eb;
            font-weight: bold;
        }
    }
    /* ===== DESKTOP OVERRIDES ===== */
    @media (min-width: 769px) {
        .sticky-search-bar {
            display: none !important;
        }
        .stButton button {
            border-radius: 10px !important;
        }
        .dua-card p {
            font-size: 20px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Language Translations (ID/EN)
# ----------------------------------------------------------------------
LANG = {
    "id": {
        "app_title": "🔎 Cari Kerja",
        "app_caption": "Mencari dari LinkedIn, Indeed, ZipRecruiter, dan Glassdoor. Google tidak discrap — kami berikan saran pencarian manual.",
        "search_settings": "🔧 Pengaturan Pencarian",
        "search_settings_desc": "Atur parameter pencarian di sini.",
        "keyword": "Kata kunci pekerjaan (opsional)",
        "keyword_help": "Kosongkan untuk mencari semua postingan.",
        "location": "Lokasi (opsional)",
        "location_help": "Kosongkan untuk pencarian lebih luas (cocok untuk remote).",
        "location_empty": "💡 Lokasi kosong → pencarian lebih luas.",
        "country": "Negara (Indeed/Glassdoor)",
        "country_help": "Contoh: Indonesia, USA, Singapore, Malaysia.",
        "results": "Hasil per situs",
        "hours": "Diposting dalam (jam)",
        "hours_help": "0 = tidak ada filter.",
        "select_sites": "Pilih situs pekerjaan",
        "glassdoor_disabled": "⚠️ Glassdoor dinonaktifkan — tidak tersedia untuk '{country}'.",
        "ziprecruiter_note": "⚠️ zip_recruiter hanya mencakup US/Canada.",
        "google_suggestion": "✨ Tampilkan saran pencarian Google manual setelah scraping",
        "google_help": "Google tidak discrap — kami akan buatkan query yang bisa Anda gunakan secara manual.",
        "google_extra": "🔍 Pengaturan tambahan untuk pencarian Google manual",
        "age_filter": "Hilangkan listing yang sebut usia (-usia -age -umur)",
        "age_filter_help": "Hanya untuk pencarian Google manual, tidak mempengaruhi hasil scraper.",
        "custom_exclude": "Tambahkan kata kunci yang ingin dikecualikan (pisahkan dengan spasi)",
        "custom_exclude_placeholder": "Contoh: fresh graduate entry level",
        "custom_exclude_help": "Kata kunci akan ditambahkan tanda minus (-) secara otomatis.",
        "search_button": "🔍 Cari Pekerjaan",
        "searching": "🔍 Mencari di **{site}**...",
        "searching_progress": "⏳ Mencari... ({current}/{total})",
        "searching_dua": "⏳ Sedang mencari... semoga dimudahkan.",
        "per_site_results": "📊 Hasil per situs",
        "per_site_ok": "✅ **{site}**: {count} pekerjaan ditemukan",
        "per_site_empty": "⚠️ **{site}**: tidak ada pekerjaan ditemukan",
        "per_site_error": "❌ **{site}**: gagal — {error}",
        "no_jobs": "Tidak ada pekerjaan ditemukan. Coba ubah filter, atau buka tab Panduan Pencarian untuk teknik manual.",
        "no_jobs_valid": "Ditemukan {raw} hasil mentah, tapi tidak ada yang lolos validasi. Coba longgarkan filter.",
        "jobs_found": "✅ Ditemukan {count} pekerjaan valid dari {sites} situs",
        "jobs_filtered": " — {filtered} difilter (tidak lengkap, duplikat, atau sudah kadaluwarsa)",
        "download_csv": "📥 Download CSV",
        "google_manual": "🔍 Ekstra: Pencarian Manual Google Jobs",
        "google_manual_desc": "Salin query ini dan tempelkan di Google Jobs untuk hasil tambahan.",
        "google_search_link": "🔗 Cari di Google Jobs",
        "age_active": "✅ Filter usia aktif: -usia -age -umur",
        "custom_active": "✅ Pengecualian kustom aktif: {exclude}",
        "empty_title": "Belum ada pekerjaan ditemukan",
        "empty_desc": "Coba beberapa saran di bawah ini untuk memperluas pencarian:",
        "empty_suggest_1": "Coba lokasi yang lebih luas (atau kosongkan)",
        "empty_suggest_2": "Coba kata kunci yang berbeda atau lebih umum",
        "empty_suggest_3": "Kurangi filter jam (misal: dari 72 jam ke 168 jam)",
        "empty_suggest_4": "Lihat Panduan Pencarian untuk teknik manual",
        "filter_location": "📍 {location}",
        "filter_hours": "⏰ {hours}h",
        "filter_keyword": "🔍 {keyword}",
        "filter_age": "🚫 usia",
        "filter_custom": "🚫 {word}",
        "playbook_tab": "📖 Panduan Pencarian",
        "search_tab": "🔍 Cari Pekerjaan",
        "footer": "Ditenagai oleh [damarowen/JobSpy](https://github.com/damarowen/JobSpy) — dibuat untuk pencari kerja yang tidak menyerah.",
        "lang_en": "English",
        "lang_id": "Indonesia"
    },
    "en": {
        "app_title": "🔎 Job Search",
        "app_caption": "Searching LinkedIn, Indeed, ZipRecruiter, and Glassdoor. Google is not scraped — we provide a manual search suggestion.",
        "search_settings": "🔧 Search Settings",
        "search_settings_desc": "Configure your search parameters here.",
        "keyword": "Job title / keywords (optional)",
        "keyword_help": "Leave blank to get all postings.",
        "location": "Location (optional)",
        "location_help": "Leave empty for broader search (good for remote).",
        "location_empty": "💡 Location empty → broader search.",
        "country": "Country (Indeed/Glassdoor)",
        "country_help": "Example: Indonesia, USA, Singapore, Malaysia.",
        "results": "Results per site",
        "hours": "Posted within (hours)",
        "hours_help": "0 = no filter.",
        "select_sites": "Select job sites",
        "glassdoor_disabled": "⚠️ Glassdoor disabled — not available for '{country}'.",
        "ziprecruiter_note": "⚠️ zip_recruiter only covers US/Canada.",
        "google_suggestion": "✨ Show Google manual search suggestion after scraping",
        "google_help": "Google is not scraped — we'll build a query you can use manually.",
        "google_extra": "🔍 Additional settings for manual Google search",
        "age_filter": "Exclude listings mentioning age (-usia -age -umur)",
        "age_filter_help": "Only for manual Google search, does not affect scraper results.",
        "custom_exclude": "Add keywords to exclude (separate with space)",
        "custom_exclude_placeholder": "Example: fresh graduate entry level",
        "custom_exclude_help": "Keywords will automatically get a minus (-) prefix.",
        "search_button": "🔍 Search Jobs",
        "searching": "🔍 Searching **{site}**...",
        "searching_progress": "⏳ Searching... ({current}/{total})",
        "searching_dua": "⏳ Searching... may it be made easy.",
        "per_site_results": "📊 Per-site results",
        "per_site_ok": "✅ **{site}**: {count} jobs found",
        "per_site_empty": "⚠️ **{site}**: no jobs found",
        "per_site_error": "❌ **{site}**: failed — {error}",
        "no_jobs": "No jobs found. Try different filters, or check the Playbook tab for manual techniques.",
        "no_jobs_valid": "Found {raw} raw results, but none passed validation. Try loosening filters.",
        "jobs_found": "✅ Found {count} valid jobs across {sites} site(s)",
        "jobs_filtered": " — {filtered} filtered out (incomplete, duplicate, or expired)",
        "download_csv": "📥 Download CSV",
        "google_manual": "🔍 Extra: Google Jobs Manual Search",
        "google_manual_desc": "Copy this query and paste it into Google Jobs for more listings.",
        "google_search_link": "🔗 Search on Google Jobs",
        "age_active": "✅ Age filter active: -usia -age -umur",
        "custom_active": "✅ Custom exclusions active: {exclude}",
        "empty_title": "No jobs found yet",
        "empty_desc": "Try these suggestions to broaden your search:",
        "empty_suggest_1": "Try a wider location (or leave it empty)",
        "empty_suggest_2": "Try different or more general keywords",
        "empty_suggest_3": "Reduce the hours filter (e.g., from 72h to 168h)",
        "empty_suggest_4": "Check the Playbook tab for manual techniques",
        "filter_location": "📍 {location}",
        "filter_hours": "⏰ {hours}h",
        "filter_keyword": "🔍 {keyword}",
        "filter_age": "🚫 age",
        "filter_custom": "🚫 {word}",
        "playbook_tab": "📖 Job Search Playbook",
        "search_tab": "🔍 Search Jobs",
        "footer": "Powered by [damarowen/JobSpy](https://github.com/damarowen/JobSpy) — built for job seekers who refuse to give up.",
        "lang_en": "English",
        "lang_id": "Indonesia"
    }
}

# ----------------------------------------------------------------------
# Initialize Session State
# ----------------------------------------------------------------------
if "lang" not in st.session_state:
    st.session_state.lang = "id"
if "search_clicked" not in st.session_state:
    st.session_state.search_clicked = False
if "settings" not in st.session_state:
    st.session_state.settings = {}

def t(key: str, **kwargs) -> str:
    """Get translated text."""
    text = LANG[st.session_state.lang].get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

# ----------------------------------------------------------------------
# Helper functions (unchanged)
# ----------------------------------------------------------------------
def is_permanent_block(error_msg: str) -> bool:
    if not error_msg:
        return False
    lowered = error_msg.lower()
    return any(marker in lowered for marker in ("403", "cf-waf", "forbidden", "cloudflare", "just a moment"))

def glassdoor_supports_country(country_str: str) -> bool:
    try:
        country = Country.from_string(country_str)
    except ValueError:
        return False
    return len(country.value) == 3

def build_google_search_term(
    search_term: str,
    location: str,
    hours_old: int,
    exclude_age: bool = False,
    custom_exclude: str = "",
) -> str:
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

    if exclude_age:
        term += " -usia -age -umur"

    if custom_exclude and custom_exclude.strip():
        for word in custom_exclude.strip().split():
            if word.strip():
                term += f" -{word.strip()}"

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

    if search_term and search_term.strip():
        kwargs["search_term"] = search_term.strip()

    return kwargs

def scrape_one_site(site: str, **kwargs_inputs) -> tuple[pd.DataFrame | None, str | None]:
    last_error = None
    kwargs = build_kwargs_for_site(site, **kwargs_inputs)

    for attempt in range(1, 3):  # MAX_RETRIES = 2
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(scrape_jobs, **kwargs)
                df = future.result(timeout=60)
            return df, None
        except FutureTimeoutError:
            last_error = f"timed out after 60s"
        except Exception as e:
            last_error = str(e)
            if is_permanent_block(last_error):
                break

        if attempt < 2:
            time.sleep(3)

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
# Render Search Settings (mobile-friendly expander)
# ----------------------------------------------------------------------
def render_search_settings():
    with st.expander(t("search_settings"), expanded=not st.session_state.get("search_clicked", False)):
        st.caption(t("search_settings_desc"))

        col1, col2 = st.columns(2)

        with col1:
            search_term = st.text_input(
                t("keyword"),
                value="",
                help=t("keyword_help")
            )
            location = st.text_input(
                t("location"),
                value="",
                help=t("location_help")
            )
            if not location:
                st.caption(t("location_empty"))

        with col2:
            country_indeed = st.text_input(
                t("country"),
                value="Indonesia",
                help=t("country_help")
            )
            results_wanted = st.slider(t("results"), min_value=5, max_value=100, value=20, step=5)
            hours_old = st.number_input(
                t("hours"),
                min_value=0,
                value=72,
                step=24,
                help=t("hours_help")
            )

        st.caption(t("select_sites"))
        glassdoor_ok = glassdoor_supports_country(country_indeed)
        sites = []
        cols = st.columns(3)
        for i, site in enumerate(["indeed", "linkedin", "zip_recruiter", "glassdoor"]):
            col = cols[i % 3]
            if site == "glassdoor" and not glassdoor_ok:
                col.checkbox(
                    "glassdoor 🚫",
                    value=False,
                    disabled=True,
                    help=t("glassdoor_disabled", country=country_indeed),
                    key="site_glassdoor",
                )
            else:
                checked = col.checkbox(site, value=(site in ["indeed", "linkedin"]), key=f"site_{site}")
                if checked:
                    sites.append(site)

        if not glassdoor_ok:
            st.caption(t("glassdoor_disabled", country=country_indeed))
        st.caption(t("ziprecruiter_note"))

        # Google manual suggestion
        google_enabled = st.checkbox(
            t("google_suggestion"),
            value=False,
            help=t("google_help")
        )

        exclude_age = False
        custom_exclude = ""
        if google_enabled:
            st.markdown("---")
            st.caption(t("google_extra"))

            exclude_age = st.checkbox(
                t("age_filter"),
                value=False,
                help=t("age_filter_help")
            )

            custom_exclude = st.text_input(
                t("custom_exclude"),
                value="",
                placeholder=t("custom_exclude_placeholder"),
                help=t("custom_exclude_help")
            )

        # Save settings to session state
        st.session_state.settings = {
            "search_term": search_term,
            "location": location,
            "country_indeed": country_indeed,
            "results_wanted": results_wanted,
            "hours_old": hours_old,
            "sites": sites,
            "google_enabled": google_enabled,
            "exclude_age": exclude_age,
            "custom_exclude": custom_exclude,
        }

        return st.session_state.settings

# ==================== LANGUAGE TOGGLE ====================
def render_lang_toggle():
    col1, col2, col3 = st.columns([1, 5, 1])
    with col3:
        if st.button("🇮🇩 ID" if st.session_state.lang == "en" else "🇬🇧 EN", key="lang_toggle"):
            st.session_state.lang = "en" if st.session_state.lang == "id" else "id"
            st.rerun()

# ==================== FILTER CHIPS ====================
def render_filter_chips(settings):
    chips = []
    if settings.get("location") and settings["location"].strip():
        chips.append(t("filter_location", location=settings["location"]))
    if settings.get("hours_old") and settings["hours_old"] > 0:
        chips.append(t("filter_hours", hours=settings["hours_old"]))
    if settings.get("search_term") and settings["search_term"].strip():
        chips.append(t("filter_keyword", keyword=settings["search_term"][:30]))
    if settings.get("exclude_age"):
        chips.append(t("filter_age"))
    if settings.get("custom_exclude") and settings["custom_exclude"].strip():
        for word in settings["custom_exclude"].strip().split()[:2]:
            chips.append(t("filter_custom", word=word))

    if chips:
        html = '<div class="filter-chips">'
        for chip in chips:
            html += f'<span class="filter-chip">{chip}</span>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

# ==================== EMPTY STATE ====================
def render_empty_state():
    st.markdown(f"""
    <div class="empty-state">
        <div class="emoji">🔍</div>
        <h3>{t("empty_title")}</h3>
        <p>{t("empty_desc")}</p>
        <div class="suggestions">
            <li>{t("empty_suggest_1")}</li>
            <li>{t("empty_suggest_2")}</li>
            <li>{t("empty_suggest_3")}</li>
            <li>{t("empty_suggest_4")}</li>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==================== DUA CARD ====================
def render_dua_card():
    st.markdown("""
    <div class="dua-card">
        <p>
            "Barang siapa memperbanyak istighfar; niscaya Allah memberikan jalan keluar bagi setiap kesedihannya, kelapangan untuk setiap kesempitannya dan rizki dari arah yang tidak disangka-sangka."
        </p>
        <div class="attribution">— HR. Ahmad dari Ibnu Abbas</div>
    </div>
    <div class="dua-card">
        <p>
            "Aku (Nabi Nuh) berkata (pada mereka), 'Beristighfarlah kepada Rabb kalian, sungguh Dia Maha Pengampun. Niscaya Dia akan menurunkan kepada kalian hujan yang lebat dari langit. Dan Dia akan memperbanyak harta serta anak-anakmu, juga mengadakan kebun-kebun dan sungai-sungai untukmu.'"
        </p>
        <div class="attribution">— QS. Nuh: 10-12</div>
    </div>
    """, unsafe_allow_html=True)

# ==================== TAB 1: SEARCH ====================
tab1, tab2 = st.tabs([t("search_tab"), t("playbook_tab")])

with tab1:
    render_lang_toggle()

    st.caption(t("app_caption"))

    # Mobile-friendly: search settings in expander
    settings = render_search_settings()

    # Search button (main)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        search_clicked = st.button(
            t("search_button"),
            type="primary",
            use_container_width=True,
            key="search_button_main"
        )

    if search_clicked:
        st.session_state.search_clicked = True

    # ===== MAIN SEARCH LOGIC =====
    if search_clicked:
        sites = settings["sites"]
        if not sites:
            st.error("Pilih minimal satu situs pekerjaan.")
            st.stop()

        common_inputs = {
            "search_term": settings["search_term"],
            "location": settings["location"],
            "country_indeed": settings["country_indeed"],
            "results_wanted": settings["results_wanted"],
            "hours_old": settings["hours_old"],
        }

        all_dfs = []
        site_status = {}
        total_sites = len(sites)

        # ---- DUA CARD + PROGRESS ----
        render_dua_card()

        status_area = st.empty()
        progress_area = st.empty()

        for idx, site in enumerate(sites):
            progress_area.caption(t("searching_progress", current=idx+1, total=total_sites))
            status_area.info(t("searching", site=site))

            df, err = scrape_one_site(site, **common_inputs)
            if err:
                site_status[site] = ("error", err)
            elif df is None or len(df) == 0:
                site_status[site] = ("empty", 0)
            else:
                site_status[site] = ("ok", len(df))
                all_dfs.append(df)

        status_area.empty()
        progress_area.empty()

        # ---- RESULTS ----
        if all_dfs:
            jobs = pd.concat(all_dfs, ignore_index=True)
            if "job_url" in jobs.columns:
                jobs = jobs.drop_duplicates(subset="job_url")

            raw_count = len(jobs)
            jobs = validate_jobs(jobs, settings["hours_old"])
            jobs = dedupe_cross_site(jobs)
            filtered_count = raw_count - len(jobs)

            if jobs.empty:
                st.warning(t("no_jobs_valid", raw=raw_count))
                render_empty_state()
            else:
                # ---- FILTER CHIPS ----
                render_filter_chips(settings)

                # ---- PER-SITE RESULTS ----
                with st.expander(t("per_site_results"), expanded=True):
                    for site in sites:
                        kind, info = site_status[site]
                        if kind == "ok":
                            st.success(t("per_site_ok", site=site, count=info))
                        elif kind == "empty":
                            st.warning(t("per_site_empty", site=site))
                        else:
                            st.error(t("per_site_error", site=site, error=info))

                # ---- JOB DATA ----
                summary = t("jobs_found", count=len(jobs), sites=len(all_dfs))
                if filtered_count:
                    summary += t("jobs_filtered", filtered=filtered_count)
                st.success(summary)

                # Company career column
                if "company_url" in jobs.columns:
                    jobs["company_career"] = jobs["company_url"].fillna("")
                    mask = jobs["company_career"].str.strip().eq("") | jobs["company_career"].isna()
                    jobs.loc[mask, "company_career"] = jobs.loc[mask, "company"].astype(str) + " " + jobs.loc[mask, "title"].astype(str)
                else:
                    jobs["company_career"] = jobs["company"].astype(str) + " " + jobs["title"].astype(str)

                preferred_cols = ["site", "title", "company", "location", "job_type", "is_remote", "date_posted", "job_url", "company_career"]
                existing_preferred = [c for c in preferred_cols if c in jobs.columns]
                other_cols = [c for c in jobs.columns if c not in existing_preferred]
                jobs_display = jobs[existing_preferred + other_cols]

                st.dataframe(jobs_display, width="stretch", hide_index=True)

                # ---- CSV DOWNLOAD ----
                loc_part = settings["location"].strip().replace(" ", "_") if settings["location"] and settings["location"].strip() else "anywhere"
                search_part = settings["search_term"].strip().replace(" ", "_") if settings["search_term"] and settings["search_term"].strip() else "all_jobs"
                timestamp = datetime.now().strftime("%Y-%b-%d_%H%M")
                csv_filename = f"jobs_{search_part}_{loc_part}_{timestamp}.csv"

                csv = jobs.to_csv(index=False).encode("utf-8")
                st.download_button(
                    t("download_csv"),
                    data=csv,
                    file_name=csv_filename,
                    mime="text/csv",
                    use_container_width=True,
                )

                # ---- GOOGLE MANUAL SUGGESTION ----
                if settings["google_enabled"]:
                    st.divider()
                    st.subheader(t("google_manual"))

                    google_query = build_google_search_term(
                        search_term=settings["search_term"],
                        location=settings["location"],
                        hours_old=settings["hours_old"],
                        exclude_age=settings["exclude_age"],
                        custom_exclude=settings["custom_exclude"],
                    )

                    st.caption(t("google_manual_desc"))
                    st.code(google_query, language="text")

                    encoded_query = urllib.parse.quote(google_query)
                    google_url = f"https://www.google.com/search?q={encoded_query}&ibp=htl;jobs"
                    st.markdown(f"[{t('google_search_link')}]({google_url})")

                    if settings["exclude_age"]:
                        st.caption(t("age_active"))
                    if settings["custom_exclude"]:
                        st.caption(t("custom_active", exclude=settings["custom_exclude"]))

        else:
            # ---- NO JOBS FROM ANY SITE ----
            with st.expander(t("per_site_results"), expanded=True):
                for site in sites:
                    kind, info = site_status[site]
                    if kind == "ok":
                        st.success(t("per_site_ok", site=site, count=info))
                    elif kind == "empty":
                        st.warning(t("per_site_empty", site=site))
                    else:
                        st.error(t("per_site_error", site=site, error=info))

            st.warning(t("no_jobs"))
            render_empty_state()

    # ---- STICKY SEARCH BAR (Mobile only) ----
    # Always show after search or when no search yet
    if not search_clicked or st.session_state.search_clicked:
        st.markdown("""
        <div class="sticky-search-bar">
        """, unsafe_allow_html=True)
        col_s1, col_s2, col_s3 = st.columns([1, 2, 1])
        with col_s2:
            st.button(
                t("search_button"),
                type="primary",
                use_container_width=True,
                key="search_button_sticky"
            )
        st.markdown("</div>", unsafe_allow_html=True)

# ==================== TAB 2: PLAYBOOK ====================
with tab2:
    st.title("📖 Panduan Pencarian Pekerjaan")
    st.markdown("**Teknik praktis mencari informasi pekerjaan valid menggunakan Google Search.**")

    with st.expander("🚀 Mulai Cepat – Copy‑paste kata kunci ini", expanded=True):
        st.markdown("**1. Pencarian umum (Indonesia)**")
        st.code('("recruitment" OR "rekrutmen" OR "karir" OR "lowongan" OR "career" OR "pekerjaan" OR "job" OR "vacancy") (site:*.co.id OR site:*.ac.id OR site:*.go.id OR site:*.com OR site:*.org)', language="text")
        st.caption("💡 Tambahkan `-jobstreet` di akhir untuk mengecualikan JobStreet.")

        st.markdown("**2. Kota spesifik (contoh: Temanggung, Jateng)**")
        st.code('("recruitment" OR "rekrutmen" OR "karir" OR "lowongan" OR "career" OR "pekerjaan" OR "job" OR "vacancy") AND ("Temanggung" OR "Magelang" OR "Jawa Tengah") (site:*.co.id OR site:*.ac.id OR site:*.go.id OR site:*.com OR site:*.org) -jobstreet', language="text")

        st.markdown("**3. Area Surabaya – Gresik**")
        st.code('intext:(recruitment OR rekrutmen OR karir OR lowongan OR career) AND (surabaya OR gresik)', language="text")

    with st.expander("📍 Buat query lokasi sendiri"):
        col1, col2 = st.columns(2)
        with col1:
            city = st.text_input("Kota", "Temanggung")
        with col2:
            province = st.text_input("Provinsi (opsional)", "Jawa Tengah")
        exclude = st.text_input("Kata yang dikecualikan (contoh: jobstreet)", value="jobstreet")
        if st.button("Buat Query Lokasi", use_container_width=True):
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
            st.markdown(f"[🔗 Cari di Google](https://www.google.com/search?q={urllib.parse.quote(query)})")

    with st.expander("🏢 Scan portal pekerjaan spesifik (ramah remote)"):
        st.markdown("Portal ini sering digunakan perusahaan dengan budaya baik dan ramah remote.")
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
            st.markdown(f"[🔗 Cari](https://www.google.com/search?q={urllib.parse.quote(query)})")

    with st.expander("🔗 Filter waktu LinkedIn (24 jam terakhir)"):
        st.markdown("Ubah angka setelah `r` untuk rentang waktu berbeda (dalam detik).")
        linkedin_location = st.text_input("Lokasi LinkedIn", "Surabaya")
        linkedin_keyword = st.text_input("Kata kunci LinkedIn", "hiring")
        if st.button("Buat Link LinkedIn", use_container_width=True):
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
            st.markdown(f"[🔗 Buka LinkedIn]({url})")
            st.caption("💡 Ganti `r86400` ke `r172800` untuk 48 jam, `r43200` untuk 12 jam.")

    with st.expander("🤖 AI Helper – Buat kata kunci dengan ChatGPT / DeepSeek"):
        st.markdown("Salin prompt ini dan tempelkan ke ChatGPT, DeepSeek, atau Meta AI.")
        prompt = """Buatkan kata kunci untuk mencari informasi pekerjaan bidang [your field] di [your location] lewat Google Search dengan teknik Google Dorking.

Contoh output:
- site:indeed.co.id "GIS" "Indonesia" "job"
- inurl:career "GIS" "Indonesia" "vacancy"
- filetype:pdf "Lowongan Kerja GIS" "Indonesia"

Buatkan 5–10 variasi dengan operator yang berbeda."""
        st.code(prompt, language="text")
        st.caption("💡 Ganti bagian dalam kurung siku dengan bidang dan lokasi Anda.")

    with st.expander("🌐 Komunitas & Alat Gratis"):
        st.markdown("**Gabung komunitas**")
        st.markdown("[Discord: Kabur Aja Dulu](https://discord.com/invite/KaburAjaDulu)")

        st.markdown("**Alat CV & tracking lamaran gratis**")
        st.markdown("[jobresume.rndhri.com](https://jobresume.rndhri.com/)")

        st.markdown("**Laporan WEF Future of Jobs Report 2025**")
        st.markdown("[Download PDF](https://www.weforum.org/publications/the-future-of-jobs-report-2025/)")
        st.markdown("**Prompt AI untuk meringkas laporan:**")
        summarise_prompt = """Ringkaskan laporan Future of Jobs Report 2025 dari World Economic Forum dalam bahasa Indonesia. Fokus pada:
- Sektor yang paling banyak menambah lapangan kerja
- Sektor yang paling banyak mengurangi lapangan kerja
- Keterampilan yang paling dibutuhkan
- Rekomendasi untuk pencari kerja
Buat ringkasan 2–3 paragraf yang mudah dipahami."""
        st.code(summarise_prompt, language="text")

        st.markdown("---")
        st.markdown("**Bagikan tips Anda**")
        tip = st.text_area("Tips Anda (untuk komunitas)")
        if st.button("Kirim Tips", use_container_width=True):
            st.success("Terima kasih! Tips Anda telah dicatat.")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown(t("footer"))
