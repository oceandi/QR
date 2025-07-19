# 🚀 QR Reader Pro - Microsoft Store Deployment Guide
https://learn.microsoft.com/en-us/windows/apps/publish/?pivots=store-installer-msix&tabs=individual%2Cmsix-pwa-getting-started

## 📋 Ön Hazırlık

### 1. Gereksinimler
- Windows 10/11 (64-bit)
- Python 3.10+
- Windows SDK (MSIX tools için)
- Microsoft Partner Center hesabı

### 2. Proje Kurulumu
```bash
# Proje klasörü oluştur
mkdir QRReaderPro
cd QRReaderPro

# Virtual environment
python -m venv venv
venv\Scripts\activate

# Gereksinimleri yükle
pip install -r requirements.txt
```

## 🔨 Build İşlemi

### Adım 1: Dosyaları Hazırla
```
QRReaderPro/
├── qr_reader_pro.py      # Ana uygulama (store version)
├── build_store.py        # Build scripti
├── sign_msix.ps1        # İmzalama scripti
├── requirements.txt      # Python gereksinimleri
└── README.md            # Dokümantasyon
```

### Adım 2: Build Et
```bash
# Build scriptini çalıştır
python build_store.py
```

Bu işlem:
- ✅ Icon dosyalarını oluşturur
- ✅ PyInstaller ile EXE yapar
- ✅ MSIX paket dosyalarını hazırlar
- ✅ MakeAppx ile MSIX paketi oluşturur

### Adım 3: İmzala
```powershell
# PowerShell'i ADMIN olarak aç
.\sign_msix.ps1
```

## 📦 Microsoft Store'a Yükleme

### 1. Partner Center Hazırlık
1. https://partner.microsoft.com/dashboard
2. "Yeni uygulama oluştur" → "QR Reader Pro"
3. Uygulama kimliğini al

### 2. Store Listing
```yaml
Uygulama Adı: QR Reader Pro
Kategori: Üretkenlik / Araçlar
Diller: Türkçe, İngilizce

Açıklama:
- Profesyonel QR kod okuyucu
- Ekrandan direkt QR okuma
- WhatsApp otomatik izleme
- Tek tuşla hızlı okuma (Win+Z)
- AI destekli okuma motoru

Özellikler:
✓ Çoklu QR okuma motoru
✓ Otomatik kopyalama
✓ WhatsApp Web entegrasyonu
✓ Özelleştirilebilir kısayollar
✓ Hafif ve hızlı
```

### 3. Ekran Görüntüleri
Gereken görüntüler:
- 1366x768 (En az 3 adet)
- 2560x1440 (Opsiyonel)
- Hero image: 1920x1080

### 4. MSIX Yükleme
1. Partner Center → Paketler
2. QRReaderPro.msix dosyasını yükle
3. Doğrulama bekle (24-48 saat)
4. Yayınla

## 🛠️ Özelleştirme

### Kısayol Değiştirme
`qr_reader_pro.py` içinde:
```python
# Varsayılan Win+Z yerine
self.hotkey = 'win+q'  # veya 'ctrl+shift+q'
```

### WhatsApp Dışında Uygulama İzleme
```python
def find_window(self, title):
    # "WhatsApp" yerine istediğin uygulamayı yaz
    if "Telegram" in win32gui.GetWindowText(hwnd).lower():
```

## 🐛 Sorun Giderme

### "MakeAppx bulunamadı" hatası
```bash
# Windows SDK yükle
https://developer.microsoft.com/windows/downloads/windows-sdk/
```

### "DLL load failed" hatası
```bash
# Visual C++ Redistributable yükle
https://aka.ms/vs/17/release/vc_redist.x64.exe
```

### Certificate hatası
```powershell
# Test certificate'i güvenilir listeye ekle
Import-Certificate -FilePath .\QRReaderPro.pfx -CertStoreLocation Cert:\LocalMachine\TrustedPeople
```

## 📊 Store Analytics

Partner Center'da izlenecek metrikler:
- Günlük indirme sayısı
- Kullanıcı yorumları (4.5+ hedefle)
- Crash raporları
- Kullanım istatistikleri

## 🚀 Güncelleme Stratejisi

### Version 1.1 Planı
- [ ] Barkod okuma desteği
- [ ] OCR metin çıkarma
- [ ] Çoklu monitör desteği
- [ ] Tema desteği (dark/light)

### Version 2.0 Hedefleri
- [ ] Mobil companion app
- [ ] Cloud sync
- [ ] Toplu QR okuma
- [ ] API desteği

## 💰 Monetizasyon

### Freemium Model
- **Free**: Temel QR okuma
- **Pro ($4.99)**: 
  - WhatsApp izleme
  - Sınırsız okuma
  - Öncelikli destek
  - Reklamsız

### Store Badge
```html
<a href="https://www.microsoft.com/store/apps/[APP_ID]">
  <img src="https://get.microsoft.com/images/en-us%20dark.svg" width="200"/>
</a>
```

## 📞 Destek

### Store Description'a Ekle
```
Destek: qrreaderpro@outlook.com
Web: https://qrreaderpro.com
Twitter: @qrreaderpro
```

## ✅ Launch Checklist

- [ ] Tüm dillerde açıklama hazır
- [ ] Ekran görüntüleri yüklendi
- [ ] MSIX test edildi
- [ ] Certificate doğru
- [ ] Privacy policy hazır
- [ ] Support email aktif
- [ ] Marketing materyalleri hazır

## 🎉 Başarılar!

Store'da yayınlandıktan sonra:
1. Sosyal medyada duyur
2. Product Hunt'a ekle
3. Reddit r/Windows10 ve r/software
4. İlk 100 kullanıcıya özel indirim

---

**Not**: Xbox geliştirici hesabınla direkt yükleyebilirsin. Partner Center'da "Xbox console" yerine "Windows desktop" seç.