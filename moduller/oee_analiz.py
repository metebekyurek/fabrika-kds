import streamlit as st
import pandas as pd
import veritabani
import hesap_motoru

def goster():
    st.title("🎯 OEE — Toplam Ekipman Etkinliği")
    st.caption("Dünya standardı verimlilik ölçüsü: makinen, ideal dünyada üretebileceğinin yüzde kaçını üretti?")

    veritabani.tablolari_olustur()
    uretim_df = veritabani.veri_oku("uretim")

    if uretim_df.empty:
        st.info("ℹ️ OEE için önce Üretim modülünden kayıt girilmeli.")
        return

    calisilan = uretim_df.copy()
    for kol in ["uretilen_adet", "fire_adet"]:
        if kol in calisilan.columns:
            calisilan[kol] = pd.to_numeric(calisilan[kol], errors="coerce")

    oee_gerekli = ["planlanan_sure_dk", "durus_dk", "ideal_hiz_adet_dk"]
    for kol in oee_gerekli:
        if kol not in calisilan.columns:
            calisilan[kol] = pd.NA
        calisilan[kol] = pd.to_numeric(calisilan[kol], errors="coerce")

    oee_veri = calisilan.dropna(subset=["uretilen_adet", "planlanan_sure_dk", "durus_dk", "ideal_hiz_adet_dk"])
    oee_veri = oee_veri[(oee_veri["planlanan_sure_dk"] > 0) & (oee_veri["ideal_hiz_adet_dk"] > 0)]

    if len(oee_veri) == 0:
        st.info("ℹ️ OEE için Üretim tablosunda 'Planlanan Süre', 'Duruş' ve 'İdeal Hız' sütunları dolu olmalı.")
        return

    planlanan = oee_veri["planlanan_sure_dk"].sum()
    durus = oee_veri["durus_dk"].fillna(0).sum()
    calisma = planlanan - durus

    uretilen = oee_veri["uretilen_adet"].sum()
    fire = oee_veri["fire_adet"].fillna(0).sum()
    saglam = uretilen - fire

    oee_veri = oee_veri.copy()
    oee_veri["net_calisma_dk"] = oee_veri["planlanan_sure_dk"] - oee_veri["durus_dk"].fillna(0)
    teorik = (oee_veri["net_calisma_dk"] * oee_veri["ideal_hiz_adet_dk"]).sum()

    kullanilabilirlik = (calisma / planlanan) if planlanan > 0 else 0
    performans = (uretilen / teorik) if teorik > 0 else 0
    performans = min(performans, 1.0)
    kalite = (saglam / uretilen) if uretilen > 0 else 0
    oee = kullanilabilirlik * performans * kalite

    o1, o2, o3, o4 = st.columns(4)
    o1.metric("Kullanılabilirlik", f"%{kullanilabilirlik*100:,.1f}", help="Planlanan sürenin ne kadarında makine gerçekten çalıştı")
    o2.metric("Performans", f"%{performans*100:,.1f}", help="Çalışırken ideal hıza ne kadar yaklaştı")
    o3.metric("Kalite", f"%{kalite*100:,.1f}", help="Üretilenlerin ne kadarı sağlam çıktı")
    o4.metric("OEE", f"%{oee*100:,.1f}", help="Üçünün çarpımı — genel verimlilik")

    if oee >= 0.85:
        st.success(f"🟢 OEE %{oee*100:,.1f} — dünya standardında (%85+). Bu seviyeyi korumak esas iş.")
    elif oee >= 0.60:
        st.warning(f"🟡 OEE %{oee*100:,.1f} — ortalamanın üstü ama dünya standardının (%85) altında. İyileştirme alanı var.")
    else:
        st.error(f"🔴 OEE %{oee*100:,.1f} — kayıp büyük. Aşağıdaki TL hesabına bak.")

    st.markdown("**💰 Bu kaybın TL karşılığı**")
    st.caption("OEE %100 olsaydı üretebileceğin ama üretemediğin sağlam parçaların kâr değeri. Ürün kârları 📦 Ürünler sayfasından otomatik alınır.")

    # Ortalama parça kârı: üretim karışımından (motordan) — elle giriş yok
    karlar = hesap_motoru.urun_karlari()
    ort_kar = 0.0
    if karlar and "urun_kodu" in oee_veri.columns:
        v = oee_veri.copy()
        v["urun_kodu"] = v["urun_kodu"].astype(str).str.strip().str.upper()
        v["parca_kar"] = v["urun_kodu"].map(karlar)
        v = v.dropna(subset=["parca_kar"])
        if not v.empty and v["uretilen_adet"].sum() > 0:
            ort_kar = float((v["uretilen_adet"] * v["parca_kar"]).sum() / v["uretilen_adet"].sum())

    ideal_toplam = (oee_veri["planlanan_sure_dk"] * oee_veri["ideal_hiz_adet_dk"]).sum()
    kacan_adet = ideal_toplam - saglam

    if kacan_adet > 0 and ort_kar > 0:
        kayip_tl = kacan_adet * ort_kar
        st.error(f"🔴 Bu dönemde OEE kayıpları yüzünden üretilemeyen ~**{kacan_adet:,.0f} sağlam parça** = olası minimum **{kayip_tl:,.0f} TL** kaçan kâr (ürün karışımının ağırlıklı ortalama kârı: {ort_kar:,.2f} TL). OEE'yi 10 puan iyileştirmek bile bunun önemli kısmını geri kazandırır.")
    elif kacan_adet > 0:
        st.info("ℹ️ TL hesabı için 📦 Ürünler sayfasında parça kârları tanımlı olmalı.")
    else:
        st.success("🟢 Kayıtlara göre kayıp görünmüyor.")