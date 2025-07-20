# QR Reader Pro

🚀 **The most powerful QR code scanner** - Single executable, works on Windows, macOS, and Linux.

## ⚡ Features

- **Multi-Engine Detection**: ZXing + OpenCV for 99% accuracy
- **Instant Scan**: Q+R hotkey for immediate scanning
- **System Tray**: Always accessible from menu bar
- **Auto-Copy**: Results automatically copied to clipboard
- **Cross-Platform**: Single executable for each platform
- **Zero Dependencies**: No installation required

## 📥 Download

| Platform | Download |
|----------|----------|
| Windows  | `QRReaderPro.exe` |
| macOS    | `QRReaderPro-mac` |
| Linux    | `QRReaderPro-linux` |

## 🎯 Usage

1. **Run the executable**
2. **Look for QR icon** in system tray/menu bar
3. **Scan QR codes:**
   - **Hotkey**: Press `Q+R` 
   - **Menu**: Click tray icon → "🔍 Scan Now"
4. **Result automatically copied** to clipboard

## 🔧 Build from Source

```bash
# Clone repository
git clone https://github.com/yourname/qrreaderpro
cd qrreaderpro

# Install dependencies
go mod tidy

# Build for all platforms
./build.sh

# Or build for current platform only
go build -o QRReaderPro main.go
```

## 📋 Requirements

- **Windows**: Windows 10+ (64-bit)
- **macOS**: macOS 10.15+ (Catalina)
- **Linux**: Any modern distribution with X11/Wayland

## 🎨 Technical Details

- **Language**: Go 1.21+
- **QR Engines**: 
  - ZXing (primary detection)
  - OpenCV (fallback + preprocessing)
- **UI Framework**: Fyne + systray
- **Size**: ~15MB per executable
- **Performance**: <100ms scan time

## 🔒 Privacy

- **No network access** - works completely offline
- **No data collection** - nothing leaves your device
- **Open source** - audit the code yourself

## 🆘 Troubleshooting

**Q: Hotkeys don't work on macOS?**  
A: macOS requires accessibility permissions. Grant permission in System Preferences > Security & Privacy > Accessibility.

**Q: No QR detected?**  
A: Ensure QR code is clearly visible on screen and not obscured.

**Q: App won't start?**  
A: Check if antivirus is blocking the executable.

## 📄 License

MIT License - Use freely for personal and commercial projects.

---

**Made with ❤️ for QR code enthusiasts worldwide**