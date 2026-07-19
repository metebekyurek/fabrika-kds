import streamlit as st
import pandas as pd
import veritabani
import os
from datetime import datetime 

# Varsayılan değerler — kullanıcı hiç ayar girmemişse bunlar kullanılır
VARSAYILAN = {
    "firma_adi": "Fabrikam",
    "yonetici_mail": "",
    "tarife_gunduz": "2.85",
    "tarife_puant": "4.20",
    "tarife_gece": "1.60",
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
    st.markdown("---")
    st.markdown("**⚡ Elektrik Tarife Fiyatları (TL/kWh)**")
    st.caption("Elektrik faturandaki üç zamanlı tarife fiyatlarını bir kez gir — Enerji sayfası buradan okur. "
               "Fatura değişince burayı güncellemen yeterli.")

    t1, t2, t3 = st.columns(3)
    tarife_gunduz = t1.number_input("Gündüz (06-17)", min_value=0.0,
                                    value=float(mevcut["tarife_gunduz"]), step=0.05, format="%.2f")
    tarife_puant = t2.number_input("Puant / akşam (17-22)", min_value=0.0,
                                   value=float(mevcut["tarife_puant"]), step=0.05, format="%.2f")
    tarife_gece = t3.number_input("Gece (22-06)", min_value=0.0,
                                  value=float(mevcut["tarife_gece"]), step=0.05, format="%.2f")
    if st.button("💾 Ayarları kaydet"):
        yeni = pd.DataFrame([{
            "firma_adi": firma,
            "yonetici_mail": yonetici_mail,
            "tarife_gunduz": str(tarife_gunduz),
            "tarife_puant": str(tarife_puant),
            "tarife_gece": str(tarife_gece),
        }])
        veritabani.veri_kaydet("ayarlar", yeni)
        st.success("✅ Ayarlar kaydedildi!") 
        # ================= YEDEKLEME =================
    st.markdown("---")
    st.subheader("💾 Veri Yedekleme")
    st.caption("Tüm verilerin tek dosyada: fabrika.db. Düzenli yedek almak, olası kayıplara karşı sigortadır.")

    db_yolu = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fabrika.db")

    y1, y2 = st.columns(2)

    with y1:
        st.markdown("**Yedek al**")
        if os.path.exists(db_yolu):
            with open(db_yolu, "rb") as f:
                db_bytes = f.read()
            boyut_mb = len(db_bytes) / (1024 * 1024)
            st.download_button(
                "💾 Yedek dosyasını indir",
                data=db_bytes,
                file_name=f"fabrika_yedek_{datetime.now().strftime('%Y%m%d_%H%M')}.db",
                mime="application/octet-stream",
                help="İnen dosyayı USB'ye veya başka bir diske kopyala. Haftada bir yedek almak iyi alışkanlıktır."
            )
            st.caption(f"Veritabanı boyutu: {boyut_mb:.1f} MB")
        else:
            st.info("Henüz veritabanı dosyası oluşmamış — bir kayıt girince oluşur.")

    with y2:
        st.markdown("**Yedekten geri yükle**")
        st.caption("⚠️ Mevcut TÜM verilerin üzerine yazar — geri alınamaz!")
        yedek_dosya = st.file_uploader("Yedek dosyası seç (.db)", type=["db"], key="yedek_yukle")
        if yedek_dosya is not None:
            onay = st.checkbox("Mevcut verilerin silinip yedekteki verilerin geleceğini anladım", key="yedek_onay")
            if onay and st.button("📤 Yedeği geri yükle", type="primary"):
                try:
                    with open(db_yolu, "wb") as f:
                        f.write(yedek_dosya.getvalue())
                    st.success("✅ Yedek geri yüklendi! Verilerin yenilenmesi için uygulamayı kapatıp BASLAT.bat ile yeniden aç.")
                except Exception as e:
                    st.error(f"❌ Geri yükleme başarısız: {e}")