import streamlit as st
import pandas as pd
import veritabani

# Varsayılan değerler — kullanıcı hiç ayar girmemişse bunlar kullanılır
VARSAYILAN = {
    "firma_adi": "Fabrikam",
    "yonetici_mail": "",
}

def ayarlari_oku():
    """Kayıtlı fabrika ayarlarını sözlük olarak döner. Kayıt yoksa varsayılanları verir."""
    veritabani.tablolari_olustur()
    try:
        df = veritabani.veri_oku("ayarlar")
    except Exception:
        return VARSAYILAN.copy()

    if df.empty:
        return VARSAYILAN.copy()

    satir = df.iloc[-1]  # en son kaydedilen ayar
    sonuc = VARSAYILAN.copy()
    for anahtar in VARSAYILAN:
        if anahtar in df.columns:
            deger = satir.get(anahtar)
            if pd.notna(deger) and str(deger).strip() != "":
                sonuc[anahtar] = str(deger)
    return sonuc

def goster():
    st.title("⚙️ Fabrika Ayarları")
    st.caption("Fabrikana özel temel bilgiler. Bir kez gir — raporlar ve mailler buradan okusun.")

    st.info("💡 **Hesaplama değerleri burada değil:** Parça kârları 📦 **Ürünler** sayfasında (ürün bazlı), makine kapasiteleri ⚙️ **Makineler** sayfasında (makine bazlı) tanımlanır. Tüm TL hesapları oradan otomatik beslenir.")

    mevcut = ayarlari_oku()

    firma = st.text_input("Firma adı", value=mevcut["firma_adi"],
                          help="Raporlarda ve maillerde görünecek isim")
    yonetici_mail = st.text_input("Yönetici e-posta adresi", value=mevcut["yonetici_mail"],
                                  help="Günün özeti maili buraya gönderilecek")

    if st.button("💾 Ayarları kaydet"):
        yeni = pd.DataFrame([{
            "firma_adi": firma,
            "yonetici_mail": yonetici_mail,
        }])
        veritabani.veri_kaydet("ayarlar", yeni)
        st.success("✅ Ayarlar kaydedildi!")