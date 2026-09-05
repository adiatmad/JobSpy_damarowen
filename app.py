import urllib.parse
from datetime import datetime
import pandas as pd
import streamlit as st

from utils import (
    inject_custom_css, render_dua_cards, glassdoor_supports_country, build_google_search_term
)
from scraper import scrape_one_site_cached
from pipeline import (
    validate_jobs, deduplicate_jobs, detect_ats_friendly, categorize_work_type, calculate_match_score
)

# Konfigurasi Halaman
st.set_page_config(
    page_title="Teman Cari Kerja",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

inject_custom_css()

ALL_SITES = ["indeed", "linkedin", "zip_recruiter", "glassdoor"]
DEFAULT_SITES = ["indeed", "linkedin"]

# --- INISIALISASI SESSION STATE ---
if "raw_jobs" not in st.session_state:
    st.session_state.raw_jobs = pd.DataFrame()
if "search_executed" not in st.session_state:
    st.session_state.search_executed = False

def render_search_settings():
    with st.expander("🔧 Pengaturan & Filter Pencarian", expanded=not st.session_state.search_executed):
        st.caption("Atur kata kunci, lokasi, dan filter kecocokan skill kamu di sini.")

        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("Kata kunci / Posisi pekerjaan", value="Python Developer")
            location = st.text_input("Lokasi (opsional)", value="Indonesia")
            target_keywords = st.text_input("Target Skill Kamu (pisahkan dengan koma)", value="Python, SQL, Docker")

        with col2:
            country_indeed = st.text_input("Negara (Indeed/Glassdoor)", value="Indonesia")
            results_wanted = st.slider("Hasil per situs", min_value=5, max_value=50, value=15, step=5)
            hours_old = st.number_input("Diposting dalam (jam)", min_value=0, value=72, step=24)
            exclude_keywords = st.text_input("Kata kunci yang dihindari (pisahkan dengan koma)", value="Senior, Lead, Manager")

        st.caption("Pilih situs pekerjaan:")
        glassdoor_ok = glassdoor_supports_country(country_indeed)
        sites = []
        cols = st.columns(4)
        for i, site in enumerate(ALL_SITES):
            col = cols[i % 4]
            if site == "glassdoor" and not glassdoor_ok:
                col.checkbox("glassdoor 🚫", value=False, disabled=True, key="site_glassdoor")
            else:
                checked = col.checkbox(site, value=(site in DEFAULT_SITES), key=f"site_{site}")
                if checked:
                    sites.append(site)

        st.markdown("---")
        proxy_input = st.text_input("Proxy Opsional (Pengguna Lanjutan)", value="", placeholder="http://user:pass@host:port")

        st.markdown("---")
        google_enabled = st.checkbox("✨ Buatkan juga saran pencarian Google Jobs manual", value=False)
        exclude_age = False
        custom_exclude = ""
        if google_enabled:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                exclude_age = st.checkbox("Hilangkan kata usia (-usia -age -umur)", value=False)
            with col_g2:
                custom_exclude = st.text_input("Kecualikan kata kunci Google kustom", value="")

        return {
            "search_term": search_term,
            "location": location,
            "country_indeed": country_indeed,
            "results_wanted": results_wanted,
            "hours_old": hours_old,
            "sites": sites,
            "proxy": proxy_input,
            "target_keywords": target_keywords,
            "exclude_keywords": exclude_keywords,
            "google_enabled": google_enabled,
            "exclude_age": exclude_age,
            "custom_exclude": custom_exclude,
        }

# --- HEADER APLIKASI ---
st.title("🔎 Teman Cari Kerja")
st.caption("Alat bantu pencari kerja sederhana untuk mengumpulkan lowongan valid, membuang duplikat, dan mengukur kecocokan skill.")

with st.expander("❓ **Petunjuk Penggunaan (Klik Untuk Membaca)**", expanded=False):
    st.markdown("""
    **Panduan Singkat:**
    1. Buka expander **🔧 Pengaturan & Filter Pencarian** di bawah.
    2. Masukkan posisi yang dicari dan lokasi.
    3. Masukkan **Target Skill** kamu. Aplikasi akan menghitung persen kecocokan (Match Score).
    4. Klik **🔍 Cari Pekerjaan**.
    5. **Centang Status Lamaran:** Kamu bisa menandai lowongan yang sudah kamu lamar langsung di tabel!
    
    💡 **Penting untuk Calon Perantau:**
    Cek kalkulasi biaya hidup & simulasi merantau di **[Nafkah - Kalkulator Merantau](https://nafkah.adenaufal.com/)**.
    """)

tab1, tab2 = st.tabs(["🔍 Cari Pekerjaan", "📖 Panduan Pencarian"])

# ==================== TAB 1: CARI PEKERJAAN ====================
with tab1:
    settings = render_search_settings()

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        search_clicked = st.button("🔍 Cari Pekerjaan", type="primary", use_container_width=True)

    if search_clicked:
        sites = settings["sites"]
        if not sites:
            st.error("Pilih minimal satu situs pekerjaan.")
            st.stop()

        render_dua_cards()
        status_area = st.empty()
        all_dfs = []
        site_status = {}

        for site in sites:
            status_area.info(f"⏳ Sedang mencari di **{site}**...")
            df, err = scrape_one_site_cached(
                site=site,
                search_term=settings["search_term"],
                location=settings["location"],
                country_indeed=settings["country_indeed"],
                results_wanted=settings["results_wanted"],
                hours_old=settings["hours_old"],
                proxy=settings["proxy"]
            )
            if err:
                site_status[site] = ("error", err)
            elif df is None or len(df) == 0:
                site_status[site] = ("empty", 0)
            else:
                site_status[site] = ("ok", len(df))
                all_dfs.append(df)

        status_area.empty()

        with st.expander("📊 Status Hasil Pencarian Per Situs", expanded=True):
            for site in sites:
                kind, info = site_status[site]
                if kind == "ok":
                    st.success(f"✅ **{site}**: {info} lowongan ditemukan")
                elif kind == "empty":
                    st.warning(f"⚠️ **{site}**: tidak ada lowongan ditemukan")
                else:
                    st.error(f"❌ **{site}**: kendala — {info}")

        if not all_dfs:
            st.warning("Tidak ada lowongan ditemukan. Coba perluas filter lokasi atau buka tab Panduan Pencarian.")
            st.session_state.raw_jobs = pd.DataFrame()
            st.session_state.search_executed = False
        else:
            combined_jobs = pd.concat(all_dfs, ignore_index=True)
            valid_jobs = validate_jobs(combined_jobs, settings["hours_old"])
            clean_jobs = deduplicate_jobs(valid_jobs)
            
            clean_jobs["Form Type"] = clean_jobs["job_url"].apply(detect_ats_friendly)
            clean_jobs["Work Type"] = clean_jobs.apply(categorize_work_type, axis=1)
            clean_jobs["Sudah Dilamar"] = False
            
            st.session_state.raw_jobs = clean_jobs
            st.session_state.search_executed = True

    # --- TAMPILAN HASIL (STATE DRIVEN) ---
    if st.session_state.search_executed and not st.session_state.raw_jobs.empty:
        jobs_to_display = calculate_match_score(
            st.session_state.raw_jobs.copy(), 
            settings["target_keywords"], 
            settings["exclude_keywords"]
        )

        st.info("💡 **Tips Merantau:** Cek simulasi biaya hidup lengkap di **[Nafkah.adenaufal.com](https://nafkah.adenaufal.com/)**.")

        # FILTER REAL-TIME
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_work = st.multiselect("Filter Jenis Kerja", options=["🌐 Remote", "🏢 Hybrid", "📍 On-site"], default=["🌐 Remote", "🏢 Hybrid", "📍 On-site"])
        with col_f2:
            filter_ats_only = st.checkbox("Hanya tampilkan ⚡ Quick Apply (ATS)", value=False)

        if filter_work and "Work Type" in jobs_to_display.columns:
            jobs_to_display = jobs_to_display[jobs_to_display["Work Type"].isin(filter_work)]
        if filter_ats_only and "Form Type" in jobs_to_display.columns:
            jobs_to_display = jobs_to_display[jobs_to_display["Form Type"] == "⚡ Quick Apply (ATS)"]

        st.success(f"✅ Menampilkan **{len(jobs_to_display)}** lowongan unik & terfilter.")

        # TABEL INTERAKTIF TRACKER (AMUNISI SAFEGUARD DENGAN FALLBACK)
        desired_cols = ["Sudah Dilamar", "title", "company", "Rekomendasi & Match", "Detail & Finansial", "job_url"]
        display_cols = [c for c in desired_cols if c in jobs_to_display.columns]

        edited_df = st.data_editor(
            jobs_to_display[display_cols],
            column_config={
                "Sudah Dilamar": st.column_config.CheckboxColumn("Status", help="Centang jika sudah dilamar", default=False),
                "title": "Posisi Pekerjaan",
                "company": "Perusahaan",
                "Rekomendasi & Match": "Match & Format",
                "Detail & Finansial": "Sistem, Lokasi & UMR",
                "job_url": st.column_config.LinkColumn("Lamaran", display_text="Lamar ↗️")
            },
            use_container_width=True,
            hide_index=True,
            key="job_tracker_editor"
        )

        if edited_df is not None and "Sudah Dilamar" in edited_df.columns:
            st.session_state.raw_jobs.update(edited_df[["Sudah Dilamar"]])

        # DOWNLOAD CSV DENGAN STATUS TRACKER
        loc_part = settings["location"].strip().replace(" ", "_") if settings["location"] else "anywhere"
        search_part = settings["search_term"].strip().replace(" ", "_") if settings["search_term"] else "all_jobs"
        timestamp = datetime.now().strftime("%Y-%b-%d_%H%M")
        csv_filename = f"jobs_tracker_{search_part}_{loc_part}_{timestamp}.csv"

        csv_bytes = edited_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Tracker Lamaran (CSV)", data=csv_bytes, file_name=csv_filename, mime="text/csv", use_container_width=True)

        if settings["google_enabled"]:
            st.divider()
            st.subheader("🔍 Ekstra: Query Pencarian Manual Google Jobs")
            google_query = build_google_search_term(
                search_term=settings["search_term"], location=settings["location"],
                hours_old=settings["hours_old"], exclude_age=settings["exclude_age"],
                custom_exclude=settings["custom_exclude"]
            )
            st.code(google_query, language="text")
            encoded_q = urllib.parse.quote(google_query)
            st.markdown(f"[🔗 Klik di sini untuk cari langsung di Google Jobs](https://www.google.com/search?q={encoded_q}&ibp=htl;jobs)")

# ==================== TAB 2: PANDUAN PENCARIAN ====================
with tab2:
    st.title("📖 Panduan Pencarian Pekerjaan")
    st.markdown("**Teknik praktis mencari informasi pekerjaan valid dan katalog portal spesialis.**")

    with st.expander("🌐 **Mana Platform Remote yang Cocok Untukmu? (Katalog Spesialis)**", expanded=True):
        st.markdown("**1. NGO & Non-Profit Internasional:** [Katalog NGO (Wasian)](https://wasian.my.id/remoteworks/?cat=NGO+%26+International+Development)")
        st.markdown("**2. Tech & Software:** [Katalog Engineering (Wasian)](https://wasian.my.id/remoteworks/?cat=Engineering+%26+Tech)")
        st.markdown("**3. Desain & Konten Kreatif:** [Katalog Creative (Wasian)](https://wasian.my.id/remoteworks/?cat=Design+%26+Creative)")
        st.markdown("**4. Support & Operations:** [Katalog Customer Support (Wasian)](https://wasian.my.id/remoteworks/?cat=Customer+Support)")

    with st.expander("🌐 Komunitas & Alat Gratis Pendukung Karier", expanded=False):
        st.markdown("[Nafkah - Kalkulator Merantau & Biaya Hidup](https://nafkah.adenaufal.com/)")
        st.markdown("[Katalog Remote Works (Wasian)](https://wasian.my.id/remoteworks/)")
        st.markdown("[Discord: Kabur Aja Dulu](https://discord.com/invite/KaburAjaDulu)")

st.markdown("---")
st.markdown("Ditenagai oleh [damarowen/JobSpy](https://github.com/damarowen/JobSpy) & [Nafkah](https://github.com/adenaufal/nafkah).")
