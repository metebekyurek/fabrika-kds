import streamlit as st
import pandas as pd
import streamlit as st
import pandas as pd
import requests
import veritabani
from grafikler import enerji_grafigi
from moduller import ayarlar 

def goster():
    st.title("⚡ Enerji — Tüketim ve Fatura Analizi")
    st.caption("Geçmiş faturalardan tahmini fatura, tarife optimizasyonu ve GES takibi.")

    ornek_veri = pd.DataFrame([
        {"donem": "2026-01", "toplam_tuketim_kwh": 12000, "toplam_tutar_tl": 34200},
        {"donem": "2026-02", "toplam_tuketim_kwh": 11500, "toplam_tutar_tl": 32775},
        {"donem": "2026-03", "toplam_tuketim_kwh": 13200, "toplam_tutar_tl": 37620},
        {"donem": "2026-04", "toplam_tuketim_kwh": 12800, "toplam_tutar_tl": 36480},
        {"donem": "2026-05", "toplam_tuketim_kwh": 14100, "toplam_tutar_tl": 40185},
        {"donem": "2026-06", "toplam_tuketim_kwh": 15300, "toplam_tutar_tl": 43605},
    ])

    st.subheader("Geçmiş Faturalar")
    st.caption("Faturalarını gir, 'Kaydet'e bas — veriler kalıcı olur. Sistem tüketim desenini öğrenip gelecek faturayı tahmin eder.")

    veritabani.tablolari_olustur()

    yuklenen = st.file_uploader("📁 Veya Excel dosyası yükle (.xlsx)", type=["xlsx"], key="enerji_excel")

    if yuklenen is not None:
        try:
            baslangic_veri = pd.read_excel(yuklenen)
            st.success(f"✅ Excel okundu: {len(baslangic_veri)} satır. Kontrol edip 'Kaydet'e bas.")
        except Exception as e:
            st.error(f"❌ Excel okunamadı. Sütun başlıkları doğru mu? Hata: {e}")
            baslangic_veri = ornek_veri
    else:
        kayitli = veritabani.veri_oku("enerji")
        if kayitli.empty:
            baslangic_veri = ornek_veri
        else:
            baslangic_veri = kayitli.drop(columns=["id"]) if "id" in kayitli.columns else kayitli

    df = st.data_editor(
        baslangic_veri,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "donem": "Dönem (YYYY-AA)",
            "toplam_tuketim_kwh": st.column_config.NumberColumn("Tüketim (kWh)", format="%d"),
            "toplam_tutar_tl": st.column_config.NumberColumn("Tutar (TL)", format="%d TL"),
        }
    )

    if st.button("💾 Faturaları kaydet"):
        veritabani.veri_kaydet("enerji", df)
        st.success("✅ Kaydedildi! Uygulamayı kapatıp açsan bile bu veriler duracak.")
    st.markdown("---")
    st.subheader("📊 Tüketim ve Fatura Grafiği")
    enerji_grafigi(df)
    
    st.markdown("---")
    st.subheader("📈 Tahmini Gelecek Fatura")

    calisilan = df.copy()
    calisilan["toplam_tuketim_kwh"] = pd.to_numeric(calisilan["toplam_tuketim_kwh"], errors="coerce")
    calisilan["toplam_tutar_tl"] = pd.to_numeric(calisilan["toplam_tutar_tl"], errors="coerce")
    gecerli = calisilan.dropna(subset=["toplam_tuketim_kwh", "toplam_tutar_tl"])

    if len(gecerli) < 3:
        st.warning("Tahmin için en az 3 fatura gerekir. Ne kadar çok fatura, o kadar isabetli tahmin.")
        return

    # Ortalama birim fiyat (tutar / tüketim)
    gecerli["birim_fiyat"] = gecerli["toplam_tutar_tl"] / gecerli["toplam_tuketim_kwh"]
    ortalama_birim = gecerli["birim_fiyat"].mean()

    # Tüketim trendi: son 3 ayın ortalaması
    son3 = gecerli.tail(3)
    tahmini_tuketim = son3["toplam_tuketim_kwh"].mean()

    # Tahmini fatura aralığı (±%8 belirsizlik)
    tahmini_tutar = tahmini_tuketim * ortalama_birim
    alt = tahmini_tutar * 0.92
    ust = tahmini_tutar * 1.08

    t1, t2, t3 = st.columns(3)
    t1.metric("Tahmini Tüketim", f"{tahmini_tuketim:,.0f} kWh", help="Son 3 ayın ortalaması")
    t2.metric("Ortalama Birim Fiyat", f"{ortalama_birim:,.2f} TL/kWh")
    t3.metric("Tahmini Fatura", f"{alt:,.0f} – {ust:,.0f} TL")

    st.info(f"📊 Bir sonraki faturanız tahminen **{alt:,.0f} – {ust:,.0f} TL** aralığında olacak. Bu tahmin {len(gecerli)} faturaya dayanır; veri arttıkça isabet artar.")
    st.caption("⚠️ Birim fiyat geçmiş faturalardan hesaplanır. Zam/indirim olduysa yeni faturayı girince tahmin güncellenir.")
    st.markdown("---")
    st.subheader("🕐 Tarife Saati Optimizasyonu")
    st.caption("Elektrik gece ucuz, akşam saatleri (puant, 17:00-22:00) en pahalı. İşleri ucuz saate kaydırırsan tasarruf edersin.")

    # Tarife fiyatlarını Fabrika Ayarları'ndan oku
    ayar = ayarlar.ayarlari_oku()
    try:
        varsayilan_gunduz = float(ayar.get("tarife_gunduz", 2.85))
        varsayilan_puant = float(ayar.get("tarife_puant", 4.20))
        varsayilan_gece = float(ayar.get("tarife_gece", 1.60))
    except (ValueError, TypeError):
        varsayilan_gunduz, varsayilan_puant, varsayilan_gece = 2.85, 4.20, 1.60

    st.markdown("**Üç zamanlı tarife fiyatların** (⚙️ Fabrika Ayarları'ndan okunur, buradan geçici değiştirebilirsin):")
    tf1, tf2, tf3 = st.columns(3)
    gunduz_fiyat = tf1.number_input("Gündüz (TL/kWh)", min_value=0.0, value=varsayilan_gunduz)
    puant_fiyat = tf2.number_input("Puant / akşam (TL/kWh)", min_value=0.0, value=varsayilan_puant)
    gece_fiyat = tf3.number_input("Gece (TL/kWh)", min_value=0.0, value=varsayilan_gece)

    # Kaydırılabilir kWh önerisi: kayıtlı faturaların ortalamasından temkinli tahmin
    oneri_kwh = 3000.0
    oneri_kaynagi = "varsayılan değer"
    if len(gecerli) >= 3:
        aylik_ort = gecerli["toplam_tuketim_kwh"].mean()
        oneri_kwh = round(aylik_ort * 0.25 / 100) * 100  # yüzlüğe yuvarla
        oneri_kaynagi = f"kayıtlı {len(gecerli)} faturanın ortalamasından (aylık ~{aylik_ort:,.0f} kWh'in ~%25'i)"

    st.markdown("**Kaydırılabilir tüketim:**")
    st.caption(f"💡 Başlangıç önerisi {oneri_kaynagi} hesaplandı. Kaba bir tahmindir — "
               f"hangi makinelerin gece çalışabileceğini en iyi sen bilirsin, rakamı düzeltebilirsin.")
    ks1, ks2 = st.columns(2)
    kaydirilabilir_kwh = ks1.number_input("Aylık kaç kWh'lik iş geceye kaydırılabilir?", min_value=0.0,
                                          value=float(oneri_kwh),
                                          help="Örn. enerji yoğun makinelerin bir kısmı gece çalıştırılabilirse")
    mevcut_saat = ks2.selectbox("Bu işler şu an hangi saatte yapılıyor?", ["Gündüz", "Puant / akşam"])

    mevcut_fiyat = gunduz_fiyat if mevcut_saat == "Gündüz" else puant_fiyat
    mevcut_maliyet = kaydirilabilir_kwh * mevcut_fiyat
    gece_maliyet = kaydirilabilir_kwh * gece_fiyat
    aylik_tasarruf = mevcut_maliyet - gece_maliyet

    if aylik_tasarruf > 0:
        o1, o2, o3 = st.columns(3)
        o1.metric("Şu anki maliyet", f"{mevcut_maliyet:,.0f} TL/ay")
        o2.metric("Geceye kaydırınca", f"{gece_maliyet:,.0f} TL/ay")
        o3.metric("Aylık tasarruf", f"{aylik_tasarruf:,.0f} TL", delta=f"yılda {aylik_tasarruf*12:,.0f} TL")
        st.success(f"🟢 Bu işleri geceye kaydırırsan olası minimum **{aylik_tasarruf:,.0f} TL/ay** ({aylik_tasarruf*12:,.0f} TL/yıl) tasarruf edersin.")
    else:
        st.info("Girilen fiyatlarla geceye kaydırmanın avantajı görünmüyor. Tarife fiyatlarını kontrol et.")
    st.markdown("---")
    st.subheader("☀️ GES (Güneş Enerjisi) Takibi")
    st.caption("Panel varsa: teorik beklenen üretim ile gerçekleşeni kıyaslar. Hava açıkken düşük üretim = olası kirlilik/arıza.")

    ges_var = st.toggle("Fabrikamda güneş enerjisi paneli var")

    if ges_var:
        gc1, gc2, gc3 = st.columns(3)
        ges_kapasite = gc1.number_input("Panel kapasitesi (kWp)", min_value=0.0, value=10.0,
                                        help="Panelin etiketinde/faturasında yazan kurulu güç. Bilmiyorsan paneli kurana sor.")
        enlem = gc2.number_input("Enlem", value=40.19, format="%.2f", help="Bursa ~40.19. Konumunun enlemini gir.")
        boylam = gc3.number_input("Boylam", value=29.06, format="%.2f", help="Bursa ~29.06.")

        gerceklesen = st.number_input("Bugün panelin ürettiği enerji (kWh)", min_value=0.0, value=45.0)

        if st.button("🌤️ Hava verisini çek ve karşılaştır"):
            try:
                url = (f"https://api.open-meteo.com/v1/forecast?latitude={enlem}&longitude={boylam}"
                       f"&daily=shortwave_radiation_sum&timezone=auto&forecast_days=1")
                cevap = requests.get(url, timeout=10)
                veri = cevap.json()

                # Günlük güneş ışınımı (MJ/m²) -> kWh/m² çevrimi (1 MJ = 0.2778 kWh)
                radyasyon_mj = veri["daily"]["shortwave_radiation_sum"][0]
                radyasyon_kwh = radyasyon_mj * 0.2778

                # Teorik üretim: kapasite × ışınım × performans oranı (PR=0.80)
                # Standart test 1 kW/m² referansına göre normalize
                pr = 0.80
                teorik_uretim = ges_kapasite * radyasyon_kwh * pr

                st.markdown("**Karşılaştırma**")
                r1, r2, r3 = st.columns(3)
                r1.metric("Teorik beklenen", f"{teorik_uretim:,.1f} kWh")
                r2.metric("Gerçekleşen", f"{gerceklesen:,.1f} kWh")
                sapma = ((gerceklesen - teorik_uretim) / teorik_uretim * 100) if teorik_uretim > 0 else 0
                r3.metric("Sapma", f"%{sapma:,.1f}")

                if sapma < -20:
                    st.error(f"🔴 Üretim beklenenin %{abs(sapma):,.0f} altında. Hava iyiyse bu **olası panel kirliliği veya arıza** işareti — panelleri kontrol ettir.")
                elif sapma < -10:
                    st.warning(f"🟡 Üretim beklenenin biraz altında (%{abs(sapma):,.0f}). Hava kapalıysa normal; açıksa panelleri gözden geçir.")
                else:
                    st.success(f"🟢 Üretim beklenen aralıkta. Paneller sağlıklı çalışıyor.")

                st.caption(f"Bugünkü güneş ışınımı: {radyasyon_kwh:,.1f} kWh/m² · Hesapta panellerin %80 verimle çalıştığı varsayıldı (kayıplar için pay bırakılmış temkinli değer).")
            except Exception as e:
                st.warning("⚠️ Hava verisi çekilemedi (internet yok veya API geçici erişilemez). İnternet gelince tekrar dene.")
    else:
        st.info("GES yoksa bu bölüm gizli kalır. Panel eklersen buradan takip edebilirsin.")         
             