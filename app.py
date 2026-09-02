import urllib.parse
from datetime import datetime
import pandas as pd
import streamlit as st

from utils import (
    inject_custom_css, render_dua_cards, glassdoor_supports_country, build_google_search_term
)
from scraper import scrape_one_site
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

# --- HELPER UI: EXPANDER PENGATURAN ---
def render_search_settings():
    with st.expander("🔧 Pengaturan & Filter Pencarian", expanded=not st.session_state.get("search_clicked", False)):
        st.caption("Atur kata kunci, lokasi, dan filter kecocokan skill kamu di sini.")

        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("Kata kunci / Posisi pekerjaan", value="Python Developer", help="Kosongkan untuk pencarian umum.")
            location = st.text_input("Lokasi (opsional)", value="Indonesia", help="Contoh: Jakarta, Indonesia, atau kosongkan untuk remote.")
            target_keywords = st.text_input("Target Skill Kamu (pisahkan dengan koma)", value="Python, SQL, Docker", help="Ketik skill wajib untuk menghitung skor kecocokan.")

        with col2:
            country_indeed = st.text_input("Negara (Indeed/Glassdoor)", value="Indonesia", help="Contoh: Indonesia, USA, Singapore.")
            results_wanted = st.slider("Hasil per situs", min_value=5, max_value=100, value=20, step=5)
            hours_old = st.number_input("Diposting dalam (jam)", min_value=0, value=72, step=24, help="0 = semua umur postingan.")
            exclude_keywords = st.text_input("Kata kunci yang dihindari (pisahkan dengan koma)", value="Senior, Lead, Manager", help="Posisikan kata seperti 'Senior' untuk menyaring posisi entry-level.")

        st.caption("Pilih situs pekerjaan:")
        glassdoor_ok = glassdoor_supports_country(country_indeed)
        sites = []
        cols = st.columns(4)
        for i, site in enumerate(ALL_SITES):
            col = cols[i % 4]
            if site == "glassdoor" and not glassdoor_ok:
                col.checkbox("glassdoor 🚫", value=False, disabled=True, help=f"Tidak tersedia untuk '{country_indeed}'.", key="site_glassdoor")
            else:
                checked = col.checkbox(site, value=(site in DEFAULT_SITES), key=f"site_{site}")
                if checked:
                    sites.append(site)

        if not glassdoor_ok:
            st.caption(f"⚠️ Glassdoor dinonaktifkan — tidak mendukung negara '{country_indeed}'.")
        st.caption("⚠️ Note: Zip_recruiter utamanya mencakup wilayah US/Canada.")

        st.markdown("---")
        google_enabled = st.checkbox("✨ Buatkan juga saran pencarian Google Jobs manual", value=False)
        exclude_age = False
        custom_exclude = ""
        if google_enabled:
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                exclude_age = st.checkbox("Hilangkan kata usia (-usia -age -umur)", value=False)
            with col_g2:
                custom_exclude = st.text_input("Kecualikan kata kunci Google kustom", value="", placeholder="fresh graduate entry level")

        return {
            "search_term": search_term,
            "location": location,
            "country_indeed": country_indeed,
            "results_wanted": results_wanted,
            "hours_old": hours_old,
            "sites": sites,
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
    2. Masukkan posisi yang dicari (misal: `Data Analyst`) dan lokasi (`Indonesia`).
    3. Masukkan **Target Skill** kamu (misal: `Python, SQL`). Aplikasi akan menghitung persen kecocokan (Match Score).
    4. Klik tombol **🔍 Cari Pekerjaan**.
    5. **Fitur Otomatis:**
       - 🧹 **Anti-Duplikat:** Posisi sama dari platform berbeda otomatis digabung.
       - ⚡ **Quick Apply (ATS):** Menandai portal lamaran langsung seperti Greenhouse/Lever agar kamu melamar lebih cepat.
    6. **Tab Panduan Pencarian:** Buka tab kedua di atas jika kamu ingin belajar teknik Google Dorking untuk menemukan lowongan tersembunyi.
    """)

# --- TABS UTAMA ---
tab1, tab2 = st.tabs(["🔍 Cari Pekerjaan", "📖 Panduan Pencarian"])

# ==================== TAB 1: CARI PEKERJAAN ====================
with tab1:
    settings = render_search_settings()

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        search_clicked = st.button("🔍 Cari Pekerjaan", type="primary", use_container_width=True)

    if search_clicked:
        st.session_state["search_clicked"] = True
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

        render_dua_cards()
        status_area = st.empty()
        all_dfs = []
        site_status = {}

        for site in sites:
            status_area.info(f"⏳ Sedang mencari di **{site}**...")
            df, err = scrape_one_site(site, **common_inputs)
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
        else:
            combined_jobs = pd.concat(all_dfs, ignore_index=True)
            raw_count = len(combined_jobs)
            
            # PIPELINE PROSES DATA
            valid_jobs = validate_jobs(combined_jobs, settings["hours_old"])
            clean_jobs = deduplicate_jobs(valid_jobs)
            
            clean_jobs["Form Type"] = clean_jobs["job_url"].apply(detect_ats_friendly)
            clean_jobs["Work Type"] = clean_jobs.apply(categorize_work_type, axis=1)
            final_jobs = calculate_match_score(clean_jobs, settings["target_keywords"], settings["exclude_keywords"])

            filtered_count = raw_count - len(final_jobs)
            st.success(f"✅ Menemukan **{len(final_jobs)}** lowongan unik & valid (Telah menyaring {filtered_count} duplikat / tidak valid).")

            # FILTER UI INTERAKTIF
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_work = st.multiselect("Filter Jenis Kerja", options=["🌐 Remote", "🏢 Hybrid", "📍 On-site"], default=["🌐 Remote", "🏢 Hybrid", "📍 On-site"])
            with col_f2:
                filter_ats_only = st.checkbox("Hanya tampilkan ⚡ Quick Apply (ATS)", value=False)

            if filter_work:
                final_jobs = final_jobs[final_jobs["Work Type"].isin(filter_work)]
            if filter_ats_only:
                final_jobs = final_jobs[final_jobs["Form Type"] == "⚡ Quick Apply (ATS)"]

            # TAMPILAN TABEL
            display_cols = ["Match Score", "title", "company", "location", "Work Type", "Form Type", "Matched Skills", "site", "job_url"]
            existing_cols = [c for c in display_cols if c in final_jobs.columns]

            st.dataframe(
                final_jobs[existing_cols],
                column_config={
                    "Match Score": st.column_config.ProgressColumn("Tingkat Cocok", help="Kecocokan dengan target skill", format="%d%%", min_value=0, max_value=100),
                    "title": "Judul Posisi",
                    "company": "Perusahaan",
                    "location": "Lokasi",
                    "Work Type": "Sistem Kerja",
                    "Form Type": "Format Lamaran",
                    "Matched Skills": "Skill Cocok",
                    "site": "Sumber",
                    "job_url": st.column_config.LinkColumn("Link Lamaran", display_text="Lamar ↗️")
                },
                use_container_width=True,
                hide_index=True
            )

            # DOWNLOAD CSV
            loc_part = settings["location"].strip().replace(" ", "_") if settings["location"] else "anywhere"
            search_part = settings["search_term"].strip().replace(" ", "_") if settings["search_term"] else "all_jobs"
            timestamp = datetime.now().strftime("%Y-%b-%d_%H%M")
            csv_filename = f"jobs_{search_part}_{loc_part}_{timestamp}.csv"

            csv_bytes = final_jobs.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Hasil (CSV)", data=csv_bytes, file_name=csv_filename, mime="text/csv", use_container_width=True)

            # GOOGLE JOBS QUERY MANUAL
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

    with st.expander("🤖 AI Helper – Buat kata kunci dengan ChatGPT / DeepSeek"):
        st.markdown("Salin prompt ini dan tempelkan ke ChatGPT, DeepSeek, atau Meta AI.")
        prompt = """Buatkan kata kunci untuk mencari informasi pekerjaan bidang [your field] di [your location] lewat Google Search dengan teknik Google Dorking.

Contoh output:
- site:indeed.co.id "GIS" "Indonesia" "job"
- inurl:career "GIS" "Indonesia" "vacancy"
- filetype:pdf "Lowongan Kerja GIS" "Indonesia"

Buatkan 5–10 variasi dengan operator yang berbeda."""
        st.code(prompt, language="text")

    with st.expander("🌐 Komunitas & Alat Gratis"):
        st.markdown("[Discord: Kabur Aja Dulu](https://discord.com/invite/KaburAjaDulu)")
        st.markdown("[Alat CV & Tracking Lamaran Gratis](https://jobresume.rndhri.com/)")
        st.markdown("[WEF Future of Jobs Report 2025](https://www.weforum.org/publications/the-future-of-jobs-report-2025/)")

st.markdown("---")
st.markdown("Ditenagai oleh [damarowen/JobSpy](https://github.com/damarowen/JobSpy) — dibuat untuk pencari kerja yang tidak menyerah.")