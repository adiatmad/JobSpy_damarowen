"""Job-search playbook kept separate from the Streamlit search engine."""

import streamlit as st


def render_search_guide() -> None:
    st.title("📖 Panduan Pencarian")
    st.markdown(
        "**Playbook mencari kerja di jalur terbuka maupun *Hidden Job Market*, "
        "dengan fokus pada pencarian yang lebih terarah dan menghindari lowongan zombie.**"
    )

    st.subheader("Bagian 1: Direktori & Alat Bantu")
    with st.expander("🌐 Katalog Pekerjaan Spesialis (Wasian)", expanded=True):
        st.markdown(
            "- **NGO & Non-Profit:** [Katalog NGO (Wasian)](https://wasian.my.id/remoteworks/?cat=NGO+%26+International+Development)\n"
            "- **Tech & Software:** [Katalog Engineering (Wasian)](https://wasian.my.id/remoteworks/?cat=Engineering+%26+Tech)\n"
            "- **Desain & Konten Kreatif:** [Katalog Creative (Wasian)](https://wasian.my.id/remoteworks/?cat=Design+%26+Creative)\n"
            "- **Support & Operations:** [Katalog Customer Support (Wasian)](https://wasian.my.id/remoteworks/?cat=Customer+Support)"
        )

    with st.expander("🛠️ Komunitas & Kalkulator Pendukung"):
        st.markdown(
            "- [JobResume — Tool gratis bikin CV & lacak lamaran](https://jobresume.rndhri.com/)\n"
            "- [Nafkah — Kalkulator merantau & biaya hidup](https://nafkah.adenaufal.com/)\n"
            "- [Katalog Remote Works (Wasian)](https://wasian.my.id/remoteworks/)\n"
            "- [Discord — Kabur Aja Dulu](https://discord.com/invite/KaburAjaDulu)"
        )

    st.divider()
    st.subheader("Bagian 2: Menembus Hidden Job Market")
    with st.expander("🕵️ Query untuk X / Threads"):
        st.markdown(
            """
            Banyak lowongan dibagikan langsung oleh founder, recruiter, atau tech lead dan tidak selalu masuk portal pekerjaan.

            **Direct hiring**
            - `"we are hiring" OR "i'm hiring" [Nama Posisi]`
            - `"join my team" [Nama Posisi]`

            **Bypass ATS / jalur langsung**
            - `[Nama Posisi] "send your cv to" OR "kirim CV ke"`

            **Startup lokal Indonesia**
            - `"lagi cari" [Nama Posisi] (startup OR tech)`
            - `"dibutuhkan segera" [Nama Posisi] (WFH OR Remote)`

            **Kurangi spam di X**
            - Tambahkan `-loker -rt -giveaway -bot` bila hasil terlalu kotor.
            """
        )

    with st.expander("⚠️ Awas Ghost Jobs / Lowongan Zombie"):
        st.markdown(
            """
            **Ghost job** adalah lowongan yang terus muncul atau di-*repost* tetapi belum tentu mencerminkan kebutuhan hiring yang aktif.

            **Tanda yang patut dicurigai:**
            - Posisi yang sama muncul berulang kali tanpa perubahan berarti.
            - Lowongan sudah sangat lama tetapi selalu terlihat sebagai baru.
            - Deskripsi sangat generik dan tidak menjelaskan kebutuhan tim.
            - Perusahaan memiliki banyak lowongan serupa yang terus aktif.

            **Gunakan Job Memory sebagai sinyal, bukan vonis.** Jika aplikasi menandai `Seen before` atau `Possible repost`, cek tanggal, URL, perusahaan, dan deskripsi sebelum memutuskan melamar.
            """
        )

    with st.expander("🔎 Strategi pencarian yang disarankan"):
        st.markdown(
            """
            1. Mulai dengan **1–2 keyword posisi yang spesifik**, bukan daftar skill yang terlalu panjang.
            2. Cari **Indonesia** dulu jika ingin melihat peluang remote/regional, lalu persempit ke kota bila perlu.
            3. Gunakan freshness **24–72 jam** untuk mencari peluang baru.
            4. Jalankan pencarian yang sama lagi di waktu berbeda untuk memanfaatkan **Job Memory**.
            5. Prioritaskan `Strong` dan `Partial` relevance; jangan mengejar skor hanya karena lowongan terlihat baru.
            6. Baca `Why Match`, `Novelty`, dan `Financial Signal` sebelum melamar.
            7. Gunakan Nafkah sebagai **acuan biaya hidup**, bukan sebagai klaim bahwa gaji lowongan pasti cukup.
            """
        )

    with st.expander("🧭 Cara membaca hasil Teman Cari Kerja"):
        st.markdown(
            """
            - **Strong** — sebagian besar/seluruh keyword pencarian muncul di judul.
            - **Partial** — sebagian keyword muncul di judul.
            - **Weak** — keyword terutama hanya muncul di deskripsi atau bukti kecocokannya terbatas.
            - **New** — belum terlihat di Job Memory.
            - **Seen before** — URL lowongan sudah pernah terlihat.
            - **Possible repost** — fingerprint lowongan terlihat pada URL berbeda; ini sinyal untuk diperiksa, bukan kepastian.
            - **Financial Signal** — indikator konservatif berdasarkan informasi gaji yang tersedia dan konteks Nafkah.
            """
        )

    st.info("💡 **Prinsip utama:** alat ini membantu mempersempit perhatianmu. Keputusan melamar tetap perlu melihat deskripsi lengkap, perusahaan, tanggal, dan kecocokan nyata dengan pengalamanmu.")
