import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from fpdf import FPDF
import veritabani
import hesap_motoru
from moduller import ayarlar, aksiyon

# Font dosyalarının yolu: proje kökündeki fontlar/ klasörü
FONT_KLASORU = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fontlar")

TURKCE_FONT_VAR = False  # rapor_olustur içinde güncellenir
ANA_FONT = "Helvetica"   # rapor_olustur içinde güncellenir

def _fontlari_yukle(pdf):
    """DejaVu fontlarını PDF'e kaydeder. Dosyalar yoksa False döner (Helvetica'ya düşülür)."""
    normal = os.path.join(FONT_KLASORU, "DejaVuSans.ttf")
    kalin = os.path.join(FONT_KLASORU, "DejaVuSans-Bold.ttf")
    if not (os.path.exists(normal) and os.path.exists(kalin)):
        return False
    pdf.add_font("DejaVu", "", normal)
    pdf.add_font("DejaVu", "B", kalin)
    return True

def _tr(metin):
    """DejaVu varken dokunmadan döner; yoksa Türkçe karakterleri en yakın harfe çevirir."""
    if metin is None:
        return ""
    donusum = str(metin)
    if TURKCE_FONT_VAR:
        return donusum
    cevir = {"ı": "i", "İ": "I", "ş": "s", "Ş": "S", "ğ": "g", "Ğ": "G",
             "ç": "c", "Ç": "C", "ö": "o", "Ö": "O", "ü": "u", "Ü": "U",
             "â": "a", "î": "i", "û": "u"}
    for eski, yeni in cevir.items():
        donusum = donusum.replace(eski, yeni)
    return "".join(k for k in donusum if ord(k) < 256)

def _baslik(pdf, metin):
    pdf.ln(4)
    pdf.set_font(ANA_FONT, "B", 12)
    pdf.cell(0, 8, _tr(metin), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(ANA_FONT, "", 10)

def _sadelestir(metin):
    """Emoji ve markdown işaretlerini temizler."""
    temiz = str(metin).replace("**", "")
    return "".join(k for k in temiz if ord(k) < 0x2000).strip()

def _satirla(metin, sinir=95):
    """Uzun metni kelime kelime bölerek satır listesine çevirir."""
    kelimeler = metin.split()
    satirlar, aktif = [], ""
    for kelime in kelimeler:
        if len(aktif) + len(kelime) + 1 <= sinir:
            aktif = f"{aktif} {kelime}".strip()
        else:
            if aktif:
                satirlar.append(aktif)
            aktif = kelime
    if aktif:
        satirlar.append(aktif)
    return satirlar

def rapor_olustur(firma_adi, gun_araligi, bolumler):
    """Seçilen dönem ve bölümlerle PDF üretir, bytes döner."""
    global TURKCE_FONT_VAR, ANA_FONT

    baslangic = datetime.now() - timedelta(days=gun_araligi)

    pdf = FPDF()

    TURKCE_FONT_VAR = _fontlari_yukle(pdf)
    ANA_FONT = "DejaVu" if TURKCE_FONT_VAR else "Helvetica"

    pdf.add_page()

    # --- Başlık ---
    pdf.set_font(ANA_FONT, "B", 18)
    pdf.cell(0, 12, _tr("Fabrika Durum Raporu"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(ANA_FONT, "", 11)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 7, _tr(f"Firma: {firma_adi}"), new_x="LMARGIN", new_y="NEXT")
    donem_adi = {1: "Günlük", 7: "Haftalık", 30: "Aylık"}.get(gun_araligi, f"Son {gun_araligi} gün")
    pdf.cell(0, 7, _tr(f"Kapsam: {donem_adi} ({baslangic.strftime('%d.%m.%Y')} - {datetime.now().strftime('%d.%m.%Y')})"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # --- Sızıntı özeti (her raporda olur — ana mesaj) ---
    kalemler = hesap_motoru.sizinti_kalemleri()
    toplam = sum(k[1] for k in kalemler)
    pdf.set_font(ANA_FONT, "B", 14)
    pdf.set_fill_color(230, 57, 70)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, _tr(f"  Toplam Önlenebilir Sızıntı: {toplam:,.0f} TL"), new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(ANA_FONT, "", 10)

    if "Sızıntı kalemleri" in bolumler and kalemler:
        _baslik(pdf, "Sızıntı Kalemleri (büyükten küçüğe)")
        for i, (ad, tutar, aciklama, modul) in enumerate(kalemler, 1):
            pay = (tutar / toplam * 100) if toplam > 0 else 0
            pdf.cell(0, 6, _tr(f"{i}. {ad}: {tutar:,.0f} TL (%{pay:.0f})"), new_x="LMARGIN", new_y="NEXT")

    if "Fire dökümü" in bolumler:
        fire_tl, fire_detay = hesap_motoru.fire_kaybi_tl()
        if not fire_detay.empty:
            _baslik(pdf, "Fire Kaybı — Ürün Bazında")
            for _, r in fire_detay.iterrows():
                pdf.cell(0, 6, _tr(f"   {r['urun_kodu']}: {r['fire_adet']:,.0f} adet = {r['kayip_tl']:,.0f} TL"), new_x="LMARGIN", new_y="NEXT")

    if "Duruş dökümü" in bolumler:
        durus_tl, durus_detay = hesap_motoru.durus_kaybi_tl()
        if not durus_detay.empty:
            _baslik(pdf, "Duruş Kaybı — Makine Bazında")
            for _, r in durus_detay.iterrows():
                pdf.cell(0, 6, _tr(f"   {r['makine_id']}: {r['durus_saat']:,.1f} saat = {r['kayip_tl']:,.0f} TL"), new_x="LMARGIN", new_y="NEXT")

    if "Bakım durumu" in bolumler:
        makine_df = veritabani.veri_oku("makineler")
        if not makine_df.empty and "son_bakim_tarihi" in makine_df.columns:
            _baslik(pdf, "Bakım Durumu")
            bugun = datetime.now().date()
            for _, m in makine_df.iterrows():
                son = pd.to_datetime(m.get("son_bakim_tarihi"), errors="coerce")
                periyot = pd.to_numeric(m.get("bakim_periyodu_gun"), errors="coerce")
                if pd.isna(son) or pd.isna(periyot) or periyot <= 0:
                    continue
                sonraki = son.date() + timedelta(days=int(periyot))
                kalan = (sonraki - bugun).days
                mid = str(m.get("makine_id", "")).strip()
                if kalan < 0:
                    pdf.set_text_color(230, 57, 70)
                    pdf.cell(0, 6, _tr(f"   {mid}: bakım {abs(kalan)} gün GECİKTİ"), new_x="LMARGIN", new_y="NEXT")
                    pdf.set_text_color(0, 0, 0)
                elif kalan <= 14:
                    pdf.cell(0, 6, _tr(f"   {mid}: bakıma {kalan} gün kaldı"), new_x="LMARGIN", new_y="NEXT")

    if "Kritik stoklar" in bolumler:
        stok_df = veritabani.veri_oku("stok")
        if not stok_df.empty and {"malzeme_adi", "mevcut_miktar", "kritik_seviye"}.issubset(stok_df.columns):
            s = stok_df.copy()
            s["mevcut_miktar"] = pd.to_numeric(s["mevcut_miktar"], errors="coerce")
            s["kritik_seviye"] = pd.to_numeric(s["kritik_seviye"], errors="coerce")
            kritik = s[s["mevcut_miktar"] <= s["kritik_seviye"]].dropna(subset=["mevcut_miktar"])
            if not kritik.empty:
                _baslik(pdf, "Kritik Stoklar")
                for _, r in kritik.iterrows():
                    pdf.cell(0, 6, _tr(f"   {r['malzeme_adi']}: {r['mevcut_miktar']:,.0f} kaldı (kritik: {r['kritik_seviye']:,.0f}) — SİPARİŞ ZAMANI"), new_x="LMARGIN", new_y="NEXT")

    if "Aksiyon önerileri" in bolumler:
        try:
            oneriler = aksiyon._aksiyonlari_topla()
        except Exception:
            oneriler = []
        if oneriler:
            _baslik(pdf, "Öncelikli Aksiyonlar — Bu Hafta Ne Yapmalı?")
            for i, (kazanc, ad, adimlar, sayfa, aciliyet) in enumerate(oneriler[:3], 1):
                pdf.set_font(ANA_FONT, "B", 10)
                temiz_ad = _sadelestir(ad)
                if kazanc > 0:
                    ust_satir = f"{i}. {temiz_ad} (olası kazanç: {kazanc:,.0f} TL, aciliyet: {aciliyet})"
                else:
                    ust_satir = f"{i}. {temiz_ad} (aciliyet: {aciliyet})"
                for satir in _satirla(ust_satir, 85):
                    pdf.cell(0, 6, _tr(satir), new_x="LMARGIN", new_y="NEXT")

                pdf.set_font(ANA_FONT, "", 9)
                for adim in adimlar:
                    parcalar = _satirla(_sadelestir(adim), 105)
                    for j, satir in enumerate(parcalar):
                        onek = "- " if j == 0 else "  "
                        pdf.cell(0, 5, _tr(f"{onek}{satir}"), new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)
            pdf.set_font(ANA_FONT, "", 10)

    # --- Alt not ---
    pdf.ln(8)
    pdf.set_font(ANA_FONT, "", 8)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5, _tr(
        "Bu tutarlar kayıtlı verilerden hesaplanan olası minimum kayıplardır; kesin muhasebe rakamı değildir. "
        "Fabrika KDS tarafından otomatik üretilmiştir."
    ))

    return bytes(pdf.output())

def goster():
    st.title("📄 PDF Rapor")
    st.caption("Raporunu kendin tasarla: dönemi seç, hangi bölümler girsin işaretle, indir.")

    mevcut_ayar = ayarlar.ayarlari_oku()
    firma = st.text_input("Firma adı", value=mevcut_ayar["firma_adi"])

    st.markdown("**📅 Rapor dönemi:**")
    donem = st.radio("donem", ["Günlük", "Haftalık", "Aylık"], horizontal=True, index=2,
                     label_visibility="collapsed")
    gun_araligi = {"Günlük": 1, "Haftalık": 7, "Aylık": 30}[donem]

    st.markdown("**📋 Rapora girecek bölümler:**")
    b1, b2 = st.columns(2)
    bolumler = []
    if b1.checkbox("Sızıntı kalemleri", value=True): bolumler.append("Sızıntı kalemleri")
    if b1.checkbox("Fire dökümü (ürün bazında)", value=True): bolumler.append("Fire dökümü")
    if b1.checkbox("Duruş dökümü (makine bazında)", value=True): bolumler.append("Duruş dökümü")
    if b2.checkbox("Bakım durumu (geciken/yaklaşan)", value=True): bolumler.append("Bakım durumu")
    if b2.checkbox("Kritik stoklar", value=True): bolumler.append("Kritik stoklar")
    if b2.checkbox("Aksiyon önerileri (ne yapmalı?)", value=True): bolumler.append("Aksiyon önerileri")

    if st.button("📄 Raporu oluştur", type="primary"):
        try:
            pdf_bytes = rapor_olustur(firma, gun_araligi, bolumler)
            st.success("✅ Rapor hazır!")
            dosya_adi = f"fabrika_raporu_{donem.lower()}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button("⬇️ PDF'i indir", data=pdf_bytes, file_name=dosya_adi, mime="application/pdf")
        except Exception as e:
            st.error(f"❌ Rapor oluşturulamadı: {e}")