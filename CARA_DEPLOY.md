# Cara Membuat Prototipe Ini Bisa Diakses Banyak Orang (Gratis)

Prototipe ini dibuat dengan **Python + Streamlit**. Untuk mencobanya sendiri di komputer:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Aplikasi akan terbuka di browser lewat `http://localhost:8501` — tapi ini hanya bisa
diakses dari komputermu sendiri. Supaya orang lain (dosen, teman, calon pengguna) bisa
membukanya lewat internet, pakai **Streamlit Community Cloud** (gratis, tanpa perlu sewa server):

## Langkah-langkah

1. **Buat akun GitHub** (kalau belum punya) di https://github.com
2. **Buat repository baru** (bisa publik), lalu unggah 2 file ini ke dalamnya:
   - `app.py`
   - `requirements.txt`
   - Bisa lewat upload manual di web GitHub (tombol "Add file" → "Upload files"), tidak perlu paham Git dulu.
3. **Buka https://streamlit.io/cloud** dan daftar/masuk memakai akun GitHub kamu.
4. Klik **"New app"**, pilih repository yang tadi dibuat, pastikan file utama diarahkan ke `app.py`.
5. Klik **Deploy**. Tunggu 1-2 menit.
6. Streamlit akan memberikan alamat publik seperti:
   `https://nama-app-kamu.streamlit.app`
   Alamat ini bisa dibuka siapa saja lewat HP atau laptop, tanpa perlu install apa-apa.

## Catatan penting soal prototipe ini

- Data yang diisi pengguna **belum tersimpan permanen** — begitu halaman ditutup atau
  aplikasi dimuat ulang, riwayat pengecekan hilang. Untuk versi lanjutan, perlu ditambah
  database sederhana (misalnya Google Sheets atau database gratis seperti Supabase).
- Logika skor (batas margin 25%, rasio utang, dsb.) masih berupa **angka perkiraan awal**
  yang bisa disesuaikan lagi setelah diuji ke usaha kecil yang sesungguhnya.
- Sertifikat PDF, sesi konsultasi berbayar, dan integrasi dengan bank/koperasi belum
  dibuat di prototipe ini — itu tahap pengembangan berikutnya setelah konsep dasarnya
  terbukti berguna.
