import streamlit as st
from moduller import finans, bakim

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
    st.title("⚡ Enerji")
    st.info("Fatura tahmini, tarife ve GES takibi burada olacak.")

elif secim == "🔧 Üretim":
    st.title("🔧 Üretim")
    st.info("Kota, fire ve operatör sapması burada olacak.")

elif secim == "🛠️ Bakım":
    bakim.goster()

elif secim == "📦 Stok":
    st.title("📦 Stok")
    st.info("Stok takibi ve tedarikçi karnesi burada olacak.")