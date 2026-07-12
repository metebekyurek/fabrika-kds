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

    if not stok_df.empty and "mevcut_miktar" in stok_df.columns:
        for _, s in stok_df.iterrows():
            mevcut = pd.to_numeric(s.get("mevcut_miktar"), errors="coerce")
            kritik = pd.to_numeric(s.get("kritik_seviye"), errors="coerce")
            if pd.notna(mevcut) and pd.notna(kritik) and mevcut <= kritik:
                st.error(f"🔴 Stok: **{s['malzeme_adi']}** kritik seviyede ({mevcut:,.0f} kaldı). Sipariş zamanı.")
                uyari_bulundu = True

    if not ariza_df.empty:
        st.warning(f"🟡 Bakım: {len(ariza_df)} kayıtlı arıza var. Detay için Bakım modülüne bak.")
        uyari_bulundu = True

    if not uyari_bulundu:
        st.success("🟢 Şu an acil dikkat gerektiren bir durum görünmüyor.")

    st.markdown("---")
    st.subheader("💱 Güncel Kurlar")
    doviz_seridi_goster()