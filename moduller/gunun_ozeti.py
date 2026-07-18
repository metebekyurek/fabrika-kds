import streamlit as st
import pandas as pd
import veritabani
from doviz_seridi import doviz_seridi_goster
from grafikler import uretim_trend_grafigi

def goster():
    veritabani.tablolari_olustur()

    st.title("📊 Günün Özeti")
    st.caption("Fabrikanızın bugünkü genel durumu — tek bakışta.")

    ariza_df = veritabani.veri_oku("arizalar")
    uretim_df = veritabani.veri_oku("uretim")
    stok_df = veritabani.veri_oku("stok")

    k1, k2, k3, k4 = st.columns(4)

    if not ariza_df.empty and "tamir_maliyeti_tl" in ariza_df.columns:
        toplam_tamir = pd.to_numeric(ariza_df["tamir_maliyeti_tl"], errors="coerce").sum()
        k1.metric("🛠️ Kayıtlı Arıza", f"{len(ariza_df)} adet")
        k2.metric("💸 Toplam Tamir Gideri", f"{toplam_tamir:,.0f} TL")
    else:
        k1.metric("🛠️ Kayıtlı Arıza", "0 adet")
        k2.metric("💸 Toplam Tamir Gideri", "0 TL")

    if not uretim_df.empty and "uretilen_adet" in uretim_df.columns:
        top_uretim = pd.to_numeric(uretim_df["uretilen_adet"], errors="coerce").sum()
        top_fire = pd.to_numeric(uretim_df["fire_adet"], errors="coerce").sum()
        fire_or = (top_fire / (top_uretim + top_fire) * 100) if (top_uretim + top_fire) > 0 else 0
        k3.metric("🔧 Toplam Üretim", f"{top_uretim:,.0f} adet")
        k4.metric("♻️ Fire Oranı", f"%{fire_or:,.1f}")
    else:
        k3.metric("🔧 Toplam Üretim", "0 adet")
        k4.metric("♻️ Fire Oranı", "%0")

    st.subheader("📈 Üretim Trendi")
    uretim_trend_grafigi(uretim_df)

    st.markdown("---")
    st.subheader("🚨 Dikkat Gerektirenler")
    uyari_bulundu = False

    def _git_butonu(hedef_sayfa, anahtar):
        """Uyarının yanına minik 'git' butonu koyar — tıklayınca ilgili sayfayı açar."""
        if st.button("➜ Git", key=anahtar, use_container_width=True):
            st.session_state["aktif_sayfa"] = hedef_sayfa
            st.rerun()

    if not stok_df.empty and "mevcut_miktar" in stok_df.columns:
        for i, (_, s) in enumerate(stok_df.iterrows()):
            mevcut = pd.to_numeric(s.get("mevcut_miktar"), errors="coerce")
            kritik = pd.to_numeric(s.get("kritik_seviye"), errors="coerce")
            if pd.notna(mevcut) and pd.notna(kritik) and mevcut <= kritik:
                u1, u2 = st.columns([6, 1])
                u1.error(f"🔴 Stok: **{s['malzeme_adi']}** kritik seviyede ({mevcut:,.0f} kaldı). Sipariş zamanı.")
                with u2:
                    _git_butonu("Stok", f"git_stok_{i}")
                uyari_bulundu = True

    if not ariza_df.empty and "ariza_baslangic" in ariza_df.columns:
        from datetime import datetime, timedelta
        a = ariza_df.copy()
        a["bas"] = pd.to_datetime(a["ariza_baslangic"], errors="coerce")
        son7 = a[a["bas"] >= datetime.now() - timedelta(days=7)]
        if len(son7) > 0:
            u1, u2 = st.columns([6, 1])
            u1.warning(f"🟡 Bakım: son 7 günde **{len(son7)} arıza** kaydedildi. Detay için Bakım modülüne bak.")
            with u2:
                _git_butonu("Bakım", "git_bakim")
            uyari_bulundu = True 
    # Bakımı gecikmiş makineler (Bakım Takvimi'nden)
    makine_df = veritabani.veri_oku("makineler")
    if not makine_df.empty and "son_bakim_tarihi" in makine_df.columns:
        from datetime import datetime, timedelta
        bugun = datetime.now().date()
        gecikenler = []
        for _, m in makine_df.iterrows():
            son = pd.to_datetime(m.get("son_bakim_tarihi"), errors="coerce")
            periyot = pd.to_numeric(m.get("bakim_periyodu_gun"), errors="coerce")
            if pd.notna(son) and pd.notna(periyot) and periyot > 0:
                sonraki = son.date() + timedelta(days=int(periyot))
                if (sonraki - bugun).days < 0:
                    gecikenler.append(str(m.get("makine_id", "")).strip())
        if gecikenler:
            u1, u2 = st.columns([6, 1])
            u1.error(f"🔴 Bakım gecikmiş: **{', '.join(gecikenler[:5])}**{' ve diğerleri' if len(gecikenler) > 5 else ''}. Takvime bak.")
            with u2:
                _git_butonu("Bakım Takvimi", "git_takvim")
            uyari_bulundu = True

    if not uyari_bulundu:
        st.success("🟢 Şu an acil dikkat gerektiren bir durum görünmüyor.")

    st.markdown("---")
    st.subheader("💱 Güncel Kurlar")
    doviz_seridi_goster()