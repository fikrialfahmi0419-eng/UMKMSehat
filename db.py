"""
Modul kecil untuk menyambungkan UMKMSehat ke database Supabase (opsional).

Kalau kredensial belum diatur (lewat Streamlit Secrets), DB_READY akan
bernilai False dan aplikasi utama akan otomatis memakai penyimpanan
sementara (st.session_state) sebagai cadangan — supaya aplikasi tetap
bisa dicoba meski database belum disambungkan.
"""

import streamlit as st

DB_READY = False
_client = None

try:
    from supabase import create_client

    _url = st.secrets.get("SUPABASE_URL", None)
    _key = st.secrets.get("SUPABASE_KEY", None)

    if _url and _key:
        _client = create_client(_url, _key)
        DB_READY = True
except Exception:
    DB_READY = False
    _client = None


def get_client():
    return _client


def load_rows(table, nama_usaha, order_by="id"):
    """Ambil semua baris milik satu usaha dari sebuah tabel. Mengembalikan list of dict."""
    if not DB_READY:
        return []
    try:
        res = (
            _client.table(table)
            .select("*")
            .eq("nama_usaha", nama_usaha)
            .order(order_by)
            .execute()
        )
        return res.data or []
    except Exception as e:
        st.warning(f"Gagal memuat data dari database ({table}): {e}")
        return []


def insert_row(table, data: dict):
    """Tambah satu baris baru. Mengembalikan True/False sesuai berhasil atau tidak."""
    if not DB_READY:
        return False
    try:
        _client.table(table).insert(data).execute()
        return True
    except Exception as e:
        st.warning(f"Gagal menyimpan ke database ({table}): {e}")
        return False


def update_row(table, row_id, data: dict):
    """Perbarui satu baris berdasarkan id."""
    if not DB_READY:
        return False
    try:
        _client.table(table).update(data).eq("id", row_id).execute()
        return True
    except Exception as e:
        st.warning(f"Gagal memperbarui data ({table}): {e}")
        return False


def load_all_videos(order_by="id"):
    """Ambil semua video di katalog (tidak difilter per usaha — ini konten bersama)."""
    if not DB_READY:
        return []
    try:
        res = _client.table("video_konten").select("*").order(order_by).execute()
        return res.data or []
    except Exception as e:
        st.warning(f"Gagal memuat katalog video: {e}")
        return []


def upsert_stok(nama_usaha, nama_barang, jumlah, batas_minimum):
    """Tambah barang baru, atau perbarui kalau nama barang itu sudah ada untuk usaha ini."""
    if not DB_READY:
        return False
    try:
        _client.table("stok_barang").upsert(
            {
                "nama_usaha": nama_usaha,
                "nama_barang": nama_barang,
                "jumlah": jumlah,
                "batas_minimum": batas_minimum,
            },
            on_conflict="nama_usaha,nama_barang",
        ).execute()
        return True
    except Exception as e:
        st.warning(f"Gagal menyimpan stok: {e}")
        return False
