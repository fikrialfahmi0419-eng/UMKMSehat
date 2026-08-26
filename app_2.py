import streamlit as st
import pandas as pd
import re
from datetime import date, datetime

st.set_page_config(page_title="UMKMSehat", page_icon="🩺", layout="centered")

# ------------------------------------------------------------------
# Gaya tambahan (di luar yang sudah diatur lewat .streamlit/config.toml)
# Tujuan: tombol & teks lebih besar supaya nyaman dibaca segala usia,
# kartu-kartu punya sudut membulat dan sedikit bayangan biar terasa ramah.
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
div[data-testid="stExpander"] {
    border-radius: 10px;
}
.paket-card {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    padding: 20px;
    height: 100%;
}
.paket-harga {
    font-size: 1.4rem;
    font-weight: 700;
    color: #0E9F6E;
    margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)


def format_rupiah(n):
    try:
        return "Rp" + "{:,.0f}".format(n).replace(",", ".")
    except (ValueError, TypeError):
        return "Rp0"


def clip(nilai, low=0, high=100):
    return max(low, min(high, nilai))


# ====================================================================
# STATE AWAL
# ====================================================================
if "riwayat_skor" not in st.session_state:
    st.session_state.riwayat_skor = []
if "penjualan_harian" not in st.session_state:
    st.session_state.penjualan_harian = []
if "stok" not in st.session_state:
    st.session_state.stok = []
if "utang" not in st.session_state:
    st.session_state.utang = []
if "pengeluaran" not in st.session_state:
    st.session_state.pengeluaran = []
if "invoice_items" not in st.session_state:
    st.session_state.invoice_items = []

# ====================================================================
# HEADER
# ====================================================================
st.title("🩺 UMKMSehat")
st.caption("Teman digital untuk usaha kecil — cek kesehatan usaha, bantu urusan admin harian, dan siap naik kelas digital.")

tab_cek, tab_asisten, tab_go = st.tabs(["🩺 Cek Kesehatan Usaha", "🤖 UMKM Assistant", "🚀 UMKMGo"])

# ====================================================================
# TAB 1 — CEK KESEHATAN USAHA (fitur inti sebelumnya)
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

    def buat_rekomendasi(pertumbuhan, margin_kotor, rasio_utang, rasio_stok, rasio_biaya):
        saran = []
        if pertumbuhan < 0:
            saran.append("Omzet bulan ini turun dibanding bulan lalu. Coba evaluasi pelanggan tetap yang berhenti membeli, atau buat promosi ringan untuk menarik kembali pembeli.")
        elif pertumbuhan < 0.05:
            saran.append("Omzet cenderung stagnan. Coba tambahkan promosi kecil atau paket bundling.")
        if margin_kotor < 0.15:
            saran.append(f"Keuntungan kotor sekitar {margin_kotor*100:.1f}%, di bawah rata-rata usaha sejenis (15-20%). Coba naikkan sedikit harga produk yang laris, atau nego ulang harga bahan baku ke pemasok.")
        if rasio_utang > 0.7:
            saran.append("Utang usaha cukup besar dibanding modal. Sebaiknya tahan dulu utang baru dan prioritaskan melunasi utang berbunga tertinggi.")
        if rasio_stok > 0.3:
            saran.append("Ada cukup banyak barang menumpuk belum laku. Coba buat promo diskon khusus untuk menghabiskan stok lama.")
        if rasio_biaya > 0.5:
            saran.append("Biaya operasional memakan porsi besar dari omzet. Coba periksa pos biaya mana yang bisa dikurangi.")
        if not saran:
            saran.append("Kondisi usaha secara umum cukup baik. Pertahankan pola yang sudah berjalan dan tetap pantau tiap bulan.")
        return saran

    def kategori_skor(skor):
        if skor >= 80:
            return "Sehat", "🟢"
        elif skor >= 60:
            return "Cukup Sehat", "🟡"
        elif skor >= 40:
            return "Perlu Perhatian", "🟠"
        return "Bermasalah", "🔴"

    st.subheader("1. Isi Data Usaha")
    nama_usaha = st.text_input("Nama usaha", placeholder="Contoh: Warung Bu Sari")
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

            st.session_state.riwayat_skor.append({
                "Tanggal": date.today().strftime("%Y-%m-%d"),
                "Skor Penjualan": round(s_jual, 1),
                "Skor Keuangan": round(s_uang, 1),
                "Skor Operasional": round(s_ops, 1),
                "Skor Total": round(skor_total, 1),
            })

            st.divider()
            st.subheader("2. Hasil Pengecekan")
            label, emoji = kategori_skor(skor_total)
            st.metric(f"Skor Kesehatan Usaha {'— ' + nama_usaha if nama_usaha else ''}", f"{skor_total:.0f} / 100", label)
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
                st.success("🏆 Usaha ini memenuhi ambang nilai untuk **Sertifikat UMKM Sehat**, yang bisa dilampirkan saat mengajukan pinjaman ke bank/koperasi.")
            elif skor_total < 50:
                st.warning("Skor masih tergolong rendah. Pada versi lengkap, usaha dengan skor seperti ini akan ditawari sesi konsultasi singkat dengan pendamping.")

    if st.session_state.riwayat_skor:
        st.divider()
        st.subheader("4. Pemantauan (dalam sesi ini)")
        df = pd.DataFrame(st.session_state.riwayat_skor)
        st.line_chart(df.set_index("Tanggal")[["Skor Penjualan", "Skor Keuangan", "Skor Operasional", "Skor Total"]])
        st.dataframe(df, use_container_width=True, hide_index=True)


# ====================================================================
# TAB 2 — UMKM ASSISTANT
# ====================================================================
with tab_asisten:
    st.subheader("🤖 UMKM Assistant")
    st.write(
        "Anggap ini admin digital untuk usahamu. Tidak perlu menggaji admin penuh waktu "
        "(biasanya Rp2-3 juta/bulan) — cukup catat aktivitas harian di sini, dengan biaya "
        "layanan yang jauh lebih ringan."
    )

    menu = st.radio(
        "Pilih yang mau dipakai:",
        ["📒 Catat Penjualan", "🧮 Hitung Harga Jual", "🧾 Buat Invoice",
         "📦 Ingat Stok", "💳 Utang Pelanggan", "💸 Cek Pengeluaran",
         "💬 Balas Pelanggan", "📱 Bikin Konten"],
        horizontal=False,
    )
    st.divider()

    # ---------------- 1. Catat Penjualan ----------------
    if menu == "📒 Catat Penjualan":
        st.markdown("**Ceritakan aktivitas hari ini seperti chat biasa.**")
        st.caption('Contoh: "Hari ini 12 pelanggan, total Rp850.000, paling laku cuci + setrika"')

        laporan = st.text_input("Laporan hari ini", placeholder="Hari ini 12 pelanggan, total Rp850.000")
        produk_favorit = st.text_input("Produk/jasa paling laku (opsional)", placeholder="Contoh: Cuci + Setrika")
        margin_persen = st.slider("Perkiraan margin keuntungan (%)", 5, 80, 30,
                                   help="Dipakai untuk memperkirakan laba dari total penjualan yang kamu catat.")

        if st.button("✅ Catat", type="primary"):
            jml_pelanggan_match = re.search(r"(\d+)\s*pelanggan", laporan, re.IGNORECASE)
            total_match = re.search(r"rp\s?([\d.,]+)", laporan, re.IGNORECASE)

            jml_pelanggan = int(jml_pelanggan_match.group(1)) if jml_pelanggan_match else None
            if total_match:
                angka_bersih = total_match.group(1).replace(".", "").replace(",", "")
                total = int(angka_bersih) if angka_bersih.isdigit() else 0
            else:
                total = 0

            if total == 0:
                st.warning("Nominal penjualan tidak terbaca otomatis dari kalimat itu. Coba tulis nominalnya jelas, contoh: Rp850.000")
            else:
                estimasi_laba = total * margin_persen / 100
                st.session_state.penjualan_harian.append({
                    "Tanggal": date.today().strftime("%Y-%m-%d"),
                    "Jumlah Pelanggan": jml_pelanggan if jml_pelanggan else "-",
                    "Omzet": total,
                    "Estimasi Laba": estimasi_laba,
                    "Produk Favorit": produk_favorit if produk_favorit else "-",
                })
                st.success("Tercatat! Ringkasan diperbarui di bawah.")

        if st.session_state.penjualan_harian:
            df_pj = pd.DataFrame(st.session_state.penjualan_harian)
            omzet_hari_ini = df_pj.iloc[-1]["Omzet"]
            laba_hari_ini = df_pj.iloc[-1]["Estimasi Laba"]
            omzet_minggu = df_pj["Omzet"].sum()

            produk_valid = [p for p in df_pj["Produk Favorit"] if p != "-"]
            produk_terlaris = pd.Series(produk_valid).mode()[0] if produk_valid else "-"

            st.divider()
            st.markdown("**Ringkasan**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Omzet hari ini", format_rupiah(omzet_hari_ini))
            c2.metric("Estimasi laba", format_rupiah(laba_hari_ini))
            c3.metric("Omzet total tercatat", format_rupiah(omzet_minggu))
            st.write(f"🏆 Produk/jasa paling sering laku: **{produk_terlaris}**")

            st.line_chart(df_pj.set_index("Tanggal")[["Omzet"]])
            st.dataframe(df_pj, use_container_width=True, hide_index=True)

    # ---------------- 2. Hitung Harga Jual ----------------
    elif menu == "🧮 Hitung Harga Jual":
        st.markdown("**Hitung harga jual yang wajar dari modal/biaya produksi.**")
        hpp_item = st.number_input("Biaya modal per produk/jasa (Rp)", min_value=0, step=1000, value=15000)
        margin_target = st.slider("Margin keuntungan yang diinginkan (%)", 5, 100, 30)
        harga_jual = hpp_item / (1 - margin_target / 100) if margin_target < 100 else 0

        st.metric("Harga jual yang disarankan", format_rupiah(harga_jual))
        st.caption(f"Dengan harga ini, keuntungan per item sekitar {format_rupiah(harga_jual - hpp_item)}.")

    # ---------------- 3. Buat Invoice ----------------
    elif menu == "🧾 Buat Invoice":
        st.markdown("**Buat invoice/nota sederhana untuk pelanggan.**")
        nama_pelanggan = st.text_input("Nama pelanggan", placeholder="Contoh: Ibu Rina")
        tgl_invoice = st.date_input("Tanggal", value=date.today())

        with st.form("form_item_invoice", clear_on_submit=True):
            colA, colB, colC = st.columns([2, 1, 1])
            nama_item = colA.text_input("Nama barang/jasa")
            qty = colB.number_input("Jumlah", min_value=1, step=1, value=1)
            harga_satuan = colC.number_input("Harga satuan (Rp)", min_value=0, step=1000, value=10000)
            tambah = st.form_submit_button("+ Tambah item")
            if tambah and nama_item:
                st.session_state.invoice_items.append({"Item": nama_item, "Jumlah": qty, "Harga Satuan": harga_satuan, "Subtotal": qty * harga_satuan})

        if st.session_state.invoice_items:
            df_inv = pd.DataFrame(st.session_state.invoice_items)
            st.dataframe(df_inv, use_container_width=True, hide_index=True)
            total_invoice = df_inv["Subtotal"].sum()
            st.metric("Total tagihan", format_rupiah(total_invoice))

            teks_invoice = f"INVOICE\nTanggal: {tgl_invoice.strftime('%d-%m-%Y')}\nPelanggan: {nama_pelanggan or '-'}\n\n"
            for it in st.session_state.invoice_items:
                teks_invoice += f"- {it['Item']} x{it['Jumlah']} @ {format_rupiah(it['Harga Satuan'])} = {format_rupiah(it['Subtotal'])}\n"
            teks_invoice += f"\nTOTAL: {format_rupiah(total_invoice)}\nTerima kasih!"

            st.text_area("Pratinjau invoice (bisa disalin)", teks_invoice, height=220)
            st.download_button("⬇️ Unduh invoice (.txt)", teks_invoice, file_name=f"invoice_{nama_pelanggan or 'pelanggan'}.txt")

            if st.button("🗑️ Kosongkan daftar item"):
                st.session_state.invoice_items = []
                st.rerun()
        else:
            st.info("Belum ada item. Tambahkan lewat form di atas.")

    # ---------------- 4. Ingat Stok ----------------
    elif menu == "📦 Ingat Stok":
        st.markdown("**Catat stok barang supaya tidak kehabisan mendadak.**")
        with st.form("form_stok", clear_on_submit=True):
            colA, colB, colC = st.columns(3)
            nama_barang = colA.text_input("Nama barang")
            jumlah_stok = colB.number_input("Jumlah saat ini", min_value=0, step=1, value=10)
            batas_min = colC.number_input("Batas minimum (peringatan)", min_value=0, step=1, value=3)
            simpan_stok = st.form_submit_button("💾 Simpan / perbarui")
            if simpan_stok and nama_barang:
                ada = False
                for s in st.session_state.stok:
                    if s["Barang"].lower() == nama_barang.lower():
                        s["Jumlah"] = jumlah_stok
                        s["Batas Minimum"] = batas_min
                        ada = True
                if not ada:
                    st.session_state.stok.append({"Barang": nama_barang, "Jumlah": jumlah_stok, "Batas Minimum": batas_min})

        if st.session_state.stok:
            df_stok = pd.DataFrame(st.session_state.stok)
            st.dataframe(df_stok, use_container_width=True, hide_index=True)
            menipis = df_stok[df_stok["Jumlah"] <= df_stok["Batas Minimum"]]
            for _, row in menipis.iterrows():
                st.warning(f"⚠️ Stok **{row['Barang']}** diperkirakan menipis (sisa {row['Jumlah']}).")
        else:
            st.info("Belum ada barang yang dicatat.")

    # ---------------- 5. Utang Pelanggan ----------------
    elif menu == "💳 Utang Pelanggan":
        st.markdown("**Catat siapa saja yang masih punya utang ke usahamu.**")
        with st.form("form_utang", clear_on_submit=True):
            colA, colB = st.columns(2)
            nama_pel = colA.text_input("Nama pelanggan")
            jml_utang = colB.number_input("Jumlah utang (Rp)", min_value=0, step=5000, value=50000)
            simpan_utang = st.form_submit_button("💾 Catat utang")
            if simpan_utang and nama_pel:
                st.session_state.utang.append({"Nama": nama_pel, "Jumlah": jml_utang, "Status": "Belum Lunas", "Tanggal": date.today().strftime("%Y-%m-%d")})

        if st.session_state.utang:
            for i, u in enumerate(st.session_state.utang):
                c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                c1.write(u["Nama"])
                c2.write(format_rupiah(u["Jumlah"]))
                c3.write(u["Status"])
                if u["Status"] == "Belum Lunas":
                    if c4.button("Lunas", key=f"lunas_{i}"):
                        st.session_state.utang[i]["Status"] = "Lunas"
                        st.rerun()
            total_belum_lunas = sum(u["Jumlah"] for u in st.session_state.utang if u["Status"] == "Belum Lunas")
            st.metric("Total utang belum lunas", format_rupiah(total_belum_lunas))
        else:
            st.info("Belum ada catatan utang pelanggan.")

    # ---------------- 6. Cek Pengeluaran ----------------
    elif menu == "💸 Cek Pengeluaran":
        st.markdown("**Catat pengeluaran usaha supaya gampang dipantau.**")
        with st.form("form_pengeluaran", clear_on_submit=True):
            colA, colB = st.columns(2)
            keterangan = colA.text_input("Untuk apa", placeholder="Contoh: Beli deterjen")
            jml_keluar = colB.number_input("Jumlah (Rp)", min_value=0, step=5000, value=25000)
            simpan_keluar = st.form_submit_button("💾 Catat pengeluaran")
            if simpan_keluar and keterangan:
                st.session_state.pengeluaran.append({"Tanggal": date.today().strftime("%Y-%m-%d"), "Keterangan": keterangan, "Jumlah": jml_keluar})

        if st.session_state.pengeluaran:
            df_keluar = pd.DataFrame(st.session_state.pengeluaran)
            st.dataframe(df_keluar, use_container_width=True, hide_index=True)
            st.metric("Total pengeluaran tercatat", format_rupiah(df_keluar["Jumlah"].sum()))
        else:
            st.info("Belum ada pengeluaran yang dicatat.")

    # ---------------- 7. Balas Pelanggan ----------------
    elif menu == "💬 Balas Pelanggan":
        st.markdown("**Contoh balasan siap kirim untuk pertanyaan pelanggan yang sering muncul.**")
        pertanyaan = st.selectbox("Pelanggan biasanya nanya...", [
            "Masih buka?", "Barang/jasa ini ready?", "Ongkos kirim berapa?",
            "Bisa bayar di tempat (COD)?", "Kapan bisa diambil/selesai?",
        ])
        nama_toko = st.text_input("Nama usahamu", value=nama_usaha if "nama_usaha" in dir() else "")
        detail = st.text_input("Detail tambahan (nama barang, jam buka, ongkir, dll — opsional)")

        template = {
            "Masih buka?": f"Halo, kak! {nama_toko or 'Kami'} masih buka kok{(' — ' + detail) if detail else ''}. Silakan mampir atau order ya 😊",
            "Barang/jasa ini ready?": f"Halo kak, untuk {detail or 'barang yang ditanyakan'} ready ya, bisa langsung order 🙏",
            "Ongkos kirim berapa?": f"Untuk ongkir {(' ke ' + detail) if detail else ''} nanti kami infokan setelah tahu alamat lengkap ya kak 🙏",
            "Bisa bayar di tempat (COD)?": "Bisa kak, kami menerima COD untuk area yang masih terjangkau ya 😊",
            "Kapan bisa diambil/selesai?": f"Perkiraan selesai {(detail or 'dalam 1-2 hari')} ya kak, nanti kami kabari kalau sudah siap 🙏",
        }
        st.text_area("Contoh balasan (bisa disalin)", template[pertanyaan], height=100)

    # ---------------- 8. Bikin Konten ----------------
    elif menu == "📱 Bikin Konten":
        st.markdown("**Buat caption promosi sederhana untuk Instagram/WhatsApp.**")
        nama_produk = st.text_input("Nama produk/jasa", placeholder="Contoh: Nasi Ayam Geprek")
        harga_produk = st.number_input("Harga (Rp)", min_value=0, step=1000, value=15000)
        keunggulan = st.text_input("Keunggulan singkat", placeholder="Contoh: pedasnya nampol, porsi banyak")
        promo = st.text_input("Promo (opsional)", placeholder="Contoh: beli 2 gratis es teh")

        caption = f"🔥 {nama_produk or 'Produk kamu'} — {format_rupiah(harga_produk)} 🔥\n\n"
        if keunggulan:
            caption += f"✨ {keunggulan}\n"
        if promo:
            caption += f"🎉 Promo: {promo}\n"
        caption += "\n📍 Order sekarang, stok terbatas!\n#UMKM #UsahaLokal"

        st.text_area("Contoh caption (bisa disalin)", caption, height=180)


# ====================================================================
# TAB 3 — UMKMGo
# ====================================================================
with tab_go:
    st.subheader("🚀 UMKMGo")
    st.write(
        "Buat pemilik usaha yang ingin mulai \"digital\" tapi bingung harus mulai dari mana. "
        "UMKMGo adalah jasa pendampingan digitalisasi usaha, dari langkah paling dasar sampai "
        "siap dipantau lewat dashboard."
    )
    st.caption("Catatan: harga di bawah adalah contoh/perkiraan awal, bisa disesuaikan lagi.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="paket-card">
        <h3>🌱 STARTER</h3>
        <div class="paket-harga">Rp150.000<span style="font-size:0.9rem;font-weight:400;">/sekali setup</span></div>
        """, unsafe_allow_html=True)
        st.write("Cocok untuk usaha yang belum punya kehadiran digital sama sekali.")
        for item in ["Google Business Profile", "WhatsApp Business", "Katalog digital", "Bantuan pasang QRIS", "Instagram bisnis", "Google Maps", "Menu digital"]:
            st.write(f"✅ {item}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="paket-card">
        <h3>🌿 GROWTH</h3>
        <div class="paket-harga">Rp300.000<span style="font-size:0.9rem;font-weight:400;">/bulan</span></div>
        """, unsafe_allow_html=True)
        st.write("Untuk usaha yang sudah online, tapi butuh dorongan supaya lebih ramai.")
        st.write("Semua di paket STARTER, ditambah:")
        for item in ["Konten promosi rutin", "Digital marketing dasar", "Laporan penjualan bulanan", "Evaluasi kepuasan pelanggan"]:
            st.write(f"✅ {item}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="paket-card">
        <h3>🌳 PRO</h3>
        <div class="paket-harga">Rp500.000<span style="font-size:0.9rem;font-weight:400;">/bulan</span></div>
        """, unsafe_allow_html=True)
        st.write("Untuk usaha yang siap naik kelas dan ingin memantau semuanya secara rapi.")
        st.write("Semua di paket GROWTH, ditambah:")
        for item in ["Dashboard pemantauan usaha", "Analisis performa usaha", "Monitoring rutin", "Sesi konsultasi berkala"]:
            st.write(f"✅ {item}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.info("💡 Paket ini bisa dipadukan dengan **UMKM Assistant** — jadi setelah usaha \"tampil\" secara digital lewat UMKMGo, urusan catat-mencatatnya tetap dibantu lewat Assistant.")


st.divider()
st.caption("Prototipe UMKMSehat — cek kesehatan usaha, admin digital (UMKM Assistant), dan pendampingan digitalisasi (UMKMGo).")
