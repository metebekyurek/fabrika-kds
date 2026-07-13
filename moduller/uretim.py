import streamlit as st
import pandas as pd
import veritabani


def goster():
    st.title("🔧 Üretim — Kota ve Sapma Raporu")
    st.caption("Hedef, gerçekleşen ve fire takibi. Sadece sapma dili — maaş/prim/İK yok.")
    
    ornek_veri = pd.DataFrame([
        {"tarih": "2026-06-01", "vardiya": "gündüz", "makine_id": "PRES-01", "operator_id": "OP-01",
         "urun_kodu": "URN-A", "hedef_adet": 800, "uretilen_adet": 760, "fire_adet": 20, "fire_nedeni": "kalıp",
         "planlanan_sure_dk": 480, "durus_dk": 45, "ideal_hiz_adet_dk": 2.0},
        {"tarih": "2026-06-01", "vardiya": "gece", "makine_id": "PRES-01", "operator_id": "OP-02",
         "urun_kodu": "URN-A", "hedef_adet": 800, "uretilen_adet": 690, "fire_adet": 35, "fire_nedeni": "hammadde",
         "planlanan_sure_dk": 480, "durus_dk": 70, "ideal_hiz_adet_dk": 2.0},
        {"tarih": "2026-06-02", "vardiya": "gündüz", "makine_id": "PRES-01", "operator_id": "OP-01",
         "urun_kodu": "URN-A", "hedef_adet": 800, "uretilen_adet": 820, "fire_adet": 10, "fire_nedeni": "ayar",
         "planlanan_sure_dk": 480, "durus_dk": 20, "ideal_hiz_adet_dk": 2.0},
    ])

    st.subheader("Üretim Kayıtları")
    st.caption("Tabloyu düzenle, satır ekle/sil, sonra 'Kaydet'e bas — veriler kalıcı olur.")

    veritabani.tablolari_olustur()

    yuklenen = st.file_uploader("📁 Veya Excel dosyası yükle (.xlsx)", type=["xlsx"], key="uretim_excel")

    if yuklenen is not None:
        try:
            baslangic_veri = pd.read_excel(yuklenen)
            st.success(f"✅ Excel okundu: {len(baslangic_veri)} satır. Kontrol edip 'Kaydet'e bas.")
        except Exception as e:
            st.error(f"❌ Excel okunamadı. Sütun başlıkları doğru mu? Hata: {e}")
            baslangic_veri = ornek_veri
    else:
        kayitli = veritabani.veri_oku("uretim")
        if kayitli.empty:
            baslangic_veri = ornek_veri
        else:
            baslangic_veri = kayitli.drop(columns=["id"]) if "id" in kayitli.columns else kayitli
        # Eski kayıtlarda olmayan yeni sütunları boş olarak ekle (OEE için)
    for yeni_kolon in ["planlanan_sure_dk", "durus_dk", "ideal_hiz_adet_dk"]:
        if yeni_kolon not in baslangic_veri.columns:
            baslangic_veri[yeni_kolon] = None
    df = st.data_editor(
        baslangic_veri,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "tarih": "Tarih",
            "vardiya": st.column_config.SelectboxColumn("Vardiya", options=["gündüz", "gece", "tam gün"]),
            "makine_id": "Makine",
            "operator_id": "Operatör",
            "urun_kodu": "Ürün",
            "hedef_adet": st.column_config.NumberColumn("Hedef", format="%d"),
            "uretilen_adet": st.column_config.NumberColumn("Üretilen", format="%d"),
            "fire_adet": st.column_config.NumberColumn("Fire", format="%d"),
            "fire_nedeni": st.column_config.SelectboxColumn("Fire Nedeni", options=["ayar", "hammadde", "kalıp", "operatör", "diğer"]),
            "planlanan_sure_dk": st.column_config.NumberColumn("Planlanan Süre (dk)", format="%d dk", help="Vardiyada makinenin çalışması planlanan süre. 8 saat = 480 dk"),
            "durus_dk": st.column_config.NumberColumn("Duruş (dk)", format="%d dk", help="Arıza, ayar, bekleme — makinenin durduğu toplam dakika"),
            "ideal_hiz_adet_dk": st.column_config.NumberColumn("İdeal Hız (adet/dk)", format="%.1f", help="Makine ideal koşulda dakikada kaç adet üretir"),
        }
    )

    if st.button("💾 Üretim kayıtlarını kaydet"):
        veritabani.veri_kaydet("uretim", df)
        st.success("✅ Kaydedildi! Uygulamayı kapatıp açsan bile bu veriler duracak.")

    st.markdown("---")
    st.subheader("📊 Sapma Analizi")

    calisilan = df.copy()
    calisilan["uretilen_adet"] = pd.to_numeric(calisilan["uretilen_adet"], errors="coerce")
    calisilan["hedef_adet"] = pd.to_numeric(calisilan["hedef_adet"], errors="coerce")
    calisilan["fire_adet"] = pd.to_numeric(calisilan["fire_adet"], errors="coerce")
    gecerli = calisilan.dropna(subset=["uretilen_adet"])

    if len(gecerli) == 0:
        st.warning("Geçerli üretim kaydı yok. Lütfen 'Üretilen' sütununu doldur.")
        return

    toplam_uretim = gecerli["uretilen_adet"].sum()
    toplam_fire = gecerli["fire_adet"].sum()
    fire_orani = (toplam_fire / (toplam_uretim + toplam_fire) * 100) if (toplam_uretim + toplam_fire) > 0 else 0

    g1, g2, g3 = st.columns(3)
    g1.metric("Toplam Üretim", f"{toplam_uretim:,.0f} adet")
    g2.metric("Toplam Fire", f"{toplam_fire:,.0f} adet")
    g3.metric("Fire Oranı", f"%{fire_orani:,.1f}")

    hedefli = gecerli.dropna(subset=["hedef_adet"])
    hedefli = hedefli[hedefli["hedef_adet"] > 0]
    if len(hedefli) > 0:
        st.markdown("**Hedefe Göre Sapma**")
        for _, satir in hedefli.iterrows():
            sapma = ((satir["uretilen_adet"] - satir["hedef_adet"]) / satir["hedef_adet"]) * 100
            etiket = f"{satir['tarih']} · {satir['vardiya']} · {satir['operator_id']}"
            if sapma >= 0:
                st.write(f"• {etiket}: hedefin **%{sapma:,.1f} üstünde** ✅")
            else:
                st.write(f"• {etiket}: hedefin **%{abs(sapma):,.1f} altında** ⚠️")

    st.markdown("---")
    st.subheader("🔍 Fire Nedeni Analizi")
    st.caption("Firelerin çoğu nereden geliyor? Asıl kaybın kaynağını gösterir.")

    if gecerli["fire_adet"].sum() > 0:
        fire_grup = gecerli.groupby("fire_nedeni")["fire_adet"].sum().sort_values(ascending=False)
        en_buyuk_neden = fire_grup.index[0]
        en_buyuk_deger = fire_grup.iloc[0]
        oran = (en_buyuk_deger / gecerli["fire_adet"].sum()) * 100
        st.warning(f"⚠️ En büyük fire kaynağı: **{en_buyuk_neden}** (toplam firenin %{oran:,.0f}'i, {en_buyuk_deger:,.0f} adet). Önce buraya odaklan.")
        st.markdown("**Nedene göre fire dağılımı:**")
        for neden, adet in fire_grup.items():
            st.write(f"• {neden}: {adet:,.0f} adet")
    else:
        st.info("Fire kaydı yok veya fire nedeni girilmemiş.")

    st.markdown("---")
    st.subheader("🌙 Vardiya Karşılaştırması")
    st.caption("Hangi vardiya daha verimli? Fark varsa görünür.")

    vardiya_grup = gecerli.groupby("vardiya").agg(
        toplam_uretim=("uretilen_adet", "sum"),
        toplam_fire=("fire_adet", "sum")
    )
    vardiya_grup["fire_orani"] = (vardiya_grup["toplam_fire"] / (vardiya_grup["toplam_uretim"] + vardiya_grup["toplam_fire"]) * 100)
    st.markdown("**Vardiya bazında:**")
    for vardiya, satir in vardiya_grup.iterrows():
        st.write(f"• **{vardiya}**: {satir['toplam_uretim']:,.0f} adet üretim, fire oranı %{satir['fire_orani']:,.1f}")
   
    