import streamlit as st

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
    st.title("💰 Finans — Sanal CFO")
    st.subheader("Parça Başı Maliyet Hesabı")
    st.caption("Bir ürünü üretmenin gerçek maliyetini hesaplar. Elle giriş — Excel okuma sonra eklenecek.")

    st.markdown("**Girdiler**")
    kol1, kol2 = st.columns(2)
    with kol1:
        uretilen_adet = st.number_input("Üretilen adet", min_value=1, value=1000)
        hammadde_tl = st.number_input("Toplam hammadde maliyeti (TL)", min_value=0.0, value=5000.0)
    with kol2:
        elektrik_tl = st.number_input("Toplam elektrik maliyeti (TL)", min_value=0.0, value=1200.0)
        iscilik_tl = st.number_input("Toplam işçilik maliyeti (TL)", min_value=0.0, value=2000.0)

    toplam_maliyet = hammadde_tl + elektrik_tl + iscilik_tl
    birim_maliyet = toplam_maliyet / uretilen_adet

    st.markdown("---")
    st.markdown("**Sonuç**")
    s1, s2 = st.columns(2)
    s1.metric("Toplam Maliyet", f"{toplam_maliyet:,.0f} TL")
    s2.metric("Parça Başı Maliyet", f"{birim_maliyet:,.2f} TL")

    if iscilik_tl == 0:
        st.warning("İşçilik girilmedi — bu hesap işçilik hariçtir (varsayımsal).") 

elif secim == "⚡ Enerji":
    st.title("⚡ Enerji")
    st.info("Fatura tahmini, tarife ve GES takibi burada olacak.")

elif secim == "🔧 Üretim":
    st.title("🔧 Üretim")
    st.info("Kota, fire ve operatör sapması burada olacak.")

elif secim == "🛠️ Bakım":
    st.title("🛠️ Bakım")
    st.info("MTBF, RUL ve kök neden analizi burada olacak.")

elif secim == "📦 Stok":
    st.title("📦 Stok")
    st.info("Stok takibi ve tedarikçi karnesi burada olacak.")