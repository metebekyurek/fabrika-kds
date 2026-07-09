import streamlit as st
import pandas as pd
import veritabani

def goster():
    st.title("💸 Kâr Sızıntısı Haritası")
    st.caption("Tüm modüllerdeki kayıplar tek ekranda, TL cinsinden, büyükten küçüğe. Paran nereden sızıyor?")

    veritabani.tablolari_olustur()
    ariza_df = veritabani.veri_oku("arizalar")
    uretim_df = veritabani.veri_oku("uretim")

    st.markdown("**Hesap için iki bilgi** (fabrikana göre doldur):")
    p1, p2 = st.columns(2)
    saatlik_uretim = p1.number_input("Makine saatte kaç parça üretir?", min_value=0.0, value=100.0, key="ksh_saatlik")
    parca_kar = p2.number_input("Parça başı kâr (TL)", min_value=0.0, value=2.0, key="ksh_parca_kar")

    sizintilar = []  # (kalem, tutar, açıklama, hangi modül)

    # 1) Tamir giderleri
    if not ariza_df.empty and "tamir_maliyeti_tl" in ariza_df.columns:
        tamir = pd.to_numeric(ariza_df["tamir_maliyeti_tl"], errors="coerce").fillna(0).sum()
        if tamir > 0:
            sizintilar.append(("🛠️ Tamir giderleri", tamir,
                               f"{len(ariza_df)} arıza kaydının toplam tamir maliyeti", "Bakım"))

    # 2) Duruş kaynaklı kaçan kâr
    if not ariza_df.empty and {"ariza_baslangic", "ariza_bitis"}.issubset(ariza_df.columns):
        a = ariza_df.copy()
        a["bas"] = pd.to_datetime(a["ariza_baslangic"], errors="coerce")
        a["bit"] = pd.to_datetime(a["ariza_bitis"], errors="coerce")
        a = a.dropna(subset=["bas", "bit"])
        if not a.empty:
            durus_saat = ((a["bit"] - a["bas"]).dt.total_seconds() / 3600).sum()
            durus_kaybi = durus_saat * saatlik_uretim * parca_kar
            if durus_kaybi > 0:
                sizintilar.append(("⏸️ Duruş kaynaklı kaçan kâr", durus_kaybi,
                                   f"Toplam {durus_saat:,.1f} saat duruş × {saatlik_uretim:,.0f} adet/saat × {parca_kar:,.2f} TL", "Bakım"))

    # 3) Fire kaybı
    if not uretim_df.empty and "fire_adet" in uretim_df.columns:
        fire = pd.to_numeric(uretim_df["fire_adet"], errors="coerce").fillna(0).sum()
        fire_kaybi = fire * parca_kar
        if fire_kaybi > 0:
            sizintilar.append(("♻️ Fire kaybı", fire_kaybi,
                               f"{fire:,.0f} adet fire × {parca_kar:,.2f} TL", "Üretim"))

    # 4) Enerji: puant israfı (isteğe bağlı giriş)
    st.markdown("---")
    with st.expander("⚡ Enerji puant israfını da eklemek istersen (isteğe bağlı)"):
        e1, e2, e3 = st.columns(3)
        kaydirilabilir = e1.number_input("Geceye kaydırılabilir tüketim (kWh/ay)", min_value=0.0, value=0.0, key="ksh_kwh")
        mevcut_f = e2.number_input("Şu anki fiyat (TL/kWh)", min_value=0.0, value=4.20, key="ksh_mevcut")
        gece_f = e3.number_input("Gece fiyatı (TL/kWh)", min_value=0.0, value=1.60, key="ksh_gece")
        puant_israf = kaydirilabilir * max(mevcut_f - gece_f, 0)
        if puant_israf > 0:
            sizintilar.append(("⚡ Puant israfı (aylık)", puant_israf,
                               f"{kaydirilabilir:,.0f} kWh × {mevcut_f - gece_f:,.2f} TL fark", "Enerji"))

    st.markdown("---")

    if not sizintilar:
        st.info("Henüz sızıntı hesaplanacak veri yok. Bakım ve Üretim modüllerine kayıt girildikçe harita dolacak.")
        return

    sizinti_df = pd.DataFrame(sizintilar, columns=["Sızıntı Kalemi", "Tutar (TL)", "Nasıl hesaplandı", "Modül"])
    sizinti_df = sizinti_df.sort_values("Tutar (TL)", ascending=False).reset_index(drop=True)
    toplam = sizinti_df["Tutar (TL)"].sum()

    st.metric("🔴 Toplam Sızıntı", f"{toplam:,.0f} TL",
              help="Kayıtlı verilerden hesaplanan, önlenebilir kayıpların toplamı")

    for i, satir in sizinti_df.iterrows():
        pay = (satir["Tutar (TL)"] / toplam * 100) if toplam > 0 else 0
        st.markdown(f"**{i+1}. {satir['Sızıntı Kalemi']}** — **{satir['Tutar (TL)']:,.0f} TL** (%{pay:,.0f})")
        st.progress(min(pay / 100, 1.0))
        st.caption(f"{satir['Nasıl hesaplandı']} · Kaynak: {satir['Modül']} modülü")

    en_buyuk = sizinti_df.iloc[0]
    st.error(f"🎯 **Önce buraya odaklan:** En büyük sızıntı **{en_buyuk['Sızıntı Kalemi']}** — {en_buyuk['Tutar (TL)']:,.0f} TL. Buradaki %20'lik bir iyileşme bile ~{en_buyuk['Tutar (TL)']*0.2:,.0f} TL kazandırır.")
    st.caption("⚠️ Bu tutarlar kayıtlı verilerden hesaplanan olası minimum kayıplardır; kesin muhasebe rakamı değildir. OEE kaybı, duruş ve fire kalemlerinin içinde olduğundan çift sayım olmasın diye ayrıca listelenmez.")