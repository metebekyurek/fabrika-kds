import streamlit as st
from datetime import datetime
from fpdf import FPDF
import hesap_motoru
from moduller import ayarlar

def _tr(metin):
    """fpdf2'nin standart fontu bazı Türkçe karakterleri basamaz; en yakın harfe çevirir."""
    if metin is None:
        return ""
    donusum = str(metin)
    cevir = {"ı": "i", "İ": "I", "ş": "s", "Ş": "S", "ğ": "g", "Ğ": "G",
             "ç": "c", "Ç": "C", "ö": "o", "Ö": "O", "ü": "u", "Ü": "U",
             "â": "a", "î": "i", "û": "u"}
    for eski, yeni in cevir.items():
        donusum = donusum.replace(eski, yeni)
    # Emojileri temizle (PDF fontu basamaz)
    return "".join(k for k in donusum if ord(k) < 256)

def rapor_olustur(firma_adi):
    """Kâr sızıntısı özetini tek sayfalık PDF olarak üretir, bytes döner."""
    kalemler = hesap_motoru.sizinti_kalemleri()
    toplam = sum(k[1] for k in kalemler)

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, _tr("Kar Sizintisi Raporu"), new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 7, _tr(f"Firma: {firma_adi}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, _tr(f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_fill_color(230, 57, 70)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, _tr(f"  Toplam Onlenebilir Sizinti: {toplam:,.0f} TL"), new_x="LMARGIN", new_y="NEXT", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, _tr("Sizinti Kalemleri (buyukten kucuge):"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 11)
    if kalemler:
        for i, (ad, tutar, aciklama, modul) in enumerate(kalemler, 1):
            pay = (tutar / toplam * 100) if toplam > 0 else 0
            pdf.cell(0, 7, _tr(f"{i}. {ad}: {tutar:,.0f} TL  (%{pay:.0f})"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(0, 5, _tr(f"     {aciklama}"), new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 11)
            pdf.ln(2)
    else:
        pdf.cell(0, 8, _tr("Henuz hesaplanacak sizinti verisi yok."), new_x="LMARGIN", new_y="NEXT")

    # Detay: fire ürün bazında
    fire_tl, fire_detay = hesap_motoru.fire_kaybi_tl()
    if not fire_detay.empty:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, _tr("Fire kaybi - urun bazinda:"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for _, r in fire_detay.iterrows():
            pdf.cell(0, 6, _tr(f"   {r['urun_kodu']}: {r['fire_adet']:,.0f} adet = {r['kayip_tl']:,.0f} TL"),
                     new_x="LMARGIN", new_y="NEXT")

    # Detay: duruş makine bazında
    durus_tl, durus_detay = hesap_motoru.durus_kaybi_tl()
    if not durus_detay.empty:
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, _tr("Durus kaybi - makine bazinda:"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        for _, r in durus_detay.iterrows():
            pdf.cell(0, 6, _tr(f"   {r['makine_id']}: {r['durus_saat']:,.1f} saat durus = {r['kayip_tl']:,.0f} TL"),
                     new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 5, _tr(
        "Bu tutarlar kayitli verilerden hesaplanan olasi minimum kayiplardir; kesin muhasebe "
        "rakami degildir. Her fire kendi urununun kariyla, her durus o makinenin kendi kapasitesi "
        "ve gercekte bastigi urun karisimiyla hesaplanmistir. Fabrika KDS tarafindan otomatik uretilmistir."
    ))

    return bytes(pdf.output())

def goster():
    st.title("📄 PDF Rapor")
    st.caption("Kâr sızıntısı özetini tek sayfalık, paylaşılabilir bir PDF'e dök. Ziyaretten sonra masada kalan somut çıktı.")

    mevcut_ayar = ayarlar.ayarlari_oku()
    firma = st.text_input("Firma adı (raporda görünecek)", value=mevcut_ayar["firma_adi"])
    st.caption("💡 Firma adını ⚙️ Fabrika Ayarları'ndan kalıcı olarak değiştirebilirsin.")

    if st.button("📄 Raporu oluştur"):
        try:
            pdf_bytes = rapor_olustur(firma)
            st.success("✅ Rapor hazır! Aşağıdaki butondan indir.")
            dosya_adi = f"kar_sizintisi_raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button("⬇️ PDF'i indir", data=pdf_bytes, file_name=dosya_adi, mime="application/pdf")
        except Exception as e:
            st.error(f"❌ Rapor oluşturulamadı: {e}")