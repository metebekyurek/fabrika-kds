import streamlit as st
import pandas as pd
import veritabani
from grafikler import stok_grafigi


def goster():
    st.title("📦 Stok — Envanter ve Tedarikçi")
    st.caption("Stok takibi, kritik seviye uyarısı ve tedarikçi karşılaştırması. Elle veya Excel.")

    ornek_veri = pd.DataFrame([
        {"malzeme_adi": "5mm sac levha", "tur": "hammadde", "birim": "kg",
         "mevcut_miktar": 1200, "kritik_seviye": 500, "gunluk_tuketim": 150, "birim_maliyet_tl": 45},
        {"malzeme_adi": "M8 cıvata", "tur": "hammadde", "birim": "adet",
         "mevcut_miktar": 3000, "kritik_seviye": 1000, "gunluk_tuketim": 200, "birim_maliyet_tl": 2},
        {"malzeme_adi": "URN-A mamul", "tur": "mamul", "birim": "adet",
         "mevcut_miktar": 400, "kritik_seviye": 200, "gunluk_tuketim": 250, "birim_maliyet_tl": 120},
    ])

    st.subheader("Stok Durumu")
    st.caption("Tabloyu düzenle, 'Kaydet'e bas — veriler kalıcı olur. Günlük tüketim girersen 'kaç gün yeter' hesaplanır.")

    veritabani.tablolari_olustur()

    yuklenen = st.file_uploader("📁 Veya Excel dosyası yükle (.xlsx)", type=["xlsx"], key="stok_excel")

    if yuklenen is not None:
        try:
            baslangic_veri = pd.read_excel(yuklenen)
            st.success(f"✅ Excel okundu: {len(baslangic_veri)} satır. Kontrol edip 'Kaydet'e bas.")
        except Exception as e:
            st.error(f"❌ Excel okunamadı. Sütun başlıkları doğru mu? Hata: {e}")
            baslangic_veri = ornek_veri
    else:
        kayitli = veritabani.veri_oku("stok")
        if kayitli.empty:
            baslangic_veri = ornek_veri
        else:
            baslangic_veri = kayitli.drop(columns=["id"]) if "id" in kayitli.columns else kayitli

    df = st.data_editor(
        baslangic_veri,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "malzeme_adi": "Malzeme",
            "tur": st.column_config.SelectboxColumn("Tür", options=["hammadde", "yarı mamul", "mamul"]),
            "birim": st.column_config.SelectboxColumn("Birim", options=["kg", "adet", "metre", "litre"]),
            "mevcut_miktar": st.column_config.NumberColumn("Mevcut", format="%d"),
            "kritik_seviye": st.column_config.NumberColumn("Kritik Seviye", format="%d"),
            "gunluk_tuketim": st.column_config.NumberColumn("Günlük Tüketim", format="%d"),
            "birim_maliyet_tl": st.column_config.NumberColumn("Birim Maliyet (TL)", format="%d TL"),
        }
    )

    if st.button("💾 Stok kayıtlarını kaydet"):
        veritabani.veri_kaydet("stok", df)
        st.success("✅ Kaydedildi! Uygulamayı kapatıp açsan bile bu veriler duracak.")

    st.markdown("---")
    st.subheader("🚨 Kritik Seviye Uyarıları")

    calisilan = df.copy()
    for kol in ["mevcut_miktar", "kritik_seviye", "gunluk_tuketim", "birim_maliyet_tl"]:
        calisilan[kol] = pd.to_numeric(calisilan[kol], errors="coerce")
    gecerli = calisilan.dropna(subset=["mevcut_miktar"])

    if len(gecerli) == 0:
        st.warning("Geçerli stok kaydı yok.")
        return

    gecerli["stok_degeri"] = gecerli["mevcut_miktar"] * gecerli["birim_maliyet_tl"].fillna(0)
    toplam_deger = gecerli["stok_degeri"].sum()
    st.metric("Toplam Stok Değeri", f"{toplam_deger:,.0f} TL")
    stok_grafigi(gecerli)
     

    uyari_var = False
    for _, satir in gecerli.iterrows():
        mevcut = satir["mevcut_miktar"]
        kritik = satir["kritik_seviye"] if pd.notna(satir["kritik_seviye"]) else 0
        gunluk = satir["gunluk_tuketim"] if pd.notna(satir["gunluk_tuketim"]) else 0

        kalan_gun = (mevcut / gunluk) if gunluk > 0 else None
        gun_metni = f" (~{kalan_gun:,.0f} günlük)" if kalan_gun is not None else ""

        if mevcut <= kritik:
            uyari_var = True
            st.error(f"🔴 **{satir['malzeme_adi']}**: {mevcut:,.0f} {satir['birim']} kaldı — kritik seviyenin ({kritik:,.0f}) altında!{gun_metni} Sipariş zamanı.")
        elif kalan_gun is not None and kalan_gun <= 5:
            uyari_var = True
            st.warning(f"🟡 **{satir['malzeme_adi']}**: {mevcut:,.0f} {satir['birim']} kaldı{gun_metni}. Yakında sipariş vermen gerekebilir.")
        else:
            st.write(f"🟢 **{satir['malzeme_adi']}**: {mevcut:,.0f} {satir['birim']}{gun_metni} — yeterli.")

    if not uyari_var:
        st.success("Tüm stoklar yeterli seviyede.")

    st.markdown("---")
    st.subheader("🏷️ Tedarikçi Karnesi")
    st.caption("Aynı malzemeyi kimden almalı? Ucuz ama geç mi, pahalı ama zamanında mı? Sistem kıyaslar, kararı sen verirsin.")

    ted_veri = pd.DataFrame([
        {"tedarikci": "A Firması", "malzeme": "5mm sac levha", "birim_fiyat_tl": 42, "ortalama_gecikme_gun": 4},
        {"tedarikci": "B Firması", "malzeme": "5mm sac levha", "birim_fiyat_tl": 47, "ortalama_gecikme_gun": 0},
        {"tedarikci": "C Firması", "malzeme": "5mm sac levha", "birim_fiyat_tl": 45, "ortalama_gecikme_gun": 1},
    ])

    ted_kayitli = veritabani.veri_oku("tedarikciler")
    if ted_kayitli.empty:
        ted_baslangic = ted_veri
    else:
        ted_baslangic = ted_kayitli.drop(columns=["id"]) if "id" in ted_kayitli.columns else ted_kayitli

    ted_df = st.data_editor(
        ted_baslangic,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "tedarikci": "Tedarikçi",
            "malzeme": "Malzeme",
            "birim_fiyat_tl": st.column_config.NumberColumn("Birim Fiyat (TL)", format="%d TL"),
            "ortalama_gecikme_gun": st.column_config.NumberColumn("Ort. Gecikme (gün)", format="%d gün"),
        }
    )

    if st.button("💾 Tedarikçileri kaydet"):
        veritabani.veri_kaydet("tedarikciler", ted_df)
        st.success("✅ Tedarikçi bilgileri kaydedildi.")

    ted_calisilan = ted_df.copy()
    ted_calisilan["birim_fiyat_tl"] = pd.to_numeric(ted_calisilan["birim_fiyat_tl"], errors="coerce")
    ted_calisilan["ortalama_gecikme_gun"] = pd.to_numeric(ted_calisilan["ortalama_gecikme_gun"], errors="coerce")
    ted_gecerli = ted_calisilan.dropna(subset=["birim_fiyat_tl"])

    if len(ted_gecerli) > 0:
        en_ucuz = ted_gecerli.loc[ted_gecerli["birim_fiyat_tl"].idxmin()]
        en_hizli = ted_gecerli.loc[ted_gecerli["ortalama_gecikme_gun"].idxmin()]
        st.markdown("**Kıyaslama**")
        st.write(f"• 💰 En ucuz: **{en_ucuz['tedarikci']}** ({en_ucuz['birim_fiyat_tl']:,.0f} TL) — ama ortalama {en_ucuz['ortalama_gecikme_gun']:,.0f} gün gecikme.")
        st.write(f"• ⏱️ En zamanında: **{en_hizli['tedarikci']}** ({en_hizli['ortalama_gecikme_gun']:,.0f} gün gecikme) — birim fiyat {en_hizli['birim_fiyat_tl']:,.0f} TL.")
        st.info("ℹ️ Bu bir kıyaslamadır, alım emri değildir. Fiyat ile teslim riskini birlikte değerlendirip kararı sen verirsin.")

    st.markdown("---")
    st.subheader("⏳ Sipariş Gecikme Maliyeti")
    st.caption("Bir malzeme siparişi gecikirse üretim durur. Bu gecikme sana kaç TL'ye mal olur?")

    gm1, gm2, gm3 = st.columns(3)
    gecikme_gun = gm1.number_input("Kaç gün gecikti / gecikecek?", min_value=0.0, value=3.0)
    gunluk_uretim_kaybi = gm2.number_input("Günlük üretim kaybı (adet)", min_value=0.0, value=800.0)
    parca_kar_gecikme = gm3.number_input("Parça başı kâr (TL)", min_value=0.0, value=2.0)

    gecikme_maliyeti = gecikme_gun * gunluk_uretim_kaybi * parca_kar_gecikme

    if gecikme_maliyeti > 0:
        st.error(f"🔴 Bu gecikme sana olası minimum **{gecikme_maliyeti:,.0f} TL** kâr kaybettiriyor ({gecikme_gun:,.0f} gün × {gunluk_uretim_kaybi:,.0f} adet × {parca_kar_gecikme:,.0f} TL). Bir sonraki siparişte teslim güvenilirliği yüksek tedarikçiyi tercih etmek bu kaybı önleyebilir.")