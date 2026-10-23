# Kurumsal İK ve Kariyer İş Başvuru Scripti

[![CI Test Suite](https://github.com/eimza-kep/kurumsal-ik-is-basvuru-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/kurumsal-ik-is-basvuru-scripti/actions/workflows/ci.yml)
[![Canlı Demo](https://img.shields.io/badge/Demo-Canl%C4%B1%20Test%20Et-brightgreen.svg)](https://eimza-kep.github.io/kurumsal-ik-is-basvuru-scripti/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![PHP: 7.4+](https://img.shields.io/badge/PHP-7.4%2B-purple.svg)](https://php.net)
[![Docker Support](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](Dockerfile)

KOBİ'ler, şirketler ve insan kaynakları departmanları için geliştirilmiş; harici bağımlılık gerektirmeyen (zero-dependency), çift çalışma motorlu (Python SQLite + PHP JSON), **PDF CV Önizleme / İndirme** ve **BTK KEP & 5070 E-İmza İş Teklifi Onboarding** destekli yeni nesil kurumsal **İş Başvuru ve Aday Takip Portalı**.

---

## 🎯 Temel Özellikler

- **Modern & Mobil Uyumlu Başvuru Formu (`index.html`):**
  - Pozisyon seçimi, TCKN doğrulamalı kimlik, eğitim, iş deneyimi, maaş beklentisi, askerlik, LinkedIn linki.
  - **Base64 PDF CV Yükleme:** Adayın yüklediği özgeçmiş dosyası güvenli bir şekilde Base64 kodlanarak kaydedilir.
  - **Kayıtlı Elektronik Posta (KEP) Entegrasyonu:** Adayın KEP adresi opsiyonel olarak toplanır; BTK ve lisanslı KEPHS (`.kep.tr`) standartlarına göre anlık doğrulanır.
- **6698 Sayılı KVKK Uyumlu:** Çalışan adayı açık rıza ve aydınlatma metni onay mekanizması.
- **Otomatik Başvuru Takip Kodu:** Her başvuruya benzersiz `BASVURU-2026-XXXX` takip numarası ve yazdırılabilir başvuru alındı çıktısı.
- **Gelişmiş İK Yönetim Paneli (`admin.html`):**
  - **📄 Dahili PDF CV Önizleme ve İndirme:** Adayın yüklediği PDF / görsel özgeçmiş dosyasını panelden ayrılmadan iframe içerisinde anında önizleyin veya tek tıkla `[Aday_Adi]_CV.pdf` formatında doğrudan indirin. Yüklenmeyen adaylar için otomatik yapılandırılmış dijital özgeçmiş kartı sunulur.
  - **📨 Resmi KEP & E-İmza İş Teklifi Hazırlama:** 4857 Sayılı İş Kanunu ve 5070 Sayılı Elektronik İmza Kanunu standartlarına uygun resmi iş teklifi (maaş, başlama tarihi, deneme süresi ve yasal delil maddeleri) üretimi ve panoya kopyalama / yazdırma desteği.
  - **6 Aşamalı İşe Alım Pipeline'ı:** *Değerlendiriliyor*, *Ön Eleme Geçti*, *Mülakata Çağrıldı*, *Teklif Yapıldı*, *İşe Alındı*, *Reddedildi*.
  - **Arama ve Filtreleme:** Aday ismi, TCKN, telefon, KEP adresi veya pozisyona göre anlık filtreleme.
  - **Canlı İstatistik Kartları:** Toplam, incelemedeki, mülakattaki ve teklif/kabul aşamasındaki aday metrikleri.
  - **Excel / CSV Dışa Aktarımı:** UTF-8 BOM destekli, Türkçe karakter sorunu yaşatmayan tam kapsamlı aday veri dökümü (KEP ve onaylanan teklif bilgileri dahil).
- **Çift Motorlu & Çevrimdışı Dayanıklı Mimari:**
  - **Python Motoru:** Dahili SQLite veritabanı ile tek tıkla çalışır (`server.py`).
  - **PHP Motoru:** cPanel, Plesk ve paylaşımlı hostinglerde sıfır yapılandırmayla çalışır (`api.php`).
  - **Offline / Fallback Desteği:** Sunucu kesintisinde tarayıcı yerel hafızasına (`localStorage`) kesintisiz geçiş.

---

## 🚀 Hızlı Başlangıç ve Kurulum

### Seçenek 1: Windows (Tek Tıkla Çalıştır)
1. Repoyu indirin veya klonlayın:
   ```bash
   git clone https://github.com/eimza-kep/kurumsal-ik-is-basvuru-scripti.git
   cd kurumsal-ik-is-basvuru-scripti
   ```
2. `Baslat.bat` dosyasına çift tıklayın.
3. Tarayıcınızda otomatik açılacaktır:
   - Aday Başvuru Formu: `http://localhost:8084`
   - İK Yönetim Paneli: `http://localhost:8084/admin`

### Seçenek 2: Linux & macOS
```bash
git clone https://github.com/eimza-kep/kurumsal-ik-is-basvuru-scripti.git
cd kurumsal-ik-is-basvuru-scripti
chmod +x baslat.sh
./baslat.sh
```

### Seçenek 3: Docker ile Çalıştırma
```bash
# Docker imajını derleyin ve başlatın
docker build -t kurumsal-ik-scripti .
docker run -d -p 8084:8084 --name kurumsal-ik kurumsal-ik-scripti

# Tarayıcıdan erişin:
# http://localhost:8084
```

### Seçenek 4: PHP / Paylaşımlı Hosting (cPanel / Plesk)
Tüm dosyaları FTP ile web sunucunuzun ana dizinine veya dilediğiniz bir alt klasöre (`/ik/` veya `/kariyer/`) yükleyin. `api.php` otomatik olarak JSON veritabanını (`ik_basvurular.json`) oluşturup yönetecektir.

---

## 🔌 REST API Referansı

| Metot | Uç Nokta (Endpoint) | Açıklama |
| :--- | :--- | :--- |
| `POST` | `/api/basvuru-yap` | Yeni iş başvurusu kaydeder (`cv_base64`, `kep_address` destekli). |
| `GET` | `/api/basvurular` | Tüm aday başvuru listesini JSON formatında döndürür. |
| `POST` | `/api/durum-guncelle` | Adayın sürecini günceller (`tracking_code`, `status`). |
| `POST` | `/api/teklif-olustur` | Adaya 4857 & 5070 uyumlu resmi KEP teklifi hazırlar ve kaydeder. |
| `GET` | `/api/teklif-goruntule?tracking_code=...` | Oluşturulan teklif metnini ve maaş detaylarını döndürür. |
| `GET` | `/api/validate-kep?kep=...` | KEP adresinin BTK format uygunluğunu test eder. |
| `GET` | `/api/istatistikler` | Pozisyon ve durum bazlı özet başvuru sayılarını döndürür. |

---

## 📊 Dosya ve Dizin Yapısı

```
kurumsal-ik-is-basvuru-scripti/
├── index.html                    # Aday başvuru formu, KEP girişi ve onay ekranı
├── admin.html                    # İK yönetim paneli, PDF CV önizleme & teklif modalleri
├── server.py                     # Standalone Python SQLite HTTP sunucusu (Port 8084)
├── api.php                       # PHP tabanlı JSON/REST backend
├── Baslat.bat                    # Windows tek tıkla başlatıcı
├── baslat.sh                     # Linux / macOS başlatıcı
├── Dockerfile                    # Docker konteyner konfigürasyonu
├── scripts/
│   ├── ik_onboarding_engine.py   # BTK KEP validator ve 4857/5070 iş teklifi motoru
│   └── test_ik.py                # Otomatik birim test paketi
├── .github/
│   └── workflows/ci.yml          # GitHub Actions CI testi
└── README.md                     # Kapsamlı dokümantasyon
```

---

## 🧪 Testleri Çalıştırma

Geliştirilen tüm uç noktaların ve doğrulama motorunun doğruluğu birim testlerle korunmaktadır:

```bash
python scripts/test_ik.py
```

---

## 🌐 Kurumsal İK & E-Dönüşüm Açık Kaynak Ekosistemi

Bu aday takip sistemi, [@eimza-kep](https://github.com/eimza-kep) açık kaynak ekosisteminin insan kaynakları işe alım modülüdür. İlgili diğer araçlar:

* 🔒 [kurumsal-kvkk-basvuru-scripti](https://github.com/eimza-kep/kurumsal-kvkk-basvuru-scripti) - Çalışan adayları için KVKK aydınlatma metni ve açık rıza onay portali.
* 📊 [muhasebe-excel-sablonlari](https://github.com/eimza-kep/muhasebe-excel-sablonlari) - Personel bordro maliyeti, asgari ücret istisnası ve kıdem tazminatı hesaplama tabloları.
* 📄 [python-pdf-eimza-dogrulayici](https://github.com/eimza-kep/python-pdf-eimza-dogrulayici) - İşe alımda imzalanan dijital iş sözleşmeleri ve gizlilik taahhütnameleri doğrulama kütüphanesi.
* 🏢 [kurumsal-isg-ziyaretci-kayit-scripti](https://github.com/eimza-kep/kurumsal-isg-ziyaretci-kayit-scripti) - Kurum içi mülakatlara gelen adaylar için İSG ziyaretçi kayıt portali.
* 🌟 [awesome-turkiye-e-donusum](https://github.com/eimza-kep/awesome-turkiye-e-donusum) - Türkiye e-Dönüşüm açık kaynak araçları ve kütüphaneleri kürasyonu.

---

## ⚖️ Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında açık kaynak olarak sunulmuştur.
