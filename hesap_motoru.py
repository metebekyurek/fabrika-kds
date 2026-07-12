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
