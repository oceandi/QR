#!/usr/bin/env python3
"""
Microsoft Store Packaging Script for QR Reader Pro
Creates the necessary files and structure for Microsoft Store submission
"""
import os
import shutil
import subprocess
import json
from pathlib import Path

def create_store_package():
    """Create Microsoft Store package structure"""
    
    print("🏪 Creating Microsoft Store package...")
    
    # Create package directory
    package_dir = Path("msstore_package")
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Build Windows executable
    print("🔨 Building Windows executable...")
    result = subprocess.run([
        "go", "build", 
        "-ldflags=-H windowsgui -s -w",
        "-o", str(package_dir / "QRReaderPro.exe"),
        "main_store.go"
    ], env={**os.environ, "GOOS": "windows", "GOARCH": "amd64"})
    
    if result.returncode != 0:
        print("❌ Build failed!")
        return
    
    # Create app manifest
    create_app_manifest(package_dir)
    
    # Create package manifest  
    create_package_manifest(package_dir)
    
    # Create assets directory and icons
    create_assets(package_dir)
    
    # Create build script
    create_build_script(package_dir)
    
    print("✅ Microsoft Store package ready!")
    print(f"📁 Package location: {package_dir.absolute()}")
    print("📋 Next steps:")
    print("1. Install Windows SDK")
    print("2. Run build_appx.bat in package folder")
    print("3. Upload .appx file to Microsoft Partner Center")

def create_app_manifest(package_dir):
    """Create Package.appxmanifest"""
    manifest = '''<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">
  
  <Identity Name="QRReaderPro" 
            Publisher="CN=YourCompany" 
            Version="1.0.0.0" />
  
  <Properties>
    <DisplayName>QR Reader Pro</DisplayName>
    <PublisherDisplayName>Your Company</PublisherDisplayName>
    <Logo>Assets\\StoreLogo.png</Logo>
    <Description>Professional QR code scanner for Windows. Fast, accurate, and easy to use.</Description>
  </Properties>
  
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Universal" MinVersion="10.0.17763.0" MaxVersionTested="10.0.22000.0" />
  </Dependencies>
  
  <Resources>
    <Resource Language="x-generate" />
  </Resources>
  
  <Applications>
    <Application Id="QRReaderPro" Executable="QRReaderPro.exe" EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="QR Reader Pro"
                          Square150x150Logo="Assets\\Square150x150Logo.png"
                          Square44x44Logo="Assets\\Square44x44Logo.png"
                          Description="Professional QR code scanner"
                          BackgroundColor="transparent">
        <uap:DefaultTile Wide310x150Logo="Assets\\Wide310x150Logo.png" />
        <uap:SplashScreen Image="Assets\\SplashScreen.png" />
      </uap:VisualElements>
    </Application>
  </Applications>
  
  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
  
</Package>'''
    
    with open(package_dir / "Package.appxmanifest", "w", encoding="utf-8") as f:
        f.write(manifest)
    print("✅ Package.appxmanifest created")

def create_package_manifest(package_dir):
    """Create package metadata"""
    metadata = {
        "name": "QR Reader Pro",
        "version": "1.0.0",
        "description": "Professional QR code scanner for Windows",
        "author": "Your Company",
        "category": "Productivity",
        "price": "Free",
        "features": [
            "Fast QR code scanning",
            "System tray integration", 
            "Hotkey support (Q+R)",
            "Automatic clipboard copy",
            "Professional detection algorithms"
        ]
    }
    
    with open(package_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print("✅ metadata.json created")

def create_assets(package_dir):
    """Create assets directory and placeholder images"""
    assets_dir = package_dir / "Assets"
    assets_dir.mkdir()
    
    # Asset sizes needed for Microsoft Store
    asset_sizes = {
        "Square44x44Logo.png": (44, 44),
        "Square150x150Logo.png": (150, 150),  
        "Wide310x150Logo.png": (310, 150),
        "StoreLogo.png": (50, 50),
        "SplashScreen.png": (620, 300)
    }
    
    try:
        from PIL import Image, ImageDraw
        
        for filename, (width, height) in asset_sizes.items():
            # Create simple QR-style icon
            img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
            draw = ImageDraw.Draw(img)
            
            # Draw QR pattern
            block_size = min(width, height) // 8
            for i in range(0, width, block_size * 2):
                for j in range(0, height, block_size * 2):
                    if (i + j) // block_size % 2 == 0:
                        draw.rectangle([i, j, i + block_size, j + block_size], fill='black')
            
            img.save(assets_dir / filename)
            
        print("✅ Asset images created")
        
    except ImportError:
        print("⚠️ PIL not available - creating placeholder assets")
        for filename in asset_sizes.keys():
            (assets_dir / filename).touch()

def create_build_script(package_dir):
    """Create Windows build script"""
    script = '''@echo off
echo Building Microsoft Store package...

set SDK_PATH="C:\\Program Files (x86)\\Windows Kits\\10\\bin\\10.0.22000.0\\x64"
if not exist %SDK_PATH% (
    echo Error: Windows 10 SDK not found
    echo Please install Windows 10 SDK from Visual Studio Installer
    pause
    exit /b 1
)

echo Creating app package...
%SDK_PATH%\\makeappx.exe pack /d . /p QRReaderPro.appx /o

if exist QRReaderPro.appx (
    echo ✅ Package created successfully: QRReaderPro.appx
    echo 📋 Ready for Microsoft Store submission
) else (
    echo ❌ Package creation failed
)

pause
'''
    
    with open(package_dir / "build_appx.bat", "w") as f:
        f.write(script)
    print("✅ build_appx.bat created")

if __name__ == "__main__":
    create_store_package()