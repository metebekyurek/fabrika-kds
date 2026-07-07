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
# Üretim kayıtları (Üretim modülü)
    c.execute("""
        CREATE TABLE IF NOT EXISTS uretim (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT, vardiya TEXT, makine_id TEXT, operator_id TEXT,
            urun_kodu TEXT, hedef_adet REAL, uretilen_adet REAL,
            fire_adet REAL, fire_nedeni TEXT
        )
    """)

    # Enerji faturaları (Enerji modülü)
    c.execute("""
        CREATE TABLE IF NOT EXISTS enerji (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donem TEXT, toplam_tuketim_kwh REAL, toplam_tutar_tl REAL
        )
    """)

    # Stok kartları (Stok modülü)
    c.execute("""
        CREATE TABLE IF NOT EXISTS stok (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            malzeme_adi TEXT, tur TEXT, birim TEXT,
            mevcut_miktar REAL, kritik_seviye REAL,
            gunluk_tuketim REAL, birim_maliyet_tl REAL
        )
    """)

    # Tedarikçiler (Stok modülü)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tedarikciler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tedarikci TEXT, malzeme TEXT,
            birim_fiyat_tl REAL, ortalama_gecikme_gun REAL
        )
    """)
    # Makine Kimlik Kartları
    c.execute("""
        CREATE TABLE IF NOT EXISTS makineler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            makine_id TEXT, makine_adi TEXT, makine_tipi TEXT,
            marka TEXT, model TEXT, uretim_yili REAL,
            motor_gucu_kw REAL, saatlik_kapasite REAL,
            max_yag_sicakligi_c REAL, max_titresim_mm_s REAL, max_motor_akimi_a REAL,
            bakim_periyodu_saat REAL
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