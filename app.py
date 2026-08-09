import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime
import urllib.parse

import pandas as pd
import streamlit as st
from jobspy import scrape_jobs
from jobspy.model import Country

st.set_page_config(
    page_title="Job Search Scraper",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------------------------------------------------
# Custom CSS for better mobile experience
# ----------------------------------------------------------------------
st.markdown("""
<style>
    /* Larger touch targets on mobile */
    @media (max-width: 768px) {
        .stButton button {
            font-size: 18px !important;
            padding: 0.75rem 1.5rem !important;
            min-height: 50px !important;
        }
        .stCheckbox label {
            font-size: 16px !important;
        }
        .stTextInput input {
            font-size: 16px !important;
            min-height: 44px !important;
        }
        .stSelectbox select {
            font-size: 16px !important;
            min-height: 44px !important;
        }
        .stNumberInput input {
            font-size: 16px !important;
            min-height: 44px !important;
        }
        .stExpander {
            margin-bottom: 8px !important;
        }
        .stCodeBlock {
            max-height: 300px !important;
            overflow-y: auto !important;
        }
        /* Sticky search button on mobile */
        .sticky-search {
            position: sticky;
            bottom: 0;
            background: white;
            padding: 12px 0;
            z-index: 100;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        }
        /* Dua card styling */
        .dua-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
            border-right: 4px solid #2e7d32;
        }
        .dua-card p {
            font-size: 18px;
            line-height: 1.8;
            color: #1a1a1a;
        }
        .dua-card .attribution {
            font-size: 14px;
            color: #555;
            font-style: italic;
        }
    }
    /* Desktop styles for dua card */
    .dua-card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 24px;
        margin: 16px 0;
        border-right: 4px solid #2e7d32;
    }
    .dua-card p {
        font-size: 20px;
        line-height: 1.8;
        color: #1a1a1a;
    }
    .dua-card .attribution {
        font-size: 14px;
        color: #555;
        font-style: italic;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
ALL_SITES = ["indeed", "linkedin", "zip_recruiter", "glassdoor"]
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

def build_google_search_term(
    search_term: str,
    location: str,
    hours_old: int,
    exclude_age: bool = False,
    custom_exclude: str = "",
) -> str:
    """Build the query Google Jobs expects, with optional exclusions."""
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

    # Age exclusions
    if exclude_age:
        term += " -usia -age -umur"

    # Custom exclusions (app adds - automatically)
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
# Render Search Settings (mobile-friendly expander)
# ----------------------------------------------------------------------
def render_search_settings():
    """Render search settings in a collapsible expander (mobile-friendly)"""
    with st.expander("🔧 Pengaturan Pencarian", expanded=not st.session_state.get("search_clicked", False)):
        st.caption("Atur parameter pencarian di sini.")

        col1, col2 = st.columns(2)

        with col1:
            search_term = st.text_input(
                "Kata kunci pekerjaan (opsional)",
                value="",
                help="Kosongkan untuk mencari semua postingan."
            )
            location = st.text_input(
                "Lokasi (opsional)",
                value="",
                help="Kosongkan untuk pencarian lebih luas (cocok untuk remote)."
            )
            if not location:
                st.caption("💡 Lokasi kosong → pencarian lebih luas.")

        with col2:
            country_indeed = st.text_input(
                "Negara (Indeed/Glassdoor)",
                value="Indonesia",
                help="Contoh: Indonesia, USA, Singapore, Malaysia."
            )
            results_wanted = st.slider("Hasil per situs", min_value=5, max_value=100, value=20, step=5)
            hours_old = st.number_input(
                "Diposting dalam (jam)",
                min_value=0,
                value=72,
                step=24,
                help="0 = tidak ada filter."
            )

        st.caption("Pilih situs pekerjaan")
        glassdoor_ok = glassdoor_supports_country(country_indeed)
        sites = []
        cols = st.columns(3)
        for i, site in enumerate(ALL_SITES):
            col = cols[i % 3]
            if site == "glassdoor" and not glassdoor_ok:
                col.checkbox(
                    "glassdoor 🚫",
                    value=False,
                    disabled=True,
                    help=f"Tidak tersedia untuk '{country_indeed}'.",
                    key="site_glassdoor",
                )
            else:
                checked = col.checkbox(site, value=(site in DEFAULT_SITES), key=f"site_{site}")
                if checked:
                    sites.append(site)

        if not glassdoor_ok:
            st.caption(f"⚠️ Glassdoor dinonaktifkan — tidak tersedia untuk '{country_indeed}'.")
        st.caption("⚠️ zip_recruiter hanya mencakup US/Canada.")

        # Google manual suggestion
        google_enabled = st.checkbox(
            "✨ Tampilkan saran pencarian Google manual setelah scraping",
            value=False,
            help="Google tidak discrap — kami akan buatkan query yang bisa Anda gunakan secara manual."
        )

        # Google extra settings (only shown when google_enabled is checked)
        exclude_age = False
        custom_exclude = ""
        if google_enabled:
            st.markdown("---")
            st.caption("🔍 Pengaturan tambahan untuk pencarian Google manual")

            exclude_age = st.checkbox(
                "Hilangkan listing yang sebut usia (-usia -age -umur)",
                value=False,
                help="Hanya untuk pencarian Google manual, tidak mempengaruhi hasil scraper."
            )

            custom_exclude = st.text_input(
                "Tambahkan kata kunci yang ingin dikecualikan (pisahkan dengan spasi)",
                value="",
                placeholder="Contoh: fresh graduate entry level",
                help="Kata kunci akan ditambahkan tanda minus (-) secara otomatis."
            )

        return {
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

# ==================== TAB 1: SEARCH ====================
tab1, tab2 = st.tabs(["🔍 Cari Pekerjaan", "📖 Panduan Pencarian"])

with tab1:
    st.caption(
        "🔎 Mencari dari LinkedIn, Indeed, ZipRecruiter, dan Glassdoor. "
        "**Google tidak discrap** — kami berikan saran pencarian manual sebagai gantinya."
    )

    # Mobile-friendly: search settings in expander (not sidebar)
    settings = render_search_settings()

    # Sticky search button (mobile-friendly)
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        search_clicked = st.button(
            "🔍 Cari Pekerjaan",
            type="primary",
            use_container_width=True,
            key="search_button"
        )

    if search_clicked:
        st.session_state["search_clicked"] = True

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
        status_area = st.empty()

        # ---- DUA CARD ----
        st.markdown("""
        <div class="dua-card">
            <p>
                "Barang siapa memperbanyak istighfar; niscaya Allah memberikan jalan keluar bagi setiap kesedihannya, kelapangan untuk setiap kesempitannya dan rizki dari arah yang tidak disangka-sangka."
            </p>
            <div class="attribution">— HR. Ahmad dari Ibnu Abbas</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="dua-card">
            <p>
                "Aku (Nabi Nuh) berkata (pada mereka), 'Beristighfarlah kepada Rabb kalian, sungguh Dia Maha Pengampun. Niscaya Dia akan menurunkan kepada kalian hujan yang lebat dari langit. Dan Dia akan memperbanyak harta serta anak-anakmu, juga mengadakan kebun-kebun dan sungai-sungai untukmu.'"
            </p>
            <div class="attribution">— QS. Nuh: 10-12</div>
        </div>
        """, unsafe_allow_html=True)

        st.caption("⏳ Sedang mencari... semoga dimudahkan.")

        # ---- Scraping loop with progress ----
        for site in sites:
            status_area.info(f"🔍 Mencari di **{site}**...")
            df, err = scrape_one_site(site, **common_inputs)
            if err:
                site_status[site] = ("error", err)
            elif df is None or len(df) == 0:
                site_status[site] = ("empty", 0)
            else:
                site_status[site] = ("ok", len(df))
                all_dfs.append(df)

        status_area.empty()

        # ---- Results ----
        with st.expander("📊 Hasil per situs", expanded=True):
            for site in sites:
                kind, info = site_status[site]
                if kind == "ok":
                    st.success(f"✅ **{site}**: {info} pekerjaan ditemukan")
                elif kind == "empty":
                    st.warning(f"⚠️ **{site}**: tidak ada pekerjaan ditemukan")
                else:
                    st.error(f"❌ **{site}**: gagal — {info}")

        if not all_dfs:
            st.warning(
                "Tidak ada pekerjaan ditemukan. Coba ubah filter, atau buka tab "
                "Panduan Pencarian untuk teknik manual."
            )
        else:
            jobs = pd.concat(all_dfs, ignore_index=True)
            if "job_url" in jobs.columns:
                jobs = jobs.drop_duplicates(subset="job_url")

            raw_count = len(jobs)
            jobs = validate_jobs(jobs, settings["hours_old"])
            jobs = dedupe_cross_site(jobs)
            filtered_count = raw_count - len(jobs)

            if jobs.empty:
                st.warning(
                    f"Ditemukan {raw_count} hasil mentah, tapi tidak ada yang lolos validasi. Coba longgarkan filter."
                )
            else:
                # Company career column
                if "company_url" in jobs.columns:
                    jobs["company_career"] = jobs["company_url"].fillna("")
                    mask = jobs["company_career"].str.strip().eq("") | jobs["company_career"].isna()
                    jobs.loc[mask, "company_career"] = jobs.loc[mask, "company"].astype(str) + " " + jobs.loc[mask, "title"].astype(str)
                else:
                    jobs["company_career"] = jobs["company"].astype(str) + " " + jobs["title"].astype(str)

                summary = f"✅ Ditemukan {len(jobs)} pekerjaan valid dari {len(all_dfs)} situs"
                if filtered_count:
                    summary += f" — {filtered_count} difilter (tidak lengkap, duplikat, atau sudah kadaluwarsa)"
                st.success(summary)

                # Show essential columns first
                preferred_cols = ["site", "title", "company", "location", "job_type", "is_remote", "date_posted", "job_url", "company_career"]
                existing_preferred = [c for c in preferred_cols if c in jobs.columns]
                other_cols = [c for c in jobs.columns if c not in existing_preferred]
                jobs_display = jobs[existing_preferred + other_cols]

                st.dataframe(jobs_display, width="stretch", hide_index=True)

                # CSV download
                loc_part = settings["location"].strip().replace(" ", "_") if settings["location"] and settings["location"].strip() else "anywhere"
                search_part = settings["search_term"].strip().replace(" ", "_") if settings["search_term"] and settings["search_term"].strip() else "all_jobs"
                timestamp = datetime.now().strftime("%Y-%b-%d_%H%M")
                csv_filename = f"jobs_{search_part}_{loc_part}_{timestamp}.csv"

                csv = jobs.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download CSV",
                    data=csv,
                    file_name=csv_filename,
                    mime="text/csv",
                    use_container_width=True,
                )

                # Google manual suggestion (only if enabled)
                if settings["google_enabled"]:
                    st.divider()
                    st.subheader("🔍 Ekstra: Pencarian Manual Google Jobs")

                    google_query = build_google_search_term(
                        search_term=settings["search_term"],
                        location=settings["location"],
                        hours_old=settings["hours_old"],
                        exclude_age=settings["exclude_age"],
                        custom_exclude=settings["custom_exclude"],
                    )

                    st.caption("Salin query ini dan tempelkan di Google Jobs untuk hasil tambahan.")
                    st.code(google_query, language="text")

                    encoded_query = urllib.parse.quote(google_query)
                    google_url = f"https://www.google.com/search?q={encoded_query}&ibp=htl;jobs"
                    st.markdown(f"[🔗 Cari di Google Jobs]({google_url})")

                    if settings["exclude_age"]:
                        st.caption("✅ Filter usia aktif: -usia -age -umur")
                    if settings["custom_exclude"]:
                        st.caption(f"✅ Pengecualian kustom aktif: {settings['custom_exclude']}")

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
st.markdown(
    "Ditenagai oleh [damarowen/JobSpy](https://github.com/damarowen/JobSpy) — "
    "dibuat untuk pencari kerja yang tidak menyerah."
)
