import streamlit as st
import pandas as pd
import veritabani

def goster():
    st.title("🎚️ Kâr Artırma Simülatörü")
    st.caption("Kaydırıcıları oynat, 'ya şöyle yapsaydım' senaryosunun yıllık TL karşılığını canlı gör.")

    st.info("ℹ️ Buradaki rakamlar **bugünkü verinin yıllık izdüşümüdür** — kesin garanti değil, olası bir aralıktır. Gerçek sonuç saha koşullarına göre değişir. Amaç: hangi iyileştirmenin kabaca ne kadar değdiğini görmek.")

    veritabani.tablolari_olustur()
    ariza_df = veritabani.veri_oku("arizalar")
    uretim_df = veritabani.veri_oku("uretim")

    st.markdown("**Fabrika bilgileri** (hesabın temeli):")
    p1, p2 = st.columns(2)
    saatlik_uretim = p1.number_input("Makine saatte kaç parça üretir?", min_value=0.0, value=100.0, key="sim_saatlik")
    parca_kar = p2.number_input("Parça başı kâr (TL)", min_value=0.0, value=2.0, key="sim_parca_kar")

    # --- Mevcut yıllık kayıpları hesapla (kayıtlı veriden, yıla ölçekle) ---
    # Kayıtlar kısa bir dönemi kapsıyor; kabaca yıllığa çevirmek için basit oranlama yaparız.
    # Çift sayım olmasın diye: duruş kaybı (bakım) + fire kaybı (üretim) ayrı ayrı.

    # Duruş kaybı
    durus_saat = 0.0
    if not ariza_df.empty and {"ariza_baslangic", "ariza_bitis"}.issubset(ariza_df.columns):
        a = ariza_df.copy()
        a["bas"] = pd.to_datetime(a["ariza_baslangic"], errors="coerce")
        a["bit"] = pd.to_datetime(a["ariza_bitis"], errors="coerce")
        a = a.dropna(subset=["bas", "bit"])
        if not a.empty:
            durus_saat = ((a["bit"] - a["bas"]).dt.total_seconds() / 3600).sum()
    durus_kaybi = durus_saat * saatlik_uretim * parca_kar

    # Fire kaybı
    fire_adet = 0.0
    if not uretim_df.empty and "fire_adet" in uretim_df.columns:
        fire_adet = pd.to_numeric(uretim_df["fire_adet"], errors="coerce").fillna(0).sum()
    fire_kaybi = fire_adet * parca_kar

    if durus_kaybi == 0 and fire_kaybi == 0:
        st.warning("Simülasyon için Bakım (arıza/duruş) ve Üretim (fire) modüllerine veri girilmeli. Şu an hesaplanacak kayıp yok.")
        return

    st.markdown("---")
    st.subheader("🎛️ Senaryo Kaydırıcıları")
    st.caption("Her kaydırıcı: 'bu kaybı yüzde kaç azaltabilirim?' Gerçekçi hedefler koy — %100 azaltma mümkün değildir.")

    c1, c2 = st.columns(2)
    fire_azalt = c1.slider("♻️ Fireyi azalt (%)", 0, 80, 20,
                           help="Fire kaybını yüzde kaç düşürmeyi hedefliyorsun?")
    durus_azalt = c2.slider("⏸️ Duruşu azalt (%)", 0, 80, 20,
                            help="Arıza duruşlarını yüzde kaç düşürmeyi hedefliyorsun?")

    # --- Kazanç hesabı (dönemsel) ---
    fire_kazanc = fire_kaybi * (fire_azalt / 100)
    durus_kazanc = durus_kaybi * (durus_azalt / 100)
    donem_kazanc = fire_kazanc + durus_kazanc

    # Kayıtların kapsadığı gün sayısını tahmin et (yıla ölçeklemek için)
    gun_sayisi = _donem_gun_say(ariza_df, uretim_df)
    if gun_sayisi < 1:
        gun_sayisi = 1
    yillik_carpan = 365 / gun_sayisi

    yillik_orta = donem_kazanc * yillik_carpan
    yillik_alt = yillik_orta * 0.7   # olası minimum (temkinli)
    yillik_ust = yillik_orta * 1.0   # olası maksimum (bu dönem hızının aynen sürmesi)

    st.markdown("---")
    st.subheader("💰 Bu Senaryonun Yıllık Karşılığı")

    m1, m2 = st.columns(2)
    m1.metric("Fireden kazanç (dönem)", f"{fire_kazanc:,.0f} TL",
              help=f"Fireyi %{fire_azalt} azaltırsan bu kayıtların döneminde")
    m2.metric("Duruştan kazanç (dönem)", f"{durus_kazanc:,.0f} TL",
              help=f"Duruşu %{durus_azalt} azaltırsan bu kayıtların döneminde")

    st.success(
        f"🟢 Bu iki iyileştirmeyi birlikte yaparsan, olası yıllık kazanç: "
        f"**{yillik_alt:,.0f} – {yillik_ust:,.0f} TL** aralığında."
    )
    st.caption(
        f"Hesap: bu kayıtlar ~{gun_sayisi:,.0f} günü kapsıyor; dönem kazancı {donem_kazanc:,.0f} TL "
        f"→ yıla ölçeklendi. Alt sınır temkinli (×0.7), üst sınır bu dönem hızının aynen sürmesi varsayımı. "
        f"Gerçek sonuç saha koşullarına göre değişir."
    )

def _donem_gun_say(ariza_df, uretim_df):
    """Kayıtların kabaca kaç günü kapsadığını tahmin eder."""
    tarihler = []
    if not ariza_df.empty and "ariza_baslangic" in ariza_df.columns:
        tarihler += list(pd.to_datetime(ariza_df["ariza_baslangic"], errors="coerce").dropna())
    if not uretim_df.empty and "tarih" in uretim_df.columns:
        tarihler += list(pd.to_datetime(uretim_df["tarih"], errors="coerce").dropna())
    if len(tarihler) < 2:
        return 30  # veri azsa varsayılan olarak 1 ay kabul et
    return max((max(tarihler) - min(tarihler)).days, 1)