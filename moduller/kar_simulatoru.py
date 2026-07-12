import streamlit as st
import pandas as pd
import veritabani
import hesap_motoru

def goster():
    st.title("🎚️ Kâr Artırma Simülatörü")
    st.caption("Kaydırıcıları oynat, 'ya şöyle yapsaydım' senaryosunun yıllık TL karşılığını canlı gör.")

    st.info("ℹ️ Rakamlar **bugünkü verinin yıllık izdüşümüdür** — kesin garanti değil, olası bir aralıktır. Tüm hesaplar kayıtlı verilerinden yapılır; elle değer girmene gerek yok.")

    fire_kaybi, _ = hesap_motoru.fire_kaybi_tl()
    durus_kaybi, _ = hesap_motoru.durus_kaybi_tl()

    if fire_kaybi == 0 and durus_kaybi == 0:
        st.warning("Simülasyon için veri yok.")
        st.markdown("""
        **Gerekenler:**
        - 📦 **Ürünler** sayfasında parça kârları tanımlı olmalı
        - ⚙️ **Makineler** sayfasında saatlik kapasite girilmiş olmalı
        - 🔧 **Üretim** ve 🛠️ **Bakım** modüllerinde kayıt olmalı
        """)
        return

    st.markdown("**Mevcut durum (kayıtlı verinden):**")
    d1, d2 = st.columns(2)
    d1.metric("♻️ Fire kaybı", f"{fire_kaybi:,.0f} TL")
    d2.metric("⏸️ Duruş kaybı", f"{durus_kaybi:,.0f} TL")

    st.markdown("---")
    st.subheader("🎛️ Senaryo Kaydırıcıları")
    st.caption("Her kaydırıcı: 'bu kaybı yüzde kaç azaltabilirim?' Gerçekçi hedefler koy — %100 azaltma mümkün değildir.")

    c1, c2 = st.columns(2)
    fire_azalt = c1.slider("♻️ Fireyi azalt (%)", 0, 80, 20)
    durus_azalt = c2.slider("⏸️ Duruşu azalt (%)", 0, 80, 20)

    fire_kazanc = fire_kaybi * (fire_azalt / 100)
    durus_kazanc = durus_kaybi * (durus_azalt / 100)
    donem_kazanc = fire_kazanc + durus_kazanc

    gun_sayisi = _donem_gun_say()
    yillik_carpan = 365 / max(gun_sayisi, 1)

    yillik_orta = donem_kazanc * yillik_carpan
    yillik_alt = yillik_orta * 0.7
    yillik_ust = yillik_orta * 1.0

    st.markdown("---")
    st.subheader("💰 Bu Senaryonun Yıllık Karşılığı")

    m1, m2 = st.columns(2)
    m1.metric("Fireden kazanç (dönem)", f"{fire_kazanc:,.0f} TL")
    m2.metric("Duruştan kazanç (dönem)", f"{durus_kazanc:,.0f} TL")

    st.success(f"🟢 Bu iki iyileştirmeyi birlikte yaparsan, olası yıllık kazanç: "
               f"**{yillik_alt:,.0f} – {yillik_ust:,.0f} TL** aralığında.")
    st.caption(f"Hesap: bu kayıtlar ~{gun_sayisi:,.0f} günü kapsıyor; dönem kazancı {donem_kazanc:,.0f} TL → yıla ölçeklendi. "
               f"Alt sınır temkinli (×0.7). Gerçek sonuç saha koşullarına göre değişir.")

def _donem_gun_say():
    """Kayıtların kabaca kaç günü kapsadığını tahmin eder."""
    tarihler = []
    ariza = veritabani.veri_oku("arizalar")
    uretim = veritabani.veri_oku("uretim")
    if not ariza.empty and "ariza_baslangic" in ariza.columns:
        tarihler += list(pd.to_datetime(ariza["ariza_baslangic"], errors="coerce").dropna())
    if not uretim.empty and "tarih" in uretim.columns:
        tarihler += list(pd.to_datetime(uretim["tarih"], errors="coerce").dropna())
    if len(tarihler) < 2:
        return 30
    return max((max(tarihler) - min(tarihler)).days, 1)