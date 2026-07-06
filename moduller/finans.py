import streamlit as st


def goster():
    st.title("💰 Finans — Sanal CFO")
    st.subheader("Parça Başı Maliyet Hesabı")
    st.caption("Bir ürünü üretmenin gerçek maliyetini hesaplar. Elle giriş — Excel okuma sonra eklenecek.")

    fason = st.toggle("Fason üretim (hammaddeyi müşteri veriyor)")

    st.markdown("**Girdiler**")
    kol1, kol2 = st.columns(2)
    with kol1:
        uretilen_adet = st.number_input("Üretilen adet", min_value=1, value=1000)
        if not fason:
            hammadde_tl = st.number_input("Toplam hammadde maliyeti (TL)", min_value=0.0, value=5000.0)
        else:
            hammadde_tl = 0.0
            st.caption("🔵 Fason modu: hammadde maliyete katılmıyor.")
    with kol2:
        iscilik_tl = st.number_input("Toplam işçilik maliyeti (TL) — bilmiyorsan 0 bırak", min_value=0.0, value=2000.0)

    st.markdown("**Elektrik maliyeti**")
    elektrik_yontem = st.radio(
        "Elektrik maliyetini nasıl gireceksin?",
        ["Hazır rakamı biliyorum", "Makineden hesaplat"],
        horizontal=True
    )

    if elektrik_yontem == "Hazır rakamı biliyorum":
        elektrik_tl = st.number_input("Toplam elektrik maliyeti (TL)", min_value=0.0, value=1200.0)
    else:
        e1, e2, e3 = st.columns(3)
        motor_gucu_kw = e1.number_input("Motor gücü (kW)", min_value=0.0, value=15.0)
        calisma_saat = e2.number_input("Çalışma süresi (saat)", min_value=0.0, value=8.0)
        birim_fiyat = e3.number_input("Elektrik fiyatı (TL/kWh)", min_value=0.0, value=2.85)
        elektrik_tl = motor_gucu_kw * calisma_saat * birim_fiyat
        st.caption(f"⚡ Hesaplanan elektrik: {motor_gucu_kw} kW × {calisma_saat} saat × {birim_fiyat} TL = **{elektrik_tl:,.2f} TL**")

    iscilik_varsayimsal = False
    if iscilik_tl == 0:
        iscilik_varsayimsal = True
        iscilik_tl = (hammadde_tl + elektrik_tl) * 0.25

    toplam_maliyet = hammadde_tl + elektrik_tl + iscilik_tl
    birim_maliyet = toplam_maliyet / uretilen_adet

    st.markdown("---")
    st.markdown("**Sonuç**")
    s1, s2 = st.columns(2)
    s1.metric("Toplam Maliyet", f"{toplam_maliyet:,.0f} TL")
    s2.metric("Parça Başı Maliyet", f"{birim_maliyet:,.2f} TL")

    if iscilik_varsayimsal:
        st.warning(f"⚠️ İşçilik girilmedi — sektörel varsayım kullanıldı (~{iscilik_tl:,.0f} TL). Gerçek değeri girersen hesap kesinleşir.")
    if fason:
        st.info("ℹ️ Fason modu aktif: sadece işçilik + elektrik hesaplandı, hammadde hariç.")

    # === TEKLİF MOTORU ===
    st.markdown("---")
    st.subheader("📋 Teklif Motoru")
    st.caption("Bu maliyetle bir siparişe en az kaç TL fiyat vermelisin? Zarar sınırını gösterir.")

    t1, t2 = st.columns(2)
    with t1:
        kar_orani = st.slider("Hedef kâr oranı (%)", min_value=0, max_value=100, value=20)
    with t2:
        teklif_fiyat = st.number_input("Vermeyi düşündüğün fiyat (TL/parça)", min_value=0.0, value=round(birim_maliyet * 1.2, 2))

    minimum_fiyat = birim_maliyet * (1 + kar_orani / 100)

    st.markdown("**Sonuç**")
    r1, r2 = st.columns(2)
    r1.metric("Önerilen Minimum Fiyat", f"{minimum_fiyat:,.2f} TL", help=f"Parça başı maliyet {birim_maliyet:,.2f} TL + %{kar_orani} kâr")

    if teklif_fiyat < birim_maliyet:
        r2.metric("Durum", "ZARAR", delta=f"{teklif_fiyat - birim_maliyet:,.2f} TL/parça", delta_color="inverse")
        st.error(f"🔴 Bu fiyat maliyetin altında! Her parçada {birim_maliyet - teklif_fiyat:,.2f} TL zarar edersin.")
    else:
        gerceklesende_kar = ((teklif_fiyat - birim_maliyet) / birim_maliyet) * 100
        r2.metric("Bu fiyatta kâr oranı", f"%{gerceklesende_kar:,.1f}", delta=f"{teklif_fiyat - birim_maliyet:,.2f} TL/parça")
        if teklif_fiyat < minimum_fiyat:
            st.warning(f"🟡 Bu fiyat kâr getiriyor ama hedefinin (%{kar_orani}) altında.")
        else:
            st.success(f"🟢 Bu fiyat hedef kârını karşılıyor. Toplam sipariş kârı: {(teklif_fiyat - birim_maliyet) * uretilen_adet:,.0f} TL")

    # === NE OLURDU? SİMÜLATÖRÜ ===
    st.markdown("---")
    st.subheader("🔮 \"Ne Olurdu?\" Simülatörü")
    st.caption("Maliyetler değişse ne olurdu? Kaydırıcıları oynat, geleceği test et.")

    sim1, sim2, sim3 = st.columns(3)
    elektrik_degisim = sim1.slider("Elektrik değişimi (%)", -50, 100, 0)
    hammadde_degisim = sim2.slider("Hammadde değişimi (%)", -50, 100, 0)
    iscilik_degisim = sim3.slider("İşçilik değişimi (%)", -50, 100, 0)

    yeni_elektrik = elektrik_tl * (1 + elektrik_degisim / 100)
    yeni_hammadde = hammadde_tl * (1 + hammadde_degisim / 100)
    yeni_iscilik = iscilik_tl * (1 + iscilik_degisim / 100)

    yeni_toplam = yeni_elektrik + yeni_hammadde + yeni_iscilik
    yeni_birim = yeni_toplam / uretilen_adet
    fark = yeni_birim - birim_maliyet

    st.markdown("**Simülasyon Sonucu**")
    sn1, sn2, sn3 = st.columns(3)
    sn1.metric("Şu anki parça maliyeti", f"{birim_maliyet:,.2f} TL")
    sn2.metric("Senaryodaki maliyet", f"{yeni_birim:,.2f} TL", delta=f"{fark:,.2f} TL", delta_color="inverse")
    sn3.metric("Sipariş geneli fark", f"{fark * uretilen_adet:,.0f} TL", delta_color="inverse")

    if fark > 0:
        st.info(f"📈 Bu senaryoda her parça {fark:,.2f} TL daha pahalıya mal olur. Bu fiyatla kârın azalır — teklif fiyatını gözden geçir.")
    elif fark < 0:
        st.success(f"📉 Bu senaryoda her parça {abs(fark):,.2f} TL ucuzlar. Rekabette avantaj veya ek kâr fırsatı.")