import streamlit as st
import pandas as pd
from moduller import finans, bakim, uretim, enerji, stok, makineler, kar_sizintisi, capraz_zeka, kar_simulatoru, pdf_rapor, bakim_takvimi, gunluk_ozet_mail, ayarlar, urunler, demo_veri, oee_analiz, gunun_ozeti

st.set_page_config(page_title="Fabrika KDS", page_icon="🏭", layout="wide")

st.sidebar.title("🏭 Fabrika KDS")
st.sidebar.caption("Entegre Karar Destek Sistemi")

MENU_GRUPLARI = {
    "📊 GENEL BAKIŞ": ["Günün Özeti", "Kâr Sızıntısı", "Çapraz Zekâ", "Simülatör"],
    "🏭 OPERASYON": ["Üretim", "OEE Analizi", "Bakım", "Bakım Takvimi", "Stok", "Enerji", "Finans"],
    "📋 TANIMLAR": ["Makineler", "Ürünler", "Fabrika Ayarları"],
    "📤 RAPOR & İLETİŞİM": ["PDF Rapor", "Günün Özeti Maili"],
    "🔧 DİĞER": ["Demo Verisi"],
}

if "aktif_sayfa" not in st.session_state:
    st.session_state["aktif_sayfa"] = "Günün Özeti"

for grup, sayfalar in MENU_GRUPLARI.items():
    st.sidebar.markdown(f"**{grup}**")
    for sayfa in sayfalar:
        if st.sidebar.button(sayfa, key=f"btn_{sayfa}", use_container_width=True,
                             type="primary" if st.session_state["aktif_sayfa"] == sayfa else "secondary"):
            st.session_state["aktif_sayfa"] = sayfa
            st.rerun()

secim = st.session_state["aktif_sayfa"]

SAYFALAR = {
    "Günün Özeti": gunun_ozeti.goster,
    "Kâr Sızıntısı": kar_sizintisi.goster,
    "Çapraz Zekâ": capraz_zeka.goster,
    "Simülatör": kar_simulatoru.goster,
    "Üretim": uretim.goster,
    "OEE Analizi": oee_analiz.goster,
    "Bakım": bakim.goster,
    "Bakım Takvimi": bakim_takvimi.goster,
    "Stok": stok.goster,
    "Enerji": enerji.goster,
    "Finans": finans.goster,
    "Makineler": makineler.goster,
    "Ürünler": urunler.goster,
    "Fabrika Ayarları": ayarlar.goster,
    "PDF Rapor": pdf_rapor.goster,
    "Günün Özeti Maili": gunluk_ozet_mail.goster,
    "Demo Verisi": demo_veri.goster,
}

SAYFALAR[secim]()