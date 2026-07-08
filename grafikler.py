import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def uretim_trend_grafigi(uretim_df):
    """Günlere göre üretim ve fire adetlerini çizgi grafikle gösterir."""
    if uretim_df.empty or "tarih" not in uretim_df.columns:
        st.caption("📈 Grafik için henüz yeterli üretim verisi yok. Üretim modülünden kayıt girildikçe burada trend oluşacak.")
        return

    df = uretim_df.copy()
    df["tarih"] = pd.to_datetime(df["tarih"], errors="coerce")
    df["uretilen_adet"] = pd.to_numeric(df["uretilen_adet"], errors="coerce")
    df["fire_adet"] = pd.to_numeric(df["fire_adet"], errors="coerce")
    df = df.dropna(subset=["tarih"])

    if df.empty:
        st.caption("📈 Tarih bilgisi okunabilen üretim kaydı bulunamadı.")
        return

    gunluk = df.groupby(df["tarih"].dt.date)[["uretilen_adet", "fire_adet"]].sum().reset_index()
    gunluk.columns = ["Tarih", "Üretilen (adet)", "Fire (adet)"]

    fig = px.line(
        gunluk,
        x="Tarih",
        y=["Üretilen (adet)", "Fire (adet)"],
        markers=True,
        color_discrete_map={"Üretilen (adet)": "#2E86AB", "Fire (adet)": "#E63946"},
    )
    fig.update_layout(
        legend_title_text="",
        yaxis_title="Adet",
        xaxis_title="",
        margin=dict(l=10, r=10, t=10, b=10),
        height=350,
    )
    fig.update_xaxes(tickformat="%d %b", dtick=86400000)
    st.plotly_chart(fig, use_container_width=True)

def enerji_grafigi(enerji_df):
    """Aylara göre elektrik tüketimi (çubuk) ve fatura tutarı (çizgi) — tek grafikte."""
    gerekli = {"donem", "toplam_tuketim_kwh", "toplam_tutar_tl"}
    if enerji_df.empty or not gerekli.issubset(enerji_df.columns):
        st.caption("⚡ Grafik için henüz enerji verisi yok. Enerji modülünden fatura girildikçe burada grafik oluşacak.")
        return

    df = enerji_df.copy()
    df["toplam_tuketim_kwh"] = pd.to_numeric(df["toplam_tuketim_kwh"], errors="coerce")
    df["toplam_tutar_tl"] = pd.to_numeric(df["toplam_tutar_tl"], errors="coerce")
    df = df.dropna(subset=["donem", "toplam_tuketim_kwh", "toplam_tutar_tl"])
    df = df.sort_values("donem")

    if df.empty:
        st.caption("⚡ Okunabilir enerji kaydı bulunamadı.")
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["donem"], y=df["toplam_tuketim_kwh"],
        name="Tüketim (kWh)", marker_color="#F4A261",
        hovertemplate="%{x}<br>%{y:,.0f} kWh<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["donem"], y=df["toplam_tutar_tl"],
        name="Fatura (TL)", mode="lines+markers",
        line=dict(color="#E63946", width=3), yaxis="y2",
        hovertemplate="%{x}<br>%{y:,.0f} TL<extra></extra>",
    ))
    fig.update_layout(
        yaxis=dict(title="kWh"),
        yaxis2=dict(title="TL", overlaying="y", side="right", showgrid=False),
        xaxis_title="",
        legend=dict(orientation="h", y=1.1),
        margin=dict(l=10, r=10, t=10, b=10),
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

def bakim_grafigi(ariza_df):
    """Makine başına toplam tamir maliyetini yatay çubukla gösterir — en pahalı üstte."""
    gerekli = {"makine_id", "tamir_maliyeti_tl"}
    if ariza_df.empty or not gerekli.issubset(ariza_df.columns):
        st.caption("🛠️ Grafik için henüz arıza kaydı yok. Bakım modülünden kayıt girildikçe burada maliyet karşılaştırması oluşacak.")
        return

    df = ariza_df.copy()
    df["tamir_maliyeti_tl"] = pd.to_numeric(df["tamir_maliyeti_tl"], errors="coerce")
    df = df.dropna(subset=["makine_id", "tamir_maliyeti_tl"])

    if df.empty:
        st.caption("🛠️ Okunabilir arıza kaydı bulunamadı.")
        return

    makine_ozet = df.groupby("makine_id").agg(
        toplam_maliyet=("tamir_maliyeti_tl", "sum"),
        ariza_sayisi=("tamir_maliyeti_tl", "count"),
    ).reset_index().sort_values("toplam_maliyet")

    fig = px.bar(
        makine_ozet,
        x="toplam_maliyet",
        y="makine_id",
        orientation="h",
        color_discrete_sequence=["#E76F51"],
        custom_data=["ariza_sayisi"],
    )
    fig.update_traces(
        hovertemplate="%{y}<br>Toplam: %{x:,.0f} TL<br>Arıza sayısı: %{customdata[0]}<extra></extra>",
    )
    fig.update_layout(
        xaxis_title="Toplam Tamir Maliyeti (TL)",
        yaxis_title="",
        margin=dict(l=10, r=10, t=10, b=10),
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)

def stok_grafigi(stok_df):
    """Malzemelerin kritik seviyeye göre doluluk oranı — kırmızı/sarı/yeşil çubuklar."""
    gerekli = {"malzeme_adi", "mevcut_miktar", "kritik_seviye"}
    if stok_df.empty or not gerekli.issubset(stok_df.columns):
        st.caption("📦 Grafik için henüz stok verisi yok. Stok modülünden kayıt girildikçe burada durum grafiği oluşacak.")
        return

    df = stok_df.copy()
    df["mevcut_miktar"] = pd.to_numeric(df["mevcut_miktar"], errors="coerce")
    df["kritik_seviye"] = pd.to_numeric(df["kritik_seviye"], errors="coerce")
    if "gunluk_tuketim" in df.columns:
        df["gunluk_tuketim"] = pd.to_numeric(df["gunluk_tuketim"], errors="coerce")
    else:
        df["gunluk_tuketim"] = pd.NA
    df = df.dropna(subset=["malzeme_adi", "mevcut_miktar", "kritik_seviye"])
    df = df[df["kritik_seviye"] > 0]

    if df.empty:
        st.caption("📦 Kritik seviyesi tanımlı stok kaydı bulunamadı.")
        return

    # Kritik seviyeye oran: 1.0 = tam kritik sınırda, 2.0 = kritik seviyenin 2 katı stok var
    df["oran"] = df["mevcut_miktar"] / df["kritik_seviye"]

    def renk_sec(oran):
        if oran <= 1.0:
            return "#E63946"  # kırmızı: kritik seviyenin altında/sınırında
        elif oran <= 1.5:
            return "#F4A261"  # sarı/turuncu: yaklaşıyor
        return "#2A9D8F"      # yeşil: rahat

    df["renk"] = df["oran"].apply(renk_sec)
    df["kalan_gun"] = df.apply(
        lambda s: s["mevcut_miktar"] / s["gunluk_tuketim"]
        if pd.notna(s["gunluk_tuketim"]) and s["gunluk_tuketim"] > 0 else None,
        axis=1,
    )
    df["kalan_gun_metin"] = df["kalan_gun"].apply(
        lambda g: f"~{g:,.0f} gün yeter" if g is not None else "günlük tüketim girilmemiş"
    )
    df = df.sort_values("oran")

    fig = go.Figure(go.Bar(
        x=df["oran"],
        y=df["malzeme_adi"],
        orientation="h",
        marker_color=df["renk"],
        customdata=df[["mevcut_miktar", "kritik_seviye", "kalan_gun_metin"]],
        hovertemplate="%{y}<br>Mevcut: %{customdata[0]:,.0f} · Kritik: %{customdata[1]:,.0f}<br>%{customdata[2]}<extra></extra>",
    ))
    fig.add_vline(x=1.0, line_dash="dash", line_color="#E63946",
                  annotation_text="kritik sınır", annotation_position="top")
    fig.update_layout(
        xaxis_title="Kritik seviyeye oran (1.0 = kritik sınır)",
        yaxis_title="",
        margin=dict(l=10, r=10, t=30, b=10),
        height=350,
    )
    st.plotly_chart(fig, use_container_width=True)