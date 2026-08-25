# UMKMSehat
Startup Pembinaan UMKM
import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="UMKMSehat", page_icon="🩺", layout="centered")

# ----------------------------------------------------------------------
# Fungsi-fungsi penilaian (logika skoring)
# ----------------------------------------------------------------------

def clip(nilai, low=0, high=100):
    return max(low, min(high, nilai))

def skor_penjualan(omzet_ini, omzet_lalu):
    """Skor 0-100 berdasarkan pertumbuhan omzet bulan ini vs bulan lalu."""
    if omzet_lalu <= 0:
        return 50.0, 0.0
    pertumbuhan = (omzet_ini - omzet_lalu) / omzet_lalu
    skor = clip(50 + pertumbuhan * 300)
    return skor, pertumbuhan

def skor_keuangan(omzet_ini, hpp, modal, utang):
    """Skor 0-100 dari margin kotor dan rasio utang terhadap modal."""
    margin_kotor = (omzet_ini - hpp) / omzet_ini if omzet_ini > 0 else 0
    rasio_utang = utang / modal if modal > 0 else 2.0

    skor_margin = clip(margin_kotor / 0.25 * 100)
    skor_utang = clip(100 - rasio_utang * 100)
    skor = skor_margin * 0.6 + skor_utang * 0.4
    return skor, margin_kotor, rasio_utang

def skor_operasional(omzet_ini, stok_belum_laku, biaya_operasional):
    """Skor 0-100 dari rasio stok menumpuk dan biaya operasional terhadap omzet."""
    rasio_stok = stok_belum_laku / omzet_ini if omzet_ini > 0 else 0
    rasio_biaya = biaya_operasional / omzet_ini if omzet_ini > 0 else 0

    skor_stok = clip(100 - rasio_stok * 200)
    skor_biaya = clip(100 - rasio_biaya * 150)
    skor = (skor_stok + skor_biaya) / 2
    return skor, rasio_stok, rasio_biaya

def buat_rekomendasi(pertumbuhan, margin_kotor, rasio_utang, rasio_stok, rasio_biaya):
    saran = []

    if pertumbuhan < 0:
        saran.append(
            "Omzet bulan ini turun dibanding bulan lalu. Coba evaluasi apakah ada pelanggan "
            "tetap yang berhenti membeli, atau apakah perlu promosi ringan untuk menarik kembali pembeli."
        )
    elif pertumbuhan < 0.05:
        saran.append(
            "Omzet cenderung stagnan. Coba tambahkan promosi kecil, paket bundling, atau jam operasional "
            "yang lebih sesuai kebiasaan pelanggan."
        )

    if margin_kotor < 0.15:
        saran.append(
            f"Keuntungan kotor sekitar {margin_kotor*100:.1f}%, di bawah rata-rata usaha sejenis (15-20%). "
            "Coba naikkan sedikit harga jual produk yang paling laku, atau tawar ulang harga bahan baku ke pemasok."
        )

    if rasio_utang > 0.7:
        saran.append(
            "Jumlah utang cukup besar dibanding modal yang dimiliki. Sebaiknya tahan dulu utang baru dan "
            "prioritaskan melunasi utang yang bunganya paling tinggi lebih dulu."
        )

    if rasio_stok > 0.3:
        saran.append(
            "Ada cukup banyak barang yang belum laku dan menumpuk. Coba buat promo diskon khusus untuk "
            "menghabiskan stok lama, supaya uang tidak tertahan di barang yang tidak berputar."
        )

    if rasio_biaya > 0.5:
        saran.append(
            "Biaya operasional (sewa, listrik, gaji, dll.) memakan porsi besar dari omzet. Coba periksa "
            "pos biaya mana yang bisa dikurangi tanpa mengganggu kualitas layanan."
        )

    if not saran:
        saran.append("Kondisi usaha secara umum cukup baik. Pertahankan pola yang sudah berjalan dan tetap pantau setiap bulan.")

    return saran


def kategori_skor(skor):
    if skor >= 80:
        return "Sehat", "🟢"
    elif skor >= 60:
        return "Cukup Sehat", "🟡"
    elif skor >= 40:
        return "Perlu Perhatian", "🟠"
    else:
        return "Bermasalah", "🔴"


# ----------------------------------------------------------------------
# State riwayat (supaya grafik pemantauan bulanan bisa jalan dalam 1 sesi)
# ----------------------------------------------------------------------
if "riwayat" not in st.session_state:
    st.session_state.riwayat = []

# ----------------------------------------------------------------------
# UI - Header
# ----------------------------------------------------------------------
st.title("🩺 UMKMSehat")
st.caption("Prototipe sederhana — cek kondisi kesehatan usaha kecil dalam 5 menit")

with st.expander("ℹ️ Tentang aplikasi ini"):
    st.write(
        "UMKMSehat membantu pemilik usaha kecil mengetahui kondisi usahanya secara objektif. "
        "Isi beberapa angka penting di bawah, dan sistem akan memberi skor kesehatan usaha "
        "beserta saran yang bisa langsung dicoba. Ini adalah prototipe awal untuk menguji konsep "
        "penilaian, belum menyimpan data secara permanen."
    )

st.divider()

# ----------------------------------------------------------------------
# Form input
# ----------------------------------------------------------------------
st.subheader("1. Isi Data Usaha")

nama_usaha = st.text_input("Nama usaha", placeholder="Contoh: Warung Bu Sari")
sektor = st.selectbox("Sektor usaha", ["Kuliner", "Retail / Toko", "Jasa", "Produksi / Kerajinan", "Lainnya"])

col1, col2 = st.columns(2)
with col1:
    omzet_ini = st.number_input("Omzet bulan ini (Rp)", min_value=0, step=100000, value=5000000)
    modal = st.number_input("Modal usaha saat ini (Rp)", min_value=0, step=100000, value=10000000)
    hpp = st.number_input("Harga pokok / biaya bahan baku bulan ini (Rp)", min_value=0, step=100000, value=3500000)
with col2:
    omzet_lalu = st.number_input("Omzet bulan lalu (Rp)", min_value=0, step=100000, value=4500000)
    utang = st.number_input("Total utang usaha saat ini (Rp)", min_value=0, step=100000, value=2000000)
    stok_belum_laku = st.number_input("Nilai stok/barang yang belum laku (Rp)", min_value=0, step=100000, value=500000)

biaya_operasional = st.number_input(
    "Biaya operasional bulan ini di luar bahan baku — sewa, listrik, gaji, dll (Rp)",
    min_value=0, step=100000, value=1000000
)

hitung = st.button("🔍 Cek Kondisi Usaha", type="primary", use_container_width=True)

# ----------------------------------------------------------------------
# Hasil
# ----------------------------------------------------------------------
if hitung:
    if omzet_ini <= 0:
        st.error("Omzet bulan ini harus diisi lebih dari 0 agar bisa dihitung.")
    else:
        s_jual, pertumbuhan = skor_penjualan(omzet_ini, omzet_lalu)
        s_uang, margin_kotor, rasio_utang = skor_keuangan(omzet_ini, hpp, modal, utang)
        s_ops, rasio_stok, rasio_biaya = skor_operasional(omzet_ini, stok_belum_laku, biaya_operasional)
        skor_total = (s_jual + s_uang + s_ops) / 3

        st.session_state.riwayat.append({
            "Tanggal": date.today().strftime("%Y-%m-%d"),
            "Skor Penjualan": round(s_jual, 1),
            "Skor Keuangan": round(s_uang, 1),
            "Skor Operasional": round(s_ops, 1),
            "Skor Total": round(skor_total, 1),
        })

        st.divider()
        st.subheader("2. Hasil Pengecekan")

        label, emoji = kategori_skor(skor_total)
        st.metric(f"Skor Kesehatan Usaha {'— ' + nama_usaha if nama_usaha else ''}",
                  f"{skor_total:.0f} / 100", label)
        st.write(f"{emoji} **Status: {label}**")

        c1, c2, c3 = st.columns(3)
        c1.metric("Penjualan", f"{s_jual:.0f}")
        c2.metric("Keuangan", f"{s_uang:.0f}")
        c3.metric("Operasional", f"{s_ops:.0f}")

        st.progress(int(skor_total))

        st.subheader("3. Saran yang Bisa Dicoba")
        for i, saran in enumerate(buat_rekomendasi(pertumbuhan, margin_kotor, rasio_utang, rasio_stok, rasio_biaya), 1):
            st.write(f"{i}. {saran}")

        if skor_total >= 80:
            st.success(
                "🏆 Usaha ini memenuhi ambang nilai untuk **Sertifikat UMKM Sehat**, "
                "yang bisa dilampirkan saat mengajukan pinjaman ke bank/koperasi. "
                "(Pada versi lengkap, sertifikat ini bisa diunduh dalam bentuk PDF.)"
            )
        elif skor_total < 50:
            st.warning(
                "Skor masih tergolong rendah. Pada versi lengkap, usaha dengan skor seperti ini "
                "akan ditawari sesi konsultasi singkat dengan pendamping."
            )

# ----------------------------------------------------------------------
# Riwayat / grafik pemantauan
# ----------------------------------------------------------------------
if st.session_state.riwayat:
    st.divider()
    st.subheader("4. Pemantauan (dalam sesi ini)")
    df = pd.DataFrame(st.session_state.riwayat)
    st.line_chart(df.set_index("Tanggal")[["Skor Penjualan", "Skor Keuangan", "Skor Operasional", "Skor Total"]])
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(
        "Catatan: pada prototipe ini riwayat hanya tersimpan selama sesi berjalan (belum ada "
        "penyimpanan permanen ke database)."
    )

st.divider()
st.caption("Prototipe UMKMSehat — dibuat untuk menguji konsep penilaian kesehatan usaha kecil.")
