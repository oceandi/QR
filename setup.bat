@echo off
echo [1/4] Sanal ortam oluşturuluyor...
python -m venv venv

echo [2/4] Sanal ortam aktive ediliyor...
call venv\Scripts\activate

echo [3/4] Gerekli paketler yükleniyor...
pip install -r requirements.txt

echo [4/4] Uygulama arka planda başlatılıyor...
call qr.bat

echo Tamamlandi.
exit
