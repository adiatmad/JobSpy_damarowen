# TABEL INTERAKTIF TRACKER (Pengecekan Kolom Aman)
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
