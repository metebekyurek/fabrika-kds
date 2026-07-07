import streamlit as st
import pandas as pd
import veritabani


def goster():
    st.title("⚙️ Makineler — Kimlik Kartları")
    st.caption("Her makinenin sabit bilgileri. Bir kez gir, tüm modüller kullansın. Sınır girmezsen sistem tip bazlı standart önerir.")

    ornek_veri = pd.DataFrame([
        {"makine_id": "PRES-01", "makine_adi": "Hidrolik Pres 1", "makine_tipi": "pres",
         "marka": "Durma", "model": "DHP-200", "uretim_yili": 2018,
         "motor_gucu_kw": 15, "saatlik_kapasite": 100,
         "max_yag_sicakligi_c": 70, "max_titresim_mm_s": 4.5, "max_motor_akimi_a": 32,
         "bakim_periyodu_saat": 500},
        {"makine_id": "CNC-01", "makine_adi": "CNC Torna 1", "makine_tipi": "CNC",
         "marka": "Haas", "model": "ST-20", "uretim_yili": 2020,
         "motor_gucu_kw": 22, "saatlik_kapasite": 60,
         "max_yag_sicakligi_c": 65, "max_titresim_mm_s": 2.8, "max_motor_akimi_a": 45,
         "bakim_periyodu_saat": 400},
    ])

    st.subheader("Makine Listesi")
    st.caption("Tabloyu düzenle, makine ekle/sil, 'Kaydet'e bas. Excel de yükleyebilirsin.")

    veritabani.tablolari_olustur()

    yuklenen = st.file_uploader("📁 Veya Excel dosyası yükle (.xlsx)", type=["xlsx"], key="makine_excel")

    if yuklenen is not None:
        try:
            baslangic_veri = pd.read_excel(yuklenen)
            st.success(f"✅ Excel okundu: {len(baslangic_veri)} makine. Kontrol edip 'Kaydet'e bas.")
        except Exception as e:
            st.error(f"❌ Excel okunamadı. Hata: {e}")
            baslangic_veri = ornek_veri
    else:
        kayitli = veritabani.veri_oku("makineler")
        if kayitli.empty:
            baslangic_veri = ornek_veri
        else:
            baslangic_veri = kayitli.drop(columns=["id"]) if "id" in kayitli.columns else kayitli

    df = st.data_editor(
        baslangic_veri,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "makine_id": "Makine ID",
            "makine_adi": "Adı",
            "makine_tipi": st.column_config.SelectboxColumn("Tip", options=["pres", "CNC", "enjeksiyon", "torna", "diğer"]),
            "marka": "Marka",
            "model": "Model",
            "uretim_yili": st.column_config.NumberColumn("Üretim Yılı", format="%d"),
            "motor_gucu_kw": st.column_config.NumberColumn("Motor Gücü (kW)", format="%.1f"),
            "saatlik_kapasite": st.column_config.NumberColumn("Saatlik Kapasite", format="%d"),
            "max_yag_sicakligi_c": st.column_config.NumberColumn("Max Yağ Sıc. (°C)", format="%d"),
            "max_titresim_mm_s": st.column_config.NumberColumn("Max Titreşim (mm/s)", format="%.1f"),
            "max_motor_akimi_a": st.column_config.NumberColumn("Max Akım (A)", format="%d"),
            "bakim_periyodu_saat": st.column_config.NumberColumn("Bakım Periyodu (saat)", format="%d"),
        }
    )

    if st.button("💾 Makineleri kaydet"):
        veritabani.veri_kaydet("makineler", df)
        st.success("✅ Makine kimlik kartları kaydedildi! Diğer modüller bu bilgileri kullanacak.")

    st.info(f"📋 Toplam {len(df)} makine tanımlı. Bu bilgiler Bakım, Üretim ve Enerji modüllerinde kullanılacak.")