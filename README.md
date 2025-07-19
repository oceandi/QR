# 📱 Windows QR Reader

iPhone'daki gibi QR kod okuma deneyimi Windows'ta! Alan seçimi yaparak ekrandaki QR kodları okuyun.

## 🚀 Özellikler

- **Win+Q** kısayolu ile hızlı erişim
- Ekranda alan seçimi ile QR okuma
- System tray'de sürekli çalışma
- Otomatik kopyalama desteği
- Hafif ve hızlı (10-15MB RAM)

## 📋 Kurulum

### 1. Gereksinimleri Yükle

```bash
# Virtual environment oluştur
python -m venv venv

# Aktif et
venv\Scripts\activate

# Gereksinimleri yükle
pip install -r requirements.txt
```

### 2. Programı Çalıştır

```bash
python qr_reader.pyw
```

### 3. Başlangıca Ekle (Opsiyonel)

```bash
# Başlangıca ekle
python install_startup.py

# Başlangıçtan kaldır
python install_startup.py --remove
```

## 🎯 Kullanım

1. **Win+Q** tuşlarına basın
2. QR kodun üzerine tıklayın ve sürükleyerek seçin
3. QR kod içeriği otomatik olarak gösterilir
4. "Kopyala" butonuna tıklayın veya Enter'a basın

### Kısayollar
- **Win+Q**: QR okuma başlat
- **ESC**: İptal et
- **Enter**: Metni kopyala (popup'ta)

## 🔧 Sorun Giderme

### "QR Bulunamadı" Hatası
- QR kodun tamamını seçtiğinizden emin olun
- Ekranı yakınlaştırın (Ctrl++)
- Daha net bir görüntü deneyin

### DLL Hatası
Eğer pyzbar DLL hatası veriyorsa:
1. [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) yükleyin
2. Sistemi yeniden başlatın

## 📁 Dosya Yapısı

```
QR/
├── qr_reader.pyw          # Ana program
├── install_startup.py     # Başlangıç kurulum scripti
├── requirements.txt       # Python gereksinimleri
└── README.md             # Bu dosya
```

## 🎨 Özelleştirme

Kısayolu değiştirmek için `qr_reader.pyw` dosyasında:
```python
keyboard.add_hotkey('win+q', self.start_selection)  # 'win+q' yerine istediğinizi yazın
```

## 🤝 Katkıda Bulunma

Her türlü öneri ve katkıya açığız!