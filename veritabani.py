import sqlite3
import pandas as pd

# Veritabanı dosyasının adı — proje klasöründe "fabrika.db" olarak yaşayacak
DB_DOSYA = "fabrika.db"


def baglan():
    """Veritabanına bağlantı açar."""
    return sqlite3.connect(DB_DOSYA)


def tablolari_olustur():
    """İlk çalıştırmada gerekli tabloları oluşturur (yoksa)."""
    conn = baglan()
    c = conn.cursor()

    # Arıza kayıtları tablosu (Bakım modülü)
    c.execute("""
        CREATE TABLE IF NOT EXISTS arizalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            makine_id TEXT,
            ariza_baslangic TEXT,
            ariza_bitis TEXT,
            ariza_tipi TEXT,
            aciklama TEXT,
            tamir_maliyeti_tl REAL
        )
    """)

    conn.commit()
    conn.close()


def veri_kaydet(tablo, df):
    """Bir DataFrame'i verilen tabloya yazar (eskisini silip yeniden yazar)."""
    conn = baglan()
    df.to_sql(tablo, conn, if_exists="replace", index=False)
    conn.close()


def veri_oku(tablo):
    """Bir tablodaki tüm veriyi DataFrame olarak okur. Tablo yoksa boş döner."""
    conn = baglan()
    try:
        df = pd.read_sql(f"SELECT * FROM {tablo}", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df