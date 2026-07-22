import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
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

    # Kayıtların hangi tarih aralığını kapsadığını göster — rakamların bağlamı belli olsun
    _tarihler = []
    if not uretim_df.empty and "tarih" in uretim_df.columns:
        _tarihler += list(pd.to_datetime(uretim_df["tarih"], errors="coerce").dropna())
    if not ariza_df.empty and "ariza_baslangic" in ariza_df.columns:
        _tarihler += list(pd.to_datetime(ariza_df["ariza_baslangic"], errors="coerce").dropna())
    if _tarihler:
        _ilk, _son = min(_tarihler), max(_tarihler)
        _gun = (_son - _ilk).days + 1
        st.caption(f"📅 Sistemdeki kayıtlar **{_ilk.strftime('%d.%m.%Y')} – {_son.strftime('%d.%m.%Y')}** "
                   f"arasını ({_gun} gün) kapsıyor. Aşağıdaki kartlar **son 7 günü** gösterir; "
                   f"toplam rakamlar için 💸 Kâr Sızıntısı ve 📈 Dönem Kıyaslama sayfalarına bak.")
    else:
        st.caption("📅 Henüz tarihli kayıt yok — modüllere veri girdikçe bu özet dolacak.")

    _sinir = datetime.now() - timedelta(days=7)

    st.markdown("**Son 7 Gün**")
    k1, k2, k3, k4 = st.columns(4)

    # --- Arıza & tamir (son 7 gün) ---
    if not ariza_df.empty and "ariza_baslangic" in ariza_df.columns:
        _a7 = ariza_df.copy()
        _a7["bas"] = pd.to_datetime(_a7["ariza_baslangic"], errors="coerce")
        _a7 = _a7[_a7["bas"] >= _sinir]
        _tamir7 = pd.to_numeric(_a7["tamir_maliyeti_tl"], errors="coerce").sum() if "tamir_maliyeti_tl" in _a7.columns else 0
        k1.metric("🛠️ Arıza", f"{len(_a7)} adet", help="Son 7 günde kaydedilen arıza sayısı")
        k2.metric("💸 Tamir Gideri", f"{_tamir7:,.0f} TL", help="Son 7 gündeki tamir maliyetleri")
    else:
        k1.metric("🛠️ Arıza", "0 adet")
        k2.metric("💸 Tamir Gideri", "0 TL")

    # --- Üretim & fire (son 7 gün) ---
    if not uretim_df.empty and {"tarih", "uretilen_adet"}.issubset(uretim_df.columns):
        _u7 = uretim_df.copy()
        _u7["tarih_dt"] = pd.to_datetime(_u7["tarih"], errors="coerce")
        _u7 = _u7[_u7["tarih_dt"] >= _sinir]
        _uret7 = pd.to_numeric(_u7["uretilen_adet"], errors="coerce").sum()
        _fire7 = pd.to_numeric(_u7["fire_adet"], errors="coerce").sum() if "fire_adet" in _u7.columns else 0
        _oran7 = (_fire7 / (_uret7 + _fire7) * 100) if (_uret7 + _fire7) > 0 else 0
        k3.metric("🔧 Üretim", f"{_uret7:,.0f} adet", help="Son 7 günde üretilen toplam adet")
        k4.metric("♻️ Fire Oranı", f"%{_oran7:,.1f}", help="Son 7 günün fire oranı")
    else:
        k3.metric("🔧 Üretim", "0 adet")
        k4.metric("♻️ Fire Oranı", "%0")

    st.subheader("📈 Üretim Trendi")
    uretim_trend_grafigi(uretim_df)

    st.markdown("---")
    st.subheader("🚨 Dikkat Gerektirenler")
    uyari_bulundu = False

    def _git_butonu(hedef_sayfa, anahtar):
        """Uyarının yanına minik 'git' butonu koyar — tıklayınca ilgili sayfayı açar."""
        if st.button("➜ Git", key=anahtar, use_container_width=True):
            st.session_state["aktif_sayfa"] = hedef_sayfa
            st.rerun()

    if not stok_df.empty and "mevcut_miktar" in stok_df.columns:
        for i, (_, s) in enumerate(stok_df.iterrows()):
            mevcut = pd.to_numeric(s.get("mevcut_miktar"), errors="coerce")
            kritik = pd.to_numeric(s.get("kritik_seviye"), errors="coerce")
            if pd.notna(mevcut) and pd.notna(kritik) and mevcut <= kritik:
                u1, u2 = st.columns([6, 1])
                u1.error(f"🔴 Stok: **{s['malzeme_adi']}** kritik seviyede ({mevcut:,.0f} kaldı). Sipariş zamanı.")
                with u2:
                    _git_butonu("Stok", f"git_stok_{i}")
                uyari_bulundu = True

    if not ariza_df.empty and "ariza_baslangic" in ariza_df.columns:
        a = ariza_df.copy()
        a["bas"] = pd.to_datetime(a["ariza_baslangic"], errors="coerce")
        son7 = a[a["bas"] >= _sinir]
        if len(son7) > 0:
            u1, u2 = st.columns([6, 1])
            u1.warning(f"🟡 Bakım: son 7 günde **{len(son7)} arıza** kaydedildi. Detay için Bakım modülüne bak.")
            with u2:
                _git_butonu("Bakım", "git_bakim")
            uyari_bulundu = True

    # Bakımı gecikmiş makineler (Bakım Takvimi'nden)
    makine_df = veritabani.veri_oku("makineler")
    if not makine_df.empty and "son_bakim_tarihi" in makine_df.columns:
        bugun = datetime.now().date()
        gecikenler = []
        for _, m in makine_df.iterrows():
            son = pd.to_datetime(m.get("son_bakim_tarihi"), errors="coerce")
            periyot = pd.to_numeric(m.get("bakim_periyodu_gun"), errors="coerce")
            if pd.notna(son) and pd.notna(periyot) and periyot > 0:
                sonraki = son.date() + timedelta(days=int(periyot))
                if (sonraki - bugun).days < 0:
                    gecikenler.append(str(m.get("makine_id", "")).strip())
        if gecikenler:
            u1, u2 = st.columns([6, 1])
            u1.error(f"🔴 Bakım gecikmiş: **{', '.join(gecikenler[:5])}**{' ve diğerleri' if len(gecikenler) > 5 else ''}. Takvime bak.")
            with u2:
                _git_butonu("Bakım Takvimi", "git_takvim")
            uyari_bulundu = True

    if not uyari_bulundu:
        st.success("🟢 Şu an acil dikkat gerektiren bir durum görünmüyor.")

    st.markdown("---")
    st.subheader("💱 Güncel Kurlar")
    doviz_seridi_goster()