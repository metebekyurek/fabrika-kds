import streamlit as st

def goster():
    st.title("📖 Yardım ve Rehber")
    st.caption("Sistem nasıl kullanılır, hangi sayfa ne işe yarar, terimler ne demek — hepsi burada.")

    # ================= HIZLI BAŞLANGIÇ =================
    st.subheader("🚀 Hızlı Başlangıç")
    st.markdown("""
    Sistemi ilk kez kuruyorsan sıralama şu — **tanımlar önce, kayıtlar sonra:**

    1. **⚙️ Fabrika Ayarları** → firma adı, e-posta, elektrik tarife fiyatları (faturandan bir kez gir)
    2. **📦 Ürünler** → her ürünün kodu ve parça başı kârı (tüm TL hesapları buradan beslenir)
    3. **⚙️ Makineler** → her makinenin kimlik kartı: kapasite, bakım periyodu, kritik sınırlar
    4. **🔧 Üretim / 🛠️ Bakım / 📦 Stok / ⚡ Enerji** → günlük kayıtlar (elle ya da Excel'le)

    Kayıtlar biriktikçe analiz sayfaları (Kâr Sızıntısı, OEE, Çapraz Zekâ...) kendiliğinden dolar.

    💡 **Sistemi veri girmeden görmek için:** 🎬 **Demo Verisi** sayfasından tek tuşla örnek fabrika yükle.
    """)

    st.markdown("---")

    # ================= VERİ GİRİŞİ =================
    st.subheader("📝 Veri Nasıl Girilir?")
    st.markdown("""
    Her veri sayfasında iki yol var:

    - **Elle giriş:** Tablodaki hücrelere tıklayıp yaz, satır eklemek için tablonun altındaki boş satırı kullan.
      Bitince mutlaka **💾 Kaydet** butonuna bas — kaydetmeden sayfa değiştirirsen girdiğin veri kaybolur.
    - **Excel ile:** **📥 Boş Excel şablonunu indir** butonuyla şablonu al, muhasebecine/ustabaşına ver.
      Doldurulan dosyayı **Excel yükle** kutusundan geri yükle, kontrol et, **Kaydet**'e bas.

    ⚠️ Excel yüklerken sütun başlıklarını **değiştirme** — sistem başlıklardan tanır.
    """)

    st.markdown("---")

    # ================= SAYFA REHBERİ =================
    st.subheader("🗺️ Sayfa Rehberi")

    with st.expander("📊 Günün Özeti — her sabah ilk bakılacak yer"):
        st.markdown("""
        Fabrikanın genel durumu tek ekranda: toplam üretim, fire oranı, tamir gideri ve
        **Dikkat Gerektirenler** listesi (kritik stoklar, son arızalar, geciken bakımlar).
        Uyarıların yanındaki **➜ Git** butonu seni ilgili sayfaya götürür.
        """)

    with st.expander("💸 Kâr Sızıntısı — para nereden kaçıyor?"):
        st.markdown("""
        Tüm modüllerdeki kayıpları TL cinsinden tek listede toplar: tamir giderleri,
        duruş kaynaklı kaçan kâr, fire kaybı. Büyükten küçüğe sıralar — **en üstteki kalem,
        ilk odaklanılacak sorundur.**
        """)

    with st.expander("🧠 Çapraz Zekâ — modüllerin göremediği bağlantılar"):
        st.markdown("""
        Verileri birleştirip ipucu arar: *en çok arızalanan makine en çok fire vereni mi,
        bakımı gecikenler mi arızalanıyor, parça başına elektrik artıyor mu, vardiyalar arasında
        fire farkı var mı?* Buradaki çıkarımlar **kesin teşhis değil, "buraya bak" işaretidir.**
        """)

    with st.expander("🎚️ Simülatör — 'ya şöyle yapsaydım?'"):
        st.markdown("""
        Kaydırıcılarla senaryo dener: *"Fireyi %20 azaltsam yılda kaç TL kazanırım?"*
        Rakamlar kayıtlı verinden hesaplanır ve **aralık olarak** verilir — kesin vaat değil,
        gerçekçi tahmindir.
        """)

    with st.expander("📈 Dönem Kıyaslama — gidişat iyi mi kötü mü?"):
        st.markdown("""
        Bu dönemi önceki dönemle yan yana koyar: üretim, fire, tamir, duruş.
        Hazır dönemler (haftalık, aylık...) ya da **📅 Özel Aralık** ile takvimden kendi
        tarihlerini seçebilirsin — sistem aynı uzunluktaki önceki dönemle otomatik kıyaslar.
        """)

    with st.expander("🔧 Üretim — kota ve fire takibi"):
        st.markdown("""
        Günlük üretim kayıtları: hangi makine, hangi ürün, kaç adet, ne kadar fire, neden.
        OEE hesabı için **Planlanan Süre, Duruş ve İdeal Hız** sütunlarını da doldur.
        Fire nedeni girersen sistem *"firelerin çoğu nereden geliyor"* analizini kendisi yapar.
        """)

    with st.expander("🎯 OEE — makine verimliliği"):
        st.markdown("""
        Dünyada yaygın kullanılan verimlilik ölçüsü. Tek soruya cevap verir:
        *makinelerin, kusursuz şartlarda üretebileceğinin yüzde kaçını üretti?*
        Üç bileşenin çarpımıdır: **Çalışma Oranı × Hız × Kalite**. %85 üstü iyi kabul edilir.
        Kaybın TL karşılığını da gösterir.
        """)

    with st.expander("🛠️ Bakım — arıza takibi ve önleyici bakım"):
        st.markdown("""
        Arıza kayıtları, arıza sıklığı (makine kaç günde bir bozuluyor), duruş maliyeti ve
        kök neden analizi. **Duruş maliyeti** her makinenin kendi kapasitesi ve ürün karışımıyla
        hesaplanır — Kâr Sızıntısı ile aynı rakamı gösterir. Sensör ölçümleri girilirse
        kritik sınır aşımlarında uyarır.
        """)

    with st.expander("📅 Bakım Takvimi — hangi makinenin bakımı ne zaman?"):
        st.markdown("""
        Makine kimlik kartlarındaki bakım periyotlarından takvim çıkarır:
        geciken (kırmızı), yaklaşan (sarı), rahat (yeşil). Geciken bakım = yaklaşan arıza riski.
        """)

    with st.expander("📦 Stok — kritik seviye ve tedarikçi"):
        st.markdown("""
        Malzeme stokları ve kritik seviye uyarıları. Günlük tüketim girersen
        *"kaç gün yeter"* hesabı da yapılır. Kritik seviyenin altına düşenler
        Günün Özeti'nde kırmızı uyarı olarak görünür.
        """)

    with st.expander("⚡ Enerji — fatura analizi ve tasarruf"):
        st.markdown("""
        Aylık faturaları gir; sistem tüketim deseninden **gelecek faturayı aralık olarak** tahmin eder.
        **Tarife Saati Optimizasyonu**: işleri ucuz saate (gece) kaydırmanın yıllık tasarrufunu hesaplar.
        Güneş paneli varsa hava verisiyle üretim sağlığını da izler.
        """)

    with st.expander("💰 Finans — maliyet ve teklif hesabı"):
        st.markdown("""
        Parça başı gerçek maliyeti hesaplar (hammadde + işçilik + elektrik).
        **Teklif Motoru**: bir siparişe verebileceğin minimum fiyatı ve zarar sınırını gösterir.
        Fason üretim modu da var (hammadde müşteriden).
        """)

    with st.expander("📄 PDF Rapor & 📧 Günün Özeti Maili"):
        st.markdown("""
        **PDF Rapor**: dönemi ve bölümleri seç, tek tuşla patrona/ortağa verilecek rapor indir.
        **Mail**: günün özetini otomatik e-posta ile gönderir (Fabrika Ayarları'ndaki adrese).
        """)

    st.markdown("---")

    # ================= TERİMLER SÖZLÜĞÜ =================
    st.subheader("📚 Terimler Sözlüğü")
    st.markdown("""
    | Terim | Anlamı |
    |---|---|
    | **Fire** | Üretilen ama kusurlu/hurda çıkan parça. Her fire, o ürünün kârı kadar kayıptır. |
    | **Fire oranı** | Fire ÷ (üretilen + fire). %3'ün altı genelde iyi kabul edilir. |
    | **Duruş** | Makinenin planlı çalışma saatinde durması (arıza, ayar, bekleme). Asıl maliyeti tamir değil, **üretilemeyen parçalardır.** |
    | **OEE** | Makine verimliliği notu: Çalışma Oranı × Hız × Kalite. %85+ iyi seviye. |
    | **Parça başı kâr** | Bir ürünü satınca eline geçen para eksi maliyeti. Ürünler sayfasında tanımlanır, tüm TL hesapları bundan beslenir. |
    | **Arıza sıklığı** | Bir makinenin ortalama kaç günde bir arızalandığı. Kısalıyorsa makine yaşlanıyor demektir. |
    | **Kritik seviye** | Stokta "artık sipariş ver" alarmı çalan miktar. Tedarik süresini hesaba katarak belirle. |
    | **Puant** | Elektriğin en pahalı olduğu akşam saatleri (17:00–22:00). Gece en ucuz dilimdir. |
    | **kWh** | Elektrik tüketim birimi. Faturadaki ana kalem. |
    | **Fason üretim** | Hammaddeyi müşterinin verdiği, senin sadece işçilik yaptığın üretim. |
    | **Sızıntı** | Önlenebilir kayıpların toplamı: tamir + duruş kaybı + fire kaybı. |
    """)

    st.markdown("---")

    # ================= SIK SORULANLAR =================
    st.subheader("❓ Sık Sorulanlar")

    with st.expander("Rakamlar neden 'aralık' olarak veriliyor, kesin söylese ya?"):
        st.markdown("""
        Bilerek. Bu sistem **olası minimum kayıpları** gösterir, muhasebe kesinliği iddia etmez.
        Kesin görünen ama yanlış olan rakam, temkinli aralıktan daha tehlikelidir.
        Kararı her zaman saha bilginle birlikte sen verirsin.
        """)

    with st.expander("İki sayfada farklı rakam görürsem?"):
        st.markdown("""
        Görmemen gerekir — tüm TL hesapları tek merkezden (hesap motoru) yapılır.
        Farklı rakam görürsen büyük ihtimalle biri kaydedilmemiş taze veriyle, diğeri kayıtlı veriyle
        bakıyordur: **Kaydet**'e basıp sayfayı yenile.
        """)

    with st.expander("Verilerim nerede duruyor, güvende mi?"):
        st.markdown("""
        Tüm veriler bilgisayarındaki `fabrika.db` dosyasında durur — buluta gitmez,
        kimseyle paylaşılmaz. Bu dosyayı ara sıra bir USB'ye veya başka bir diske
        kopyalamak iyi bir yedekleme alışkanlığıdır.
        """)

    with st.expander("Excel yükledim, 'okunamadı' hatası aldım?"):
        st.markdown("""
        En sık sebep: sütun başlıklarının değiştirilmiş olması. **📥 Boş Excel şablonunu indir**
        ile temiz şablon al, başlıklara dokunmadan veriyi doldur, tekrar yükle.
        """)

    with st.expander("Bir makineyi/ürünü sildim ama hesaplarda hâlâ görünüyor?"):
        st.markdown("""
        Eski üretim/arıza kayıtları o makineye ait olduğu için geçmiş hesaplarda görünmeye devam eder —
        bu normaldir, geçmiş değişmez. Yeni kayıtlarda artık listede çıkmaz.
        """)
    """)