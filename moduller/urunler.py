import streamlit as st
import pandas as pd
import veritabani

def goster():
    st.title("📦 Ürünler — Parça Kârı Tanımları")
    st.caption("Her ürünün parça başı kârını bir kez gir. Tüm modüller (fire kaybı, duruş kaybı, sızıntı, rapor) bu değerleri otomatik kullanır — bir daha hiçbir ekranda kâr sorulmaz.")

    st.info("💡 **Parça başı kâr nedir?** Bir ürünü satınca eline geçen para eksi o ürünün maliyeti. Yani o parçadan cebine kalan net kâr. Fire olan her parça = kaybedilen bu kâr.")

    veritabani.tablolari_olustur()

    ornek_veri = pd.DataFrame([
        {"urun_kodu": "URN-A", "urun_adi": "Sac braket", "parca_kar_tl": 2.0},
        {"urun_kodu": "URN-B", "urun_adi": "Lazer kesim panel", "parca_kar_tl": 5.5},
    ])

    yuklenen = st.file_uploader("📁 Veya Excel dosyası yükle (.xlsx)", type=["xlsx"], key="urun_excel")

    if yuklenen is not None:
        try:
            baslangic_veri = pd.read_excel(yuklenen)
            st.success(f"✅ Excel okundu: {len(baslangic_veri)} ürün. Kontrol edip 'Kaydet'e bas.")
        except Exception as e:
            st.error(f"❌ Excel okunamadı. Hata: {e}")
            baslangic_veri = ornek_veri
    else:
        kayitli = veritabani.veri_oku("urunler")
        if kayitli.empty:
            baslangic_veri = ornek_veri
        else:
            baslangic_veri = kayitli.drop(columns=["id"]) if "id" in kayitli.columns else kayitli

    df = st.data_editor(
        baslangic_veri,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "urun_kodu": st.column_config.TextColumn("Ürün Kodu", help="Üretim kayıtlarında kullandığın kod. Örn: URN-A"),
            "urun_adi": st.column_config.TextColumn("Ürün Adı", help="İnsanların anlayacağı isim"),
            "parca_kar_tl": st.column_config.NumberColumn("Parça Başı Kâr (TL)", format="%.2f TL",
                                                          help="Bu üründen bir adet üretip sattığında cebine kalan net kâr"),
        }
    )

    if st.button("💾 Ürünleri kaydet"):
        veritabani.veri_kaydet("urunler", df)
        st.success("✅ Kaydedildi! Artık tüm hesaplar bu kâr değerlerini kullanacak.")

    st.markdown("---")
    st.caption("⚠️ Üretim modülündeki 'Ürün' sütununa yazdığın kodlar, buradaki 'Ürün Kodu' ile aynı olmalı — yoksa sistem eşleştiremez.")