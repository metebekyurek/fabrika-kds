# VERİ ŞEMASI — Fabrika KDS (Faz 0)

## 1. MAKİNE KİMLİK KARTI
Bir kez girilir, değişince güncellenir. Her gün sorulmaz.

### Kimlik
- makine_id (örn. PRES-01)
- makine_adi
- makine_tipi (pres / CNC / enjeksiyon / torna / diğer)
- marka
- model
- uretim_yili

### Teknik
- saatlik_kapasite (parça/saat)
- max_hidrolik_basinc_bar (varsa)

### Motorlar / Üniteler (bir veya birden fazla)
Her ünite için ayrı satır:
- unite_adi (örn. hidrolik motor, ısıtıcı rezistans)
- motor_gucu_kw
- enerji_verimlilik_sinifi (IE1 / IE2 / IE3 / IE4)

### Kritik Sınırlar (boşsa sistem tip bazlı önerir, kullanıcı düzenleyebilir)
- max_yag_sicakligi_c
- max_titresim_mm_s
- max_motor_akimi_a

### Bakım
- son_bakim_tarihi
- bakim_periyodu_saat
- calisma_saati_toplam
## 2. ARIZA LOGU (Bakım Modülü)
Her satır bir arıza olayı. İlk 5 kolon dolsa sistem çalışır; gerisi analizi zenginleştirir.

- ariza_id (sıra no)
- makine_id (Kimlik Kartı ile eşleşir, örn. PRES-01)
- ariza_baslangic (tarih + saat, örn. 06.07.2026 14:30)
- ariza_bitis (tarih + saat — sistem duruş süresini ve MTBF'i hesaplar)
- ariza_tipi (mekanik / elektrik / hidrolik / yazılım / diğer)
- aciklama (serbest metin)
- degisen_parca (örn. rulman 6204 — opsiyonel)
- mudahale_eden (usta adı veya kod — opsiyonel)
- tamir_maliyeti_tl (elle girilir, sistem tahmin etmez)
- duran_uretim_adedi (opsiyonel — sistem üretimden de bulabilir)
## 3. ÜRETİM KAYDI (Üretim Modülü)
Her satır = bir vardiya + bir makine + bir ürün. Aynı vardiyada farklı ürün varsa ayrı satır.

- kayit_id (sıra no)
- tarih (06.07.2026)
- vardiya (gündüz / gece / tam gün)
- makine_id (PRES-01)
- operator_id (OP-01 — kod; firma isterse isim eşler)
- urun_kodu (örn. URN-A)
- hedef_adet (opsiyonel — boşsa sistem geçmiş ortalamayı referans alır)
- uretilen_adet (sağlam üretim)
- fire_adet (bozuk/atılan)
- fire_nedeni (ayar / hammadde / kalıp / operatör / diğer)
- calisma_suresi_saat (fiili çalışma, duruşlar hariç)
## 4. ENERJİ (Enerji Modülü)

### 4A. Elektrik Faturası (her satır = bir aylık fatura)
- fatura_id (sıra no)
- donem (2026-06)
- toplam_tuketim_kwh
- gunduz_kwh / puant_kwh / gece_kwh (opsiyonel — üç zamanlı tarife varsa)
- toplam_tutar_tl
- birim_fiyat_tl_kwh (opsiyonel — boşsa sistem tutar/tüketimden hesaplar)

### 4B. GES Üretim (varsa; her satır = bir gün)
- kayit_id (sıra no)
- tarih (06.07.2026)
- gerceklesen_uretim_kwh (kullanıcı girer)
- NOT: beklenen üretimi sistem hava API'si + GES kapasitesinden hesaplar

### GES Kimlik (sabit, bir kez girilir)
- ges_kapasite_kwp (kurulu panel gücü)
- panel_egim_yon (opsiyonel)
- konum (il/ilçe — hava API'si için)
## 4. ENERJİ (Enerji Modülü)

### 4A. Elektrik Faturası (her satır = bir aylık fatura)
- fatura_id (sıra no)
- donem (2026-06)
- toplam_tuketim_kwh
- gunduz_kwh / puant_kwh / gece_kwh (opsiyonel — üç zamanlı tarife varsa)
- toplam_tutar_tl
- birim_fiyat_tl_kwh (opsiyonel — boşsa sistem tutar/tüketimden hesaplar)

### 4B. GES Üretim (varsa; her satır = bir gün)
- kayit_id (sıra no)
- tarih (06.07.2026)
- gerceklesen_uretim_kwh (kullanıcı girer)
- NOT: beklenen üretimi sistem hava API'si + GES kapasitesinden hesaplar

### GES Kimlik (sabit, bir kez girilir)
- ges_kapasite_kwp (kurulu panel gücü)
- panel_egim_yon (opsiyonel)
- konum (il/ilçe — hava API'si için)
## 5. STOK (Stok Modülü)

### 5A. Stok Kartı (her satır = bir malzeme)
- stok_id (sıra no)
- malzeme_adi (örn. 5mm sac levha)
- tur (hammadde / yarı mamul / mamul)
- birim (kg / adet / metre / litre)
- mevcut_miktar (sistem hareketlerden günceller, elle düzeltilebilir)
- kritik_seviye (rakamsal alt sınır)
- birim_maliyet_tl (opsiyonel)
- NOT: sistem tüketim hızından "kaç günlük kaldı"yı ayrıca hesaplar

### 5B. Stok Hareketi (her satır = giriş veya çıkış)
- hareket_id (sıra no)
- tarih (06.07.2026)
- stok_id (Stok Kartı ile eşleşir)
- hareket_tipi (giriş / çıkış)
- miktar
- tedarikci (giriş ise kimden)
- teslim_gecikme_gun (opsiyonel)