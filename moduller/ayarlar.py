import streamlit as st
import pandas as pd
import veritabani

# Varsayılan değerler — kullanıcı hiç ayar girmemişse bunlar kullanılır
VARSAYILAN = {
    "parca_kar_tl": 2.0,
    "saatlik_uretim": 100.0,
    "firma_adi": "Fabrikam",
    "yonetici_mail": "",
}

def ayarlari_oku():
    """Kayıtlı fabrika ayarlarını sözlük olarak döner. Kayıt yoksa varsayılanları verir.
    TÜM MODÜLLER bu fonksiyonu kullanacak — değerler tek yerden gelsin, çelişki olmasın."""
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
                # sayısal alanları sayıya çevir
                if anahtar in ["parca_kar_tl", "saatlik_uretim"]:
                    sayi = pd.to_numeric(deger, errors="coerce")
                    if pd.notna(sayi):
                        sonuc[anahtar] = float(sayi)
                else:
                    sonuc[anahtar] = str(deger)
    return sonuc

def goster():
    st.title("⚙️ Fabrika Ayarları")
    st.caption("Fabrikana özel sabit bilgiler. Bir kez gir — tüm modüller buradan okusun, her ekranda tekrar sorulmasın.")

    mevcut = ayarlari_oku()

    st.markdown("**Temel bilgiler**")
    firma = st.text_input("Firma adı", value=mevcut["firma_adi"],
                          help="Raporlarda ve maillerde görünecek isim")
    yonetici_mail = st.text_input("Yönetici e-posta adresi", value=mevcut["yonetici_mail"],
                                  help="Günün özeti maili buraya gönderilecek")

    st.markdown("**Hesaplama sabitleri**")
    st.caption("Bu iki değer, tüm modüllerdeki TL hesaplarının temelidir. Doğru girmek önemli.")

    a1, a2 = st.columns(2)
    parca_kar = a1.number_input("Parça başı kâr (TL)", min_value=0.0, value=float(mevcut["parca_kar_tl"]), step=0.5,
                                help="Ürettiğin bir parçadan ortalama kaç TL kâr ediyorsun? Fire ve duruş kayıpları bununla TL'ye çevrilir.")
    saatlik = a2.number_input("Saatlik üretim (adet/saat)", min_value=0.0, value=float(mevcut["saatlik_uretim"]), step=10.0,
                              help="Makinen saatte ortalama kaç parça üretir? Duruş kaybı bununla hesaplanır.")

    if st.button("💾 Ayarları kaydet"):
        yeni = pd.DataFrame([{
            "firma_adi": firma,
            "yonetici_mail": yonetici_mail,
            "parca_kar_tl": parca_kar,
            "saatlik_uretim": saatlik,
        }])
        veritabani.veri_kaydet("ayarlar", yeni)
        st.success("✅ Ayarlar kaydedildi! Artık tüm modüller bu değerleri kullanacak.")
        st.info("💡 Kâr Sızıntısı, Simülatör, PDF Rapor ve Günün Özeti Maili bu değerleri otomatik okuyacak — o ekranlarda ayrıca sorulmayacak.")

    st.markdown("---")
    st.markdown("**Şu an geçerli değerler:**")
    g1, g2 = st.columns(2)
    g1.metric("Parça başı kâr", f"{mevcut['parca_kar_tl']:,.2f} TL")
    g2.metric("Saatlik üretim", f"{mevcut['saatlik_uretim']:,.0f} adet/saat")