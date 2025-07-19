# build_store.py - Microsoft Store için build scripti
import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_icon():
    """Icon oluştur"""
    try:
        from PIL import Image, ImageDraw
        
        # 256x256 icon
        icon = Image.new('RGBA', (256, 256), (255, 255, 255, 0))
        draw = ImageDraw.Draw(icon)
        
        # QR pattern
        block_size = 32
        for i in range(0, 256, block_size):
            for j in range(0, 256, block_size):
                if (i//block_size + j//block_size) % 2 == 0:
                    draw.rectangle([i, j, i+block_size-4, j+block_size-4], 
                                 fill=(33, 150, 243, 255))
        
        # Köşe işaretleri
        corner_size = 80
        corner_color = (33, 150, 243, 255)
        thickness = 16
        
        # Sol üst
        draw.rectangle([0, 0, corner_size, thickness], fill=corner_color)
        draw.rectangle([0, 0, thickness, corner_size], fill=corner_color)
        # Sağ üst
        draw.rectangle([256-corner_size, 0, 256, thickness], fill=corner_color)
        draw.rectangle([256-thickness, 0, 256, corner_size], fill=corner_color)
        # Sol alt
        draw.rectangle([0, 256-thickness, corner_size, 256], fill=corner_color)
        draw.rectangle([0, 256-corner_size, thickness, 256], fill=corner_color)
        
        # Farklı boyutlarda kaydet
        sizes = [16, 32, 48, 64, 128, 256]
        icons = []
        
        for size in sizes:
            resized = icon.resize((size, size), Image.Resampling.LANCZOS)
            filename = f'icon_{size}.png'
            resized.save(filename)
            icons.append(filename)
            
        # ICO dosyası oluştur
        icon.save('icon.ico', format='ICO', sizes=[(s, s) for s in sizes])
        
        print("✅ Icon dosyaları oluşturuldu")
        return True
        
    except Exception as e:
        print(f"❌ Icon oluşturma hatası: {e}")
        return False

def build_exe():
    """PyInstaller ile exe oluştur"""
    print("\n🔨 EXE oluşturuluyor...")
    
    # PyInstaller spec dosyası
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['qr_reader_pro.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('icon.ico', '.'),
        ('icon_*.png', '.'),
    ],
    hiddenimports=[
        'pystray._win32',
        'pkg_resources.py2_warn',
        'win32gui',
        'win32con',
        'cv2',
        'numpy',
        'PIL',
        'pyzbar',
        'keyboard',
        'mss',
        'pyperclip',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='QRReaderPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
    version='file_version_info.txt',
)
'''
    
    # Version info
    version_info = '''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Ahmet Emirhan Korkmaz'),
        StringStruct(u'FileDescription', u'QR Reader Pro - Profesyonel QR kod okuyucu'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'QRReaderPro'),
        StringStruct(u'LegalCopyright', u'© 2024 Ahmet Emirhan Korkmaz'),
        StringStruct(u'OriginalFilename', u'QRReaderPro.exe'),
        StringStruct(u'ProductName', u'QR Reader Pro'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    # Dosyaları oluştur
    with open('qr_reader_pro.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
        
    with open('file_version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    # PyInstaller çalıştır
    cmd = [sys.executable, '-m', 'PyInstaller', '--clean', 'qr_reader_pro.spec']
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ EXE başarıyla oluşturuldu")
        return True
    else:
        print(f"❌ PyInstaller hatası: {result.stderr}")
        return False

def create_msix_files():
    """MSIX paket dosyalarını oluştur"""
    print("\n📦 MSIX dosyaları hazırlanıyor...")
    
    # AppxManifest.xml
    manifest = '''<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"
         IgnorableNamespaces="uap rescap">
  
  <Identity Name="QRReaderPro.AhmetEmirhanKorkmaz"
            Publisher="CN=Ahmet Emirhan Korkmaz"
            Version="1.0.0.0" />
            
  <Properties>
    <DisplayName>QR Reader Pro</DisplayName>
    <PublisherDisplayName>Ahmet Emirhan Korkmaz</PublisherDisplayName>
    <Logo>Assets\StoreLogo.png</Logo>
  </Properties>
  
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxVersionTested="10.0.22621.0" />
  </Dependencies>
  
  <Resources>
    <Resource Language="tr-TR" />
    <Resource Language="en-US" />
  </Resources>
  
  <Applications>
    <Application Id="QRReaderPro" Executable="QRReaderPro.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements
        DisplayName="QR Reader Pro"
        Description="Profesyonel QR kod okuyucu. Ekrandan QR kod okuma, WhatsApp izleme ve daha fazlası."
        BackgroundColor="transparent"
        Square150x150Logo="Assets\Square150x150Logo.png"
        Square44x44Logo="Assets\Square44x44Logo.png">
        <uap:DefaultTile Wide310x150Logo="Assets\Wide310x150Logo.png" Square71x71Logo="Assets\Square71x71Logo.png" Square310x310Logo="Assets\Square310x310Logo.png"/>
        <uap:SplashScreen Image="Assets\SplashScreen.png" />
      </uap:VisualElements>
    </Application>
  </Applications>
  
  <Capabilities>
    <Capability Name="internetClient" />
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
  
</Package>
'''
    
    # Klasör yapısı oluştur
    os.makedirs('MSIX/Assets', exist_ok=True)
    
    # Manifest dosyası
    with open('MSIX/AppxManifest.xml', 'w', encoding='utf-8') as f:
        f.write(manifest)
    
    # Store için gerekli asset'leri oluştur
    try:
        from PIL import Image, ImageDraw
        
        assets = {
            'Square44x44Logo.png': (44, 44),
            'Square71x71Logo.png': (71, 71),
            'Square150x150Logo.png': (150, 150),
            'Square310x310Logo.png': (310, 310),
            'Wide310x150Logo.png': (310, 150),
            'StoreLogo.png': (50, 50),
            'SplashScreen.png': (620, 300),
        }
        
        for filename, (width, height) in assets.items():
            img = Image.new('RGBA', (width, height), (33, 150, 243, 255))
            draw = ImageDraw.Draw(img)
            
            # QR pattern çiz
            block_size = min(width, height) // 8
            for i in range(0, width, block_size):
                for j in range(0, height, block_size):
                    if (i//block_size + j//block_size) % 2 == 0:
                        draw.rectangle([i, j, i+block_size-2, j+block_size-2], 
                                     fill=(255, 255, 255, 255))
            
            img.save(f'MSIX/Assets/{filename}')
            
        print("✅ Asset dosyaları oluşturuldu")
        
    except Exception as e:
        print(f"❌ Asset oluşturma hatası: {e}")
        
    # EXE'yi kopyala
    if os.path.exists('dist/QRReaderPro.exe'):
        shutil.copy('dist/QRReaderPro.exe', 'MSIX/QRReaderPro.exe')
        print("✅ EXE kopyalandı")
    
    # priconfig.xml
    priconfig = '''<?xml version="1.0" encoding="utf-8"?>
<resources targetOsVersion="10.0.0" majorVersion="1">
  <index root="\" startIndexAt="\">
    <default>
      <qualifier name="Language" value="tr-TR,en-US"/>
      <qualifier name="Contrast" value="standard"/>
      <qualifier name="Scale" value="100"/>
      <qualifier name="HomeRegion" value="001"/>
      <qualifier name="TargetSize" value="256"/>
      <qualifier name="LayoutDirection" value="LTR"/>
      <qualifier name="Theme" value="dark"/>
      <qualifier name="AlternateForm" value=""/>
      <qualifier name="DXFeatureLevel" value="DX9"/>
      <qualifier name="Configuration" value=""/>
      <qualifier name="DeviceFamily" value="Desktop"/>
    </default>
    <indexer-config type="folder" foldernameAsQualifier="true" filenameAsQualifier="true" qualifierDelimiter="."/>
  </index>
</resources>
'''
    
    with open('MSIX/priconfig.xml', 'w', encoding='utf-8') as f:
        f.write(priconfig)
    
    print("✅ MSIX dosyaları hazır")
    return True

def build_msix():
    """MSIX paketi oluştur"""
    print("\n📦 MSIX paketi oluşturuluyor...")
    
    # MakeAppx komutu
    cmd = [
        'MakeAppx.exe', 'pack',
        '/d', 'MSIX',
        '/p', 'QRReaderPro.msix',
        '/nv'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MSIX paketi oluşturuldu")
            return True
        else:
            print(f"❌ MakeAppx hatası: {result.stderr}")
            print("\n💡 Windows SDK kurulu değilse:")
            print("   https://developer.microsoft.com/windows/downloads/windows-sdk/")
            return False
    except FileNotFoundError:
        print("❌ MakeAppx.exe bulunamadı!")
        print("\n💡 Windows SDK kurmanız gerekiyor:")
        print("   https://developer.microsoft.com/windows/downloads/windows-sdk/")
        return False

def main():
    """Ana build işlemi"""
    print("🚀 QR Reader Pro - Microsoft Store Build")
    print("=" * 50)
    
    # 1. Icon oluştur
    if not create_icon():
        return
    
    # 2. EXE oluştur
    if not build_exe():
        return
    
    # 3. MSIX dosyaları oluştur
    if not create_msix_files():
        return
    
    # 4. MSIX paketi oluştur
    build_msix()
    
    print("\n✅ Build tamamlandı!")
    print("\n📝 Sonraki adımlar:")
    print("1. QRReaderPro.msix dosyasını imzala")
    print("2. Microsoft Partner Center'da yükle")
    print("3. Store listing'i doldur")
    
    # Temizlik
    if input("\n🧹 Build dosyalarını temizle? (y/n): ").lower() == 'y':
        shutil.rmtree('build', ignore_errors=True)
        shutil.rmtree('dist', ignore_errors=True)
        os.remove('qr_reader_pro.spec')
        os.remove('file_version_info.txt')
        print("✅ Temizlik tamamlandı")

if __name__ == "__main__":
    main()