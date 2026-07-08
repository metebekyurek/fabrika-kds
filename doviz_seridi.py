import streamlit as st
import requests

@st.cache_data(ttl=1800)  # 1800 saniye = 30 dakika boyunca cevabı hatırla
def kurlari_getir():
    """Dolar ve Euro'nun TL karşılığını ücretsiz API'den çeker."""
    try:
        cevap = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        veri = cevap.json()
        usd_try = veri["rates"]["TRY"]              # 1 Dolar kaç TL
        eur_try = usd_try / veri["rates"]["EUR"]    # 1 Euro kaç TL
        return usd_try, eur_try
    except Exception:
        return None, None  # İnternet yoksa uygulama çökmesin, sessizce geç

def doviz_seridi_goster():
    """Günün Özeti'nin altına yerleşecek döviz şeridi."""
    usd, eur = kurlari_getir()
    if usd is None:
        st.caption("⚠️ Döviz kurları şu an alınamadı (internet bağlantısını kontrol edin).")
        return
    kolon1, kolon2 = st.columns(2)
    kolon1.metric("💵 Dolar (USD/TL)", f"{usd:.2f} ₺")
    kolon2.metric("💶 Euro (EUR/TL)", f"{eur:.2f} ₺")
    st.caption("Kurlar günde birkaç kez güncellenir · Kaynak: open.er-api.com (ücretsiz)")