import streamlit as st
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import veritabani

def _tr(metin):
    """fpdf2'nin standart fontu bazı Türkçe karakterleri basamaz; onları en yakın harfe çevirir.
    (İleride DejaVu font eklersek bu fonksiyonu kaldıracağız — şimdilik güvenli yol.)"""
    if metin is None:
        return ""
    donusum = str(metin)
    cevir = {"ı": "i", "İ": "I", "ş": "s", "Ş": "S", "ğ": "g", "Ğ": "G",
             "ç": "c", "Ç": "C", "ö": "o", "Ö": "O", "ü": "u", "Ü": "U"}
    for eski, yeni in cevir.items():
        donusum = donusum.replace(eski, yeni)
    return donusum

def rapor_olustur(firma_adi, saatlik_uretim, parca_kar):
    """Kâr sızıntısı özetini tek sayfalık PDF olarak üretir, bytes döner."""
    veritabani.tablolari_olustur()
    ariza_df = veritabani.veri_oku("arizalar")
    uretim_df = veritabani.veri_oku("uretim")

    # --- Sızıntı kalemlerini hesapla (Kâr Sızıntısı modülüyle aynı mantık) ---
    kalemler = []

    if not ariza_df.empty and "tamir_maliyeti_tl" in ariza_df.columns:
        tamir = pd.to_numeric(ariza_df["tamir_maliyeti_tl"], errors="coerce").fillna(0).sum()
        if tamir > 0:
            kalemler.append(("Tamir giderleri", tamir))

    if not ariza_df.empty and {"ariza_baslangic", "ariza_bitis"}.issubset(ariza_df.columns):
        a = ariza_df.copy()
        a["bas"] = pd.to_datetime(a["ariza_baslangic"], errors="coerce")
        a["bit"] = pd.to_datetime(a["ariza_bitis"], errors="coerce")
        a = a.dropna(subset=["bas", "bit"])
        if not a.empty:
            durus_saat = ((a["bit"] - a["bas"]).dt.total_seconds() / 3600).sum()
            durus_kaybi = durus_saat * saatlik_uretim * parca_kar
            if durus_kaybi > 0:
                kalemler.append(("Durus kaynakli kacan kar", durus_kaybi))

    if not uretim_df.empty and "fire_adet" in uretim_df.columns:
        fire = pd.to_numeric(uretim_df["fire_adet"], errors="coerce").fillna(0).sum()
        fire_kaybi = fire * parca_kar
        if fire_kaybi > 0:
            kalemler.append(("Fire kaybi", fire_kaybi))

    kalemler.sort(key=lambda x: x[1], reverse=True)
    toplam = sum(k[1] for k in kalemler)

    # --- PDF çiz ---
    pdf = FPDF()
    pdf.add_page()

    # Başlık
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, _tr("Kar Sizintisi Raporu"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 7, _tr(f"Firma: {firma_adi}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, _tr(f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # Toplam kutusu
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_fill_color(230, 57, 70)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, _tr(f"  Toplam Onlenebilir Sizinti: {toplam:,.0f} TL"), new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    # Kalem listesi
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, _tr("Sizinti Kalemleri (buyukten kucuge):"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 11)
    if kalemler:
        for i, (ad, tutar) in enumerate(kalemler, 1):
            pay = (tutar / toplam * 100) if toplam > 0 else 0
            pdf.cell(0, 8, _tr(f"{i}. {ad}: {tutar:,.0f} TL  (%{pay:.0f})"), new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.cell(0, 8, _tr("Henuz hesaplanacak sizinti verisi yok."), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)

    # Alt not
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5, _tr(
        "Bu tutarlar kayitli verilerden hesaplanan olasi minimum kayiplardir; kesin muhasebe "
        "rakami degildir. Fabrika KDS tarafindan otomatik uretilmistir."
    ))

    # bytes olarak döndür
    return bytes(pdf.output())

def goster():
    st.title("📄 PDF Rapor")
    st.caption("Kâr sızıntısı özetini tek sayfalık, paylaşılabilir bir PDF'e dök. Ziyaretten sonra masada kalan somut çıktı.")

    firma = st.text_input("Firma adı (raporda görünecek)", value="Örnek Fabrika A.Ş.")
    p1, p2 = st.columns(2)
    saatlik = p1.number_input("Makine saatte kaç parça üretir?", min_value=0.0, value=100.0, key="pdf_saatlik")
    kar = p2.number_input("Parça başı kâr (TL)", min_value=0.0, value=2.0, key="pdf_kar")

    if st.button("📄 Raporu oluştur"):
        try:
            pdf_bytes = rapor_olustur(firma, saatlik, kar)
            st.success("✅ Rapor hazır! Aşağıdaki butondan indir.")
            dosya_adi = f"kar_sizintisi_raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button("⬇️ PDF'i indir", data=pdf_bytes, file_name=dosya_adi, mime="application/pdf")
        except Exception as e:
            st.error(f"❌ Rapor oluşturulamadı: {e}")