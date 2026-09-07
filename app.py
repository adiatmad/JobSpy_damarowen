import urllib.parse
from datetime import datetime
import pandas as pd
import streamlit as st

from utils import (
    inject_custom_css, render_dua_cards, glassdoor_supports_country, build_google_search_term
)
from scraper import scrape_one_site_cached
from pipeline import (
    validate_jobs, deduplicate_jobs, categorize_work_type, process_job_data
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
        st.caption("Atur kata kunci dan lokasi pekerjaan yang ingin kamu cari.")

        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("Kata kunci / Posisi pekerjaan", value="Python Developer")
            location = st.text_input("Lokasi (opsional)", value="Indonesia")

        with col2:
            country_indeed = st.text_input("Negara (Indeed/Glassdoor)", value="Indonesia")
            results_wanted = st.slider("Hasil per situs", min_value=5, max_value=50, value=15, step=5)
            hours_old = st.number_input("Diposting dalam (jam)", min_value=0, value=72, step=24)

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
        google_enabled = st.checkbox("✨ Buatkan saran pencarian Google Jobs manual", value=False)
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
            "google_enabled": google_enabled,
            "exclude_age": exclude_age,
            "custom_exclude": custom_exclude,
        }

# --- HEADER APLIKASI ---
st.title("🔎 Teman Cari Kerja")
st.caption("Alat bantu pencari kerja sederhana untuk mengumpulkan lowongan valid dari berbagai portal secara cepat.")

with st.expander("❓ **Petunjuk Penggunaan**", expanded=False):
    st.markdown("""
    **Panduan Singkat:**
    1. Buka **🔧 Pengaturan & Filter Pencarian**.
    2. Masukkan posisi yang dicari dan lokasi.
    3. Klik **🔍 Cari Pekerjaan**.
    4. Centang lowongan yang sudah dilamar, lalu **Download CSV** untuk menyimpannya sebagai catatan pribadi (termasuk full deskripsi pekerjaan).
    """)

tab1, tab2 = st.tabs(["🔍 Cari Pekerjaan", "📖 Panduan & Taktik Gerilya"])

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

        with st.expander("📊 Status Hasil Pencarian", expanded=True):
            for site in sites:
                kind, info = site_status[site]
                if kind == "ok":
                    st.success(f"✅ **{site}**: {info} lowongan ditemukan")
                elif kind == "empty":
                    st.warning(f"⚠️ **{site}**: tidak ada lowongan")
                else:
                    st.error(f"❌ **{site}**: kendala — {info}")

        if not all_dfs:
            st.warning("Tidak ada lowongan ditemukan. Coba perluas lokasi atau buka tab Panduan & Taktik Gerilya.")
            st.session_state.raw_jobs = pd.DataFrame()
            st.session_state.search_executed = False
        else:
            combined_jobs = pd.concat(all_dfs, ignore_index=True)
            valid_jobs = validate_jobs(combined_jobs, settings["hours_old"])
            clean_jobs = deduplicate_jobs(valid_jobs)
            
            clean_jobs["Work Type"] = clean_jobs.apply(categorize_work_type, axis=1)
            clean_jobs["Sudah Dilamar"] = False
            
            st.session_state.raw_jobs = clean_jobs
            st.session_state.search_executed = True

    # --- TAMPILAN HASIL ---
    if st.session_state.search_executed and not st.session_state.raw_jobs.empty:
        jobs_to_display = process_job_data(st.session_state.raw_jobs.copy())

        st.info("💡 **Tips Merantau:** Cek simulasi biaya hidup lengkap di **[Nafkah.adenaufal.com](https://nafkah.adenaufal.com/)**.")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_work = st.multiselect("Filter Jenis Kerja", options=["Remote", "Hybrid", "On-site"], default=["Remote", "Hybrid", "On-site"])

        if filter_work and "Work Type" in jobs_to_display.columns:
            jobs_to_display = jobs_to_display[jobs_to_display["Work Type"].isin(filter_work)]

        st.success(f"✅ Menampilkan **{len(jobs_to_display)}** lowongan unik.")

        # TAMPILAN UI
        ui_cols = ["Sudah Dilamar", "date_posted", "title", "company", "Lokasi & Gaji", "Acuan Finansial", "job_url"]
        display_cols = [c for c in ui_cols if c in jobs_to_display.columns]

        edited_df = st.data_editor(
            jobs_to_display[display_cols],
            column_config={
                "Sudah Dilamar": st.column_config.CheckboxColumn("Status", help="Centang jika sudah dilamar", default=False),
                "date_posted": "Tgl Posting",
                "title": "Posisi",
                "company": "Perusahaan",
                "Lokasi & Gaji": "Detail Lokasi & Gaji",
                "Acuan Finansial": "Biaya Hidup (Nafkah)",
                "job_url": st.column_config.LinkColumn("Tindakan", display_text="Lamar ↗")
            },
            use_container_width=True,
            hide_index=True,
            key="job_tracker_editor"
        )

        if edited_df is not None and "Sudah Dilamar" in edited_df.columns:
            st.session_state.raw_jobs.update(edited_df[["Sudah Dilamar"]])
            jobs_to_display.update(edited_df[["Sudah Dilamar"]])

        # --- LOGIKA EKSPOR CSV BERSIH ---
        export_raw_cols = [
            "Sudah Dilamar", "date_posted", "title", "company", "location", 
            "Work Type", "Gaji Asli", "Info UMR", "Est. Biaya Hidup", 
            "job_url", "description"
        ]
        
        valid_export_cols = [c for c in export_raw_cols if c in jobs_to_display.columns]
        export_df = jobs_to_display[valid_export_cols].copy()

        rename_map = {
            "date_posted": "Tanggal Posting",
            "title": "Posisi",
            "company": "Perusahaan",
            "location": "Lokasi",
            "Work Type": "Sistem Kerja",
            "job_url": "Link Lamaran",
            "description": "Deskripsi Lengkap"
        }
        export_df.rename(columns=rename_map, inplace=True)

        keyword_str = settings["search_term"].strip().replace(" ", "_") if settings["search_term"] else "SemuaPosisi"
        loc_str = settings["location"].strip().replace(" ", "_") if settings["location"] else "SemuaLokasi"
        hours_str = f"{settings['hours_old']}jam" if settings['hours_old'] > 0 else "semuawaktu"
        limit_str = f"{settings['results_wanted']}limit"
        timestamp_str = datetime.now().strftime("%Y-%b-%d_%H%M")
        
        csv_filename = f"Tracker_{keyword_str}_{loc_str}_{hours_str}_{limit_str}_{timestamp_str}.csv"

        csv_bytes = export_df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 Download Data Tracker (CSV Full)", data=csv_bytes, file_name=csv_filename, mime="text/csv", use_container_width=True)

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
            st.markdown(f"[🔗 Cari langsung di Google Jobs](https://www.google.com/search?q={encoded_q}&ibp=htl;jobs)")


# ==================== TAB 2: PANDUAN PENCARIAN & TAKTIK ====================
with tab2:
    st.title("📖 Playbook & Taktik Gerilya")
    st.markdown("**Gabungan sumber daya dan teknik mencari kerja di jalur tersembunyi (*Hidden Job Market*) dan Google Dorking.**")

    st.subheader("Bagian 1: Direktori & Alat Bantu")
    with st.expander("🌐 **Katalog Pekerjaan Spesialis (Wasian)**", expanded=True):
        st.markdown("- **NGO & Non-Profit:** [Katalog NGO (Wasian)](https://wasian.my.id/remoteworks/?cat=NGO+%26+International+Development)")
        st.markdown("- **Tech & Software:** [Katalog Engineering (Wasian)](https://wasian.my.id/remoteworks/?cat=Engineering+%26+Tech)")
        st.markdown("- **Desain & Konten Kreatif:** [Katalog Creative (Wasian)](https://wasian.my.id/remoteworks/?cat=Design+%26+Creative)")
        st.markdown("- **Support & Operations:** [Katalog Customer Support (Wasian)](https://wasian.my.id/remoteworks/?cat=Customer+Support)")

    with st.expander("🛠️ **Komunitas & Kalkulator Pendukung**", expanded=False):
        st.markdown("- [JobResume - Tool Gratis Bikin CV & Lacak Lamaran](https://jobresume.rndhri.com/)")
        st.markdown("- [Nafkah - Kalkulator Merantau & Biaya Hidup](https://nafkah.adenaufal.com/)")
        st.markdown("- [Katalog Remote Works (Wasian)](https://wasian.my.id/remoteworks/)")
        st.markdown("- [Discord: Kabur Aja Dulu](https://discord.com/invite/KaburAjaDulu)")

    st.markdown("---")
    
    st.subheader("Bagian 2: Menembus *Hidden Job Market*")
    with st.expander("🕵️ **Query Sakti untuk X (Twitter) & Threads**", expanded=False):
        st.markdown("""
        Banyak lowongan bagus yang hanya diposting oleh Founder/Tech Lead di sosial media (tidak pernah masuk LinkedIn). 
        Gunakan teks ini di kolom pencarian **X (Twitter)** atau **Threads**:
        
        *   **Bidikan "Direct Hiring" (Jalur Langsung):**
            *   `"we are hiring" OR "i'm hiring" [Nama Posisi]`
            *   `"join my team" [Nama Posisi]`
        *   **Bidikan Lempar CV (Bypass ATS):**
            *   `[Nama Posisi] "send your cv to" OR "kirim CV ke"`
        *   **Bidikan Startup Lokal Indonesia:**
            *   `"lagi cari" [Nama Posisi] (startup OR tech)`
            *   `"dibutuhkan segera" [Nama Posisi] (WFH OR Remote)`
        *   **Filter Negatif (Penting untuk X/Twitter agar bebas spam):**
            *   Tambahkan `-loker -rt -giveaway -bot` di akhir pencarian agar bersih dari akun *bot*.
        """)

    with st.expander("⚠️ **Awas Jebakan 'Ghost Jobs' (Lowongan Zombie)**", expanded=False):
        st.markdown("""
        **Apa itu Ghost Jobs?**
        Lowongan yang terus-menerus muncul sebagai "Baru" atau di-*repost* setiap beberapa minggu, tetapi perusahaan sebenarnya tidak sedang merekrut siapa-siapa (hanya untuk *branding* atau mengumpulkan CV).
        
        **Cara Menghindarinya:**
        Jika kamu mengunduh Tracker CSV dari aplikasi ini dan menyadari ada satu posisi dari perusahaan yang sama terus muncul bulan demi bulan, **berhenti melamarnya**. Jangan buang waktumu.
        """)
        
    with st.expander("🎯 **Mitos Tombol 'Easy Apply' & Strategi Cold Email**", expanded=False):
        st.markdown("""
        **Fakta Pahit:** Mengklik "Easy Apply" di LinkedIn berarti CV kamu akan ditumpuk bersama 1.000 pelamar lain. Persentase dibaca HRD sangat kecil.
        
        **Taktik Gerilya (Cold Outreach):**
        1. Temukan lowongan yang cocok menggunakan alat ini.
        2. Jangan langsung klik *Apply*. Buka halaman perusahaan di LinkedIn.
        3. Cari menu **People/Orang**, ketikkan "HR", "Talent Acquisition", atau "[Nama Departemen] Manager".
        4. Kirim *Direct Message* (DM) yang sopan dan langsung ke intinya (lampirkan portfolio). 
        5. *Bypass the system.* Jadilah pelamar yang proaktif.
        """)

    st.markdown("---")
    
    st.subheader("Bagian 3: Senjata Rahasia Google Dorking")
    with st.expander("🔍 **Trik Mencari Lowongan via Google Search (Bypass Portal)**", expanded=False):
        st.markdown("""
        Gunakan teknik **Google Dorking** ini di kolom pencarian `google.com` untuk menemukan info lowongan yang spesifik:

        **1. Membidik Situs Pemerintah & Universitas:**
        `site:go.id OR site:ac.id "lowongan kerja" OR "rekrutmen" OR "karir"`
        
        **2. Mencari di Kota Spesifik Tanpa Sampah Agregator (misal: Hindari Jobstreet):**
        `("recruitment" OR "rekrutmen" OR "lowongan" OR "pekerjaan") AND ("Surabaya" OR "Gresik") (site:*.co.id OR site:*.com) -jobstreet`
        
        **3. Tembus Langsung ke Sistem ATS (BambooHR, Greenhouse, Lever, Workable):**
        `inurl:bamboohr.com "jobs/view" "remote" after:2026-05-01`
        *(Kamu bisa mengganti bamboohr.com dengan `greenhouse.io`, `jobs.lever.co`, atau `careers.workable.com`)*
        
        **4. Filter Waktu Lowongan (Hanya yang Baru Diposting):**
        Tambahkan parameter `after:YYYY-MM-DD` di akhir pencarianmu (contoh: `after:2026-09-01`).
        
        **5. Trik Filter 24 Jam di LinkedIn URL:**
        Saat mencari kerja di browser, kamu bisa tambahkan `&f_TPR=r86400` di akhir URL halaman pencarian LinkedIn. (86400 detik = 24 jam terakhir).
        """)

    st.markdown("---")
    
    st.subheader("Bagian 4: Evaluasi Lowongan Pakai AI")
    with st.expander("🤖 **Prompt 'Career Advisor' (Copy-Paste ke ChatGPT/Claude)**", expanded=False):
        st.markdown("Gunakan prompt kritis ini untuk membantu menganalisis apakah suatu lowongan layak dilamar atau justru *red flag*:")
        st.code("""Bertindaklah sebagai career advisor yang kritis, objektif, dan evidence-based.
Tujuanmu adalah membantuku mengambil keputusan nyata: apakah lowongan ini layak dikejar, layak dikejar dengan syarat, atau sebaiknya dihindari.

Langkah 1 - Klarifikasi Konteks
Ajukan pertanyaan terstruktur untuk mengumpulkan:
- Detail lowongan (tanggung jawab, scope, ekspektasi hasil, tech stack, senioritas, kompensasi jika ada)
- Profilku (pengalaman, skill, kekuatan, kelemahan, tujuan karier 1-3 tahun, batasan pribadi seperti gaji minimum, jam kerja, lokasi, dan risk tolerance)

Langkah 2 - Diagnosis Posisi
Susun daftar pertanyaan spesifik untuk menilai:
- Kesesuaian skill teknis & non-teknis
- Senioritas aktual vs klaim iklan
- Beban kerja & metrik performa nyata
- Risiko tersembunyi (ambiguity, underpaid, overworked, churn tinggi, struktur tim buruk)
- Upside potensial (learning acceleration, exposure, reputasi, jalur promosi)

Langkah 3 - Analisis Dua Arah
Identifikasi gap di pihakku
Identifikasi kemungkinan masalah di pihak lowongan
Pisahkan mana yang bisa diperbaiki dengan upskilling dan mana yang bersifat struktural.

Langkah 4 - Rekomendasi Konkret
Berikan keputusan: Go / Conditional Go / No-Go
Jelaskan alasan utama
Jika ada gap di pihakku: jelaskan secara blak-blakan dan beri rencana peningkatan dengan prioritas
Jika ada red flag struktural: jelaskan risiko jangka pendek & panjang
Gunakan bahasa lugas, tidak normatif, tidak basa-basi.
Tandai asumsi yang kamu buat dan tingkat keyakinanmu pada tiap kesimpulan.""", language="text")

st.markdown("---")
st.markdown("Ditenagai oleh [damarowen/JobSpy](https://github.com/damarowen/JobSpy) & [Nafkah](https://github.com/adenaufal/nafkah).")
