import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import veritabani

def goster():
    st.title("📅 Planlı Bakım Takvimi")
    st.caption("Her makinenin bir sonraki bakımı ne zaman? Arıza olmadan önce bakım yap — takvimle görünür.")

    veritabani.tablolari_olustur()
    makine_df = veritabani.veri_oku("makineler")

    if makine_df.empty:
        st.warning("Henüz makine tanımlı değil. Önce ⚙️ Makineler sayfasından makine ekle ve kaydet.")
        return

    bugun = datetime.now().date()
    satirlar = []

    for _, m in makine_df.iterrows():
        makine_id = str(m.get("makine_id", "")).strip()
        if not makine_id or makine_id == "None":
            continue

        # Son bakım tarihi
        son_bakim = pd.to_datetime(m.get("son_bakim_tarihi"), errors="coerce")
        if pd.isna(son_bakim):
            satirlar.append((makine_id, None, None, "Son bakım tarihi girilmemiş"))
            continue
        son_bakim = son_bakim.date()

        # İki yöntemle sonraki bakım tarihini hesapla, EN ERKEN olanı al (temkinli)
        adaylar = []

        # Yöntem 1: takvim günü bazlı
        periyot_gun = pd.to_numeric(m.get("bakim_periyodu_gun"), errors="coerce")
        if pd.notna(periyot_gun) and periyot_gun > 0:
            adaylar.append(son_bakim + timedelta(days=int(periyot_gun)))

        # Yöntem 2: çalışma saati bazlı (saat periyodu ÷ günlük çalışma = kaç gün)
        periyot_saat = pd.to_numeric(m.get("bakim_periyodu_saat"), errors="coerce")
        gunluk_saat = pd.to_numeric(m.get("gunluk_calisma_saat"), errors="coerce")
        if pd.notna(periyot_saat) and periyot_saat > 0 and pd.notna(gunluk_saat) and gunluk_saat > 0:
            gun = periyot_saat / gunluk_saat
            adaylar.append(son_bakim + timedelta(days=int(gun)))

        if not adaylar:
            satirlar.append((makine_id, son_bakim, None, "Periyot bilgisi girilmemiş"))
            continue

        sonraki = min(adaylar)  # en erken uyaran yöntem kazanır
        kalan_gun = (sonraki - bugun).days
        satirlar.append((makine_id, son_bakim, sonraki, kalan_gun))

    st.markdown("---")

    # Önce durumları ayır
    gecmis = [s for s in satirlar if isinstance(s[3], int) and s[3] < 0]
    yakin = [s for s in satirlar if isinstance(s[3], int) and 0 <= s[3] <= 14]
    ilerki = [s for s in satirlar if isinstance(s[3], int) and s[3] > 14]
    eksik = [s for s in satirlar if not isinstance(s[3], int)]

    if gecmis:
        st.subheader("🔴 Bakımı Gecikmiş")
        for makine_id, son, sonraki, kalan in gecmis:
            st.error(f"**{makine_id}** — bakım tarihi **{abs(kalan)} gün önce** geçti "
                     f"({sonraki.strftime('%d.%m.%Y')}). Son bakım: {son.strftime('%d.%m.%Y')}. "
                     f"**Acilen planla** — geciken bakım arıza riskini artırır.")

    if yakin:
        st.subheader("🟡 Yaklaşan (14 gün içinde)")
        for makine_id, son, sonraki, kalan in yakin:
            st.warning(f"**{makine_id}** — **{kalan} gün** içinde bakım gerekiyor "
                       f"({sonraki.strftime('%d.%m.%Y')}). Şimdiden usta/parça ayarla.")

    if ilerki:
        st.subheader("🟢 Planlı (14 günden uzak)")
        for makine_id, son, sonraki, kalan in ilerki:
            st.success(f"**{makine_id}** — sıradaki bakım {sonraki.strftime('%d.%m.%Y')} "
                       f"(**{kalan} gün** var). Şimdilik sorun yok.")

    if eksik:
        st.subheader("⚪ Bilgi Eksik")
        for makine_id, son, sonraki, sebep in eksik:
            st.info(f"**{makine_id}** — {sebep}. ⚙️ Makineler sayfasından tamamla.")

    st.markdown("---")
    st.caption("ℹ️ Sonraki bakım tarihi iki yöntemden (takvim günü / çalışma saati) **en erken** uyaranına göre hesaplanır — temkinli yaklaşım. Tarihler son bakım + periyot bilgisine dayanır; kesin değil, planlama içindir.")