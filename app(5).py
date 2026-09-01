import streamlit as st
import pandas as pd
from datetime import date

import db  # modul koneksi database (lihat db.py)

st.set_page_config(page_title="UMKMSehat", page_icon="🩺", layout="centered")

# ------------------------------------------------------------------
# Gaya tambahan
# ------------------------------------------------------------------
st.markdown("""
<style>
html, body, [class*="css"] { font-size: 17px; }
h1 { font-size: 2.1rem !important; }
h2 { font-size: 1.5rem !important; }
h3 { font-size: 1.25rem !important; }
.stButton>button {
    border-radius: 10px;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
    font-size: 1.02rem;
}
div[data-testid="stMetric"] {
    background-color: #EAF7F1;
    border-radius: 12px;
    padding: 12px 14px;
    border: 1px solid #D5EFE3;
}
.video-card {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 14px;
}
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    margin-right: 6px;
}
.badge-kategori { background-color: #EAF7F1; color: #0E9F6E; }
.badge-gratis { background-color: #E8F0FE; color: #1A56DB; }
.badge-premium { background-color: #FEF3E7; color: #C2740A; }
</style>
""", unsafe_allow_html=True)

VIDEO_PLACEHOLDER_URL = "https://www.w3schools.com/html/mov_bbb.mp4"  # video contoh bebas hak cipta, ganti dengan videomu sendiri


def clip(nilai, low=0, high=100):
    return max(low, min(high, nilai))


# ====================================================================
# SIDEBAR — identitas usaha
# ====================================================================
st.sidebar.header("🏪 Usaha Saya")
nama_usaha_aktif = st.sidebar.text_input(
    "Nama usaha",
    placeholder="Contoh: Warung Bu Sari",
    help="Dipakai sebagai penanda supaya data usahamu tidak tercampur dengan usaha lain.",
)

if db.DB_READY:
    st.sidebar.success("🟢 Tersambung ke database — data tersimpan permanen.")
else:
    st.sidebar.warning(
        "🟡 Database belum tersambung. Data hanya tersimpan sementara di sesi ini. "
        "Lihat **SETUP_DATABASE.md** untuk mengaktifkan penyimpanan permanen."
    )

st.title("🩺 UMKMSehat")
st.caption("Cek kondisi usahamu, lalu langsung ditemani video pendampingan yang sesuai kebutuhanmu.")

if not nama_usaha_aktif:
    st.info("👋 Isi dulu **nama usaha** di kotak sebelah kiri (sidebar) untuk mulai memakai aplikasi ini.")
    st.stop()

# ====================================================================
# STATE CADANGAN
# ====================================================================
for key in ["riwayat_skor", "katalog_video_lokal", "akses_premium"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key != "akses_premium" else False

if "tag_masalah_terakhir" not in st.session_state:
    st.session_state.tag_masalah_terakhir = []


def tambah_skor(data):
    if db.DB_READY:
        db.insert_row("skor_usaha", {**data, "nama_usaha": nama_usaha_aktif})
    else:
        st.session_state.riwayat_skor.append(data)


def ambil_skor():
    if db.DB_READY:
        return db.load_rows("skor_usaha", nama_usaha_aktif)
    return st.session_state.riwayat_skor


def ambil_katalog_video():
    if db.DB_READY:
        return db.load_all_videos()
    return st.session_state.katalog_video_lokal


def tambah_video(data):
    if db.DB_READY:
        db.insert_row("video_konten", data)
    else:
        data_lokal = {**data, "id": len(st.session_state.katalog_video_lokal) + 1}
        st.session_state.katalog_video_lokal.append(data_lokal)


# Isi katalog video contoh kalau masih kosong (biar tidak mulai dari kosong melompong)
def seed_katalog_jika_kosong():
    katalog = ambil_katalog_video()
    if katalog:
        return
    contoh = [
        {"judul": "Cara Menghitung Harga Jual yang Tepat", "kategori": "Keuangan",
         "url_video": VIDEO_PLACEHOLDER_URL, "deskripsi": "Langkah sederhana menentukan harga jual dari modal dan margin yang wajar.",
         "tag_masalah": "margin_rendah", "premium": False},
        {"judul": "Strategi Menghabiskan Stok Lama", "kategori": "Operasional",
         "url_video": VIDEO_PLACEHOLDER_URL, "deskripsi": "Cara membuat promo sederhana supaya barang lama tidak terus menumpuk.",
         "tag_masalah": "stok_menumpuk", "premium": False},
        {"judul": "Cara Menagih Utang Pelanggan dengan Sopan", "kategori": "Keuangan",
         "url_video": VIDEO_PLACEHOLDER_URL, "deskripsi": "Kalimat dan cara pendekatan menagih tanpa merusak hubungan dengan pelanggan.",
         "tag_masalah": "utang_tinggi", "premium": True},
        {"judul": "Menekan Biaya Operasional Tanpa Mengorbankan Kualitas", "kategori": "Keuangan",
         "url_video": VIDEO_PLACEHOLDER_URL, "deskripsi": "Pos-pos biaya yang sering bisa dihemat tanpa mengurangi kualitas layanan.",
         "tag_masalah": "biaya_tinggi", "premium": True},
        {"judul": "Menarik Kembali Pelanggan yang Mulai Sepi", "kategori": "Penjualan",
         "url_video": VIDEO_PLACEHOLDER_URL, "deskripsi": "Langkah sederhana mengevaluasi kenapa omzet turun dan cara menariknya kembali.",
         "tag_masalah": "omzet_turun", "premium": False},
        {"judul": "Ide Promosi Ringan untuk Usaha yang Segitu-Segitu Saja", "kategori": "Penjualan",
         "url_video": VIDEO_PLACEHOLDER_URL, "deskripsi": "Promosi kecil yang bisa dicoba ketika omzet stagnan, tidak naik tidak turun.",
         "tag_masalah": "omzet_stagnan", "premium": True},
    ]
    for v in contoh:
        tambah_video(v)


seed_katalog_jika_kosong()

tab_cek, tab_video = st.tabs(["🩺 Cek Kesehatan Usaha", "🎥 Video Pendampingan"])

# ====================================================================
# TAB 1 — CEK KESEHATAN USAHA
# ====================================================================
with tab_cek:

    def skor_penjualan(omzet_ini, omzet_lalu):
        if omzet_lalu <= 0:
            return 50.0, 0.0
        pertumbuhan = (omzet_ini - omzet_lalu) / omzet_lalu
        return clip(50 + pertumbuhan * 300), pertumbuhan

    def skor_keuangan(omzet_ini, hpp, modal, utang_usaha):
        margin_kotor = (omzet_ini - hpp) / omzet_ini if omzet_ini > 0 else 0
        rasio_utang = utang_usaha / modal if modal > 0 else 2.0
        skor_margin = clip(margin_kotor / 0.25 * 100)
        skor_utang = clip(100 - rasio_utang * 100)
        return skor_margin * 0.6 + skor_utang * 0.4, margin_kotor, rasio_utang

    def skor_operasional(omzet_ini, stok_belum_laku, biaya_operasional):
        rasio_stok = stok_belum_laku / omzet_ini if omzet_ini > 0 else 0
        rasio_biaya = biaya_operasional / omzet_ini if omzet_ini > 0 else 0
        skor_stok = clip(100 - rasio_stok * 200)
        skor_biaya = clip(100 - rasio_biaya * 150)
        return (skor_stok + skor_biaya) / 2, rasio_stok, rasio_biaya

    def deteksi_tag_masalah(pertumbuhan, margin_kotor, rasio_utang, rasio_stok, rasio_biaya):
        tag = []
        if pertumbuhan < 0:
            tag.append("omzet_turun")
        elif pertumbuhan < 0.05:
            tag.append("omzet_stagnan")
        if margin_kotor < 0.15:
            tag.append("margin_rendah")
        if rasio_utang > 0.7:
            tag.append("utang_tinggi")
        if rasio_stok > 0.3:
            tag.append("stok_menumpuk")
        if rasio_biaya > 0.5:
            tag.append("biaya_tinggi")
        return tag

    def kategori_skor(skor):
        if skor >= 80:
            return "Sehat", "🟢"
        elif skor >= 60:
            return "Cukup Sehat", "🟡"
        elif skor >= 40:
            return "Perlu Perhatian", "🟠"
        return "Bermasalah", "🔴"

    st.subheader("1. Isi Data Usaha")
    st.caption(f"Data untuk: **{nama_usaha_aktif}**")
    sektor = st.selectbox("Sektor usaha", ["Kuliner", "Retail / Toko", "Jasa", "Produksi / Kerajinan", "Lainnya"])

    col1, col2 = st.columns(2)
    with col1:
        omzet_ini = st.number_input("Omzet bulan ini (Rp)", min_value=0, step=100000, value=5000000)
        modal = st.number_input("Modal usaha saat ini (Rp)", min_value=0, step=100000, value=10000000)
        hpp = st.number_input("Harga pokok / bahan baku bulan ini (Rp)", min_value=0, step=100000, value=3500000)
    with col2:
        omzet_lalu = st.number_input("Omzet bulan lalu (Rp)", min_value=0, step=100000, value=4500000)
        utang_usaha = st.number_input("Total utang usaha saat ini (Rp)", min_value=0, step=100000, value=2000000)
        stok_belum_laku = st.number_input("Nilai stok/barang belum laku (Rp)", min_value=0, step=100000, value=500000)

    biaya_operasional = st.number_input("Biaya operasional di luar bahan baku — sewa, listrik, gaji, dll (Rp)", min_value=0, step=100000, value=1000000)

    if st.button("🔍 Cek Kondisi Usaha", type="primary", use_container_width=True):
        if omzet_ini <= 0:
            st.error("Omzet bulan ini harus diisi lebih dari 0.")
        else:
            s_jual, pertumbuhan = skor_penjualan(omzet_ini, omzet_lalu)
            s_uang, margin_kotor, rasio_utang = skor_keuangan(omzet_ini, hpp, modal, utang_usaha)
            s_ops, rasio_stok, rasio_biaya = skor_operasional(omzet_ini, stok_belum_laku, biaya_operasional)
            skor_total = (s_jual + s_uang + s_ops) / 3

            tag_terdeteksi = deteksi_tag_masalah(pertumbuhan, margin_kotor, rasio_utang, rasio_stok, rasio_biaya)
            st.session_state.tag_masalah_terakhir = tag_terdeteksi

            tambah_skor({
                "tanggal": date.today().isoformat(),
                "skor_penjualan": round(s_jual, 1),
                "skor_keuangan": round(s_uang, 1),
                "skor_operasional": round(s_ops, 1),
                "skor_total": round(skor_total, 1),
            })

            st.divider()
            st.subheader("2. Hasil Pengecekan")
            label, emoji = kategori_skor(skor_total)
            st.metric(f"Skor Kesehatan Usaha — {nama_usaha_aktif}", f"{skor_total:.0f} / 100", label)
            st.write(f"{emoji} **Status: {label}**")

            c1, c2, c3 = st.columns(3)
            c1.metric("Penjualan", f"{s_jual:.0f}")
            c2.metric("Keuangan", f"{s_uang:.0f}")
            c3.metric("Operasional", f"{s_ops:.0f}")
            st.progress(int(skor_total))

            if tag_terdeteksi:
                st.success("🎥 Video pendampingan yang sesuai sudah disiapkan — buka tab **Video Pendampingan** di atas untuk menontonnya.")
            else:
                st.success("Kondisi usaha secara umum cukup baik. Tetap pantau tiap bulan supaya tetap terjaga.")

    riwayat = ambil_skor()
    if riwayat:
        st.divider()
        st.subheader("3. Pemantauan")
        df = pd.DataFrame(riwayat).rename(columns={
            "tanggal": "Tanggal", "skor_penjualan": "Skor Penjualan",
            "skor_keuangan": "Skor Keuangan", "skor_operasional": "Skor Operasional",
            "skor_total": "Skor Total",
        })
        st.line_chart(df.set_index("Tanggal")[["Skor Penjualan", "Skor Keuangan", "Skor Operasional", "Skor Total"]])
        st.dataframe(df[["Tanggal", "Skor Penjualan", "Skor Keuangan", "Skor Operasional", "Skor Total"]],
                     use_container_width=True, hide_index=True)


# ====================================================================
# TAB 2 — VIDEO PENDAMPINGAN
# ====================================================================
with tab_video:
    st.subheader("🎥 Video Pendampingan")
    st.write("Materi belajar singkat yang bisa ditonton kapan saja, sesuai kondisi usahamu.")

    LABEL_TAG = {
        "margin_rendah": "keuntungan yang terlalu tipis",
        "omzet_turun": "omzet yang menurun",
        "omzet_stagnan": "omzet yang segitu-segitu saja",
        "utang_tinggi": "utang usaha yang cukup besar",
        "stok_menumpuk": "stok barang yang menumpuk",
        "biaya_tinggi": "biaya operasional yang tinggi",
    }

    katalog = ambil_katalog_video()

    def tampilkan_video(v, alasan=None):
        premium = v.get("premium", False)
        terkunci = premium and not st.session_state.akses_premium
        with st.container():
            st.markdown('<div class="video-card">', unsafe_allow_html=True)
            badge_kategori = f'<span class="badge badge-kategori">{v.get("kategori","")}</span>'
            badge_akses = '<span class="badge badge-premium">🔒 Premium</span>' if premium else '<span class="badge badge-gratis">Gratis</span>'
            st.markdown(badge_kategori + badge_akses, unsafe_allow_html=True)
            st.markdown(f"**{v.get('judul','(tanpa judul)')}**")
            if alasan:
                st.caption(f"🎯 Direkomendasikan karena {alasan}")
            st.write(v.get("deskripsi", ""))
            if terkunci:
                st.warning("Video ini bagian dari paket premium.")
            else:
                url = v.get("url_video") or ""
                if url:
                    st.video(url)
                else:
                    st.info("🎬 Video belum diunggah untuk materi ini.")
            st.markdown("</div>", unsafe_allow_html=True)

    # ---- Rekomendasi berdasarkan checkup terakhir ----
    tag_aktif = st.session_state.tag_masalah_terakhir
    if tag_aktif:
        st.markdown("### 🎯 Direkomendasikan untuk kamu")
        alasan_list = [LABEL_TAG.get(t, t) for t in tag_aktif]
        st.caption("Berdasarkan hasil Cek Kesehatan Usaha terakhir: " + ", ".join(alasan_list))
        video_rekomendasi = [v for v in katalog if v.get("tag_masalah") in tag_aktif]
        if video_rekomendasi:
            for v in video_rekomendasi:
                tampilkan_video(v, alasan=LABEL_TAG.get(v.get("tag_masalah"), ""))
        else:
            st.info("Belum ada video yang cocok persis dengan kondisi ini di katalog.")
        st.divider()
    else:
        st.info("Coba isi **Cek Kesehatan Usaha** dulu di tab sebelah supaya video yang muncul di sini lebih sesuai kebutuhanmu. Di bawah ini katalog lengkapnya.")

    # ---- Simulasi akses premium ----
    if not st.session_state.akses_premium:
        with st.expander("🔓 Buka akses semua video premium (simulasi)"):
            st.write("Di versi sungguhan, ini akan tersambung ke pembayaran asli (misalnya QRIS). Untuk prototipe ini, klik tombol di bawah untuk mensimulasikan pembelian.")
            if st.button("Beli akses premium — Rp25.000 (simulasi)"):
                st.session_state.akses_premium = True
                st.rerun()
    else:
        st.success("🔓 Akses premium aktif untuk sesi ini (simulasi).")

    st.divider()

    # ---- Jelajahi katalog lengkap ----
    st.markdown("### 📚 Jelajahi Semua Video")
    kategori_filter = st.selectbox("Filter kategori", ["Semua", "Keuangan", "Penjualan", "Operasional"])
    katalog_tampil = katalog if kategori_filter == "Semua" else [v for v in katalog if v.get("kategori") == kategori_filter]

    if katalog_tampil:
        for v in katalog_tampil:
            tampilkan_video(v)
    else:
        st.info("Belum ada video di kategori ini.")

    # ---- Tambah video baru (mode pengelola) ----
    st.divider()
    with st.expander("🔐 Mode Pengelola — tambah video baru"):
        st.caption("Bagian ini untuk kamu sebagai pemilik aplikasi menambah konten. Di versi sungguhan, ini perlu dikunci dengan login khusus.")
        with st.form("form_tambah_video", clear_on_submit=True):
            judul_baru = st.text_input("Judul video")
            kategori_baru = st.selectbox("Kategori", ["Keuangan", "Penjualan", "Operasional"])
            url_baru = st.text_input("URL video (link video kamu — bisa YouTube atau file .mp4)")
            deskripsi_baru = st.text_area("Deskripsi singkat")
            tag_baru = st.selectbox("Cocok untuk kondisi (agar direkomendasikan otomatis)", [
                "(tidak ada — hanya bisa ditemukan lewat jelajah kategori)",
                "margin_rendah", "omzet_turun", "omzet_stagnan",
                "utang_tinggi", "stok_menumpuk", "biaya_tinggi",
            ])
            premium_baru = st.checkbox("Jadikan video premium (berbayar)")
            simpan_video = st.form_submit_button("💾 Simpan video")
            if simpan_video and judul_baru:
                tambah_video({
                    "judul": judul_baru,
                    "kategori": kategori_baru,
                    "url_video": url_baru,
                    "deskripsi": deskripsi_baru,
                    "tag_masalah": None if tag_baru.startswith("(tidak ada") else tag_baru,
                    "premium": premium_baru,
                })
                st.success("Video tersimpan! Muncul di daftar setelah halaman dimuat ulang.")


st.divider()
st.caption("Prototipe UMKMSehat — cek kesehatan usaha, dengan video pendampingan yang sesuai kondisi usahamu.")
