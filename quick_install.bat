@echo off
REM quick_install.bat - Hızlı kurulum scripti
echo ========================================
echo QR Reader Pro - Hizli Kurulum
echo ========================================
echo.

REM Python kontrolü
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python yuklu degil!
    echo Python'u https://python.org adresinden indirin.
    pause
    exit /b 1
)

echo [OK] Python bulundu
echo.

REM Virtual environment oluştur
echo [1/5] Virtual environment olusturuluyor...
python -m venv venv
call venv\Scripts\activate.bat

REM Pip güncelle
echo.
echo [2/5] Pip guncelleniyor...
python -m pip install --upgrade pip

REM Gereksinimleri yükle
echo.
echo [3/5] Gereksinimler yukleniyor...
pip install pystray pillow opencv-python numpy pyperclip keyboard mss pywin32 pyzbar

REM qreader'ı opsiyonel yükle
echo.
echo [4/5] AI-tabanli QR okuyucu yukleniyor (opsiyonel)...
pip install qreader

REM PyInstaller yükle
echo.
echo [5/5] Build araclari yukleniyor...
pip install pyinstaller

echo.
echo ========================================
echo Kurulum tamamlandi!
echo ========================================
echo.
echo Simdi yapmaniz gerekenler:
echo 1. python qr_reader_pro.py (test icin)
echo 2. python build_store.py (store versiyonu icin)
echo.
echo Win+Z ile QR okuma yapabilirsiniz!
echo.
pause