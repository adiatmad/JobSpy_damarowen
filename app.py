import urllib.parse
from datetime import datetime

import pandas as pd
import streamlit as st

from guide import render_search_guide
from intelligence import score_jobs
from pipeline import categorize_work_type, deduplicate_jobs, job_fingerprint, process_job_data, validate_jobs
from search_engine import search_sources
from storage import ALLOWED_STATUSES, JobStore
from utils import build_google_search_term, glassdoor_supports_country, inject_custom_css, render_dua_cards

st.set_page_config(page_title="Teman Cari Kerja", page_icon="🔎", layout="wide", initial_sidebar_state="collapsed")
inject_custom_css()

ALL_SITES = ["indeed", "linkedin", "zip_recruiter", "glassdoor"]
DEFAULT_SITES = ["indeed", "linkedin"]
store = JobStore()

if "raw_jobs" not in st.session_state:
    st.session_state.raw_jobs = pd.DataFrame()
if "search_executed" not in st.session_state:
    st.session_state.search_executed = False
if "last_sources" not in st.session_state:
    st.session_state.last_sources = []
if "last_filter_note" not in st.session_state:
    st.session_state.last_filter_note = ""


def render_search_settings():
    with st.expander("🔧 Pengaturan & Filter Pencarian", expanded=not st.session_state.search_executed):
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("Kata kunci / Posisi", value="Python Developer")
            location = st.text_input("Lokasi", value="Indonesia")
        with col2:
            country_indeed = st.text_input("Negara Indeed/Glassdoor", value="Indonesia")
            results_wanted = st.slider("Hasil per situs", 5, 50, 15, 5)
            hours_old = st.number_input("Diposting dalam (jam)", min_value=0, value=72, step=24)

        include_unknown_dates = st.checkbox(
            "Sertakan lowongan dengan tanggal posting tidak diketahui",
            value=False,
            help="Jika aktif, lowongan tanpa tanggal tetap ditampilkan meski filter usia digunakan. Ini kurang ketat untuk pencarian freshness.",
        )

        st.caption("Sumber:")
        glassdoor_ok = glassdoor_supports_country(country_indeed)
        sites = []
        cols = st.columns(4)
        for i, site in enumerate(ALL_SITES):
            with cols[i]:
                disabled = site == "glassdoor" and not glassdoor_ok
                checked = st.checkbox(site, value=site in DEFAULT_SITES, disabled=disabled, key=f"site_{site}")
                if checked and not disabled:
                    sites.append(site)

        proxy = st.text_input("Proxy opsional", placeholder="http://user:pass@host:port")
        google_enabled = st.checkbox("✨ Buat query Google Jobs manual", value=False)
        exclude_age, custom_exclude = False, ""
        if google_enabled:
            exclude_age = st.checkbox("Hilangkan kata usia", value=False)
            custom_exclude = st.text_input("Kata kunci yang dikecualikan")

        return {
            "search_term": search_term, "location": location, "country_indeed": country_indeed,
            "results_wanted": results_wanted, "hours_old": hours_old, "sites": sites,
            "proxy": proxy, "google_enabled": google_enabled, "exclude_age": exclude_age,
            "custom_exclude": custom_exclude, "include_unknown_dates": include_unknown_dates,
        }


def render_source_health():
    if not st.session_state.last_sources:
        return
    with st.expander("📡 Source health", expanded=True):
        for item in st.session_state.last_sources:
            label = f"{item['source']} · {item['status']} · {item['result_count']} hasil · {item['duration_ms']} ms · {item['attempts']} attempt"
            if item["status"] == "SUCCESS":
                st.success(label)
            elif item["status"] == "EMPTY":
                st.warning(label)
            else:
                st.error(f"{label} — {item.get('error') or 'tanpa detail'}")


st.title("🔎 Teman Cari Kerja")
st.caption("Cari lowongan, validasi bukti, bandingkan konteks finansial, dan simpan histori—bukan sekadar scraper.")

tab_search, tab_guide, tab_history = st.tabs(["🔍 Cari Pekerjaan", "📖 Panduan Pencarian", "🧠 Job Memory"])

with tab_search:
    settings = render_search_settings()
    if st.button("🔍 Cari Pekerjaan", type="primary", use_container_width=True):
        if not settings["sites"]:
            st.error("Pilih minimal satu situs pekerjaan.")
            st.stop()

        render_dua_cards()
        status_area = st.empty()
        status_area.info("⏳ Menjalankan search engine…")
        run = search_sources(
            settings["sites"], search_term=settings["search_term"], location=settings["location"],
            country_indeed=settings["country_indeed"], results_wanted=settings["results_wanted"],
            hours_old=settings["hours_old"], proxy=settings["proxy"],
        )
        status_area.empty()
        st.session_state.last_sources = run.source_health

        before_count = len(run.jobs)
        jobs = validate_jobs(run.jobs, settings["hours_old"], include_unknown_dates=settings["include_unknown_dates"])
        after_freshness = len(jobs)
        jobs = deduplicate_jobs(jobs)
        after_dedup = len(jobs)

        if not jobs.empty:
            jobs["Work Type"] = jobs.apply(categorize_work_type, axis=1)
            jobs["job_fingerprint"] = jobs.apply(job_fingerprint, axis=1)
            statuses = store.get_application_statuses(jobs["job_url"].tolist())
            jobs = score_jobs(jobs, settings["search_term"], settings["location"])
            jobs = process_job_data(jobs)
            jobs["application_status"] = jobs["job_url"].map(statuses).fillna("new")

            # Persist after scoring so the current result set is not used to alter ranking.
            store.upsert_jobs(jobs)
            store.record_search(settings["search_term"], settings["location"], jobs, run.sources)

        st.session_state.raw_jobs = jobs
        st.session_state.search_executed = not jobs.empty
        st.session_state.last_filter_note = f"{before_count} hasil mentah → {after_freshness} lolos freshness → {after_dedup} lowongan unik"
        if jobs.empty:
            st.warning("Tidak ada lowongan valid ditemukan. Lihat Source health untuk membedakan EMPTY dari BLOCKED/TIMEOUT.")

    render_source_health()

    if st.session_state.search_executed and not st.session_state.raw_jobs.empty:
        jobs = st.session_state.raw_jobs.copy()
        st.success(f"✅ {len(jobs)} lowongan unik setelah normalisasi dan deduplikasi.")
        if st.session_state.last_filter_note:
            st.caption(st.session_state.last_filter_note)
        st.info("💡 **Acuan finansial:** data UMR & estimasi biaya hidup berasal dari **Nafkah**. Gunakan sebagai pembanding, bukan angka gaji pasti.")
        st.markdown("[Buka Nafkah untuk simulasi biaya hidup ↗](https://nafkah.adenaufal.com/)")

        col1, col2, col3 = st.columns(3)
        with col1:
            filter_work = st.multiselect("Jenis kerja", ["Remote", "Hybrid", "On-site"], default=["Remote", "Hybrid", "On-site"])
        with col2:
            min_score = st.slider("Minimum Match Score", 0, 100, 30, 5)
        with col3:
            relevance_filter = st.multiselect("Relevance", ["Strong", "Partial", "Weak"], default=["Strong", "Partial"])

        jobs = jobs[jobs["Work Type"].isin(filter_work)]
        jobs = jobs[jobs["Match Score"] >= min_score]
        if relevance_filter:
            jobs = jobs[jobs["Relevance"].isin(relevance_filter)]

        display_cols = [
            "application_status", "Match Score", "Relevance", "Location Match", "Why Match", "date_posted", "title", "company",
            "Lokasi & Gaji", "Acuan Finansial", "Financial Signal", "Info UMR", "Est. Biaya Hidup", "Work Type",
            "location", "job_url",
        ]
        display_cols = [c for c in display_cols if c in jobs.columns]
        edited = st.data_editor(
            jobs[display_cols],
            column_config={
                "application_status": st.column_config.SelectboxColumn("Status", options=sorted(ALLOWED_STATUSES)),
                "Match Score": st.column_config.NumberColumn("Match", min_value=0, max_value=100, format="%d"),
                "job_url": st.column_config.LinkColumn("Lamaran", display_text="Buka ↗"),
                "Acuan Finansial": st.column_config.TextColumn("Biaya Hidup (Nafkah)"),
                "Financial Signal": st.column_config.TextColumn("Financial"),
            },
            use_container_width=True, hide_index=True, key="job_tracker_editor",
        )

        if edited is not None and "application_status" in edited.columns:
            for original_url, new_status in zip(jobs["job_url"], edited["application_status"]):
                old_status = store.get_application_statuses([original_url]).get(original_url, "new")
                if new_status != old_status:
                    store.update_application_status(original_url, new_status)
            st.session_state.raw_jobs.loc[jobs.index, "application_status"] = edited["application_status"].values

        export = process_job_data(st.session_state.raw_jobs.copy())
        export_cols = [
            "application_status", "Match Score", "Relevance", "Location Match", "Why Match", "date_posted", "title", "company",
            "location", "Work Type", "Gaji Asli", "Info UMR", "Est. Biaya Hidup", "Acuan Finansial", "Financial Signal",
            "job_url", "description",
        ]
        export = export[[c for c in export_cols if c in export.columns]]
        csv = export.to_csv(index=False).encode("utf-8-sig")
        stamp = datetime.now().strftime("%Y-%b-%d_%H%M")
        keyword = settings["search_term"].strip().replace(" ", "_") or "SemuaPosisi"
        st.download_button("📥 Download tracker CSV", csv, f"Tracker_{keyword}_{stamp}.csv", "text/csv", use_container_width=True)

        if settings["google_enabled"]:
            query = build_google_search_term(
                search_term=settings["search_term"], location=settings["location"], hours_old=settings["hours_old"],
                exclude_age=settings["exclude_age"], custom_exclude=settings["custom_exclude"],
            )
            st.code(query, language="text")
            encoded_q = urllib.parse.quote(query)
            st.markdown(f"[🔗 Buka Google Jobs](https://www.google.com/search?q={encoded_q}&ibp=htl;jobs)")

with tab_guide:
    render_search_guide()

with tab_history:
    st.subheader("🧠 Job Memory")
    history = store.load_jobs()
    if history.empty:
        st.info("Belum ada job tersimpan. Jalankan pencarian pertama.")
    else:
        metrics = st.columns(4)
        metrics[0].metric("Tersimpan", len(history))
        metrics[1].metric("Shortlisted", int((history.application_status == "shortlisted").sum()))
        metrics[2].metric("Applied", int((history.application_status == "applied").sum()))
        metrics[3].metric("Interview", int((history.application_status == "interview").sum()))
        history_cols = [
            "application_status", "seen_count", "title", "company", "location", "source",
            "first_seen_at", "last_seen_at", "job_url",
        ]
        st.dataframe(history[[c for c in history_cols if c in history.columns]], column_config={"job_url": st.column_config.LinkColumn("Link", display_text="Buka ↗")}, use_container_width=True, hide_index=True)
        st.subheader("📡 Recent source health")
        st.dataframe(store.load_source_health(), use_container_width=True, hide_index=True)
