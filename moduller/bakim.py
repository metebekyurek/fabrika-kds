import streamlit as st
import pandas as pd
import veritabani
import mqtt_dinleyici

def goster():
    st.title("🛠️ Bakım — Kestirimci Bakım Merkezi")
    st.caption("Arıza kayıtlarından MTBF, duruş maliyeti ve kök neden analizi. Elle giriş veya Excel.")
    # === CANLI SENSÖR AKIŞI (MQTT) ===
    with st.expander("📡 Canlı Sensör Akışı (MQTT) — tıkla aç/kapa", expanded=False):
        if "mqtt_basladi" not in st.session_state:
            mqtt_dinleyici.dinlemeye_basla()
            st.session_state["mqtt_basladi"] = True

        st.caption("Sensörlerden gelen canlı veri. Makine sınırlarıyla anlık kıyaslanır.")

        st.caption("Sensörlerden gelen canlı veri. Makine sınırlarıyla anlık kıyaslanır.")

        otomatik = st.checkbox("🔄 Otomatik yenile (her 3 saniyede)", value=False, key="mqtt_oto")
        if otomatik:
            st.caption("🟢 Canlı mod açık — sayfa kendini yeniliyor.")

        canli = mqtt_dinleyici.olcumleri_al()
        if not canli:
            st.info("⏳ Henüz veri gelmedi. 'sahte_sensor.py' çalışıyor mu? Birkaç saniye sonra 'Yenile'ye bas.")
        else:
            canli_df = pd.DataFrame(canli).tail(10).iloc[::-1]  # son 10, en yeni üstte
            st.dataframe(canli_df, use_container_width=True, hide_index=True)

            # Anlık sınır kontrolü
            makine_df = veritabani.veri_oku("makineler")
            if not makine_df.empty:
                sinir_haritasi = {"yag_sicakligi": "max_yag_sicakligi_c", "titresim": "max_titresim_mm_s", "motor_akimi": "max_motor_akimi_a"}
                for olcum in canli[-4:]:  # son birkaç ölçümü kontrol et
                    param = olcum.get("parametre")
                    if param in sinir_haritasi:
                        m_satir = makine_df[makine_df["makine_id"] == olcum.get("makine_id")]
                        if not m_satir.empty:
                            sinir = pd.to_numeric(m_satir.iloc[0].get(sinir_haritasi[param]), errors="coerce")
                            deger = olcum.get("deger", 0)
                            if pd.notna(sinir) and sinir > 0 and deger > sinir:
                                st.error(f"🔴 CANLI ALARM: **{olcum['makine_id']}** · {param} = {deger} {olcum['birim']} (sınır {sinir:.0f} aşıldı!)")
        # Otomatik yenileme: canlı mod açıksa 3 saniyede bir sayfayı tazele
        if otomatik:
            import time
            time.sleep(3)
            st.rerun()                                                      
    ornek_veri = pd.DataFrame([
        {"makine_id": "PRES-01", "ariza_baslangic": "2026-06-01 08:00", "ariza_bitis": "2026-06-01 12:00",
         "ariza_tipi": "hidrolik", "aciklama": "yağ sızıntısı", "tamir_maliyeti_tl": 3000},
        {"makine_id": "PRES-01", "ariza_baslangic": "2026-06-15 14:00", "ariza_bitis": "2026-06-15 15:30",
         "ariza_tipi": "mekanik", "aciklama": "rulman sesi", "tamir_maliyeti_tl": 1500},
        {"makine_id": "PRES-01", "ariza_baslangic": "2026-06-28 09:00", "ariza_bitis": "2026-06-28 18:00",
         "ariza_tipi": "hidrolik", "aciklama": "valf arızası", "tamir_maliyeti_tl": 5000},
    ])

    st.subheader("Arıza Kayıtları")
    st.caption("Tabloyu düzenle, satır ekle/sil, sonra 'Kaydet'e bas — veriler kalıcı olur.")

    veritabani.tablolari_olustur()

    # Excel'den yükleme — tablo çizilmeden ÖNCE karar veriyoruz
    yuklenen = st.file_uploader("📁 Veya Excel dosyası yükle (.xlsx)", type=["xlsx"], key="bakim_excel")

    if yuklenen is not None:
        try:
            baslangic_veri = pd.read_excel(yuklenen)
            st.success(f"✅ Excel okundu: {len(baslangic_veri)} satır. Aşağıdaki tabloya yansıdı — kontrol edip 'Kaydet'e bas.")
        except Exception as e:
            st.error(f"❌ Excel okunamadı. Sütun başlıkları doğru mu? Hata: {e}")
            baslangic_veri = ornek_veri
    else:
        kayitli = veritabani.veri_oku("arizalar")
        if kayitli.empty:
            baslangic_veri = ornek_veri
        else:
            baslangic_veri = kayitli.drop(columns=["id"]) if "id" in kayitli.columns else kayitli

    df = st.data_editor(
        baslangic_veri,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "makine_id": "Makine",
            "ariza_baslangic": "Arıza Başlangıç",
            "ariza_bitis": "Arıza Bitiş",
            "ariza_tipi": st.column_config.SelectboxColumn("Arıza Tipi", options=["mekanik", "elektrik", "hidrolik", "yazılım", "diğer"]),
            "aciklama": "Açıklama",
            "tamir_maliyeti_tl": st.column_config.NumberColumn("Tamir Maliyeti (TL)", format="%d TL"),
        }
    )

    if st.button("💾 Arıza kayıtlarını kaydet"):
        veritabani.veri_kaydet("arizalar", df)
        st.success("✅ Kaydedildi! Uygulamayı kapatıp açsan bile bu veriler duracak.")

    st.markdown("---")
    st.subheader("📊 Analiz")

    calisilan = df.copy()
    calisilan["baslangic_dt"] = pd.to_datetime(calisilan["ariza_baslangic"], errors="coerce")
    calisilan["bitis_dt"] = pd.to_datetime(calisilan["ariza_bitis"], errors="coerce")
    gecerli = calisilan.dropna(subset=["baslangic_dt", "bitis_dt"])

    if len(gecerli) == 0:
        st.warning("Geçerli tarih içeren arıza kaydı yok. Lütfen tarihleri 'YIL-AY-GÜN SAAT:DK' formatında gir (örn. 2026-06-01 08:00).")
        return

    gecerli["durus_saat"] = (gecerli["bitis_dt"] - gecerli["baslangic_dt"]).dt.total_seconds() / 3600
    toplam_durus = gecerli["durus_saat"].sum()

    makineler = gecerli["makine_id"].unique()
    st.markdown("**Genel Durum**")
    g1, g2, g3 = st.columns(3)
    g1.metric("Toplam Arıza", f"{len(gecerli)} adet")
    g2.metric("Toplam Duruş", f"{toplam_durus:,.1f} saat")
    g3.metric("Makine Sayısı", f"{len(makineler)}")

    st.markdown("**Makine Bazında MTBF (Arızalar Arası Ortalama Süre)**")
    for makine in makineler:
        m_veri = gecerli[gecerli["makine_id"] == makine].sort_values("baslangic_dt")
        if len(m_veri) < 2:
            st.write(f"• **{makine}**: MTBF için en az 2 arıza gerekir (şu an {len(m_veri)} kayıt).")
        else:
            farklar = m_veri["baslangic_dt"].diff().dropna()
            mtbf_gun = farklar.dt.total_seconds().mean() / 86400
            m_durus = m_veri["durus_saat"].sum()
            st.write(f"• **{makine}**: Ortalama her **{mtbf_gun:,.1f} günde** bir arızalanıyor. Toplam duruş: {m_durus:,.1f} saat.")

    st.markdown("---")
    st.subheader("💰 Duruş Maliyeti (Fırsat Maliyeti)")
    st.caption("Makine durunca sadece tamir değil, üretilemeyen parça da kayıptır. Asıl zarar budur.")

    m1, m2 = st.columns(2)
    saatlik_uretim = m1.number_input("Bu makine saatte kaç parça üretir?", min_value=0.0, value=100.0)
    parca_kar = m2.number_input("Parça başı kâr (TL)", min_value=0.0, value=2.0)

    kacan_kar = toplam_durus * saatlik_uretim * parca_kar
    toplam_tamir = gecerli["tamir_maliyeti_tl"].sum()
    gercek_zarar = kacan_kar + toplam_tamir

    st.markdown("**Arızaların Gerçek Bedeli**")
    z1, z2, z3 = st.columns(3)
    z1.metric("Kaçan Üretim Kârı", f"{kacan_kar:,.0f} TL", help="Duruş saati × saatlik üretim × parça kârı")
    z2.metric("Toplam Tamir Gideri", f"{toplam_tamir:,.0f} TL")
    z3.metric("Toplam Gerçek Zarar", f"{gercek_zarar:,.0f} TL", delta_color="inverse")

    st.error(f"🔴 Bu arızalar sana toplam **{gercek_zarar:,.0f} TL**'ye mal oldu. Bunun {kacan_kar:,.0f} TL'si duran üretimden, {toplam_tamir:,.0f} TL'si tamirden.")

    st.markdown("---")
    st.subheader("🔮 Kök Neden ve Önleyici Bakım")
    st.caption("Geçmişe bakıp geleceği uyarır: bir sonraki arıza ne zaman, önlem almak mantıklı mı?")

    en_sik_tip = gecerli["ariza_tipi"].mode()
    if len(en_sik_tip) > 0:
        tip = en_sik_tip.iloc[0]
        tip_sayi = (gecerli["ariza_tipi"] == tip).sum()
        st.info(f"🔍 **Olası kök neden:** Arızaların {tip_sayi}/{len(gecerli)}'i **{tip}** kaynaklı. Bu sistemi öncelikli kontrol ettirmek riski azaltır.")

    ortalama_zarar = gercek_zarar / len(gecerli)

    st.markdown("**Önleyici Bakım Kararı**")
    onleyici_maliyet = st.number_input(
        "Önleyici bakım/tamir maliyeti (ustandan aldığın fiyat, TL)",
        min_value=0.0, value=3000.0,
        help="Sistem bunu tahmin etmez — usta fiyatını sen gir."
    )

    k1, k2 = st.columns(2)
    k1.metric("Önlem alırsan (maliyet)", f"{onleyici_maliyet:,.0f} TL")
    k2.metric("Arızayı beklersen (olası zarar)", f"{ortalama_zarar:,.0f} TL",
              help="Geçmiş arıza başına ortalama gerçek zarar (tamir + duran üretim)")

    if ortalama_zarar > onleyici_maliyet:
        kazanc = ortalama_zarar - onleyici_maliyet
        st.success(f"🟢 **Önlem almak mantıklı.** Şimdi {onleyici_maliyet:,.0f} TL harcayıp, olası bir arızanın ~{ortalama_zarar:,.0f} TL'lik bedelini önleyebilirsin. Olası minimum net kazanç: **{kazanc:,.0f} TL**.")
    else:
        st.warning(f"🟡 Bu durumda önleyici bakım maliyeti ({onleyici_maliyet:,.0f} TL), ortalama arıza zararından ({ortalama_zarar:,.0f} TL) yüksek. Beklemek şimdilik daha ekonomik olabilir — ama arıza sıklığı artarsa bu değişir.")
    st.markdown("---")
    st.subheader("📡 Canlı Ölçüm Takibi (Sensör / Excel)")
    st.caption("Makine ölçümlerini gir. Sistem, Makineler sayfasındaki kritik sınırlarla kıyaslayıp uyarır.")

    olcum_ornek = pd.DataFrame([
        {"makine_id": "PRES-01", "zaman": "2026-07-08 10:00", "parametre": "yag_sicakligi", "deger": 75, "birim": "°C"},
        {"makine_id": "PRES-01", "zaman": "2026-07-08 10:00", "parametre": "titresim", "deger": 3.2, "birim": "mm/s"},
        {"makine_id": "CNC-01", "zaman": "2026-07-08 10:00", "parametre": "yag_sicakligi", "deger": 60, "birim": "°C"},
        {"makine_id": "CNC-01", "zaman": "2026-07-08 10:00", "parametre": "titresim", "deger": 3.5, "birim": "mm/s"},
    ])

    olcum_yuklenen = st.file_uploader("📁 Ölçüm Excel'i yükle (.xlsx)", type=["xlsx"], key="olcum_excel")
    if olcum_yuklenen is not None:
        try:
            olcum_baslangic = pd.read_excel(olcum_yuklenen)
            st.success(f"✅ Ölçüm Excel'i okundu: {len(olcum_baslangic)} satır.")
        except Exception as e:
            st.error(f"❌ Okunamadı. Hata: {e}")
            olcum_baslangic = olcum_ornek
    else:
        olcum_kayitli = veritabani.veri_oku("olcumler")
        if olcum_kayitli.empty:
            olcum_baslangic = olcum_ornek
        else:
            olcum_baslangic = olcum_kayitli.drop(columns=["id"]) if "id" in olcum_kayitli.columns else olcum_kayitli

    olcum_df = st.data_editor(
        olcum_baslangic,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "makine_id": "Makine",
            "zaman": "Zaman",
            "parametre": st.column_config.SelectboxColumn("Parametre", options=["titresim", "yag_sicakligi", "motor_sicakligi", "motor_akimi", "basinc", "devir"]),
            "deger": st.column_config.NumberColumn("Değer", format="%.1f"),
            "birim": "Birim",
        }
    )

    if st.button("💾 Ölçümleri kaydet"):
        veritabani.veri_kaydet("olcumler", olcum_df)
        st.success("✅ Ölçümler kaydedildi.")

    # === SINIR KONTROLÜ: ölçümü Makine Kimlik Kartı ile kıyasla ===
    st.markdown("**🚦 Sınır Kontrolü**")
    makine_df = veritabani.veri_oku("makineler")

    if makine_df.empty:
        st.warning("⚠️ Henüz makine tanımlı değil. Sınır kontrolü için önce 'Makineler' sayfasından kimlik kartı gir ve kaydet.")
    else:
        # Parametre adı -> Kimlik Kartı'ndaki sınır sütunu eşleşmesi
        sinir_haritasi = {
            "yag_sicakligi": "max_yag_sicakligi_c",
            "titresim": "max_titresim_mm_s",
            "motor_akimi": "max_motor_akimi_a",
        }

        uyari_cikti = False
        olcum_calisilan = olcum_df.copy()
        olcum_calisilan["deger"] = pd.to_numeric(olcum_calisilan["deger"], errors="coerce")

        for _, olcum in olcum_calisilan.iterrows():
            m_id = olcum["makine_id"]
            param = olcum["parametre"]
            deger = olcum["deger"]

            if param not in sinir_haritasi or pd.isna(deger):
                continue

            sinir_kolonu = sinir_haritasi[param]
            makine_satiri = makine_df[makine_df["makine_id"] == m_id]

            if makine_satiri.empty or sinir_kolonu not in makine_satiri.columns:
                continue

            sinir = pd.to_numeric(makine_satiri.iloc[0][sinir_kolonu], errors="coerce")
            if pd.isna(sinir) or sinir == 0:
                continue

            if deger > sinir:
                uyari_cikti = True
                asim = ((deger - sinir) / sinir) * 100
                st.error(f"🔴 **{m_id}** · {param}: ölçülen **{deger:.1f}** {olcum['birim']}, kritik sınır **{sinir:.0f}**. Sınır %{asim:.0f} aşıldı — **olası arıza riski, kontrol ettir.**")
            elif deger > sinir * 0.9:
                uyari_cikti = True
                st.warning(f"🟡 **{m_id}** · {param}: ölçülen **{deger:.1f}** {olcum['birim']}, sınıra ({sinir:.0f}) yaklaşıyor. İzlemede tut.")

        if not uyari_cikti:
            st.success("🟢 Tüm ölçümler kritik sınırların altında. Makineler sağlıklı görünüyor.")