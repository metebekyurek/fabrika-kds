import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import veritabani
import hesap_motoru

# İyileştirme varsayımı: bir kaybın gerçekçi olarak ne kadarı kapatılabilir?
# Temkinli tutuyoruz — %100 iyileşme sahada mümkün değildir.
IYILESME_ORANI = 0.20

def _git_butonu(hedef_sayfa, anahtar):
    if st.button(f"➜ {hedef_sayfa} sayfasına git", key=anahtar, use_container_width=True):
        st.session_state["aktif_sayfa"] = hedef_sayfa
        st.rerun()

def _aksiyonlari_topla():
    """Tüm modülleri tarayıp somut aksiyon önerileri üretir.
    Her aksiyon: (kazanc_tl, baslik, adimlar_listesi, hedef_sayfa, aciliyet)"""
    aksiyonlar = []

    # --- 1. Duruş kaybı: en çok kaybettiren makine ---
    durus_tl, durus_detay = hesap_motoru.durus_kaybi_tl()
    if not durus_detay.empty:
        en_kotu = durus_detay.iloc[0]
        kazanc = float(en_kotu["kayip_tl"]) * IYILESME_ORANI
        aksiyonlar.append((
            kazanc,
            f"⏸️ {en_kotu['makine_id']} makinesinin duruşlarını azalt",
            [
                f"Bu makine kayıtlı dönemde **{en_kotu['durus_saat']:,.1f} saat** durmuş, "
                f"bu da **{en_kotu['kayip_tl']:,.0f} TL** üretilemeyen kâr demek.",
                "Arıza kayıtlarına bak: aynı arıza tekrar ediyor mu? Tekrar eden arıza, kök nedeni çözülmemiş demektir.",
                "Ustabaşıyla bu makinenin bakımını öne al — duruşun %20'sini kesmek bile aşağıdaki kazancı getirir.",
            ],
            "Bakım",
            "yüksek",
        ))

    # --- 2. Fire kaybı: en çok kaybettiren ürün ---
    fire_tl, fire_detay = hesap_motoru.fire_kaybi_tl()
    if not fire_detay.empty:
        en_kotu = fire_detay.iloc[0]
        kazanc = float(en_kotu["kayip_tl"]) * IYILESME_ORANI
        aksiyonlar.append((
            kazanc,
            f"♻️ {en_kotu['urun_kodu']} ürününde fireyi düşür",
            [
                f"Bu üründe **{en_kotu['fire_adet']:,.0f} adet** fire var, karşılığı **{en_kotu['kayip_tl']:,.0f} TL**.",
                "Üretim sayfasındaki 'Fire Nedeni Analizi'ne bak: kalıp mı, hammadde mi, ayar mı?",
                "En sık neden hangisiyse bir hafta o nedene odaklan — genelde tek bir ayar/kalıp sorunu firenin çoğunu üretir.",
            ],
            "Üretim",
            "yüksek",
        ))

    # --- 3. Bakımı gecikmiş makineler ---
    makine_df = veritabani.veri_oku("makineler")
    ariza_df = veritabani.veri_oku("arizalar")
    if not makine_df.empty and "son_bakim_tarihi" in makine_df.columns:
        bugun = datetime.now().date()
        gecikenler = []
        for _, m in makine_df.iterrows():
            son = pd.to_datetime(m.get("son_bakim_tarihi"), errors="coerce")
            periyot = pd.to_numeric(m.get("bakim_periyodu_gun"), errors="coerce")
            if pd.isna(son) or pd.isna(periyot) or periyot <= 0:
                continue
            sonraki = son.date() + timedelta(days=int(periyot))
            gecikme = (bugun - sonraki).days
            if gecikme > 0:
                gecikenler.append((str(m.get("makine_id", "")).strip(), gecikme))

        if gecikenler:
            gecikenler.sort(key=lambda x: x[1], reverse=True)
            # Kazanç tahmini: geciken makinelerin duruş kaybının payı üzerinden
            kazanc = 0.0
            if not durus_detay.empty:
                geciken_idler = [g[0] for g in gecikenler]
                pay = durus_detay[durus_detay["makine_id"].isin(geciken_idler)]["kayip_tl"].sum()
                kazanc = float(pay) * IYILESME_ORANI
            liste = ", ".join(f"**{mid}** ({gun} gün)" for mid, gun in gecikenler[:4])
            aksiyonlar.append((
                kazanc,
                f"🛠️ Geciken {len(gecikenler)} makine bakımını planla",
                [
                    f"Bakımı geciken makineler: {liste}"
                    + (" ve diğerleri." if len(gecikenler) > 4 else "."),
                    "Geciken bakım, arıza riskini artırır — arıza da hem tamir hem duran üretim demektir.",
                    "Bu hafta ustayla takvim çıkar, en çok geciken makineden başla.",
                ],
                "Bakım Takvimi",
                "yüksek",
            ))

    # --- 4. Kritik stoklar ---
    risk_detay, toplam_risk = hesap_motoru.stok_gecikme_riski()
    if not risk_detay.empty and toplam_risk > 0:
        en_riskli = risk_detay.iloc[0]
        aksiyonlar.append((
            float(toplam_risk),
            "📦 Kritik seviyedeki malzemeleri sipariş et",
            [
                f"En acil: **{en_riskli['malzeme']}** — eldeki miktar ~{en_riskli['kalan_gun']:.0f} gün yetiyor, "
                f"tedarik ortalama {en_riskli['tedarik_gecikme_gun']:.0f} gün sürüyor.",
                f"Toplam **{len(risk_detay)} malzeme** kritik seviyede; önlem alınmazsa açık risk **{toplam_risk:,.0f} TL**.",
                "Bugün siparişleri ver — bu kalem, önlem alınırsa tamamen sıfırlanabilen tek risktir.",
            ],
            "Stok",
            "acil",
        ))

    # --- 5. Vardiya farkı ---
    vardiya_ozet, vardiya_fark = hesap_motoru.vardiya_kiyasi()
    if not vardiya_ozet.empty and vardiya_fark > 0:
        oran_farki = float(vardiya_ozet["fire_orani"].max() - vardiya_ozet["fire_orani"].min())
        if oran_farki >= 1.0:
            kotu = vardiya_ozet.loc[vardiya_ozet["fire_orani"].idxmax()]
            iyi = vardiya_ozet.loc[vardiya_ozet["fire_orani"].idxmin()]
            aksiyonlar.append((
                float(vardiya_fark),
                f"🌙 {kotu['vardiya'].capitalize()} vardiyasındaki fire farkını kapat",
                [
                    f"{kotu['vardiya'].capitalize()} vardiyasının fire oranı **%{kotu['fire_orani']:.1f}**, "
                    f"{iyi['vardiya']} vardiyasında **%{iyi['fire_orani']:.1f}**.",
                    "Aynı makinede aynı ürün üretiliyorsa fark makineden değil koşullardan gelir: "
                    "aydınlatma, denetim, yorgunluk, usta farkı.",
                    "Bir hafta gece vardiyasını yerinde gözlemle — fark genelde tek bir sebepten çıkar.",
                ],
                "Üretim",
                "orta",
            ))

    # --- 6. Tamir giderleri yüksekse ---
    kalemler = hesap_motoru.sizinti_kalemleri()
    if kalemler:
        en_buyuk_ad, en_buyuk_tutar = kalemler[0][0], kalemler[0][1]
        if "Tamir" in en_buyuk_ad:
            aksiyonlar.append((
                float(en_buyuk_tutar) * IYILESME_ORANI,
                "🧾 Tamir giderlerini önleyici bakıma çevir",
                [
                    f"En büyük kalem tamir giderleri: **{en_buyuk_tutar:,.0f} TL**.",
                    "Bakım sayfasındaki 'Önleyici Bakım Kararı' bölümünde ustandan aldığın fiyatı gir — "
                    "sistem, önlem almanın mı beklemenin mi ucuz olduğunu söyler.",
                    "Arızayı beklemek yerine planlı bakım, aynı parayı daha az duruşla harcamaktır.",
                ],
                "Bakım",
                "orta",
            ))

    aksiyonlar.sort(key=lambda x: x[0], reverse=True)
    return aksiyonlar

def goster():
    st.title("🎯 Aksiyon Önerileri")
    st.caption("Sistem sadece 'nerede kayıp var' demez — 'önce ne yap' der. Bu hafta odaklanılacak işler, büyükten küçüğe.")

    veritabani.tablolari_olustur()
    aksiyonlar = _aksiyonlari_topla()

    if not aksiyonlar:
        st.info("ℹ️ Öneri üretmek için yeterli veri yok.")
        st.markdown("""
        **Gerekenler:**
        - 📦 **Ürünler** sayfasında parça kârları
        - ⚙️ **Makineler** sayfasında kapasite ve bakım bilgileri
        - 🔧 **Üretim** ve 🛠️ **Bakım** modüllerinde kayıtlar
        """)
        return

    toplam_kazanc = sum(a[0] for a in aksiyonlar)
    st.success(f"💰 Aşağıdaki işlerin tamamı yapılırsa, olası minimum kazanç: **{toplam_kazanc:,.0f} TL**")
    st.caption(f"Hesap varsayımı: her kalemde **%{IYILESME_ORANI*100:.0f}** iyileşme. Temkinli bir orandır — "
               "sahada daha iyisi de mümkündür, daha azı da. Kesin vaat değil, öncelik sırasıdır.")

    st.markdown("---")
    st.subheader("🔥 Bu Haftanın İlk 3 İşi")

    for i, (kazanc, baslik, adimlar, sayfa, aciliyet) in enumerate(aksiyonlar[:3], 1):
        renk = {"acil": "🔴", "yüksek": "🟠", "orta": "🟡"}.get(aciliyet, "🟡")
        with st.container(border=True):
            k1, k2 = st.columns([4, 1])
            k1.markdown(f"### {i}. {baslik}")
            k2.metric("Olası kazanç", f"{kazanc:,.0f} TL")
            st.caption(f"{renk} Aciliyet: {aciliyet}")
            for adim in adimlar:
                st.markdown(f"- {adim}")
            _git_butonu(sayfa, f"aksiyon_git_{i}")

    if len(aksiyonlar) > 3:
        st.markdown("---")
        with st.expander(f"📋 Diğer öneriler ({len(aksiyonlar) - 3} adet)"):
            for i, (kazanc, baslik, adimlar, sayfa, aciliyet) in enumerate(aksiyonlar[3:], 4):
                st.markdown(f"**{i}. {baslik}** — olası kazanç: **{kazanc:,.0f} TL**")
                for adim in adimlar:
                    st.markdown(f"- {adim}")
                st.caption(f"İlgili sayfa: {sayfa}")
                st.markdown("")

    st.markdown("---")
    st.caption("⚠️ Tutarlar kayıtlı verilerden hesaplanan olası minimum değerlerdir; kesin muhasebe rakamı değildir. "
               "Öncelik sırası verilere göre çıkarılır — son kararı saha bilginle sen verirsin.")