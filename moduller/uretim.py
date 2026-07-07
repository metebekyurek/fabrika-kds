import streamlit as st
import pandas as pd


def goster():
    st.title("🔧 Üretim — Kota ve Sapma Raporu")
    st.caption("Hedef, gerçekleşen ve fire takibi. Sadece sapma dili — maaş/prim/İK yok.")

    ornek_veri = pd.DataFrame([
        {"tarih": "2026-06-01", "vardiya": "gündüz", "makine_id": "PRES-01", "operator_id": "OP-01",
         "urun_kodu": "URN-A", "hedef_adet": 800, "uretilen_adet": 760, "fire_adet": 20, "fire_nedeni": "kalıp"},
        {"tarih": "2026-06-01", "vardiya": "gece", "makine_id": "PRES-01", "operator_id": "OP-02",
         "urun_kodu": "URN-A", "hedef_adet": 800, "uretilen_adet": 690, "fire_adet": 35, "fire_nedeni": "hammadde"},
        {"tarih": "2026-06-02", "vardiya": "gündüz", "makine_id": "PRES-01", "operator_id": "OP-01",
         "urun_kodu": "URN-A", "hedef_adet": 800, "uretilen_adet": 820, "fire_adet": 10, "fire_nedeni": "ayar"},
    ])

    st.subheader("Üretim Kayıtları")
    st.caption("Tabloyu düzenle, satır ekle/sil. Hedef girmezsen sistem geçmiş ortalamayı referans alır.")

    df = st.data_editor(
        ornek_veri,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "tarih": "Tarih",
            "vardiya": st.column_config.SelectboxColumn("Vardiya", options=["gündüz", "gece", "tam gün"]),
            "makine_id": "Makine",
            "operator_id": "Operatör",
            "urun_kodu": "Ürün",
            "hedef_adet": st.column_config.NumberColumn("Hedef", format="%d"),
            "uretilen_adet": st.column_config.NumberColumn("Üretilen", format="%d"),
            "fire_adet": st.column_config.NumberColumn("Fire", format="%d"),
            "fire_nedeni": st.column_config.SelectboxColumn("Fire Nedeni", options=["ayar", "hammadde", "kalıp", "operatör", "diğer"]),
        }
    )

    st.markdown("---")
    st.subheader("📊 Sapma Analizi")

    calisilan = df.copy()
    calisilan["uretilen_adet"] = pd.to_numeric(calisilan["uretilen_adet"], errors="coerce")
    calisilan["hedef_adet"] = pd.to_numeric(calisilan["hedef_adet"], errors="coerce")
    calisilan["fire_adet"] = pd.to_numeric(calisilan["fire_adet"], errors="coerce")
    gecerli = calisilan.dropna(subset=["uretilen_adet"])

    if len(gecerli) == 0:
        st.warning("Geçerli üretim kaydı yok. Lütfen 'Üretilen' sütununu doldur.")
        return

    toplam_uretim = gecerli["uretilen_adet"].sum()
    toplam_fire = gecerli["fire_adet"].sum()
    fire_orani = (toplam_fire / (toplam_uretim + toplam_fire) * 100) if (toplam_uretim + toplam_fire) > 0 else 0

    g1, g2, g3 = st.columns(3)
    g1.metric("Toplam Üretim", f"{toplam_uretim:,.0f} adet")
    g2.metric("Toplam Fire", f"{toplam_fire:,.0f} adet")
    g3.metric("Fire Oranı", f"%{fire_orani:,.1f}")

    # Hedefe göre sapma (hedef girilmişse)
    hedefli = gecerli.dropna(subset=["hedef_adet"])
    hedefli = hedefli[hedefli["hedef_adet"] > 0]
    if len(hedefli) > 0:
        st.markdown("**Hedefe Göre Sapma**")
        for _, satir in hedefli.iterrows():
            sapma = ((satir["uretilen_adet"] - satir["hedef_adet"]) / satir["hedef_adet"]) * 100
            etiket = f"{satir['tarih']} · {satir['vardiya']} · {satir['operator_id']}"
            if sapma >= 0:
                st.write(f"• {etiket}: hedefin **%{sapma:,.1f} üstünde** ✅")
            else:
                st.write(f"• {etiket}: hedefin **%{abs(sapma):,.1f} altında** ⚠️")
    st.markdown("---")
    st.subheader("🔍 Fire Nedeni Analizi")
    st.caption("Firelerin çoğu nereden geliyor? Asıl kaybın kaynağını gösterir.")

    if "fire_nedeni" in gecerli and gecerli["fire_adet"].sum() > 0:
        fire_grup = gecerli.groupby("fire_nedeni")["fire_adet"].sum().sort_values(ascending=False)
        en_buyuk_neden = fire_grup.index[0]
        en_buyuk_deger = fire_grup.iloc[0]
        oran = (en_buyuk_deger / gecerli["fire_adet"].sum()) * 100
        st.warning(f"⚠️ En büyük fire kaynağı: **{en_buyuk_neden}** (toplam firenin %{oran:,.0f}'i, {en_buyuk_deger:,.0f} adet). Önce buraya odaklan.")
        st.markdown("**Nedene göre fire dağılımı:**")
        for neden, adet in fire_grup.items():
            st.write(f"• {neden}: {adet:,.0f} adet")
    else:
        st.info("Fire kaydı yok veya fire nedeni girilmemiş.")

    st.markdown("---")
    st.subheader("🌙 Vardiya Karşılaştırması")
    st.caption("Hangi vardiya daha verimli? Fark varsa görünür.")

    if "vardiya" in gecerli:
        vardiya_grup = gecerli.groupby("vardiya").agg(
            toplam_uretim=("uretilen_adet", "sum"),
            toplam_fire=("fire_adet", "sum")
        )
        vardiya_grup["fire_orani"] = (vardiya_grup["toplam_fire"] / (vardiya_grup["toplam_uretim"] + vardiya_grup["toplam_fire"]) * 100)
        st.markdown("**Vardiya bazında:**")
        for vardiya, satir in vardiya_grup.iterrows():
            st.write(f"• **{vardiya}**: {satir['toplam_uretim']:,.0f} adet üretim, fire oranı %{satir['fire_orani']:,.1f}")                