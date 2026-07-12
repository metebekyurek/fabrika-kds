import streamlit as st
import pandas as pd
import hesap_motoru

def goster():
    st.title("💸 Kâr Sızıntısı Haritası")
    st.caption("Tüm modüllerdeki kayıplar tek ekranda, TL cinsinden, büyükten küçüğe. Paran nereden sızıyor?")

    st.info("💡 Tüm hesaplar **kayıtlı verilerinden** yapılır: her fire kendi ürününün kârıyla, her duruş o makinenin kendi kapasitesi ve gerçekte bastığı ürün karışımıyla hesaplanır. Elle değer girmene gerek yok.")

    kalemler = hesap_motoru.sizinti_kalemleri()

    if not kalemler:
        st.warning("Henüz sızıntı hesaplanacak veri yok.")
        st.markdown("""
        **Hesap için gerekenler:**
        - 📦 **Ürünler** sayfasında ürünlerin parça kârı tanımlı olmalı
        - ⚙️ **Makineler** sayfasında saatlik kapasite girilmiş olmalı
        - 🔧 **Üretim** ve 🛠️ **Bakım** modüllerinde kayıt olmalı
        """)
        return

    toplam = sum(k[1] for k in kalemler)

    st.metric("🔴 Toplam Sızıntı", f"{toplam:,.0f} TL",
              help="Kayıtlı verilerden hesaplanan, önlenebilir kayıpların toplamı")

    for i, (ad, tutar, aciklama, modul) in enumerate(kalemler, 1):
        pay = (tutar / toplam * 100) if toplam > 0 else 0
        st.markdown(f"**{i}. {ad}** — **{tutar:,.0f} TL** (%{pay:,.0f})")
        st.progress(min(pay / 100, 1.0))
        st.caption(f"{aciklama} · Kaynak: {modul} modülü")

    en_buyuk = kalemler[0]
    st.error(f"🎯 **Önce buraya odaklan:** En büyük sızıntı **{en_buyuk[0]}** — {en_buyuk[1]:,.0f} TL. "
             f"Buradaki %20'lik bir iyileşme bile ~{en_buyuk[1]*0.2:,.0f} TL kazandırır.")

    # --- Detaylı dökümler ---
    st.markdown("---")
    with st.expander("🔍 Detaylı döküm — hangi ürün / hangi makine?"):
        fire_tl, fire_detay = hesap_motoru.fire_kaybi_tl()
        if not fire_detay.empty:
            st.markdown("**♻️ Fire kaybı — ürün bazında:**")
            gosterim = fire_detay.copy()
            gosterim.columns = ["Ürün", "Fire (adet)", "Kayıp (TL)"]
            st.dataframe(gosterim, use_container_width=True, hide_index=True)

        durus_tl, durus_detay = hesap_motoru.durus_kaybi_tl()
        if not durus_detay.empty:
            st.markdown("**⏸️ Duruş kaybı — makine bazında:**")
            gosterim = durus_detay.copy()
            gosterim.columns = ["Makine", "Duruş (saat)", "Kapasite (adet/saat)", "Ağırlıklı Kâr (TL)", "Kayıp (TL)"]
            st.dataframe(gosterim, use_container_width=True, hide_index=True)
            st.caption("ℹ️ 'Ağırlıklı Kâr': o makinenin gerçekte bastığı ürün karışımının ortalama kârı. Makine durunca ne üretemeyeceği bilinemez; bu, veriye dayalı en dürüst tahmindir.")

    st.caption("⚠️ Bu tutarlar kayıtlı verilerden hesaplanan olası minimum kayıplardır; kesin muhasebe rakamı değildir. OEE kaybı, duruş ve fire kalemlerinin içinde olduğundan çift sayım olmasın diye ayrıca listelenmez.")