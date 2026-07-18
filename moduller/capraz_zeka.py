import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import veritabani
import hesap_motoru

def _temizle(seri):
    """Makine adlarını karşılaştırmaya hazırlar: boşlukları kırp, büyük harfe çevir."""
    return seri.astype(str).str.strip().str.upper()

def goster():
    st.title("🧠 Çapraz Zekâ")
    st.caption("Modüller tek başına bakınca görünmeyen bağlantılar. Veriler birleşince ortaya çıkan ipuçları.")

    st.info("ℹ️ Buradaki çıkarımlar **kesin teşhis değil, 'buraya bak' işaretleridir.** İki şeyin birlikte görülmesi, birinin diğerine sebep olduğunu kanıtlamaz — ama nereye bakacağını gösterir. Kararı, sahadaki gözlemlerinle birlikte sen verirsin.")

    veritabani.tablolari_olustur()
    ariza_df = veritabani.veri_oku("arizalar")
    uretim_df = veritabani.veri_oku("uretim")
    olcum_df = veritabani.veri_oku("olcumler")
    makine_df = veritabani.veri_oku("makineler")
    enerji_df = veritabani.veri_oku("enerji")

    # Tüm makine adlarını tek tipe getir (boşluk + büyük/küçük harf farkını yok et)
    for d in [ariza_df, uretim_df, olcum_df, makine_df]:
        if not d.empty and "makine_id" in d.columns:
            d["makine_id"] = _temizle(d["makine_id"])

    bulundu = False

    # ==========================================================
    # ÇIKARIM 1: Arıza ↔ Fire
    # En çok arızalanan makine, aynı zamanda en çok fire veren mi?
    # ==========================================================
    st.markdown("---")
    st.subheader("🔗 Arıza ↔ Fire Bağlantısı")

    if (not ariza_df.empty and "makine_id" in ariza_df.columns
            and not uretim_df.empty and {"makine_id", "fire_adet"}.issubset(uretim_df.columns)):

        ariza_sayilari = ariza_df["makine_id"].value_counts()
        en_ariza_makine = ariza_sayilari.index[0]
        en_ariza_sayi = ariza_sayilari.iloc[0]

        u = uretim_df.copy()
        u["fire_adet"] = pd.to_numeric(u["fire_adet"], errors="coerce").fillna(0)
        fire_toplam = u.groupby("makine_id")["fire_adet"].sum().sort_values(ascending=False)

        if not fire_toplam.empty and fire_toplam.iloc[0] > 0:
            en_fire_makine = fire_toplam.index[0]
            en_fire_adet = fire_toplam.iloc[0]

            if en_ariza_makine == en_fire_makine:
                bulundu = True
                st.warning(
                    f"⚠️ **{en_ariza_makine}** hem en çok arızalanan makine "
                    f"({en_ariza_sayi} arıza) **hem de** en çok fire veren makine "
                    f"({en_fire_adet:,.0f} adet fire). İkisi aynı makinede toplanıyor — "
                    f"**arızalar kaliteyi de bozuyor olabilir.** Bu makinenin bakımını öne almak "
                    f"hem duruşu hem fireyi birlikte azaltabilir."
                )
            else:
                st.info(
                    f"En çok arızalanan makine **{en_ariza_makine}**, en çok fire veren ise "
                    f"**{en_fire_makine}**. Farklı makineler — arıza ve fire şimdilik ayrı "
                    f"sorunlar gibi görünüyor."
                )
        else:
            st.caption("Fire verisi yeterli değil — Üretim modülüne fire kaydı gir.")
    else:
        st.caption("Bu çıkarım için hem Bakım (arıza) hem Üretim (fire) kayıtları gerekiyor.")

    # ==========================================================
    # ÇIKARIM 2: Bakım Gecikmesi ↔ Arıza  (YENİ)
    # Bakımı geciken makineler, arıza listesinde de öne mi çıkıyor?
    # Önleyici bakımın en somut kanıtı budur.
    # ==========================================================
    st.markdown("---")
    st.subheader("🛠️ Bakım Gecikmesi ↔ Arıza Bağlantısı")

    if (not makine_df.empty and {"makine_id", "son_bakim_tarihi", "bakim_periyodu_gun"}.issubset(makine_df.columns)
            and not ariza_df.empty and "makine_id" in ariza_df.columns):

        bugun = datetime.now().date()
        ariza_sayilari = ariza_df["makine_id"].value_counts()

        gecikmis_ve_arizali = []
        for _, m in makine_df.iterrows():
            son = pd.to_datetime(m.get("son_bakim_tarihi"), errors="coerce")
            periyot = pd.to_numeric(m.get("bakim_periyodu_gun"), errors="coerce")
            if pd.isna(son) or pd.isna(periyot) or periyot <= 0:
                continue
            sonraki = son.date() + timedelta(days=int(periyot))
            gecikme = (bugun - sonraki).days
            mid = str(m.get("makine_id", "")).strip().upper()
            ariza_adet = int(ariza_sayilari.get(mid, 0))
            if gecikme > 0 and ariza_adet > 0:
                gecikmis_ve_arizali.append((mid, gecikme, ariza_adet))

        if gecikmis_ve_arizali:
            bulundu = True
            gecikmis_ve_arizali.sort(key=lambda x: x[2], reverse=True)
            satirlar = ", ".join(f"**{mid}** (bakım {g} gün gecikmiş, {a} arıza)"
                                 for mid, g, a in gecikmis_ve_arizali[:3])
            st.warning(
                f"⚠️ Bakımı geciken makinelerde arıza kayıtları var: {satirlar}. "
                f"**Geciken bakım ile arızalar aynı makinelerde buluşuyor olabilir** — "
                f"bakım takvimini yakalamak bu arızaların bir kısmını önleyebilir. "
                f"Detay için 📅 Bakım Takvimi sayfasına bak."
            )
        else:
            st.info("Bakımı geciken ve aynı zamanda arıza veren makine görünmüyor — bakım düzeni ile arızalar arasında şu an bir çakışma yok.")
    else:
        st.caption("Bu çıkarım için Makineler sayfasında bakım tarihi/periyodu ve Bakım'da arıza kaydı gerekiyor.")

    # ==========================================================
    # ÇIKARIM 3: Arıza ↔ Sensör
    # En çok arızalanan makinenin ölçümleri kritik sınıra yakın mı?
    # ==========================================================
    st.markdown("---")
    st.subheader("📡 Arıza ↔ Sensör Bağlantısı")

    if (not ariza_df.empty and "makine_id" in ariza_df.columns
            and not olcum_df.empty and {"makine_id", "parametre", "deger"}.issubset(olcum_df.columns)
            and not makine_df.empty):

        en_ariza_makine = ariza_df["makine_id"].value_counts().index[0]

        sinir_haritasi = {
            "yag_sicakligi": "max_yag_sicakligi_c",
            "titresim": "max_titresim_mm_s",
            "motor_akimi": "max_motor_akimi_a",
        }

        o = olcum_df[olcum_df["makine_id"] == en_ariza_makine].copy()
        o["deger"] = pd.to_numeric(o["deger"], errors="coerce")
        m_satir = makine_df[makine_df["makine_id"] == en_ariza_makine]

        yakin_bulundu = False
        if not o.empty and not m_satir.empty:
            for _, olcum in o.iterrows():
                param = str(olcum.get("parametre", "")).strip()
                deger = olcum.get("deger")
                if param in sinir_haritasi and pd.notna(deger):
                    sinir_kol = sinir_haritasi[param]
                    if sinir_kol in m_satir.columns:
                        sinir = pd.to_numeric(m_satir.iloc[0][sinir_kol], errors="coerce")
                        if pd.notna(sinir) and sinir > 0 and deger >= sinir * 0.9:
                            yakin_bulundu = True
                            bulundu = True
                            st.warning(
                                f"⚠️ En çok arızalanan makine **{en_ariza_makine}**'in "
                                f"**{param}** ölçümü ({deger:,.1f}), kritik sınıra ({sinir:,.0f}) "
                                f"çok yakın. **Sensör, arızayı önceden haber veriyor olabilir** — "
                                f"bu parametreyi düzenli izlemek erken müdahale sağlayabilir."
                            )
        if not yakin_bulundu:
            st.info(
                f"En çok arızalanan makine **{en_ariza_makine}**'in ölçümleri şu an kritik "
                f"sınırların altında. Sensör tarafında acil bir işaret görünmüyor."
            )
    else:
        st.caption("Bu çıkarım için arıza kaydı, ölçüm verisi ve makine kimlik kartı gerekiyor.")

    # ==========================================================
    # ÇIKARIM 4: Enerji ↔ Üretim  (GÜÇLENDİRİLDİ)
    # Artık üretim verisini de gerçekten okuyor: parça başına
    # harcanan elektrik (kWh/adet) dönemler arası kıyaslanır.
    # ==========================================================
    st.markdown("---")
    st.subheader("⚡ Enerji ↔ Üretim Bağlantısı")

    if (not enerji_df.empty and {"donem", "toplam_tuketim_kwh"}.issubset(enerji_df.columns)):
        e = enerji_df.copy()
        e["toplam_tuketim_kwh"] = pd.to_numeric(e["toplam_tuketim_kwh"], errors="coerce")
        e = e.dropna(subset=["donem", "toplam_tuketim_kwh"]).sort_values("donem")

        # Üretimi aynı dönemlere (YYYY-AA) topla
        aylik_uretim = None
        if not uretim_df.empty and {"tarih", "uretilen_adet"}.issubset(uretim_df.columns):
            u = uretim_df.copy()
            u["tarih"] = pd.to_datetime(u["tarih"], errors="coerce")
            u["uretilen_adet"] = pd.to_numeric(u["uretilen_adet"], errors="coerce").fillna(0)
            u = u.dropna(subset=["tarih"])
            if not u.empty:
                u["donem"] = u["tarih"].dt.strftime("%Y-%m")
                aylik_uretim = u.groupby("donem")["uretilen_adet"].sum()

        if aylik_uretim is not None:
            # Hem enerji hem üretim kaydı olan ortak dönemler
            e["donem"] = e["donem"].astype(str).str.strip()
            ortak = e[e["donem"].isin(aylik_uretim.index)].copy()
            ortak["uretim"] = ortak["donem"].map(aylik_uretim)
            ortak = ortak[ortak["uretim"] > 0]

            if len(ortak) >= 2:
                ortak["kwh_per_adet"] = ortak["toplam_tuketim_kwh"] / ortak["uretim"]
                ilk_d, son_d = ortak.iloc[0], ortak.iloc[-1]
                degisim = ((son_d["kwh_per_adet"] - ilk_d["kwh_per_adet"]) / ilk_d["kwh_per_adet"] * 100) if ilk_d["kwh_per_adet"] > 0 else 0

                st.caption(f"Parça başına elektrik: {ilk_d['donem']}'de **{ilk_d['kwh_per_adet']:.2f} kWh/adet** → {son_d['donem']}'de **{son_d['kwh_per_adet']:.2f} kWh/adet**")

                if degisim > 10:
                    bulundu = True
                    st.warning(
                        f"⚠️ Bir parça üretmek için harcanan elektrik **%{degisim:,.0f} artmış**. "
                        f"Üretim aynı, fatura şişiyor demektir — **olası verimsizlik işareti**: "
                        f"makine yaşlanması, ayar bozukluğu, boşta çalışma veya kaçak olabilir. "
                        f"En çok tüketen makinelerden başlayarak kontrol ettirmek mantıklı."
                    )
                elif degisim < -10:
                    st.success(
                        f"🟢 Bir parça üretmek için harcanan elektrik **%{abs(degisim):,.0f} azalmış** — "
                        f"verimlilik artmış görünüyor. Ne değiştiyse (yeni makine, ayar, düzen) korumaya değer."
                    )
                else:
                    st.info("Parça başına elektrik tüketimi dönemler arası dengeli — belirgin bir sapma yok.")
            else:
                st.caption("Kıyas için aynı aya ait hem enerji faturası hem üretim kaydı olan en az 2 dönem gerekiyor. "
                           "(Enerji dönemleri YYYY-AA formatında, üretim tarihleriyle eşleşmeli.)")
        else:
            # Üretim verisi yoksa eski basit kıyasa düş
            if len(e) >= 2:
                ilk = e["toplam_tuketim_kwh"].iloc[0]
                son = e["toplam_tuketim_kwh"].iloc[-1]
                if ilk > 0:
                    degisim = (son - ilk) / ilk * 100
                    if degisim > 10:
                        bulundu = True
                        st.warning(
                            f"⚠️ Elektrik tüketimin ilk dönemden son döneme **%{degisim:,.0f} artmış** "
                            f"({ilk:,.0f} → {son:,.0f} kWh). Üretim kaydı da girilirse sistem bunun "
                            f"normal olup olmadığını (parça başına tüketim) otomatik kontrol edebilir."
                        )
                    else:
                        st.info(f"Elektrik tüketimi: {ilk:,.0f} → {son:,.0f} kWh. Belirgin bir sapma yok.")
            else:
                st.caption("Bu çıkarım için en az 2 dönem enerji kaydı gerekiyor.")
    else:
        st.caption("Bu çıkarım için Enerji modülüne fatura kaydı gir.")

    # ==========================================================
    # ÇIKARIM 5: Vardiya ↔ Fire
    # ==========================================================
    st.markdown("---")
    st.subheader("🌙 Vardiya ↔ Fire Bağlantısı")

    vardiya_ozet, vardiya_fark_tl = hesap_motoru.vardiya_kiyasi()

    if vardiya_ozet.empty:
        st.caption("Bu çıkarım için hem gündüz hem gece vardiyasında üretim kaydı gerekiyor.")
    else:
        gosterim = vardiya_ozet.copy()
        gosterim["fire_orani"] = gosterim["fire_orani"].round(1)
        gosterim["fire_kaybi_tl"] = gosterim["fire_kaybi_tl"].round(0)
        gosterim.columns = ["Vardiya", "Üretim (adet)", "Fire (adet)", "Fire Kaybı (TL)", "Fire Oranı (%)"]
        st.dataframe(gosterim, use_container_width=True, hide_index=True)

        oran_farki = float(vardiya_ozet["fire_orani"].max() - vardiya_ozet["fire_orani"].min())
        if vardiya_fark_tl > 0 and oran_farki >= 1.0:
            bulundu = True
            iyi = vardiya_ozet.loc[vardiya_ozet["fire_orani"].idxmin()]
            kotu = vardiya_ozet.loc[vardiya_ozet["fire_orani"].idxmax()]
            st.warning(
                f"⚠️ **{kotu['vardiya'].capitalize()}** vardiyasının fire oranı (%{kotu['fire_orani']:.1f}), "
                f"**{iyi['vardiya']}** vardiyasından (%{iyi['fire_orani']:.1f}) belirgin yüksek. "
                f"{kotu['vardiya'].capitalize()} vardiyası aynı orana inseydi, bu kayıtların döneminde "
                f"olası minimum **{vardiya_fark_tl:,.0f} TL** kurtarılırdı. Sebep aydınlatma, denetim eksikliği, "
                f"yorgunluk veya usta farkı olabilir — sahada gözlemlemek gerekir."
            )
        else:
            st.info("İki vardiyanın fire oranları birbirine yakın (fark 1 puandan az) — belirgin bir vardiya sorunu görünmüyor.")

    st.markdown("---")
    if not bulundu:
        st.caption("Şu an güçlü bir çapraz bağlantı işareti bulunmadı. Veri arttıkça bu analiz güçlenir.")