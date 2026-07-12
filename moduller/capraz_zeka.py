import streamlit as st
import pandas as pd
import veritabani

def _temizle(seri):
    """Makine adlarını karşılaştırmaya hazırlar: boşlukları kırp, büyük harfe çevir."""
    return seri.astype(str).str.strip().str.upper()

def goster():
    st.title("🧠 Çapraz Modül Zekâsı")
    st.caption("Tek tek modüllerin göremediği bağlantılar. Veriler birleşince ortaya çıkan ipuçları.")

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
    # Korelasyon — "olabilir" dili şart, nedensellik iddia etmiyoruz.
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
    # ÇIKARIM 2: Arıza ↔ Sensör
    # En çok arızalanan makinenin ölçümleri kritik sınıra yakın mı?
    # Öyleyse sensör zaten erken uyarı veriyor OLABİLİR.
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
    # ÇIKARIM 3: Enerji ↔ Üretim
    # Fatura artarken üretim de arttı mı (normal), yoksa üretim
    # sabitken fatura mı şişti (olası verimsizlik)?
    # ==========================================================
    st.markdown("---")
    st.subheader("⚡ Enerji ↔ Üretim Bağlantısı")

    if (not enerji_df.empty and {"donem", "toplam_tuketim_kwh"}.issubset(enerji_df.columns)):
        e = enerji_df.copy()
        e["toplam_tuketim_kwh"] = pd.to_numeric(e["toplam_tuketim_kwh"], errors="coerce")
        e = e.dropna(subset=["donem", "toplam_tuketim_kwh"]).sort_values("donem")

        if len(e) >= 2:
            ilk = e["toplam_tuketim_kwh"].iloc[0]
            son = e["toplam_tuketim_kwh"].iloc[-1]
            if ilk > 0:
                degisim = (son - ilk) / ilk * 100
                if degisim > 10:
                    bulundu = True
                    st.warning(
                        f"⚠️ Elektrik tüketimin ilk dönemden son döneme **%{degisim:,.0f} artmış** "
                        f"({ilk:,.0f} → {son:,.0f} kWh). Üretimin de aynı oranda arttıysa bu normal; "
                        f"ama **üretim sabitken tüketim arttıysa, olası bir verimsizlik/kaçak** işareti "
                        f"olabilir — makine yaşlanması, ayar bozukluğu veya boşta çalışma olabilir."
                    )
                elif degisim < -10:
                    st.info(
                        f"Elektrik tüketimin **%{abs(degisim):,.0f} azalmış** "
                        f"({ilk:,.0f} → {son:,.0f} kWh). Üretim düşmediyse bu iyi haber — "
                        f"verimlilik artmış olabilir."
                    )
                else:
                    st.info(
                        f"Elektrik tüketimin dönemler arası stabil "
                        f"({ilk:,.0f} → {son:,.0f} kWh). Belirgin bir sapma yok."
                    )
        else:
            st.caption("Bu çıkarım için en az 2 dönem enerji kaydı gerekiyor.")
    else:
        st.caption("Bu çıkarım için Enerji modülüne fatura kaydı gir.")

    # ==========================================================
    # ==========================================================
    # ÇIKARIM 4: Vardiya ↔ Fire
    # Gece/gündüz fire ORANLARI farklı mı? Fark TL'ye çevrilir.
    # Oran kıyası önemli: az üreten vardiyanın az fire vermesi normal.
    # ==========================================================
    st.markdown("---")
    st.subheader("🌙 Vardiya ↔ Fire Bağlantısı")

    import hesap_motoru
    vardiya_ozet, vardiya_fark_tl = hesap_motoru.vardiya_kiyasi()

    if vardiya_ozet.empty:
        st.caption("Bu çıkarım için hem gündüz hem gece vardiyasında üretim kaydı gerekiyor.")
    else:
        gosterim = vardiya_ozet.copy()
        gosterim["fire_orani"] = gosterim["fire_orani"].round(1)
        gosterim["fire_kaybi_tl"] = gosterim["fire_kaybi_tl"].round(0)
        gosterim.columns = ["Vardiya", "Üretim (adet)", "Fire (adet)", "Fire Kaybı (TL)", "Fire Oranı (%)"]
        st.dataframe(gosterim, use_container_width=True, hide_index=True)

        if vardiya_fark_tl > 0:
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
            st.info("İki vardiyanın fire oranları birbirine yakın — belirgin bir vardiya sorunu görünmüyor.")
    st.markdown("---")
    if not bulundu:
        st.caption("Şu an güçlü bir çapraz bağlantı işareti bulunmadı. Veri arttıkça bu analiz güçlenir.")