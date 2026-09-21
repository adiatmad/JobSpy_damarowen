"""Job-search playbook kept separate from the Streamlit search engine."""

import streamlit as st


def render_search_guide() -> None:
    st.title("📖 Panduan Pencarian")
    st.markdown(
        "**Playbook mencari kerja di jalur terbuka maupun *Hidden Job Market*, "
        "dengan fokus pada bukti lowongan, kualitas sumber, dan pencarian yang lebih terarah.**"
    )

    st.subheader("Bagian 1: Direktori & Alat Bantu")
    with st.expander("🌐 Katalog Pekerjaan Spesialis (Wasian)", expanded=True):
        st.markdown(
            "- **NGO & Non-Profit:** [Katalog NGO (Wasian)](https://wasian.my.id/remoteworks/?cat=NGO+%26+International+Development)\n"
            "- **Tech & Software:** [Katalog Engineering (Wasian)](https://wasian.my.id/remoteworks/?cat=Engineering+%26+Tech)\n"
            "- **Desain & Konten Kreatif:** [Katalog Creative (Wasian)](https://wasian.my.id/remoteworks/?cat=Design+%26+Creative)\n"
            "- **Support & Operations:** [Katalog Customer Support (Wasian)](https://wasian.my.id/remoteworks/?cat=Customer+Support)"
        )

    with st.expander("🌍 Katalog remote-work untuk eksplorasi sumber"):
        st.markdown(
            "- [Awesome Remote Job](https://github.com/lukasz-madon/awesome-remote-job) — katalog kurasi job board, aggregator, dan sumber remote work.\n"
            "- Perlakukan katalog ini sebagai **peta sumber**, bukan feed lowongan JobSpy. Jangan menganggap semua entri aktif, valid, atau relevan untuk lokasi/keyword pencarian.\n"
            "- Jika sebuah sumber ingin diintegrasikan ke pipeline, verifikasi URL, akses, freshness, cakupan, dan kualitas datanya terlebih dahulu."
        )

    with st.expander("🧩 Direktori API untuk eksplorasi sumber baru"):
        st.markdown(
            "- [Public APIs — Jobs](https://github.com/public-apis/public-apis#jobs) — gunakan sebagai **katalog kandidat**, bukan sebagai sumber lowongan langsung.\n"
            "- Kandidat API yang ditemukan dari katalog harus diverifikasi dulu: dokumentasi aktif, HTTPS, akses yang benar-benar tersedia, cakupan geografis, freshness, dan kualitas data.\n"
            "- **Jangan menambahkan dependency atau API key hanya karena tercantum di katalog.** Integrasikan sumber hanya jika ada bukti bahwa sumber tersebut meningkatkan coverage atau reliability aplikasi."
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
    with st.expander("🔎 Web discovery dengan SearXNG"):
        st.markdown(
            """
            Jika `SEARXNG_URL` dikonfigurasi, JobSpy menambahkan SearXNG sebagai **discovery layer** di samping source adapter utama.

            Query discovery diarahkan ke halaman karier dengan pola seperti:
            - `"Nama Posisi" "Lokasi"`
            - `inurl:careers` / `inurl:jobs`
            - `intitle:"we're hiring"` / `intitle:"join our team"`
            - Untuk pencarian remote, istilah `remote`, `work from home`, dan `distributed` ikut digunakan.

            **Batas penting:** hasil SearXNG adalah kandidat untuk diperiksa, bukan otomatis lowongan terverifikasi. Tanggal tidak diketahui tetap tunduk pada aturan freshness JobSpy.
            """
        )

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

            **Gunakan Job Memory sebagai sinyal, bukan vonis.** Periksa tanggal, URL, perusahaan, dan deskripsi sebelum memutuskan melamar.
            """
        )

    with st.expander("🔎 Strategi pencarian yang disarankan"):
        st.markdown(
            """
            1. Mulai dengan **1–2 keyword posisi yang spesifik**, bukan daftar skill yang terlalu panjang.
            2. Cari **Indonesia** dulu jika ingin melihat peluang remote/regional, lalu persempit ke kota bila perlu.
            3. Gunakan freshness **24–72 jam** untuk mencari peluang baru.
            4. Jalankan pencarian yang sama lagi di waktu berbeda untuk memanfaatkan **Job Memory**.
            5. Gunakan `Match Score`, `Relevance`, `Location Match`, dan `Why Match` sebagai bukti bantu—bukan pengganti membaca lowongan.
            6. Periksa **Financial Signal** dan Nafkah sebagai konteks biaya hidup, bukan sebagai klaim bahwa gaji lowongan pasti cukup.
            7. Jika sumber bermasalah, lihat **Source health** untuk membedakan `EMPTY`, `BLOCKED`, `RATE_LIMITED`, `TIMEOUT`, dan error lainnya.
            """
        )

    with st.expander("🧭 Cara membaca hasil Teman Cari Kerja"):
        st.markdown(
            """
            - **Strong** — sebagian besar/seluruh keyword pencarian muncul di judul.
            - **Partial** — sebagian keyword muncul di judul.
            - **Weak** — keyword terutama hanya muncul di deskripsi atau bukti kecocokannya terbatas.
            - **Location Match** — apakah lokasi hasil memiliki kecocokan dengan lokasi yang diminta.
            - **Financial Signal** — indikator konservatif berdasarkan informasi gaji yang tersedia dan konteks Nafkah.
            - **Source health** — observabilitas per sumber agar hasil kosong tidak otomatis dianggap sebagai tidak ada lowongan.
            - **Job Memory** — histori lowongan dan status lamaran yang disimpan lokal untuk membantu pelacakan.
            """
        )

    st.info("💡 **Prinsip utama:** alat ini membantu menemukan dan memeriksa informasi lowongan. Validasi akhir tetap perlu melihat deskripsi lengkap, perusahaan, tanggal, sumber, dan link asli.")
