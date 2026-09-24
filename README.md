# Kurumsal İK ve Kariyer İş Başvuru Scripti

[![CI Test Suite](https://github.com/eimza-kep/kurumsal-ik-is-basvuru-scripti/actions/workflows/ci.yml/badge.svg)](https://github.com/eimza-kep/kurumsal-ik-is-basvuru-scripti/actions/workflows/ci.yml)
[![Canlı Demo](https://img.shields.io/badge/Demo-Canl%C4%B1%20Test%20Et-brightgreen.svg)](https://eimza-kep.github.io/kurumsal-ik-is-basvuru-scripti/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg)](https://python.org)
[![PHP: 7.4+](https://img.shields.io/badge/PHP-7.4%2B-purple.svg)](https://php.net)

KOBİ'ler, şirketler ve insan kaynakları departmanları için geliştirilmiş, harici bağımlılık gerektirmeyen (zero-dependency), çift çalışma motorlu (Python SQLite + PHP JSON) ve tek tıkla çalışan kurumsal **İş Başvuru ve Aday Takip Portalı**.

---

## 🎯 Özellikler

- **Modern & Mobil Uyumlu Başvuru Formu:** Pozisyon seçimi, TCKN doğrulamalı kimlik, eğitim, iş deneyimi, maaş beklentisi, askerlik, LinkedIn linki ve CV dosya yükleme alanı.
- **6698 Sayılı KVKK Uyumlu:** Çalışan adayı açık rıza ve aydınlatma metni onay mekanizması.
- **Otomatik Başvuru Takip Kodu:** Her başvuruya benzersiz `BASVURU-2026-XXXX` takip numarası ve yazdırılabilir başvuru alındı çıktısı.
- **İK Yönetim Paneli (`/admin`):**
  - Başvuru arama (İsim, TCKN, Pozisyon, Telefon).
  - Pozisyona ve duruma göre filtreleme.
  - Durum güncelleme (Değerlendiriliyor, Mülakata Çağrıldı, Teklif Yapıldı, Reddedildi).
  - Canlı başvuru istatistik kartları.
  - Tek tıkla UTF-8 BOM destekli Excel uyumlu **CSV Dışa Aktarımı**.
- **Çift Motorlu Mimari:**
  - **Python Motoru:** Dahili SQLite veritabanı ile tek tıkla çalışır (`server.py`).
  - **PHP Motoru:** cPanel, Plesk ve paylaşımlı hostinglerde sıfır yapılandırmayla çalışır (`api.php`).
  - **Offline Fallback:** İnternet veya sunucu kesintisinde tarayıcı yerel hafızasına (`localStorage`) güvenli yedekleme.

---

## 🚀 Hızlı Başlangıç

### Windows (Tek Tıkla Çalıştır)
1. Repoyu indirin veya klonlayın.
2. `Baslat.bat` dosyasına çift tıklayın.
3. Tarayıcınızda otomatik açılacaktır:
   - Form: `http://localhost:8084`
   - İK Yönetim Paneli: `http://localhost:8084/admin`

### Linux & macOS
```bash
git clone https://github.com/eimza-kep/kurumsal-ik-is-basvuru-scripti.git
cd kurumsal-ik-is-basvuru-scripti
chmod +x baslat.sh
./baslat.sh
```

### PHP / Paylaşımlı Hosting
Tüm dosyaları FTP ile web sunucunuzun ana dizinine veya bir alt klasöre (`/ik/` veya `/kariyer/`) yükleyin. `api.php` otomatik olarak JSON veritabanını oluşturup yönetecektir.

---

## 📊 Mimari ve Dosya Yapısı

```
kurumsal-ik-is-basvuru-scripti/
├── index.html              # Aday başvuru formu ve onay ekranı
├── admin.html              # İK yönetim ve takip paneli
├── server.py               # Standalone Python SQLite HTTP sunucusu (Port 8084)
├── api.php                 # PHP tabanlı JSON/REST backend
├── Baslat.bat              # Windows tek tıkla başlatıcı
├── baslat.sh               # Linux / macOS başlatıcı
├── scripts/
│   └── test_ik.py          # Otomatik birim test paketi
├── .github/
│   └── workflows/ci.yml    # GitHub Actions CI testi
└── README.md               # Dokümantasyon
```

---

## 🧪 Testleri Çalıştırma

```bash
python scripts/test_ik.py
```

---

## ⚖️ Lisans

Bu proje [MIT Lisansı](LICENSE) kapsamında açık kaynak olarak sunulmuştur.
