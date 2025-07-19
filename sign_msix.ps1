# sign_msix.ps1 - MSIX paketi imzalama scripti

# Admin yetkisi kontrolü
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Bu script admin yetkisi gerektiriyor!" -ForegroundColor Red
    Write-Host "PowerShell'i admin olarak açıp tekrar deneyin." -ForegroundColor Yellow
    exit
}

Write-Host "QR Reader Pro - MSIX İmzalama" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# 1. Self-signed certificate oluştur (test için)
Write-Host "`n📝 Self-signed certificate oluşturuluyor..." -ForegroundColor Yellow

$cert = New-SelfSignedCertificate `
    -Type Custom `
    -Subject "CN=Ahmet Emirhan Korkmaz" `
    -KeyUsage DigitalSignature `
    -FriendlyName "QR Reader Pro Certificate" `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")

$thumbprint = $cert.Thumbprint
Write-Host "✅ Certificate oluşturuldu: $thumbprint" -ForegroundColor Green

# 2. Certificate'i PFX olarak export et
Write-Host "`n📤 Certificate export ediliyor..." -ForegroundColor Yellow

$pwd = ConvertTo-SecureString -String "qrreaderpro123" -Force -AsPlainText
$certPath = ".\QRReaderPro.pfx"

Export-PfxCertificate `
    -Cert "Cert:\CurrentUser\My\$thumbprint" `
    -FilePath $certPath `
    -Password $pwd

Write-Host "✅ Certificate exported: $certPath" -ForegroundColor Green

# 3. MSIX paketini imzala
Write-Host "`n✍️ MSIX paketi imzalanıyor..." -ForegroundColor Yellow

if (Test-Path ".\QRReaderPro.msix") {
    # SignTool kullan
    $signToolPath = "${env:ProgramFiles(x86)}\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe"
    
    if (Test-Path $signToolPath) {
        & $signToolPath sign /fd SHA256 /a /f $certPath /p "qrreaderpro123" ".\QRReaderPro.msix"
        Write-Host "✅ MSIX paketi imzalandı!" -ForegroundColor Green
    } else {
        Write-Host "❌ SignTool bulunamadı! Windows SDK kurulu değil." -ForegroundColor Red
        Write-Host "   https://developer.microsoft.com/windows/downloads/windows-sdk/" -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ QRReaderPro.msix bulunamadı!" -ForegroundColor Red
}

# 4. Certificate'i Trusted Root'a ekle (test için)
Write-Host "`n🔐 Certificate güvenilir listeye ekleniyor..." -ForegroundColor Yellow

$response = Read-Host "Certificate'i güvenilir listeye eklemek istiyor musunuz? (Y/N)"
if ($response -eq 'Y') {
    Import-Certificate -FilePath $certPath -CertStoreLocation Cert:\LocalMachine\TrustedPeople
    Write-Host "✅ Certificate güvenilir listeye eklendi!" -ForegroundColor Green
}

Write-Host "`n✅ İmzalama işlemi tamamlandı!" -ForegroundColor Green
Write-Host "`n📋 Bilgiler:" -ForegroundColor Cyan
Write-Host "   Certificate: $certPath" -ForegroundColor White
Write-Host "   Password: qrreaderpro123" -ForegroundColor White
Write-Host "   Thumbprint: $thumbprint" -ForegroundColor White

Write-Host "`n💡 Store'a yüklemek için:" -ForegroundColor Yellow
Write-Host "   1. Partner Center'da gerçek certificate kullan" -ForegroundColor White
Write-Host "   2. Bu self-signed cert sadece test içindir" -ForegroundColor White