"""
FABRİKA KDS — HESAP MOTORU
Tüm TL hesapları burada yapılır. Modüller elle değer sormaz, buradan çeker.
Böylece hiçbir ekran birbiriyle çelişmez.
"""
import pandas as pd
import veritabani

def _temizle(seri):
    """Kod/ID alanlarını karşılaştırmaya hazırlar: boşluk kırp, büyük harf."""
    return seri.astype(str).str.strip().str.upper()

def urun_karlari():
    """Ürün kodu -> parça başı kâr sözlüğü döner. Örn: {'URN-A': 2.0, 'URN-B': 5.5}"""
    veritabani.tablolari_olustur()
    df = veritabani.veri_oku("urunler")
    if df.empty or not {"urun_kodu", "parca_kar_tl"}.issubset(df.columns):
        return {}
    d = df.copy()
    d["urun_kodu"] = _temizle(d["urun_kodu"])
    d["parca_kar_tl"] = pd.to_numeric(d["parca_kar_tl"], errors="coerce")
    d = d.dropna(subset=["urun_kodu", "parca_kar_tl"])
    return dict(zip(d["urun_kodu"], d["parca_kar_tl"]))

def makine_kapasiteleri():
    """Makine ID -> saatlik kapasite sözlüğü. Örn: {'PRES-01': 100, 'CNC-01': 60}"""
    df = veritabani.veri_oku("makineler")
    if df.empty or not {"makine_id", "saatlik_kapasite"}.issubset(df.columns):
        return {}
    d = df.copy()
    d["makine_id"] = _temizle(d["makine_id"])
    d["saatlik_kapasite"] = pd.to_numeric(d["saatlik_kapasite"], errors="coerce")
    d = d.dropna(subset=["makine_id", "saatlik_kapasite"])
    return dict(zip(d["makine_id"], d["saatlik_kapasite"]))

def fire_kaybi_tl():
    """Toplam fire kaybını TL olarak hesaplar.
    Her fire kaydı, KENDİ ürününün kârıyla çarpılır — bu tam doğru hesaptır.
    Döner: (toplam_tl, detay_df)"""
    uretim = veritabani.veri_oku("uretim")
    karlar = urun_karlari()

    if uretim.empty or not {"urun_kodu", "fire_adet"}.issubset(uretim.columns) or not karlar:
        return 0.0, pd.DataFrame()

    u = uretim.copy()
    u["urun_kodu"] = _temizle(u["urun_kodu"])
    u["fire_adet"] = pd.to_numeric(u["fire_adet"], errors="coerce").fillna(0)
    u["parca_kar"] = u["urun_kodu"].map(karlar)
    u = u.dropna(subset=["parca_kar"])  # kârı tanımlı olmayan ürünleri sayma
    u["fire_kaybi_tl"] = u["fire_adet"] * u["parca_kar"]

    detay = u.groupby("urun_kodu").agg(
        fire_adet=("fire_adet", "sum"),
        kayip_tl=("fire_kaybi_tl", "sum"),
    ).reset_index().sort_values("kayip_tl", ascending=False)

    return float(u["fire_kaybi_tl"].sum()), detay

def makine_agirlikli_kar(makine_id):
    """Bir makinenin ürettiği ürün karışımına göre AĞIRLIKLI ortalama parça kârı.
    Makine durunca 'ne üretemedi' bilinemez; en dürüst tahmin, o makinenin
    gerçekte bastığı ürün karışımının ortalamasıdır. Veri yoksa None döner."""
    uretim = veritabani.veri_oku("uretim")
    karlar = urun_karlari()

    if uretim.empty or not karlar or not {"makine_id", "urun_kodu", "uretilen_adet"}.issubset(uretim.columns):
        return None

    u = uretim.copy()
    u["makine_id"] = _temizle(u["makine_id"])
    u["urun_kodu"] = _temizle(u["urun_kodu"])
    u["uretilen_adet"] = pd.to_numeric(u["uretilen_adet"], errors="coerce").fillna(0)
    u = u[u["makine_id"] == str(makine_id).strip().upper()]
    u["parca_kar"] = u["urun_kodu"].map(karlar)
    u = u.dropna(subset=["parca_kar"])

    toplam_adet = u["uretilen_adet"].sum()
    if toplam_adet <= 0:
        return None

    # Ağırlıklı ortalama: (adet × kâr) toplamı ÷ toplam adet
    return float((u["uretilen_adet"] * u["parca_kar"]).sum() / toplam_adet)

def durus_kaybi_tl():
    """Arıza duruşlarının TL karşılığı.
    Her arıza, KENDİ makinesinin kapasitesi ve o makinenin ağırlıklı kârıyla hesaplanır.
    Döner: (toplam_tl, detay_df)"""
    ariza = veritabani.veri_oku("arizalar")
    kapasiteler = makine_kapasiteleri()

    if ariza.empty or not {"makine_id", "ariza_baslangic", "ariza_bitis"}.issubset(ariza.columns):
        return 0.0, pd.DataFrame()

    a = ariza.copy()
    a["makine_id"] = _temizle(a["makine_id"])
    a["bas"] = pd.to_datetime(a["ariza_baslangic"], errors="coerce")
    a["bit"] = pd.to_datetime(a["ariza_bitis"], errors="coerce")
    a = a.dropna(subset=["bas", "bit"])
    if a.empty:
        return 0.0, pd.DataFrame()

    a["durus_saat"] = (a["bit"] - a["bas"]).dt.total_seconds() / 3600

    kayitlar = []
    for makine_id, grup in a.groupby("makine_id"):
        kapasite = kapasiteler.get(makine_id)
        kar = makine_agirlikli_kar(makine_id)
        if kapasite is None or kar is None:
            continue  # bilgi eksikse uydurmuyoruz, atlıyoruz
        saat = grup["durus_saat"].sum()
        kayip = saat * kapasite * kar
        kayitlar.append({
            "makine_id": makine_id,
            "durus_saat": saat,
            "kapasite": kapasite,
            "agirlikli_kar": kar,
            "kayip_tl": kayip,
        })

    if not kayitlar:
        return 0.0, pd.DataFrame()

    detay = pd.DataFrame(kayitlar).sort_values("kayip_tl", ascending=False)
    return float(detay["kayip_tl"].sum()), detay

def tamir_gideri_tl():
    """Toplam tamir maliyeti (doğrudan veriden)."""
    ariza = veritabani.veri_oku("arizalar")
    if ariza.empty or "tamir_maliyeti_tl" not in ariza.columns:
        return 0.0
    return float(pd.to_numeric(ariza["tamir_maliyeti_tl"], errors="coerce").fillna(0).sum())

def sizinti_kalemleri():
    """Tüm sızıntı kalemlerini tek listede döner: [(ad, tutar, aciklama, modul), ...]"""
    kalemler = []

    tamir = tamir_gideri_tl()
    if tamir > 0:
        kalemler.append(("🛠️ Tamir giderleri", tamir, "Arıza kayıtlarındaki tamir maliyetleri toplamı", "Bakım"))

    durus_tl, durus_detay = durus_kaybi_tl()
    if durus_tl > 0:
        saat = durus_detay["durus_saat"].sum()
        kalemler.append(("⏸️ Duruş kaynaklı kaçan kâr", durus_tl,
                         f"Toplam {saat:,.1f} saat duruş · her makine kendi kapasitesi ve ürün karışımıyla hesaplandı", "Bakım"))

    fire_tl, fire_detay = fire_kaybi_tl()
    if fire_tl > 0:
        adet = fire_detay["fire_adet"].sum()
        kalemler.append(("♻️ Fire kaybı", fire_tl,
                         f"{adet:,.0f} adet fire · her ürün kendi kârıyla hesaplandı", "Üretim"))

    kalemler.sort(key=lambda x: x[1], reverse=True)
    return kalemler
def vardiya_kiyasi():
    """Gece/gündüz vardiya karşılaştırması — fire oranı farkını TL'ye çevirir.
    Döner: (detay_df, aylik_fark_tl) veya (boş, 0)"""
    uretim = veritabani.veri_oku("uretim")
    karlar = urun_karlari()

    gerekli = {"vardiya", "urun_kodu", "uretilen_adet", "fire_adet"}
    if uretim.empty or not gerekli.issubset(uretim.columns) or not karlar:
        return pd.DataFrame(), 0.0

    u = uretim.copy()
    u["urun_kodu"] = _temizle(u["urun_kodu"])
    u["vardiya"] = u["vardiya"].astype(str).str.strip().str.lower()
    u["uretilen_adet"] = pd.to_numeric(u["uretilen_adet"], errors="coerce").fillna(0)
    u["fire_adet"] = pd.to_numeric(u["fire_adet"], errors="coerce").fillna(0)
    u["parca_kar"] = u["urun_kodu"].map(karlar)
    u = u.dropna(subset=["parca_kar"])
    u = u[u["vardiya"].isin(["gündüz", "gece"])]

    if u.empty or u["vardiya"].nunique() < 2:
        return pd.DataFrame(), 0.0

    u["fire_kaybi"] = u["fire_adet"] * u["parca_kar"]

    ozet = u.groupby("vardiya").agg(
        uretim=("uretilen_adet", "sum"),
        fire=("fire_adet", "sum"),
        fire_kaybi_tl=("fire_kaybi", "sum"),
    ).reset_index()
    ozet["fire_orani"] = ozet["fire"] / (ozet["uretim"] + ozet["fire"]) * 100

    # Kötü vardiya iyi vardiyanın fire ORANINA inseydi, kaç TL kurtarırdı?
    iyi = ozet.loc[ozet["fire_orani"].idxmin()]
    kotu = ozet.loc[ozet["fire_orani"].idxmax()]
    if kotu["fire"] > 0 and kotu["fire_orani"] > iyi["fire_orani"]:
        hedef_fire = (kotu["uretim"] + kotu["fire"]) * iyi["fire_orani"] / 100
        onlenebilir_adet = kotu["fire"] - hedef_fire
        ort_kar = kotu["fire_kaybi_tl"] / kotu["fire"]
        fark_tl = onlenebilir_adet * ort_kar
    else:
        fark_tl = 0.0

    return ozet, float(fark_tl)
def stok_gecikme_riski():
    """Kritik seviyedeki stoklar için: 'stok biterse ve tedarik gecikirse kaç TL kayıp?' tahmini.
    Mantık: kritik stok kaç gün yeter + tedarikçi ortalama gecikmesi = açıkta kalınan gün.
    Açık gün × fabrikanın günlük ortalama üretim kâr kaybı = risk TL.
    Döner: (detay_df, toplam_risk_tl)"""
    stok = veritabani.veri_oku("stok")
    tedarik = veritabani.veri_oku("tedarikciler")
    uretim = veritabani.veri_oku("uretim")
    karlar = urun_karlari()

    gerekli = {"malzeme_adi", "mevcut_miktar", "kritik_seviye", "gunluk_tuketim"}
    if stok.empty or not gerekli.issubset(stok.columns):
        return pd.DataFrame(), 0.0

    s = stok.copy()
    for kol in ["mevcut_miktar", "kritik_seviye", "gunluk_tuketim"]:
        s[kol] = pd.to_numeric(s[kol], errors="coerce")
    s = s.dropna(subset=["mevcut_miktar", "kritik_seviye"])

    # Sadece kritik seviyede/altında olanlar risk taşır
    kritikler = s[s["mevcut_miktar"] <= s["kritik_seviye"]].copy()
    if kritikler.empty:
        return pd.DataFrame(), 0.0

    # Tedarikçilerin genel ortalama gecikmesi (veri yoksa temkinli 3 gün varsay)
    ort_gecikme = 3.0
    if not tedarik.empty and "ortalama_gecikme_gun" in tedarik.columns:
        g = pd.to_numeric(tedarik["ortalama_gecikme_gun"], errors="coerce").dropna()
        if len(g) > 0:
            ort_gecikme = float(g.mean())

    # Fabrikanın günlük ortalama kâr üretimi (son kayıtlardan)
    gunluk_kar = 0.0
    if not uretim.empty and {"tarih", "urun_kodu", "uretilen_adet"}.issubset(uretim.columns) and karlar:
        u = uretim.copy()
        u["urun_kodu"] = _temizle(u["urun_kodu"])
        u["uretilen_adet"] = pd.to_numeric(u["uretilen_adet"], errors="coerce").fillna(0)
        u["parca_kar"] = u["urun_kodu"].map(karlar)
        u = u.dropna(subset=["parca_kar"])
        u["tarih"] = pd.to_datetime(u["tarih"], errors="coerce")
        u = u.dropna(subset=["tarih"])
        if not u.empty:
            gun_sayisi = max((u["tarih"].max() - u["tarih"].min()).days, 1)
            toplam_kar = (u["uretilen_adet"] * u["parca_kar"]).sum()
            gunluk_kar = toplam_kar / gun_sayisi

    if gunluk_kar <= 0:
        return pd.DataFrame(), 0.0

    kayitlar = []
    for _, r in kritikler.iterrows():
        gunluk_tuk = r["gunluk_tuketim"] if pd.notna(r["gunluk_tuketim"]) and r["gunluk_tuketim"] > 0 else None
        kalan_gun = (r["mevcut_miktar"] / gunluk_tuk) if gunluk_tuk else 0
        acik_gun = max(ort_gecikme - kalan_gun, 0)
        # Temkinli varsayım: bu malzemenin bitmesi üretimin TAMAMINI değil,
        # kabaca dörtte birini durdurur (tek malzeme her üretimi durdurmaz)
        risk_tl = acik_gun * gunluk_kar * 0.25
        if risk_tl > 0:
            kayitlar.append({
                "malzeme": r["malzeme_adi"],
                "kalan_gun": round(kalan_gun, 1),
                "tedarik_gecikme_gun": round(ort_gecikme, 1),
                "acikta_kalinan_gun": round(acik_gun, 1),
                "risk_tl": round(risk_tl, 0),
            })

    if not kayitlar:
        return pd.DataFrame(), 0.0

    detay = pd.DataFrame(kayitlar).sort_values("risk_tl", ascending=False)
    return detay, float(detay["risk_tl"].sum())
def donem_kiyasi(gun_sayisi=30):
    """Son X gün ile ondan önceki X günü kıyaslar.
    Döner: {metrik_adi: (bu_donem, onceki_donem, degisim_yuzde)} sözlüğü."""
    from datetime import datetime, timedelta

    uretim = veritabani.veri_oku("uretim")
    ariza = veritabani.veri_oku("arizalar")
    karlar = urun_karlari()

    bugun = datetime.now()
    bu_baslangic = bugun - timedelta(days=gun_sayisi)
    onceki_baslangic = bugun - timedelta(days=gun_sayisi * 2)

    sonuc = {}

    # --- Üretim & Fire ---
    if not uretim.empty and {"tarih", "uretilen_adet", "fire_adet"}.issubset(uretim.columns):
        u = uretim.copy()
        u["tarih"] = pd.to_datetime(u["tarih"], errors="coerce")
        u["uretilen_adet"] = pd.to_numeric(u["uretilen_adet"], errors="coerce").fillna(0)
        u["fire_adet"] = pd.to_numeric(u["fire_adet"], errors="coerce").fillna(0)
        u = u.dropna(subset=["tarih"])

        bu = u[u["tarih"] >= bu_baslangic]
        onceki = u[(u["tarih"] >= onceki_baslangic) & (u["tarih"] < bu_baslangic)]

        sonuc["Üretim (adet)"] = (bu["uretilen_adet"].sum(), onceki["uretilen_adet"].sum())
        sonuc["Fire (adet)"] = (bu["fire_adet"].sum(), onceki["fire_adet"].sum())

        # Fire TL (ürün bazlı)
        if karlar and "urun_kodu" in u.columns:
            for df_, ad in [(bu, "bu"), (onceki, "on")]:
                pass
            def fire_tl(df_):
                d = df_.copy()
                d["urun_kodu"] = _temizle(d["urun_kodu"])
                d["kar"] = d["urun_kodu"].map(karlar)
                d = d.dropna(subset=["kar"])
                return (d["fire_adet"] * d["kar"]).sum()
            sonuc["Fire Kaybı (TL)"] = (fire_tl(bu), fire_tl(onceki))

    # --- Tamir gideri & Duruş ---
    if not ariza.empty and "ariza_baslangic" in ariza.columns:
        a = ariza.copy()
        a["bas"] = pd.to_datetime(a["ariza_baslangic"], errors="coerce")
        a = a.dropna(subset=["bas"])
        if "tamir_maliyeti_tl" in a.columns:
            a["tamir"] = pd.to_numeric(a["tamir_maliyeti_tl"], errors="coerce").fillna(0)
            bu_a = a[a["bas"] >= bu_baslangic]
            onceki_a = a[(a["bas"] >= onceki_baslangic) & (a["bas"] < bu_baslangic)]
            sonuc["Tamir Gideri (TL)"] = (bu_a["tamir"].sum(), onceki_a["tamir"].sum())
            sonuc["Arıza Sayısı"] = (len(bu_a), len(onceki_a))
        if "ariza_bitis" in a.columns:
            a["bit"] = pd.to_datetime(a["ariza_bitis"], errors="coerce")
            a2 = a.dropna(subset=["bit"])
            a2["durus_saat"] = (a2["bit"] - a2["bas"]).dt.total_seconds() / 3600
            bu_a = a2[a2["bas"] >= bu_baslangic]
            onceki_a = a2[(a2["bas"] >= onceki_baslangic) & (a2["bas"] < bu_baslangic)]
            sonuc["Duruş (saat)"] = (bu_a["durus_saat"].sum(), onceki_a["durus_saat"].sum())

    # Yüzde değişimleri ekle
    final = {}
    for ad, (simdi, once) in sonuc.items():
        if once > 0:
            degisim = (simdi - once) / once * 100
        elif simdi > 0:
            degisim = 100.0
        else:
            degisim = 0.0
        final[ad] = (float(simdi), float(once), float(degisim))

    return final
def takvim_ay_kiyasi():
    """Takvim bazlı kıyas: bu ay (1'inden bugüne) ↔ geçen ayın tamamı.
    Patron dilinde 'geçen ay' budur — kayan 30 gün değil."""
    from datetime import datetime

    bugun = datetime.now()
    bu_ay_bas = bugun.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # Geçen ayın başı: bu ayın başından 1 gün geri git, o günün ayının 1'i
    gecen_ay_son = bu_ay_bas - pd.Timedelta(days=1)
    gecen_ay_bas = gecen_ay_son.replace(day=1)

    uretim = veritabani.veri_oku("uretim")
    ariza = veritabani.veri_oku("arizalar")
    karlar = urun_karlari()

    sonuc = {}

    if not uretim.empty and {"tarih", "uretilen_adet", "fire_adet"}.issubset(uretim.columns):
        u = uretim.copy()
        u["tarih"] = pd.to_datetime(u["tarih"], errors="coerce")
        u["uretilen_adet"] = pd.to_numeric(u["uretilen_adet"], errors="coerce").fillna(0)
        u["fire_adet"] = pd.to_numeric(u["fire_adet"], errors="coerce").fillna(0)
        u = u.dropna(subset=["tarih"])

        bu = u[u["tarih"] >= bu_ay_bas]
        onceki = u[(u["tarih"] >= gecen_ay_bas) & (u["tarih"] < bu_ay_bas)]

        sonuc["Üretim (adet)"] = (bu["uretilen_adet"].sum(), onceki["uretilen_adet"].sum())
        sonuc["Fire (adet)"] = (bu["fire_adet"].sum(), onceki["fire_adet"].sum())

        if karlar and "urun_kodu" in u.columns:
            def fire_tl(df_):
                d = df_.copy()
                d["urun_kodu"] = _temizle(d["urun_kodu"])
                d["kar"] = d["urun_kodu"].map(karlar)
                d = d.dropna(subset=["kar"])
                return (d["fire_adet"] * d["kar"]).sum()
            sonuc["Fire Kaybı (TL)"] = (fire_tl(bu), fire_tl(onceki))

    if not ariza.empty and "ariza_baslangic" in ariza.columns:
        a = ariza.copy()
        a["bas"] = pd.to_datetime(a["ariza_baslangic"], errors="coerce")
        a = a.dropna(subset=["bas"])
        if "tamir_maliyeti_tl" in a.columns:
            a["tamir"] = pd.to_numeric(a["tamir_maliyeti_tl"], errors="coerce").fillna(0)
            bu_a = a[a["bas"] >= bu_ay_bas]
            on_a = a[(a["bas"] >= gecen_ay_bas) & (a["bas"] < bu_ay_bas)]
            sonuc["Tamir Gideri (TL)"] = (bu_a["tamir"].sum(), on_a["tamir"].sum())
            sonuc["Arıza Sayısı"] = (len(bu_a), len(on_a))
        if "ariza_bitis" in a.columns:
            a["bit"] = pd.to_datetime(a["ariza_bitis"], errors="coerce")
            a2 = a.dropna(subset=["bit"]).copy()
            a2["durus_saat"] = (a2["bit"] - a2["bas"]).dt.total_seconds() / 3600
            bu_a = a2[a2["bas"] >= bu_ay_bas]
            on_a = a2[(a2["bas"] >= gecen_ay_bas) & (a2["bas"] < bu_ay_bas)]
            sonuc["Duruş (saat)"] = (bu_a["durus_saat"].sum(), on_a["durus_saat"].sum())

    final = {}
    for ad, (simdi, once) in sonuc.items():
        if once > 0:
            degisim = (simdi - once) / once * 100
        elif simdi > 0:
            degisim = 100.0
        else:
            degisim = 0.0
        final[ad] = (float(simdi), float(once), float(degisim))
    return final
def ozel_aralik_kiyasi(bas_tarih, bit_tarih):
    """Kullanıcının takvimden seçtiği aralık ↔ aynı uzunlukta bir önceki aralık.
    Örn: 1-15 Mart seçildiyse, önceki dönem 14-28 Şubat olur."""
    from datetime import datetime, timedelta

    bu_bas = pd.to_datetime(bas_tarih)
    # Bitiş gününün TAMAMI dahil olsun diye 1 gün ekliyoruz
    bu_bit = pd.to_datetime(bit_tarih) + pd.Timedelta(days=1)
    uzunluk = bu_bit - bu_bas
    on_bas = bu_bas - uzunluk
    on_bit = bu_bas

    uretim = veritabani.veri_oku("uretim")
    ariza = veritabani.veri_oku("arizalar")
    karlar = urun_karlari()

    sonuc = {}

    if not uretim.empty and {"tarih", "uretilen_adet", "fire_adet"}.issubset(uretim.columns):
        u = uretim.copy()
        u["tarih"] = pd.to_datetime(u["tarih"], errors="coerce")
        u["uretilen_adet"] = pd.to_numeric(u["uretilen_adet"], errors="coerce").fillna(0)
        u["fire_adet"] = pd.to_numeric(u["fire_adet"], errors="coerce").fillna(0)
        u = u.dropna(subset=["tarih"])

        bu = u[(u["tarih"] >= bu_bas) & (u["tarih"] < bu_bit)]
        onceki = u[(u["tarih"] >= on_bas) & (u["tarih"] < on_bit)]

        sonuc["Üretim (adet)"] = (bu["uretilen_adet"].sum(), onceki["uretilen_adet"].sum())
        sonuc["Fire (adet)"] = (bu["fire_adet"].sum(), onceki["fire_adet"].sum())

        if karlar and "urun_kodu" in u.columns:
            def fire_tl(df_):
                d = df_.copy()
                d["urun_kodu"] = _temizle(d["urun_kodu"])
                d["kar"] = d["urun_kodu"].map(karlar)
                d = d.dropna(subset=["kar"])
                return (d["fire_adet"] * d["kar"]).sum()
            sonuc["Fire Kaybı (TL)"] = (fire_tl(bu), fire_tl(onceki))

    if not ariza.empty and "ariza_baslangic" in ariza.columns:
        a = ariza.copy()
        a["bas"] = pd.to_datetime(a["ariza_baslangic"], errors="coerce")
        a = a.dropna(subset=["bas"])
        if "tamir_maliyeti_tl" in a.columns:
            a["tamir"] = pd.to_numeric(a["tamir_maliyeti_tl"], errors="coerce").fillna(0)
            bu_a = a[(a["bas"] >= bu_bas) & (a["bas"] < bu_bit)]
            on_a = a[(a["bas"] >= on_bas) & (a["bas"] < on_bit)]
            sonuc["Tamir Gideri (TL)"] = (bu_a["tamir"].sum(), on_a["tamir"].sum())
            sonuc["Arıza Sayısı"] = (len(bu_a), len(on_a))
        if "ariza_bitis" in a.columns:
            a["bit"] = pd.to_datetime(a["ariza_bitis"], errors="coerce")
            a2 = a.dropna(subset=["bit"]).copy()
            a2["durus_saat"] = (a2["bit"] - a2["bas"]).dt.total_seconds() / 3600
            bu_a = a2[(a2["bas"] >= bu_bas) & (a2["bas"] < bu_bit)]
            on_a = a2[(a2["bas"] >= on_bas) & (a2["bas"] < on_bit)]
            sonuc["Duruş (saat)"] = (bu_a["durus_saat"].sum(), on_a["durus_saat"].sum())

    final = {}
    for ad, (simdi, once) in sonuc.items():
        if once > 0:
            degisim = (simdi - once) / once * 100
        elif simdi > 0:
            degisim = 100.0
        else:
            degisim = 0.0
        final[ad] = (float(simdi), float(once), float(degisim))
    return final