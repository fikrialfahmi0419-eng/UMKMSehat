-- ============================================================
-- Jalankan seluruh isi file ini di Supabase SQL Editor (sekali saja)
-- untuk membuat semua tabel yang dibutuhkan aplikasi UMKMSehat.
-- ============================================================

create table if not exists skor_usaha (
    id bigserial primary key,
    nama_usaha text not null,
    tanggal date not null default current_date,
    skor_penjualan numeric,
    skor_keuangan numeric,
    skor_operasional numeric,
    skor_total numeric,
    created_at timestamptz not null default now()
);

create table if not exists penjualan_harian (
    id bigserial primary key,
    nama_usaha text not null,
    tanggal date not null default current_date,
    jumlah_pelanggan text,
    omzet numeric not null default 0,
    estimasi_laba numeric not null default 0,
    produk_favorit text,
    created_at timestamptz not null default now()
);

create table if not exists stok_barang (
    id bigserial primary key,
    nama_usaha text not null,
    nama_barang text not null,
    jumlah numeric not null default 0,
    batas_minimum numeric not null default 0,
    updated_at timestamptz not null default now(),
    unique (nama_usaha, nama_barang)
);

create table if not exists utang_pelanggan (
    id bigserial primary key,
    nama_usaha text not null,
    nama_pelanggan text not null,
    jumlah numeric not null default 0,
    status text not null default 'Belum Lunas',
    tanggal date not null default current_date,
    created_at timestamptz not null default now()
);

create table if not exists pengeluaran (
    id bigserial primary key,
    nama_usaha text not null,
    tanggal date not null default current_date,
    keterangan text,
    jumlah numeric not null default 0,
    created_at timestamptz not null default now()
);

-- Katalog video pendampingan. Tabel ini BUKAN milik satu usaha (nama_usaha
-- tidak dipakai di sini) -- videonya sama dan bisa ditonton oleh semua
-- pengguna aplikasi, seperti daftar isi perpustakaan video bersama.
create table if not exists video_konten (
    id bigserial primary key,
    judul text not null,
    kategori text not null default 'Keuangan',
    url_video text,
    deskripsi text,
    tag_masalah text,
    premium boolean not null default false,
    created_at timestamptz not null default now()
);

-- Mengizinkan akses baca/tulis dari aplikasi (pakai anon key).
-- Ini pengaturan paling sederhana untuk prototipe; untuk versi produksi
-- sebaiknya diperketat lagi dengan aturan RLS yang lebih spesifik.
alter table skor_usaha enable row level security;
alter table penjualan_harian enable row level security;
alter table stok_barang enable row level security;
alter table utang_pelanggan enable row level security;
alter table pengeluaran enable row level security;
alter table video_konten enable row level security;

create policy "izinkan semua - skor_usaha" on skor_usaha for all using (true) with check (true);
create policy "izinkan semua - penjualan_harian" on penjualan_harian for all using (true) with check (true);
create policy "izinkan semua - stok_barang" on stok_barang for all using (true) with check (true);
create policy "izinkan semua - utang_pelanggan" on utang_pelanggan for all using (true) with check (true);
create policy "izinkan semua - pengeluaran" on pengeluaran for all using (true) with check (true);
create policy "izinkan semua - video_konten" on video_konten for all using (true) with check (true);
