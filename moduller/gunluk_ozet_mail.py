import streamlit as st
import pandas as pd
from datetime import datetime
import veritabani
from moduller import mail_gonder

def _ozet_html_uret(saatlik_uretim, parca_kar):
    """Kayıtlı verilerden günün özeti + kritik uyarıları HTML mail olarak hazırlar."""
    veritabani.tablolari_olustur()
    ariza_df = veritabani.veri_oku("arizalar")
    uretim_df = veritabani.veri_oku("uretim")
    stok_df = veritabani.veri_oku("stok")
    makine_df = veritabani.veri_oku("makineler")

    uyarilar = []  # (renk, metin)

    # --- Kritik stok ---
    if not stok_df.empty and {"malzeme_adi", "mevcut_miktar", "kritik_seviye"}.issubset(stok_df.columns):
        s = stok_df.copy()
        s["mevcut_miktar"] = pd.to_numeric(s["mevcut_miktar"], errors="coerce")
        s["kritik_seviye"] = pd.to_numeric(s["kritik_seviye"], errors="coerce")
        for _, r in s.iterrows():
            if pd.notna(r["mevcut_miktar"]) and pd.notna(r["kritik_seviye"]) and r["mevcut_miktar"] <= r["kritik_seviye"]:
                uyarilar.append(("#E63946", f"🔴 STOK: {r['malzeme_adi']} kritik seviyede ({r['mevcut_miktar']:,.0f} kaldı). Sipariş zamanı."))

    # --- Bakımı gecikmiş/yaklaşan makineler (Bakım Takvimi ile aynı mantık) ---
    if not makine_df.empty and "son_bakim_tarihi" in makine_df.columns:
        bugun = datetime.now().date()
        for _, m in makine_df.iterrows():
            son = pd.to_datetime(m.get("son_bakim_tarihi"), errors="coerce")
            if pd.isna(son):
                continue
            son = son.date()
            mid = str(m.get("makine_id", "")).strip()

            adaylar = []
            # Yöntem 1: takvim günü
            periyot_gun = pd.to_numeric(m.get("bakim_periyodu_gun"), errors="coerce")
            if pd.notna(periyot_gun) and periyot_gun > 0:
                adaylar.append(son + pd.Timedelta(days=int(periyot_gun)))
            # Yöntem 2: çalışma saati (saat periyodu ÷ günlük çalışma)
            periyot_saat = pd.to_numeric(m.get("bakim_periyodu_saat"), errors="coerce")
            gunluk_saat = pd.to_numeric(m.get("gunluk_calisma_saat"), errors="coerce")
            if pd.notna(periyot_saat) and periyot_saat > 0 and pd.notna(gunluk_saat) and gunluk_saat > 0:
                adaylar.append(son + pd.Timedelta(days=int(periyot_saat / gunluk_saat)))

            if not adaylar:
                continue
            sonraki = min(adaylar)  # en erken uyaran (temkinli)
            kalan = (sonraki - bugun).days

            if kalan < 0:
                uyarilar.append(("#E63946", f"🔴 BAKIM: {mid} bakımı {abs(kalan)} gün gecikti. Acilen planla."))
            elif kalan <= 14:
                uyarilar.append(("#F4A261", f"🟡 BAKIM: {mid} bakımına {kalan} gün kaldı."))

    # --- Kâr sızıntısı toplamı ---
    sizinti = 0.0
    if not ariza_df.empty and "tamir_maliyeti_tl" in ariza_df.columns:
        sizinti += pd.to_numeric(ariza_df["tamir_maliyeti_tl"], errors="coerce").fillna(0).sum()
    if not uretim_df.empty and "fire_adet" in uretim_df.columns:
        sizinti += pd.to_numeric(uretim_df["fire_adet"], errors="coerce").fillna(0).sum() * parca_kar

    # --- HTML kur ---
    tarih_str = datetime.now().strftime("%d.%m.%Y")
    uyari_html = ""
    if uyarilar:
        for renk, metin in uyarilar:
            uyari_html += f'<li style="color:{renk}; margin-bottom:8px;">{metin}</li>'
    else:
        uyari_html = '<li style="color:#2A9D8F;">🟢 Bugün acil dikkat gerektiren bir durum görünmüyor.</li>'

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width:600px; margin:auto; padding:20px;">
        <h2 style="color:#2E86AB; margin-bottom:4px;">🏭 Fabrika KDS — Günün Özeti</h2>
        <p style="color:#888; margin-top:0;">{tarih_str}</p>

        <div style="background:#f5f5f5; border-radius:8px; padding:14px; margin:16px 0;">
            <div style="font-size:13px; color:#666;">Kayıtlı verilere göre toplam önlenebilir sızıntı</div>
            <div style="font-size:24px; font-weight:bold; color:#E63946;">{sizinti:,.0f} TL</div>
        </div>

        <h3 style="color:#333;">🚨 Dikkat Gerektirenler</h3>
        <ul style="line-height:1.5; padding-left:20px;">
            {uyari_html}
        </ul>

        <p style="color:#aaa; font-size:12px; margin-top:24px;">
            Bu özet kayıtlı verilerden otomatik üretilmiştir. Tutarlar olası minimum değerlerdir, kesin muhasebe rakamı değildir.
        </p>
    </div>
    """
    return html

def goster():
    st.title("📧 Günün Özeti Maili")
    st.caption("O günün kritik uyarılarını (stok, bakım, sızıntı) tek mailde topla, patrona gönder.")

    alici = st.text_input("Maili kime gönderelim? (patron / kendi adresin)")
    p1, p2 = st.columns(2)
    saatlik = p1.number_input("Makine saatte kaç parça üretir?", min_value=0.0, value=100.0, key="ozet_saatlik")
    kar = p2.number_input("Parça başı kâr (TL)", min_value=0.0, value=2.0, key="ozet_kar")

    st.markdown("**Mail önizlemesi:**")
    html = _ozet_html_uret(saatlik, kar)
    st.components.v1.html(html, height=400, scrolling=True)

    if st.button("📨 Özet mailini gönder"):
        if not alici or "@" not in alici:
            st.warning("Lütfen geçerli bir mail adresi gir.")
            return
        with st.spinner("Gönderiliyor..."):
            basarili, mesaj = mail_gonder.mail_gonder(alici, f"Fabrika KDS — Günün Özeti ({datetime.now().strftime('%d.%m.%Y')})", html)
        if basarili:
            st.success(f"✅ {mesaj}")
        else:
            st.error(f"❌ {mesaj}")