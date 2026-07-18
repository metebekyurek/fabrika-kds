"""
Excel şablon üretici — her modülün veri giriş sayfasında 'şablonu indir' butonu için.
Şablonlar doğru sütun başlıklarıyla ve 2 örnek satırla iner: kullanıcı örneğe bakıp
formatı anlar, kendi verisini alta yazar, mevcut 'Excel yükle' kutusundan geri yükler.
"""
import io
import pandas as pd
import streamlit as st

def sablon_butonu(ornek_df, dosya_adi, buton_yazi="📥 Boş Excel şablonunu indir"):
    """Örnek DataFrame'in ilk 2 satırından Excel şablonu üretip indirme butonu gösterir."""
    sablon = ornek_df.head(2).copy()
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as yazici:
        sablon.to_excel(yazici, index=False, sheet_name="Veri")
    st.download_button(
        buton_yazi,
        data=buf.getvalue(),
        file_name=dosya_adi,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Doğru sütun başlıkları ve 2 örnek satır içerir. Örneklere bakıp kendi verini alta yaz, "
             "sonra bu sayfadaki 'Excel yükle' kutusundan geri yükle."
    )