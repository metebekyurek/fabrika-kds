import streamlit as st
import pandas as pd
from moduller import finans, bakim, uretim, enerji, stok, makineler, kar_sizintisi, capraz_zeka, kar_simulatoru
from doviz_seridi import doviz_seridi_goster
from grafikler import uretim_trend_grafigi
st.set_page_config(page_title="Fabrika KDS", page_icon="🏭", layout="wide")

st.sidebar.title("🏭 Fabrika KDS")
st.sidebar.caption("Entegre Karar Destek Sistemi")


secim = st.sidebar.radio(
    "Menü",
    ["📊 Günün Özeti", "💸 Kâr Sızıntısı", "🧠 Çapraz Zekâ", "🎚️ Simülatör", "💰 Finans", "⚡ Enerji", "🔧 Üretim", "🛠️ Bakım", "📦 Stok", "⚙️ Makineler"]
)

if secim == "📊 Günün Özeti":
    import veritabani
    veritabani.tablolari_olustur()

    st.title("📊 Günün Özeti")
    st.caption("Fabrikanızın bugünkü genel durumu — tek bakışta.")

    ariza_df = veritabani.veri_oku("arizalar")
    uretim_df = veritabani.veri_oku("uretim")
    stok_df = veritabani.veri_oku("stok")
    enerji_df = veritabani.veri_oku("enerji")

    # Üst satır: 4 ana gösterge
    k1, k2, k3, k4 = st.columns(4)

    # Bakım: kayıtlı arıza sayısı ve toplam tamir gideri
    if not ariza_df.empty and "tamir_maliyeti_tl" in ariza_df.columns:
        toplam_tamir = pd.to_numeric(ariza_df["tamir_maliyeti_tl"], errors="coerce").sum()
        k1.metric("🛠️ Kayıtlı Arıza", f"{len(ariza_df)} adet", help="Bakım modülüne kaydedilen arıza sayısı")
        k2.metric("💸 Toplam Tamir Gideri", f"{toplam_tamir:,.0f} TL")
    else:
        k1.metric("🛠️ Kayıtlı Arıza", "0 adet")
        k2.metric("💸 Toplam Tamir Gideri", "0 TL")

    # Üretim: toplam üretim ve fire oranı
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

    # Kritik stok uyarıları
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
        st.warning(f"🟡 Bakım: {len(ariza_df)} kayıtlı arıza var. Detay ve önleyici bakım kararı için Bakım modülüne bak.")
        uyari_bulundu = True

    if not uyari_bulundu:
        st.success("🟢 Şu an acil dikkat gerektiren bir durum görünmüyor.")

    st.markdown("---")
    st.info("💡 Detaylı analiz için sol menüden ilgili modüle girebilirsin. Bu özet, kaydettiğin verilerden otomatik oluşur.")
    st.markdown("---")
    st.subheader("💱 Güncel Kurlar")
    doviz_seridi_goster()
elif secim == "💰 Finans":
    finans.goster()

elif secim == "⚡ Enerji":
    enerji.goster()

elif secim == "🔧 Üretim":
    uretim.goster()

elif secim == "🛠️ Bakım":
    bakim.goster()

elif secim == "📦 Stok":
    stok.goster()

elif secim == "⚙️ Makineler":
    makineler.goster()    

elif secim == "💸 Kâr Sızıntısı":
    kar_sizintisi.goster()
elif secim == "🧠 Çapraz Zekâ":
    capraz_zeka.goster()
elif secim == "🎚️ Simülatör":
    kar_simulatoru.goster()    