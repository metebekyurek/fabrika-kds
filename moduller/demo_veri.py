import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
import veritabani

def _urunler():
    return pd.DataFrame([
        {"urun_kodu": "SAC-BRK", "urun_adi": "Sac braket", "parca_kar_tl": 2.40},
        {"urun_kodu": "LZR-PNL", "urun_adi": "Lazer kesim panel", "parca_kar_tl": 6.80},
        {"urun_kodu": "MIL-30", "urun_adi": "Çelik mil 30mm", "parca_kar_tl": 12.50},
        {"urun_kodu": "FLNS-A", "urun_adi": "Flanş A tipi", "parca_kar_tl": 8.20},
        {"urun_kodu": "KPK-15", "urun_adi": "Kapak 15cm", "parca_kar_tl": 3.10},
        {"urun_kodu": "GVD-M8", "urun_adi": "Gövde M8 bağlantı", "parca_kar_tl": 4.75},
        {"urun_kodu": "PRF-L", "urun_adi": "Profil L köşebent", "parca_kar_tl": 1.90},
        {"urun_kodu": "DSL-K", "urun_adi": "Dişli kasnak", "parca_kar_tl": 18.00},
    ])

def _makineler():
    veri = [
        ("PRES-01", "Hidrolik Pres 1", "pres", "Durma", "DHP-200", 2018, 15, 100, 70, 4.5, 32, 500, 16, 90),
        ("PRES-02", "Hidrolik Pres 2", "pres", "Durma", "DHP-160", 2016, 11, 85, 70, 4.5, 28, 500, 16, 90),
        ("PRES-03", "Eksantrik Pres", "pres", "Sahinler", "EP-60", 2014, 7.5, 120, 65, 5.0, 22, 400, 8, 60),
        ("CNC-01", "CNC Torna 1", "CNC", "Haas", "ST-20", 2020, 22, 60, 65, 2.8, 45, 400, 16, 60),
        ("CNC-02", "CNC Torna 2", "CNC", "Haas", "ST-10", 2019, 18, 55, 65, 2.8, 38, 400, 8, 60),
        ("CNC-03", "CNC İşleme Merkezi", "CNC", "Mazak", "VCN-410", 2021, 30, 40, 60, 2.5, 55, 350, 16, 45),
        ("LZR-01", "Fiber Lazer Kesim", "diğer", "Trumpf", "TL-3000", 2022, 45, 35, 55, 2.0, 70, 300, 16, 45),
        ("LZR-02", "CO2 Lazer", "diğer", "Bystronic", "BY-2000", 2015, 38, 25, 60, 2.5, 60, 300, 8, 60),
        ("TRN-01", "Universal Torna", "torna", "TOS", "SN-500", 2010, 7.5, 30, 70, 6.0, 20, 600, 8, 120),
        ("TRN-02", "Universal Torna 2", "torna", "TOS", "SN-400", 2008, 5.5, 25, 70, 6.0, 18, 600, 8, 120),
        ("FRZ-01", "Freze Tezgahı", "diğer", "Bridgeport", "BR-2", 2012, 5.5, 20, 68, 5.5, 16, 500, 8, 90),
        ("KYK-01", "Kaynak Robotu", "diğer", "Fanuc", "ARC-100", 2021, 12, 45, 60, 3.0, 35, 350, 16, 60),
        ("BKM-01", "Büküm Presi", "pres", "Baykal", "APHS-3100", 2017, 18, 70, 65, 4.0, 40, 450, 8, 75),
        ("TSF-01", "Testere Kesim", "diğer", "Kesmak", "KS-350", 2013, 4, 90, 70, 5.0, 14, 600, 8, 120),
        ("MTK-01", "Matkap Ünitesi", "diğer", "Yerli", "MT-25", 2011, 3, 150, 72, 5.5, 12, 700, 8, 150),
    ]
    kolonlar = ["makine_id", "makine_adi", "makine_tipi", "marka", "model", "uretim_yili",
                "motor_gucu_kw", "saatlik_kapasite", "max_yag_sicakligi_c", "max_titresim_mm_s",
                "max_motor_akimi_a", "bakim_periyodu_saat", "gunluk_calisma_saat", "bakim_periyodu_gun"]
    df = pd.DataFrame(veri, columns=kolonlar)

    # Son bakım tarihleri: bazıları gecikmiş, bazıları yaklaşan, bazıları rahat
    bugun = datetime.now().date()
    gecmisler = [130, 115, 100, 75, 70, 65, 55, 50, 45, 40, 35, 25, 20, 12, 5]
    df["son_bakim_tarihi"] = [str(bugun - timedelta(days=g)) for g in gecmisler]
    return df

def _uretim():
    """Son 60 günün üretim kayıtları — makineler farklı ürünler basıyor (sahadaki gerçek)."""
    makine_urun = {
        "PRES-01": ["SAC-BRK", "KPK-15", "PRF-L"],
        "PRES-02": ["SAC-BRK", "GVD-M8"],
        "PRES-03": ["PRF-L", "KPK-15"],
        "CNC-01": ["MIL-30", "DSL-K"],
        "CNC-02": ["MIL-30", "FLNS-A"],
        "CNC-03": ["DSL-K", "FLNS-A", "MIL-30"],
        "LZR-01": ["LZR-PNL", "SAC-BRK"],
        "LZR-02": ["LZR-PNL"],
        "TRN-01": ["MIL-30", "GVD-M8"],
        "TRN-02": ["GVD-M8"],
        "FRZ-01": ["FLNS-A", "DSL-K"],
        "KYK-01": ["SAC-BRK", "PRF-L"],
        "BKM-01": ["KPK-15", "SAC-BRK"],
        "TSF-01": ["PRF-L"],
        "MTK-01": ["GVD-M8", "KPK-15"],
    }
    kapasiteler = dict(zip(_makineler()["makine_id"], _makineler()["saatlik_kapasite"]))
    operatorler = ["OP-01", "OP-02", "OP-03", "OP-04", "OP-05", "OP-06", "OP-07"]
    fire_nedenleri = ["ayar", "hammadde", "kalıp", "operatör", "diğer"]

    random.seed(42)  # her seferinde aynı veri çıksın
    kayitlar = []
    bugun = datetime.now().date()

    for gun_geri in range(60, 0, -1):
        tarih = bugun - timedelta(days=gun_geri)
        if tarih.weekday() == 6:  # pazar kapalı
            continue
        # her gün rastgele 5-9 makine çalışsın
        calisan = random.sample(list(makine_urun.keys()), random.randint(5, 9))
        for makine in calisan:
            vardiya = random.choice(["gündüz", "gece"])
            urun = random.choice(makine_urun[makine])
            kapasite = kapasiteler[makine]
            planlanan = 480
            durus = random.randint(0, 90)
            ideal_hiz = round(kapasite / 60, 2)  # adet/dakika
            teorik = (planlanan - durus) * ideal_hiz
            uretilen = int(teorik * random.uniform(0.78, 0.96))
            fire = int(uretilen * random.uniform(0.01, 0.06))
            kayitlar.append({
                "tarih": str(tarih),
                "vardiya": vardiya,
                "makine_id": makine,
                "operator_id": random.choice(operatorler),
                "urun_kodu": urun,
                "hedef_adet": int(teorik * 0.95),
                "uretilen_adet": uretilen,
                "fire_adet": fire,
                "fire_nedeni": random.choice(fire_nedenleri),
                "planlanan_sure_dk": planlanan,
                "durus_dk": durus,
                "ideal_hiz_adet_dk": ideal_hiz,
            })
    return pd.DataFrame(kayitlar)

def _arizalar():
    """Son 60 günün arıza kayıtları — bazı makineler daha çok bozuluyor."""
    random.seed(7)
    ariza_tipleri = ["mekanik", "elektrik", "hidrolik", "yazılım", "diğer"]
    aciklamalar = {
        "mekanik": ["rulman sesi", "kayış koptu", "yatak aşınması", "mil boşluğu"],
        "elektrik": ["motor sigortası attı", "kontaktör arızası", "kablo teması", "panoda kısa devre"],
        "hidrolik": ["yağ sızıntısı", "valf arızası", "basınç düşüşü", "pompa arızası"],
        "yazılım": ["kontrol paneli dondu", "program hatası", "sensör okumuyor"],
        "diğer": ["sıkışma", "malzeme takıldı", "ayar bozuldu"],
    }
    # Arıza sıklığı: eski makineler daha çok bozulur
    ariza_agirlik = {
        "TRN-02": 6, "TRN-01": 5, "PRES-03": 5, "MTK-01": 4, "FRZ-01": 4,
        "LZR-02": 4, "PRES-02": 3, "TSF-01": 3, "CNC-02": 2, "BKM-01": 2,
        "PRES-01": 2, "CNC-01": 2, "KYK-01": 1, "CNC-03": 1, "LZR-01": 1,
    }
    tamir_araligi = {
        "TRN-02": (800, 3000), "TRN-01": (900, 3500), "PRES-03": (1500, 6000),
        "MTK-01": (500, 2000), "FRZ-01": (1000, 4000), "LZR-02": (3000, 12000),
        "PRES-02": (2000, 8000), "TSF-01": (600, 2500), "CNC-02": (2500, 9000),
        "BKM-01": (2000, 7000), "PRES-01": (2500, 9000), "CNC-01": (3000, 11000),
        "KYK-01": (2000, 8000), "CNC-03": (4000, 15000), "LZR-01": (5000, 18000),
    }

    kayitlar = []
    bugun = datetime.now().date()
    for makine, adet in ariza_agirlik.items():
        for _ in range(adet):
            gun_geri = random.randint(1, 60)
            tarih = bugun - timedelta(days=gun_geri)
            saat = random.randint(6, 20)
            sure = random.choice([1, 2, 3, 4, 6, 8, 12])
            bas = datetime.combine(tarih, datetime.min.time()) + timedelta(hours=saat)
            bit = bas + timedelta(hours=sure)
            tip = random.choice(ariza_tipleri)
            alt, ust = tamir_araligi[makine]
            kayitlar.append({
                "makine_id": makine,
                "ariza_baslangic": bas.strftime("%Y-%m-%d %H:%M"),
                "ariza_bitis": bit.strftime("%Y-%m-%d %H:%M"),
                "ariza_tipi": tip,
                "aciklama": random.choice(aciklamalar[tip]),
                "tamir_maliyeti_tl": random.randint(alt, ust),
            })
    return pd.DataFrame(kayitlar)

def _stok():
    return pd.DataFrame([
        {"malzeme_adi": "5mm sac levha", "tur": "hammadde", "birim": "kg", "mevcut_miktar": 1200, "kritik_seviye": 500, "gunluk_tuketim": 150, "birim_maliyet_tl": 45},
        {"malzeme_adi": "3mm sac levha", "tur": "hammadde", "birim": "kg", "mevcut_miktar": 380, "kritik_seviye": 400, "gunluk_tuketim": 90, "birim_maliyet_tl": 42},
        {"malzeme_adi": "Ç1040 çelik çubuk", "tur": "hammadde", "birim": "kg", "mevcut_miktar": 2400, "kritik_seviye": 800, "gunluk_tuketim": 200, "birim_maliyet_tl": 68},
        {"malzeme_adi": "M8 cıvata", "tur": "hammadde", "birim": "adet", "mevcut_miktar": 3000, "kritik_seviye": 1000, "gunluk_tuketim": 200, "birim_maliyet_tl": 2},
        {"malzeme_adi": "Kaynak teli", "tur": "hammadde", "birim": "kg", "mevcut_miktar": 85, "kritik_seviye": 100, "gunluk_tuketim": 12, "birim_maliyet_tl": 180},
        {"malzeme_adi": "Kesme diski", "tur": "hammadde", "birim": "adet", "mevcut_miktar": 45, "kritik_seviye": 60, "gunluk_tuketim": 8, "birim_maliyet_tl": 95},
        {"malzeme_adi": "Hidrolik yağ", "tur": "hammadde", "birim": "litre", "mevcut_miktar": 220, "kritik_seviye": 100, "gunluk_tuketim": 5, "birim_maliyet_tl": 320},
        {"malzeme_adi": "SAC-BRK mamul", "tur": "mamul", "birim": "adet", "mevcut_miktar": 1800, "kritik_seviye": 500, "gunluk_tuketim": 400, "birim_maliyet_tl": 28},
        {"malzeme_adi": "MIL-30 mamul", "tur": "mamul", "birim": "adet", "mevcut_miktar": 320, "kritik_seviye": 300, "gunluk_tuketim": 120, "birim_maliyet_tl": 145},
        {"malzeme_adi": "LZR-PNL mamul", "tur": "mamul", "birim": "adet", "mevcut_miktar": 640, "kritik_seviye": 250, "gunluk_tuketim": 180, "birim_maliyet_tl": 92},
    ])

def _enerji():
    return pd.DataFrame([
        {"donem": "2026-01", "toplam_tuketim_kwh": 42000, "toplam_tutar_tl": 119700},
        {"donem": "2026-02", "toplam_tuketim_kwh": 39500, "toplam_tutar_tl": 112575},
        {"donem": "2026-03", "toplam_tuketim_kwh": 45200, "toplam_tutar_tl": 128820},
        {"donem": "2026-04", "toplam_tuketim_kwh": 46800, "toplam_tutar_tl": 138060},
        {"donem": "2026-05", "toplam_tuketim_kwh": 51300, "toplam_tutar_tl": 158010},
        {"donem": "2026-06", "toplam_tuketim_kwh": 54700, "toplam_tutar_tl": 174 * 1000},
    ])

def goster():
    st.title("🎬 Demo Verisi Yükle")
    st.caption("Sistemi gerçekçi, dolu bir fabrika verisiyle doldur. Tanıtım ve deneme için.")

    st.warning("⚠️ **DİKKAT:** Bu işlem mevcut verilerinin üzerine yazar. Gerçek fabrika verin varsa önce yedekle!")

    st.markdown("""
    **Yüklenecek veri:**
    - ⚙️ **15 makine** (pres, CNC, lazer, torna, freze, kaynak robotu...)
    - 📦 **8 ürün** farklı parça kârlarıyla (1.90 TL – 18.00 TL)
    - 🔧 **~400 üretim kaydı** (son 60 gün, makineler farklı ürünler basıyor)
    - 🛠️ **~45 arıza kaydı** (eski makineler daha çok bozuluyor)
    - 📦 **10 stok kalemi** (bazıları kritik seviyede)
    - ⚡ **6 aylık enerji faturası**
    """)

    if st.button("🎬 Demo verisini yükle", type="primary"):
        with st.spinner("Veriler hazırlanıyor..."):
            veritabani.tablolari_olustur()
            veritabani.veri_kaydet("urunler", _urunler())
            veritabani.veri_kaydet("makineler", _makineler())
            veritabani.veri_kaydet("uretim", _uretim())
            veritabani.veri_kaydet("arizalar", _arizalar())
            veritabani.veri_kaydet("stok", _stok())
            veritabani.veri_kaydet("enerji", _enerji())
        st.success("✅ Demo verisi yüklendi! Artık tüm modüllerde dolu, gerçekçi veri var.")
        st.info("💡 Şimdi **💸 Kâr Sızıntısı**, **🎚️ Simülatör** ve **📄 PDF Rapor** sayfalarına bak — rakamlar gerçek bir fabrika ölçeğinde olacak.")
        st.balloons()