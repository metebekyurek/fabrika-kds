import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import veritabani
import hesap_motoru

# Hangi metrikte artış İYİdir? (üretim artsın 🟢, fire artmasın 🔴)
ARTIS_IYI = {
    "Üretim (adet)": True,
    "Fire (adet)": False,
    "Fire Kaybı (TL)": False,
    "Tamir Gideri (TL)": False,
    "Arıza Sayısı": False,
    "Duruş (saat)": False,
}

def goster():
    st.title("📈 Dönem Kıyaslama")
    st.caption("Bu dönem ile önceki dönemi yan yana koy. Gidişat iyi mi, kötü mü — tek bakışta.")

    donem = st.radio("Kıyas dönemi",
                     ["Bu ay ↔ Geçen ay", "Haftalık (son 7 gün)", "Aylık (son 30 gün)",
                      "3 Aylık (son 90 gün)", "Yıllık (son 365 gün)",
                      "📅 Özel Aralık (takvimden seç)"],
                     horizontal=True, index=0)

    if donem == "Bu ay ↔ Geçen ay":
        gun = 30  # grafik penceresi için
        kiyas = hesap_motoru.takvim_ay_kiyasi()
        st.caption("Karşılaştırma: içinde bulunduğumuz ay (1'inden bugüne) ↔ geçen ayın tamamı")

    elif donem == "📅 Özel Aralık (takvimden seç)":
        from datetime import date
        kol1, kol2 = st.columns(2)
        bas_t = kol1.date_input("Başlangıç", value=date.today() - timedelta(days=30))
        bit_t = kol2.date_input("Bitiş", value=date.today())
        if bas_t > bit_t:
            st.error("⚠️ Başlangıç tarihi bitişten sonra olamaz.")
            return
        gun = max((bit_t - bas_t).days + 1, 1)  # grafik penceresi için
        kiyas = hesap_motoru.ozel_aralik_kiyasi(bas_t, bit_t)
        on_bit = bas_t - timedelta(days=1)
        on_bas = on_bit - timedelta(days=gun - 1)
        st.caption(f"Karşılaştırma: {bas_t.strftime('%d.%m.%Y')} – {bit_t.strftime('%d.%m.%Y')} "
                   f"↔ önceki dönem: {on_bas.strftime('%d.%m.%Y')} – {on_bit.strftime('%d.%m.%Y')}")

    else:
        gun = {"Haftalık (son 7 gün)": 7, "Aylık (son 30 gün)": 30,
               "3 Aylık (son 90 gün)": 90, "Yıllık (son 365 gün)": 365}[donem]
        if gun == 365:
            st.caption("ℹ️ Yıllık kıyas için en az 1-2 yıllık kayıt gerekir — veriniz biriktikçe bu görünüm güçlenir.")
        kiyas = hesap_motoru.donem_kiyasi(gun)
        st.caption(f"Karşılaştırma: son {gun} gün ↔ ondan önceki {gun} gün")

    if not kiyas:
        st.info("ℹ️ Kıyas için Üretim ve Bakım modüllerinde tarihli kayıt olmalı.")
        return

    # --- Kıyas kartları ---
    kartlar = list(kiyas.items())
    for i in range(0, len(kartlar), 3):
        kolonlar = st.columns(3)
        for j, (ad, (simdi, once, degisim)) in enumerate(kartlar[i:i+3]):
            iyi_mi = ARTIS_IYI.get(ad, True)
            yon_iyi = (degisim >= 0) == iyi_mi

            if "TL" in ad:
                deger_str = f"{simdi:,.0f} TL"
                once_str = f"{once:,.0f} TL"
            elif "saat" in ad:
                deger_str = f"{simdi:,.1f} sa"
                once_str = f"{once:,.1f} sa"
            else:
                deger_str = f"{simdi:,.0f}"
                once_str = f"{once:,.0f}"

            kolonlar[j].metric(
                ad, deger_str,
                delta=f"%{degisim:+,.1f} (önceki: {once_str})",
                delta_color="normal" if iyi_mi else "inverse",
            )

    st.markdown("---")

    # --- Çift çizgili üretim grafiği ---
    st.subheader("📊 Üretim Trendi — bu dönem vs önceki dönem")
    onceki_goster = st.checkbox("Önceki dönemi göster (soluk çizgi)", value=True)

    uretim = veritabani.veri_oku("uretim")
    if uretim.empty or "tarih" not in uretim.columns:
        st.caption("Grafik için üretim kaydı gerekiyor.")
        return

    u = uretim.copy()
    u["tarih"] = pd.to_datetime(u["tarih"], errors="coerce")
    u["uretilen_adet"] = pd.to_numeric(u["uretilen_adet"], errors="coerce").fillna(0)
    u = u.dropna(subset=["tarih"])

    bugun = datetime.now()
    bu_bas = bugun - timedelta(days=gun)
    on_bas = bugun - timedelta(days=gun * 2)

    bu_df = u[u["tarih"] >= bu_bas].groupby(u["tarih"].dt.date)["uretilen_adet"].sum()
    on_df = u[(u["tarih"] >= on_bas) & (u["tarih"] < bu_bas)].groupby(u["tarih"].dt.date)["uretilen_adet"].sum()

    fig = go.Figure()
    # Önceki dönem: gün sırasına göre hizala (1. gün, 2. gün...) ki üst üste binsin
    if onceki_goster and len(on_df) > 0:
        fig.add_trace(go.Scatter(
            x=list(range(1, len(on_df) + 1)), y=on_df.values,
            name="Önceki dönem", mode="lines",
            line=dict(color="#888888", width=2, dash="dot"),
        ))
    fig.add_trace(go.Scatter(
        x=list(range(1, len(bu_df) + 1)), y=bu_df.values,
        name="Bu dönem", mode="lines+markers",
        line=dict(color="#2E86AB", width=3),
    ))
    fig.update_layout(
        xaxis_title=f"Dönemin kaçıncı günü (1–{gun})",
        yaxis_title="Üretim (adet)",
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=10, r=10, t=10, b=10),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Özet cümle ---
    st.markdown("---")
    iyiler = [ad for ad, (s, o, d) in kiyas.items() if ((d >= 0) == ARTIS_IYI.get(ad, True)) and abs(d) > 2]
    kotuler = [ad for ad, (s, o, d) in kiyas.items() if ((d >= 0) != ARTIS_IYI.get(ad, True)) and abs(d) > 2]

    if kotuler and iyiler:
        st.warning(f"📋 **Özet:** İyi giden: {', '.join(iyiler)}. Dikkat gereken: **{', '.join(kotuler)}**.")
    elif kotuler:
        st.error(f"📋 **Özet:** Bu dönem önceki döneme göre geriledi: **{', '.join(kotuler)}**. Sebeplerini ilgili modüllerde incele.")
    elif iyiler:
        st.success(f"📋 **Özet:** Bu dönem önceki dönemden iyi: {', '.join(iyiler)}. Böyle devam. 👏")
    else:
        st.info("📋 **Özet:** İki dönem birbirine yakın — belirgin değişim yok.")