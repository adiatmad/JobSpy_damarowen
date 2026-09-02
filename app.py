import streamlit as st
import pandas as pd
from scraper import fetch_jobs_safe
from pipeline import detect_ats_friendly, categorize_work_type, deduplicate_jobs, calculate_match_score

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title="Pencari Kerja Pintar (JobSpy Engine)",
    page_icon="💼",
    layout="wide"
)

# --- HEADER & PETUNJUK PENGGUNA ---
st.title("💼 Pencari Kerja Pintar (Job Intelligence Engine)")
st.caption("Alat pencari lowongan kerja cerdas yang membuang data duplikat, mendeteksi lamaran cepat, dan mengukur tingkat kecocokan skill kamu.")

with st.expander("❓ **Petunjuk Penggunaan Lengkap (Baca Ini Dulu Untuk Pemula)**", expanded=False):
    st.markdown("""
    Selamat datang! Aplikasi ini dirancang agar kamu tidak membuang waktu melamar pekerjaan yang salah. Berikut cara mudah menggunakannya:

    1. **Atur Parameter di Panel Kiri:**
       - **Ketik Posisi & Lokasi:** Contoh: `Data Analyst` di `Jakarta` atau `Remote`.
       - **Target Skill:** Masukkan skill spesifik pisahkan dengan koma (contoh: `Python, SQL, Tableau`). Aplikasi akan menghitung seberapa cocok lowongan tersebut dengan skill-mu.
       - **Kata Kunci Hindari:** Ketik kata yang ingin kamu lewati (contoh: `Senior, Manager, Lead`) jika kamu mencari posisi *entry-level*.
    2. **Klik 'Cari Lowongan Kerja':** Tunggu proses penarikan data selesai.
    3. **Cara Membaca Hasil:**
       - ⚡ **Quick Apply (ATS):** Form lamaran langsung dari sistem perusahaan (Greenhouse/Lever), melamar bisa 5x lebih cepat!
       - 🎯 **Match Score:** Nilai 0-100% seberapa cocok lowongan tersebut dengan target skill yang kamu ketik.
       - 🧹 **Anti-Duplikat:** Otomatis aktif! Jika posisi yang sama ada di LinkedIn dan Indeed, sistem hanya menampilkan 1 baris terbaik.
    4. **Gunakan Filter & Download:** Kamu bisa memfilter sistem kerja (Remote/On-site) dan mengunduh hasilnya ke file CSV.
    """)

st.divider()

# --- SIDEBAR: PARAMETER PENCARIAN ---
st.sidebar.header("🔍 Parameter Pencarian")

search_term = st.sidebar.text_input("Posisi / Judul Pekerjaan", value="Python Developer", help="Contoh: Software Engineer, Data Analyst, Admin")
location = st.sidebar.text_input("Lokasi", value="Indonesia", help="Contoh: Jakarta, Indonesia, atau biarkan Remote")
results_wanted = st.sidebar.slider("Jumlah Lowongan per Platform", min_value=10, max_value=100, value=30, step=10)
hours_old = st.sidebar.selectbox("Kesegaran Lowongan", options=[24, 72, 168, 720], index=2, 
                                 format_func=lambda x: f"Maksimal {x//24} Hari Lalu" if x >= 24 else f"{x} Jam Lalu")

site_names = st.sidebar.multiselect("Pilih Job Board", options=["linkedin", "indeed", "glassdoor", "zip_recruiter"], 
                                    default=["linkedin", "indeed", "glassdoor"])

st.sidebar.divider()
st.sidebar.header("🎯 Filter & Kecocokan Skill")
target_keywords = st.sidebar.text_area("Target Skill Kamu (Pisahkan dengan koma)", value="Python, Docker, SQL", help="Ketik skill wajib yang kamu kuasai")
exclude_keywords = st.sidebar.text_input("Kata yang Dihindari (Pisahkan dengan koma)", value="Senior, Lead, Manager", help="Sangat berguna untuk menyaring level yang belum sesuai")

# --- MEMORI SIMPAN (SESSION STATE) ---
if "raw_jobs" not in st.session_state:
    st.session_state.raw_jobs = pd.DataFrame()

# --- TOMBOL EKSEKUSI ---
if st.sidebar.button("🚀 Cari Lowongan Kerja", use_container_width=True, type="primary"):
    if not site_names:
        st.error("⚠️ Pilih minimal satu Job Board di sebelah kiri!")
    elif not search_term:
        st.error("⚠️ Masukkan judul pekerjaan yang ingin dicari!")
    else:
        with st.spinner("Sedang mengambil data terbaru dan membersihkan duplikat..."):
            df_fetched, errors = fetch_jobs_safe(site_names, search_term, location, results_wanted, hours_old)
            
            if errors:
                for err in errors:
                    st.toast(f"Peringatan: {err}", icon="⚠️")
            
            if not df_fetched.empty:
                # Pembersihan awal: Jenis kerja & ATS Check
                df_fetched["Form Type"] = df_fetched["job_url"].apply(detect_ats_friendly)
                df_fetched["Work Type"] = df_fetched.apply(categorize_work_type, axis=1)
                
                # Proses Deduplikasi Fuzzy
                df_clean = deduplicate_jobs(df_fetched)
                st.session_state.raw_jobs = df_clean
                st.success(f"Berhasil menemukan {len(df_clean)} lowongan unik! (Duplikat telah dibuang)")
            else:
                st.session_state.raw_jobs = pd.DataFrame()
                st.warning("Tidak ada lowongan ditemukan dengan kriteria tersebut. Coba perluas lokasi atau kurangi kata kunci.")

# --- TAMPILAN HASIL UTAMA ---
if not st.session_state.raw_jobs.empty:
    df_processed = st.session_state.raw_jobs.copy()

    # Hitung Skor Kata Kunci
    df_processed = calculate_match_score(df_processed, target_keywords, exclude_keywords)

    # --- FILTER INTERAKTIF DI ATAS TABEL ---
    col1, col2 = st.columns(2)
    with col1:
        filter_work_type = st.multiselect("Filter Jenis Kerja", options=["🌐 Remote", "🏢 Hybrid", "📍 On-site"], 
                                          default=["🌐 Remote", "🏢 Hybrid", "📍 On-site"])
    with col2:
        filter_ats = st.checkbox("Hanya Tampilkan ⚡ Quick Apply (ATS)", value=False)

    # Terapkan Filter Tambahan UI
    if filter_work_type:
        df_processed = df_processed[df_processed["Work Type"].isin(filter_work_type)]
    if filter_ats:
        df_processed = df_processed[df_processed["Form Type"] == "⚡ Quick Apply (ATS)"]

    st.subheader(f"📊 Menampilkan {len(df_processed)} Lowongan Terpilih")

    # Format Tampilan Tabel Streamlit
    display_columns = ["Match Score", "title", "company", "location", "Work Type", "Form Type", "Matched Skills", "site", "job_url"]
    
    # Pastikan kolom tersedia
    final_cols = [col for col in display_columns if col in df_processed.columns]

    st.dataframe(
        df_processed[final_cols],
        column_config={
            "Match Score": st.column_config.ProgressColumn(
                "Tingkat Cocok", help="Persentase kesesuaian dengan target skill kamu", format="%d%%", min_value=0, max_value=100
            ),
            "title": "Judul Posisi",
            "company": "Perusahaan",
            "location": "Lokasi",
            "Work Type": "Sistem Kerja",
            "Form Type": "Format Lamaran",
            "Matched Skills": "Skill Yang Ditemukan",
            "site": "Sumber",
            "job_url": st.column_config.LinkColumn("Link Lamaran", display_text="Lamar Sekarang ↗️")
        },
        use_container_width=True,
        hide_index=True
    )

    # --- EKSPOR DATA CSV ---
    st.divider()
    csv_data = df_processed.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Hasil Pencarian (CSV)",
        data=csv_data,
        file_name=f"job_results_{search_term.replace(' ', '_')}.csv",
        mime="text/csv",
        use_container_width=False
    )
else:
    st.info("👈 Gunakan menu di sebelah kiri dan klik **'Cari Lowongan Kerja'** untuk memulai pencarian.")