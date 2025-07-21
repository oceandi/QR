@echo off
echo Building Microsoft Store package...

set SDK_PATH="C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64"
if not exist %SDK_PATH% (
    echo Error: Windows 10 SDK not found
    echo Please install Windows 10 SDK from Visual Studio Installer
    pause
    exit /b 1
)

echo Creating app package...
%SDK_PATH%\makeappx.exe pack /d . /p QRReaderPro.appx /o

if exist QRReaderPro.appx (
    echo ✅ Package created successfully: QRReaderPro.appx
    echo 📋 Ready for Microsoft Store submission
) else (
    echo ❌ Package creation failed
)

pause
