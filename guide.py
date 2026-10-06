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
    with st.expander("🔎 Cari halaman karier langsung lewat Google", expanded=True):
        st.markdown(
            """
            Tidak perlu memahami SearXNG atau tool teknis lain untuk memakai fitur ini.

            Teman Cari Kerja bisa membuat **satu query Google tambahan** untuk mencari halaman karier perusahaan yang mungkin tidak muncul di portal pekerjaan.

            Polanya otomatis mencari:
            - posisi yang kamu masukkan
            - lokasi yang kamu masukkan
            - halaman **careers / jobs / join-us**
            - frasa hiring seperti **we're hiring / join our team**
            - opsional: **remote / work from home / distributed**

            Hasil Google ini adalah **petunjuk untuk diperiksa**, bukan jaminan bahwa lowongannya masih aktif. Buka halaman aslinya dan cek tanggal, deskripsi, perusahaan, dan cara melamar.
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

    with st.expander("🎯 Dari lowongan ke riset yang bernilai"):
        st.markdown(
            """
            Jangan berhenti pada **"lowongan ini kelihatan cocok"**. Untuk lowongan yang benar-benar ingin kamu pertimbangkan, gunakan Research Pack di hasil pencarian.

            **Alur evidence-first:**
            1. **Verifikasi listing** — buka URL asli, cek tanggal, perusahaan, deskripsi, dan jalur lamaran.
            2. **Kumpulkan bukti perusahaan** — cari halaman karier resmi, produk, pelanggan, berita, dan kebutuhan tim yang dapat diverifikasi.
            3. **Cari masalah konkret** — pertanyaan yang berguna adalah "kebutuhan bisnis/tim apa yang sedang didukung role ini?", bukan "perusahaan ini bagus atau tidak?".
            4. **Bandingkan dengan bukti pengalamanmu sendiri** — gunakan proyek atau hasil yang benar-benar pernah kamu kerjakan; jangan mengarang angka atau dampak.
            5. **Pilih tindakan** — melamar, mencari jalur kontak yang wajar, atau menyimpan hasil untuk ditelusuri kemudian.

            Research Pack sengaja **tidak menyimpulkan** bahwa perusahaan sedang membutuhkan sesuatu, bahwa kamu cocok, atau bahwa lowongan tersebut valid. Ia hanya memisahkan bukti yang sudah ada dari pertanyaan yang masih harus kamu verifikasi.
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
            - **Research Pack** — ringkasan bukti listing + query riset yang dibuat secara deterministik; bukan verifikasi otomatis atau AI matching.
            """
        )


    st.divider()
    st.subheader("💪 Bagian 3: ELI5 — Kenapa Cari Kerja Bisa Terasa 'Sial'")
    with st.expander("🍀 Kamu tidak harus 'beruntung' sekali. Kamu perlu lebih banyak kesempatan", expanded=True):
        st.markdown(
            """
            ### Bayangkan kamu sedang menangkap hujan

            Mencari kerja itu sedikit seperti menunggu hujan.

            Kamu **tidak bisa memerintah hujan turun**. Kamu juga tidak bisa menjamin perusahaan tertentu akan memilihmu.

            Tapi kamu bisa memilih ukuran embermu.

            Kalau embermu kecil, hujan deras pun mungkin menghasilkan sedikit air. Kalau embermu lebih besar, kamu punya lebih banyak peluang untuk menangkap sesuatu yang berguna.

            Dalam bahasa pencarian kerja, ukuran ember itu adalah **luck surface area**: seberapa banyak kamu bersentuhan dengan peluang.

            Jadi ketika kamu sudah mengirim lamaran dan belum berhasil, itu **tidak otomatis berarti kamu tidak cukup bagus**. Bisa saja peluang yang tepat belum bertemu denganmu.

            ### Jadi apa yang bisa kamu kontrol?

            **1. Ambil lebih banyak tembakan.**  
            Jangan menghabiskan seluruh energi untuk membuat satu lamaran sempurna. Buat eksperimen kecil, kirim lamaran yang memang masuk akal, coba jalur yang berbeda, lalu lihat apa yang mendapat respons. Lebih banyak percobaan memberi lebih banyak kesempatan untuk menemukan apa yang bekerja.

            **2. Jangan hanya mencari — buat dirimu mudah ditemukan.**  
            Kerja bagus yang tidak pernah terlihat sulit menghasilkan peluang masuk. Tunjukkan proyek, tulisan, kontribusi, atau hal yang sedang kamu pelajari. Kamu tidak harus menjadi ahli dulu untuk mulai meninggalkan "jejak" yang bisa ditemukan orang lain.

            **3. Kenalan baru itu penting.**  
            Teman dekatmu biasanya berada di lingkaran informasi yang mirip denganmu. Kenalan yang tidak terlalu dekat justru bisa membawa informasi dari dunia yang belum kamu masuki. Jadi ngobrol dengan orang baru, ikut komunitas, dan menjaga hubungan lama bukan basa-basi kosong; itu memperluas peta peluangmu.

            **4. Pergi ke tempat peluang berkumpul.**  
            Kalau kamu mencari pekerjaan di bidang tertentu, masuklah ke komunitas, forum, acara, atau ruang online tempat orang-orang di bidang itu berkumpul. Jangan berharap menemukan peluang baru sambil terus berada di lingkungan informasi yang sama.

            **5. Buat taruhan kecil, jangan pertaruhkan hidupmu.**  
            Coba hal yang punya potensi besar tetapi kerugiannya kecil: proyek sampingan, belajar skill baru, membantu komunitas, atau menghubungi seseorang secara profesional. Hindari keputusan yang kalau gagal akan menghancurkan kondisi keuangan atau hidupmu.

            **6. Sisakan ruang untuk kejutan.**  
            Kalau seluruh waktu, uang, dan energi sudah habis untuk rutinitas, kamu tidak punya ruang untuk mengambil kesempatan yang muncul tiba-tiba. Tidak semua menit harus dioptimalkan. Sedikit ruang kosong bisa menjadi ruang untuk peluang.

            **7. Belajar supaya kamu bisa mengenali kesempatan.**  
            Kadang peluang terlihat seperti sesuatu yang biasa saja. Orang yang punya pengetahuan lebih dalam bisa melihat nilai yang tidak terlihat oleh orang lain. Skill baru bukan cuma menambah CV; skill baru juga menambah hal yang bisa kamu kenali dan gabungkan.

            **8. Kegagalan bukan selalu informasi bahwa kamu harus berhenti.**  
            Ditolak berarti **lamaran itu tidak berhasil**, bukan berarti **kariermu gagal**. Tanyakan: apa yang bisa dipelajari? Apa yang bisa diubah? Siapa yang baru kamu temui? Jalur apa yang sekarang terbuka?

            **9. Mainkan permainan yang panjang.**  
            Reputasi, skill, hubungan, dan pengalaman menumpuk. Satu lamaran yang gagal hampir tidak berarti apa-apa dalam perjalanan yang panjang. Yang berbahaya justru berhenti bermain terlalu cepat.

            **10. Persistensi adalah strategi, bukan sekadar semangat.**  
            Kamu tidak perlu menang setiap kali. Kamu perlu tetap cukup lama di dalam permainan agar usaha, pengalaman, hubungan, dan peluang bisa saling menumpuk.

            ### Dan ini bagian yang paling penting

            **Job search bukan mesin yang membayar usaha secara langsung.**

            Kamu bisa melakukan semuanya dengan benar dan tetap ditolak.

            Itu menyebalkan. Dan tidak ada trik yang bisa menghapus kenyataan itu.

            Tetapi penolakan hari ini tidak memberi tahu kita bahwa besok tidak akan ada peluang. Yang bisa kamu lakukan adalah memperbesar kemungkinan bertemu peluang berikutnya: **lebih banyak mencoba, lebih mudah ditemukan, bertemu lebih banyak orang, masuk ke lingkungan yang tepat, belajar, menjaga downside tetap aman, dan terus bermain.**

            Jadi jangan ukur dirimu hanya dari jumlah "diterima".

            Ukur juga apakah **embermu makin besar**.

            🍀 **Kamu tidak perlu mengendalikan keberuntungan. Kamu perlu membangun sistem yang memberinya lebih banyak tempat untuk mendarat.**

            *Catatan: ini adalah kerangka untuk menjaga perspektif dan strategi pencarian kerja, bukan janji bahwa lebih banyak usaha pasti menghasilkan pekerjaan. Hasil tetap dipengaruhi kondisi pasar, timing, kebutuhan perusahaan, dan banyak faktor yang berada di luar kendalimu.*
            """
        )

    st.info("💡 **Prinsip utama:** alat ini membantu menemukan dan memeriksa informasi lowongan. Validasi akhir tetap perlu melihat deskripsi lengkap, perusahaan, tanggal, sumber, dan link asli.")
