# VARSAYIM KÜTÜPHANESİ — Fabrika KDS
Firma veri girmediğinde kullanılır. Ekranda HER ZAMAN "varsayım" etiketiyle gösterilir.
Firma gerçek değeri girerse varsayım devre dışı kalır. Zamanla güncellenecek.

## MOTOR VERİMLERİ (enerji verimlilik sınıfına göre, yaklaşık)
- IE1 (standart): 0.85
- IE2 (yüksek): 0.89
- IE3 (premium): 0.92
- IE4 (süper premium): 0.94
- Bilinmiyorsa varsayılan: IE2 (0.89)

## KRİTİK SICAKLIK LİMİTLERİ (makine tipine göre, yaklaşık)
- Hidrolik yağ sıcaklığı (pres, enjeksiyon): 60-70 °C bandı, alarm: 70 °C
- Genel motor gövde sıcaklığı: alarm 80 °C
- Bilinmiyorsa: makine tipine göre bu bandı öner, kullanıcı düzenleyebilir

## TİTREŞİM LİMİTLERİ (ISO 10816 basitleştirilmiş, mm/s RMS)
- Küçük makineler (<15 kW): iyi <1.8 / kabul 1.8-4.5 / alarm >4.5
- Orta makineler (15-75 kW): iyi <2.8 / kabul 2.8-7.1 / alarm >7.1
- Bilinmiyorsa: makine gücüne göre bu sınıfı seç

## MOTOR AKIMI
- Kimlik Kartı'ndaki max_motor_akimi referans alınır
- Ölçülen akım bu değeri aşarsa: aşırı yük / zorlanma uyarısı
- Bilinmiyorsa: motor gücü ve voltajdan teorik akım hesaplanır

## ELEKTRİK TARİFE SAATLERİ (Türkiye, 3 zamanlı — TİPİK, firma kendi tarifesini girebilir)
- Gündüz: 06:00 - 17:00
- Puant (en pahalı): 17:00 - 22:00
- Gece (en ucuz): 22:00 - 06:00
- NOT: Birim fiyatlar firmadan alınır, buraya sabit yazılmaz (zam/indirim değişir)

## İŞÇİLİK (maaş verisi yoksa, sektörel yaklaşım)
- Firma maaş girmezse: birim maliyette işçilik "varsayımsal" etiketiyle gösterilir
- Sektörel ortalama saatlik işçilik değeri firma onayıyla girilir
- NOT: Bu değer bölgeye/sektöre göre çok değişir, yıllık güncellenir

## GES PERFORMANS ORANI (PR — başlangıç)
- Varsayılan PR: 0.80
- İlk haftalar "kalibre oluyor" etiketiyle gösterilir
- Firma gerçek üretim verisi biriktikçe PR o panele göre düzeltilir