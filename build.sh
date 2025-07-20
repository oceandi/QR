#!/bin/bash

echo "🚀 Building QR Reader Pro for all platforms..."

# Create build directory
mkdir -p builds

# Build for Windows
echo "📦 Building for Windows..."
GOOS=windows GOARCH=amd64 go build -o builds/QRReaderPro.exe main.go

# Build for macOS
echo "📦 Building for macOS..."
GOOS=darwin GOARCH=amd64 go build -o builds/QRReaderPro-mac main.go

# Build for Linux
echo "📦 Building for Linux..."
GOOS=linux GOARCH=amd64 go build -o builds/QRReaderPro-linux main.go

echo "✅ Build complete!"
echo "📁 Executables created in builds/ directory:"
ls -la builds/