import streamlit as st
from moduller import finans, bakim, uretim, enerji, stok 

st.set_page_config(page_title="Fabrika KDS", page_icon="🏭", layout="wide")

st.sidebar.title("🏭 Fabrika KDS")
st.sidebar.caption("Entegre Karar Destek Sistemi")

secim = st.sidebar.radio(
    "Menü",
    ["📊 Günün Özeti", "💰 Finans", "⚡ Enerji", "🔧 Üretim", "🛠️ Bakım", "📦 Stok"]
)

if secim == "📊 Günün Özeti":
    st.title("📊 Günün Özeti")
    st.info("Buraya günlük net durum özeti gelecek.")

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
    