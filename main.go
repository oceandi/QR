package main

import (
	"fmt"
	"image"
	"image/color"
	"image/png"
	"math"
	"os"
	"os/exec"

	"fyne.io/systray"
	"github.com/atotto/clipboard"
	"github.com/makiuchi-d/gozxing"
	"github.com/makiuchi-d/gozxing/qrcode"
	hook "github.com/robotn/gohook"
)

type QRReader struct {
	scanner *QRScanner
}

type QRScanner struct {
	reader gozxing.Reader
}

func NewQRScanner() *QRScanner {
	return &QRScanner{
		reader: qrcode.NewQRCodeReader(),
	}
}

func (qs *QRScanner) ScanScreen() (string, error) {
	// Take screenshot using system command
	imagePath := "/tmp/qr_screenshot.png"
	
	// macOS screenshot command
	cmd := exec.Command("screencapture", "-x", imagePath)
	err := cmd.Run()
	if err != nil {
		return "", fmt.Errorf("screenshot failed: %v", err)
	}

	// Try to decode QR from image
	result, err := qs.scanImageFile(imagePath)
	if err != nil {
		return "", fmt.Errorf("QR detection failed: %v", err)
	}

	return result, nil
}

func (qs *QRScanner) scanImageFile(imagePath string) (string, error) {
	// Open and decode PNG file
	file, err := os.Open(imagePath)
	if err != nil {
		return "", fmt.Errorf("failed to open image: %v", err)
	}
	defer file.Close()

	// Decode PNG
	img, err := png.Decode(file)
	if err != nil {
		return "", fmt.Errorf("failed to decode image: %v", err)
	}

	// PROFESSIONAL PIPELINE for field work
	fmt.Println("🔬 Starting professional QR detection pipeline...")
	
	// Stage 1: Multi-scale detection (for small QRs)
	result, err := qs.multiScaleDetection(img)
	if err == nil && result != "" {
		fmt.Println("✅ Found with multi-scale detection")
		return result, nil
	}

	// Stage 2: ROI-based smart detection 
	result, err = qs.smartROIDetection(img)
	if err == nil && result != "" {
		fmt.Println("✅ Found with ROI detection")
		return result, nil
	}

	// Stage 3: Enhanced preprocessing for blurry images
	result, err = qs.enhancedPreprocessingPipeline(img)
	if err == nil && result != "" {
		fmt.Println("✅ Found with enhanced preprocessing")
		return result, nil
	}

	// Stage 4: Fallback to grid scan
	result, err = qs.gridBasedScan(img)
	if err == nil && result != "" {
		fmt.Println("✅ Found with grid scan")
		return result, nil
	}

	return "", fmt.Errorf("professional pipeline failed - QR may be too degraded")
}

// STAGE 1: Multi-scale detection for small QRs
func (qs *QRScanner) multiScaleDetection(img image.Image) (string, error) {
	bounds := img.Bounds()
	
	// Try different scales - crucial for small QRs
	scales := []float64{1.0, 1.5, 2.0, 2.5, 3.0, 0.75, 0.5}
	
	for _, scale := range scales {
		if scale == 1.0 {
			// Try original size first
			result, err := qs.scanDirect(img)
			if err == nil && result != "" {
				return result, nil
			}
		} else {
			// Scale image
			newWidth := int(float64(bounds.Dx()) * scale)
			newHeight := int(float64(bounds.Dy()) * scale)
			
			if newWidth > 50 && newHeight > 50 && newWidth < 5000 && newHeight < 5000 {
				scaled := qs.scaleImage(img, newWidth, newHeight)
				result, err := qs.scanDirect(scaled)
				if err == nil && result != "" {
					fmt.Printf("🔍 QR found at scale %.1fx\n", scale)
					return result, nil
				}
			}
		}
	}
	
	return "", fmt.Errorf("no QR found at any scale")
}

// STAGE 2: Smart ROI detection - find QR regions automatically
func (qs *QRScanner) smartROIDetection(img image.Image) (string, error) {
	bounds := img.Bounds()
	width := bounds.Dx()
	height := bounds.Dy()
	
	// Define smart regions based on common QR positions
	regions := []struct {
		name string
		x, y, w, h int
	}{
		// Center regions (most common)
		{"center", width/4, height/4, width/2, height/2},
		{"center-large", width/6, height/6, 2*width/3, 2*height/3},
		
		// Corner regions
		{"top-left", 0, 0, width/2, height/2},
		{"top-right", width/2, 0, width/2, height/2},
		{"bottom-left", 0, height/2, width/2, height/2},
		{"bottom-right", width/2, height/2, width/2, height/2},
		
		// Edge centers
		{"top-center", width/4, 0, width/2, height/3},
		{"bottom-center", width/4, 2*height/3, width/2, height/3},
		{"left-center", 0, height/4, width/3, height/2},
		{"right-center", 2*width/3, height/4, width/3, height/2},
	}
	
	for _, region := range regions {
		if region.x >= 0 && region.y >= 0 && 
		   region.x+region.w <= width && region.y+region.h <= height {
			
			roi := cropImage(img, region.x, region.y, region.x+region.w, region.y+region.h)
			if roi != nil {
				// Try multiple approaches on this ROI
				approaches := []func(image.Image) (string, error){
					qs.scanDirect,
					qs.scanWithContrast,
					qs.scanWithCV2Advanced,
					qs.scanWithBinarization,
				}
				
				for _, approach := range approaches {
					result, err := approach(roi)
					if err == nil && result != "" {
						fmt.Printf("🎯 QR found in %s region\n", region.name)
						return result, nil
					}
				}
			}
		}
	}
	
	return "", fmt.Errorf("no QR found in smart ROI regions")
}

// STAGE 3: Enhanced preprocessing pipeline for blurry/poor quality images
func (qs *QRScanner) enhancedPreprocessingPipeline(img image.Image) (string, error) {
	// Chain of enhancements specifically for field photos
	enhancements := []struct {
		name string
		process func(image.Image) image.Image
	}{
		{"unsharp-mask", qs.applyUnsharpMask},
		{"gamma-correction", qs.applyGammaCorrection},
		{"clahe-contrast", qs.applyCLAHE},
		{"noise-reduction", qs.applyNoiseReduction},
		{"edge-enhancement", qs.applyEdgeEnhancement},
	}
	
	// Try each enhancement
	for _, enhancement := range enhancements {
		enhanced := enhancement.process(img)
		
		// Try multiple detection methods on enhanced image
		methods := []func(image.Image) (string, error){
			qs.scanDirect,
			qs.scanWithCV2Advanced,
			qs.scanWithBinarization,
		}
		
		for _, method := range methods {
			result, err := method(enhanced)
			if err == nil && result != "" {
				fmt.Printf("✨ QR found with %s enhancement\n", enhancement.name)
				return result, nil
			}
		}
	}
	
	return "", fmt.Errorf("no QR found with enhanced preprocessing")
}

// Image scaling utility
func (qs *QRScanner) scaleImage(img image.Image, newWidth, newHeight int) image.Image {
	bounds := img.Bounds()
	oldWidth := bounds.Dx()
	oldHeight := bounds.Dy()
	
	scaled := image.NewRGBA(image.Rect(0, 0, newWidth, newHeight))
	
	// Simple nearest neighbor scaling
	for y := 0; y < newHeight; y++ {
		for x := 0; x < newWidth; x++ {
			srcX := x * oldWidth / newWidth
			srcY := y * oldHeight / newHeight
			
			if srcX < oldWidth && srcY < oldHeight {
				color := img.At(bounds.Min.X+srcX, bounds.Min.Y+srcY)
				scaled.Set(x, y, color)
			}
		}
	}
	
	return scaled
}

// Unsharp mask for sharpening blurry images
func (qs *QRScanner) applyUnsharpMask(img image.Image) image.Image {
	bounds := img.Bounds()
	result := image.NewRGBA(bounds)
	
	// Simple unsharp mask implementation
	for y := bounds.Min.Y + 1; y < bounds.Max.Y - 1; y++ {
		for x := bounds.Min.X + 1; x < bounds.Max.X - 1; x++ {
			// Get surrounding pixels
			center := img.At(x, y)
			cr, cg, cb, ca := center.RGBA()
			
			// Calculate average of surrounding pixels (blur)
			var avgR, avgG, avgB uint32
			count := 0
			for dy := -1; dy <= 1; dy++ {
				for dx := -1; dx <= 1; dx++ {
					if dx != 0 || dy != 0 {
						r, g, b, _ := img.At(x+dx, y+dy).RGBA()
						avgR += r
						avgG += g
						avgB += b
						count++
					}
				}
			}
			avgR /= uint32(count)
			avgG /= uint32(count)
			avgB /= uint32(count)
			
			// Enhance difference from blur
			factor := 1.5
			newR := cr + uint32(factor * float64(int32(cr) - int32(avgR)))
			newG := cg + uint32(factor * float64(int32(cg) - int32(avgG)))
			newB := cb + uint32(factor * float64(int32(cb) - int32(avgB)))
			
			// Clamp values
			if newR > 65535 { newR = 65535 }
			if newG > 65535 { newG = 65535 }
			if newB > 65535 { newB = 65535 }
			
			result.Set(x, y, color.RGBA{uint8(newR >> 8), uint8(newG >> 8), uint8(newB >> 8), uint8(ca >> 8)})
		}
	}
	
	return result
}

// Gamma correction for exposure issues
func (qs *QRScanner) applyGammaCorrection(img image.Image) image.Image {
	bounds := img.Bounds()
	result := image.NewRGBA(bounds)
	
	gamma := 1.2 // Slight gamma boost
	
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			r, g, b, a := img.At(x, y).RGBA()
			
			// Apply gamma correction
			newR := uint32(65535 * math.Pow(float64(r)/65535, 1.0/gamma))
			newG := uint32(65535 * math.Pow(float64(g)/65535, 1.0/gamma))
			newB := uint32(65535 * math.Pow(float64(b)/65535, 1.0/gamma))
			
			result.Set(x, y, color.RGBA{uint8(newR >> 8), uint8(newG >> 8), uint8(newB >> 8), uint8(a >> 8)})
		}
	}
	
	return result
}

// CLAHE-like contrast enhancement
func (qs *QRScanner) applyCLAHE(img image.Image) image.Image {
	bounds := img.Bounds()
	enhanced := image.NewRGBA(bounds)
	
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			r, g, b, a := img.At(x, y).RGBA()
			// Enhance contrast
			r = enhanceContrast(r)
			g = enhanceContrast(g)
			b = enhanceContrast(b)
			enhanced.Set(x, y, color.RGBA{uint8(r >> 8), uint8(g >> 8), uint8(b >> 8), uint8(a >> 8)})
		}
	}
	
	return enhanced
}

// Noise reduction
func (qs *QRScanner) applyNoiseReduction(img image.Image) image.Image {
	bounds := img.Bounds()
	blurred := image.NewRGBA(bounds)
	
	for y := bounds.Min.Y + 1; y < bounds.Max.Y - 1; y++ {
		for x := bounds.Min.X + 1; x < bounds.Max.X - 1; x++ {
			// Simple 3x3 blur kernel
			var r, g, b, a uint32
			for dy := -1; dy <= 1; dy++ {
				for dx := -1; dx <= 1; dx++ {
					pr, pg, pb, pa := img.At(x+dx, y+dy).RGBA()
					r += pr
					g += pg
					b += pb
					a += pa
				}
			}
			r /= 9
			g /= 9
			b /= 9
			a /= 9
			blurred.Set(x, y, color.RGBA{uint8(r >> 8), uint8(g >> 8), uint8(b >> 8), uint8(a >> 8)})
		}
	}
	
	return blurred
}

// Edge enhancement 
func (qs *QRScanner) applyEdgeEnhancement(img image.Image) image.Image {
	bounds := img.Bounds()
	result := image.NewRGBA(bounds)
	
	// Simple edge enhancement using sobel-like filter
	for y := bounds.Min.Y + 1; y < bounds.Max.Y - 1; y++ {
		for x := bounds.Min.X + 1; x < bounds.Max.X - 1; x++ {
			// Get grayscale values around pixel
			var gx, gy float64
			
			// Sobel X
			gx += -1 * float64(grayValue(img.At(x-1, y-1)))
			gx += -2 * float64(grayValue(img.At(x-1, y)))
			gx += -1 * float64(grayValue(img.At(x-1, y+1)))
			gx += 1 * float64(grayValue(img.At(x+1, y-1)))
			gx += 2 * float64(grayValue(img.At(x+1, y)))
			gx += 1 * float64(grayValue(img.At(x+1, y+1)))
			
			// Sobel Y  
			gy += -1 * float64(grayValue(img.At(x-1, y-1)))
			gy += -2 * float64(grayValue(img.At(x, y-1)))
			gy += -1 * float64(grayValue(img.At(x+1, y-1)))
			gy += 1 * float64(grayValue(img.At(x-1, y+1)))
			gy += 2 * float64(grayValue(img.At(x, y+1)))
			gy += 1 * float64(grayValue(img.At(x+1, y+1)))
			
			// Calculate magnitude
			magnitude := math.Sqrt(gx*gx + gy*gy)
			edgeVal := uint8(math.Min(255, magnitude))
			
			// Combine with original
			origR, origG, origB, origA := img.At(x, y).RGBA()
			enhanceR := uint8((origR>>8) + uint32(edgeVal)/4)
			enhanceG := uint8((origG>>8) + uint32(edgeVal)/4)  
			enhanceB := uint8((origB>>8) + uint32(edgeVal)/4)
			
			result.Set(x, y, color.RGBA{enhanceR, enhanceG, enhanceB, uint8(origA >> 8)})
		}
	}
	
	return result
}

// Helper function to get grayscale value
func grayValue(c color.Color) uint8 {
	r, g, b, _ := c.RGBA()
	// Standard luminance formula
	gray := (299*r + 587*g + 114*b + 500) / 1000
	return uint8(gray >> 8)
}

// Grid-based scanning like Python version (THE KEY!)
func (qs *QRScanner) gridBasedScan(img image.Image) (string, error) {
	bounds := img.Bounds()
	width := bounds.Max.X
	height := bounds.Max.Y
	
	gridSize := 400  // 400x400 blocks like Python
	overlap := 200   // 200px overlap like Python
	
	// Try direct scan first
	result, err := qs.scanDirect(img)
	if err == nil && result != "" {
		return result, nil
	}
	
	// Grid scanning with overlap
	for y := 0; y < height-gridSize; y += (gridSize - overlap) {
		for x := 0; x < width-gridSize; x += (gridSize - overlap) {
			// Extract grid region
			maxX := x + gridSize
			maxY := y + gridSize
			if maxX > width {
				maxX = width
			}
			if maxY > height {
				maxY = height
			}
			
			// Crop region
			region := cropImage(img, x, y, maxX, maxY)
			if region != nil {
				result, err := qs.scanDirect(region)
				if err == nil && result != "" {
					fmt.Printf("✅ QR found in grid region (%d,%d)\n", x, y)
					return result, nil
				}
			}
		}
	}
	
	return "", fmt.Errorf("no QR found in grid scan")
}

// Helper function to crop image
func cropImage(src image.Image, x1, y1, x2, y2 int) image.Image {
	bounds := image.Rect(0, 0, x2-x1, y2-y1)
	dst := image.NewRGBA(bounds)
	
	for y := y1; y < y2; y++ {
		for x := x1; x < x2; x++ {
			if x >= src.Bounds().Min.X && x < src.Bounds().Max.X &&
				y >= src.Bounds().Min.Y && y < src.Bounds().Max.Y {
				dst.Set(x-x1, y-y1, src.At(x, y))
			}
		}
	}
	
	return dst
}

// Advanced preprocessing like Python (OTSU + Adaptive threshold)
func (qs *QRScanner) scanWithCV2Advanced(img image.Image) (string, error) {
	// Try OTSU threshold
	otsuImg := qs.applyOTSUThreshold(img)
	result, err := qs.scanDirect(otsuImg)
	if err == nil && result != "" {
		return result, nil
	}
	
	// Try adaptive threshold
	adaptiveImg := qs.applyAdaptiveThreshold(img)
	result, err = qs.scanDirect(adaptiveImg)
	if err == nil && result != "" {
		return result, nil
	}
	
	return "", fmt.Errorf("no QR found with advanced preprocessing")
}

// OTSU threshold implementation
func (qs *QRScanner) applyOTSUThreshold(img image.Image) image.Image {
	bounds := img.Bounds()
	gray := image.NewGray(bounds)
	
	// Convert to grayscale first
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			originalColor := img.At(x, y)
			grayColor := color.GrayModel.Convert(originalColor)
			gray.Set(x, y, grayColor)
		}
	}
	
	// Calculate histogram
	hist := make([]int, 256)
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			grayVal := gray.GrayAt(x, y).Y
			hist[grayVal]++
		}
	}
	
	// Calculate OTSU threshold
	total := bounds.Dx() * bounds.Dy()
	sum := 0
	for i := 0; i < 256; i++ {
		sum += i * hist[i]
	}
	
	sumB := 0
	wB := 0
	wF := 0
	varMax := 0.0
	threshold := 0
	
	for i := 0; i < 256; i++ {
		wB += hist[i]
		if wB == 0 {
			continue
		}
		
		wF = total - wB
		if wF == 0 {
			break
		}
		
		sumB += i * hist[i]
		mB := float64(sumB) / float64(wB)
		mF := float64(sum-sumB) / float64(wF)
		
		varBetween := float64(wB) * float64(wF) * (mB - mF) * (mB - mF)
		
		if varBetween > varMax {
			varMax = varBetween
			threshold = i
		}
	}
	
	// Apply threshold
	binary := image.NewGray(bounds)
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			grayVal := gray.GrayAt(x, y).Y
			if int(grayVal) > threshold {
				binary.Set(x, y, color.Gray{255})
			} else {
				binary.Set(x, y, color.Gray{0})
			}
		}
	}
	
	return binary
}

// Simple adaptive threshold
func (qs *QRScanner) applyAdaptiveThreshold(img image.Image) image.Image {
	bounds := img.Bounds()
	gray := image.NewGray(bounds)
	
	// Convert to grayscale
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			originalColor := img.At(x, y)
			grayColor := color.GrayModel.Convert(originalColor)
			gray.Set(x, y, grayColor)
		}
	}
	
	// Apply adaptive threshold with 11x11 window
	adaptive := image.NewGray(bounds)
	windowSize := 11
	half := windowSize / 2
	
	for y := bounds.Min.Y + half; y < bounds.Max.Y - half; y++ {
		for x := bounds.Min.X + half; x < bounds.Max.X - half; x++ {
			// Calculate local mean
			sum := 0
			count := 0
			for dy := -half; dy <= half; dy++ {
				for dx := -half; dx <= half; dx++ {
					sum += int(gray.GrayAt(x+dx, y+dy).Y)
					count++
				}
			}
			localMean := sum / count
			
			// Apply threshold with offset
			currentVal := int(gray.GrayAt(x, y).Y)
			if currentVal > localMean - 2 { // -2 is the offset like Python
				adaptive.Set(x, y, color.Gray{255})
			} else {
				adaptive.Set(x, y, color.Gray{0})
			}
		}
	}
	
	return adaptive
}

// Direct scan without preprocessing
func (qs *QRScanner) scanDirect(img image.Image) (string, error) {
	bmp, err := gozxing.NewBinaryBitmapFromImage(img)
	if err != nil {
		return "", err
	}
	
	result, err := qs.reader.Decode(bmp, nil)
	if err != nil {
		return "", err
	}
	
	return result.GetText(), nil
}

// Convert to grayscale
func (qs *QRScanner) scanWithGrayscale(img image.Image) (string, error) {
	bounds := img.Bounds()
	gray := image.NewGray(bounds)
	
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			originalColor := img.At(x, y)
			grayColor := color.GrayModel.Convert(originalColor)
			gray.Set(x, y, grayColor)
		}
	}
	
	return qs.scanDirect(gray)
}

// Enhanced contrast
func (qs *QRScanner) scanWithContrast(img image.Image) (string, error) {
	bounds := img.Bounds()
	enhanced := image.NewRGBA(bounds)
	
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			r, g, b, a := img.At(x, y).RGBA()
			// Enhance contrast
			r = enhanceContrast(r)
			g = enhanceContrast(g)
			b = enhanceContrast(b)
			enhanced.Set(x, y, color.RGBA{uint8(r >> 8), uint8(g >> 8), uint8(b >> 8), uint8(a >> 8)})
		}
	}
	
	return qs.scanDirect(enhanced)
}

// Simple blur to reduce noise
func (qs *QRScanner) scanWithBlur(img image.Image) (string, error) {
	bounds := img.Bounds()
	blurred := image.NewRGBA(bounds)
	
	for y := bounds.Min.Y + 1; y < bounds.Max.Y - 1; y++ {
		for x := bounds.Min.X + 1; x < bounds.Max.X - 1; x++ {
			// Simple 3x3 blur kernel
			var r, g, b, a uint32
			for dy := -1; dy <= 1; dy++ {
				for dx := -1; dx <= 1; dx++ {
					pr, pg, pb, pa := img.At(x+dx, y+dy).RGBA()
					r += pr
					g += pg
					b += pb
					a += pa
				}
			}
			r /= 9
			g /= 9
			b /= 9
			a /= 9
			blurred.Set(x, y, color.RGBA{uint8(r >> 8), uint8(g >> 8), uint8(b >> 8), uint8(a >> 8)})
		}
	}
	
	return qs.scanDirect(blurred)
}

// Inverted colors
func (qs *QRScanner) scanInverted(img image.Image) (string, error) {
	bounds := img.Bounds()
	inverted := image.NewRGBA(bounds)
	
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			r, g, b, a := img.At(x, y).RGBA()
			// Invert colors
			r = 65535 - r
			g = 65535 - g
			b = 65535 - b
			inverted.Set(x, y, color.RGBA{uint8(r >> 8), uint8(g >> 8), uint8(b >> 8), uint8(a >> 8)})
		}
	}
	
	return qs.scanDirect(inverted)
}

// Black and white binarization
func (qs *QRScanner) scanWithBinarization(img image.Image) (string, error) {
	bounds := img.Bounds()
	binary := image.NewGray(bounds)
	
	// Calculate average brightness
	var total uint64
	var count uint64
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			r, g, b, _ := img.At(x, y).RGBA()
			brightness := (r + g + b) / 3
			total += uint64(brightness)
			count++
		}
	}
	threshold := uint32(total / count)
	
	// Apply threshold
	for y := bounds.Min.Y; y < bounds.Max.Y; y++ {
		for x := bounds.Min.X; x < bounds.Max.X; x++ {
			r, g, b, _ := img.At(x, y).RGBA()
			brightness := (r + g + b) / 3
			if brightness > threshold {
				binary.Set(x, y, color.Gray{255})
			} else {
				binary.Set(x, y, color.Gray{0})
			}
		}
	}
	
	return qs.scanDirect(binary)
}

// Helper function for contrast enhancement
func enhanceContrast(value uint32) uint32 {
	// Simple contrast enhancement
	value = value >> 8 // Convert from 16-bit to 8-bit
	if value < 128 {
		value = value * value / 128
	} else {
		value = 255 - ((255-value)*(255-value))/128
	}
	return value << 8 // Convert back to 16-bit
}

func (qr *QRReader) onReady() {
	// Set icon - simple black square for now
	icon := make([]byte, 16*16*4) // RGBA
	for i := 0; i < len(icon); i += 4 {
		icon[i] = 0     // R
		icon[i+1] = 0   // G  
		icon[i+2] = 0   // B
		icon[i+3] = 255 // A
	}
	
	systray.SetIcon(icon)
	systray.SetTitle("QR")
	systray.SetTooltip("QR Reader Pro - Q+R to scan")

	// Menu items
	mScan := systray.AddMenuItem("🔍 Scan Now (Q+R)", "Scan screen for QR codes")
	systray.AddSeparator()
	mStatus := systray.AddMenuItem("ℹ️ Status", "Show status")
	systray.AddSeparator() 
	mQuit := systray.AddMenuItem("❌ Quit", "Quit QR Reader Pro")

	// Handle menu clicks
	go func() {
		for {
			select {
			case <-mScan.ClickedCh:
				qr.performScan()
			case <-mStatus.ClickedCh:
				qr.showStatus()
			case <-mQuit.ClickedCh:
				systray.Quit()
				return
			}
		}
	}()

	// Start hotkey listener
	go qr.startHotkeyListener()

	fmt.Println("✅ QR Reader Pro ready!")
	fmt.Println("📱 Q+R: Scan QR codes")
	fmt.Println("📱 Menu bar icon: Manual scan")
}

func (qr *QRReader) performScan() {
	fmt.Println("🔍 Taking screenshot...")
	
	result, err := qr.scanner.ScanScreen()
	if err != nil {
		fmt.Printf("❌ Scan failed: %v\n", err)
		qr.showNotification("Scan Failed", "Could not capture screen or find QR code")
		return
	}

	fmt.Printf("✅ Result: %s\n", result)
	
	// Copy to clipboard
	err = clipboard.WriteAll(result)
	if err != nil {
		fmt.Printf("⚠️ Clipboard error: %v\n", err)
	}

	// Show result
	qr.showResult(result)
}

func (qr *QRReader) showResult(text string) {
	// Copy to clipboard first
	clipboard.WriteAll(text)
	
	// Show beautiful Apple-style dialog
	qr.showAppleDialog(text)
	
	fmt.Printf("✅ QR Found: %s\n", text)
}

func (qr *QRReader) showAppleDialog(text string) {
	// Escape text for AppleScript
	escapedText := fmt.Sprintf("%q", text)
	
	// Create beautiful Apple-style dialog
	script := fmt.Sprintf(`
	tell application "System Events"
		activate
		display dialog %s with title "QR Reader Pro" buttons {"Copy Again", "Open Link", "OK"} default button "OK" with icon note giving up after 30
		set buttonPressed to button returned of result
		
		if buttonPressed = "Copy Again" then
			set the clipboard to %s
			display notification "Copied to clipboard" with title "QR Reader Pro"
		else if buttonPressed = "Open Link" then
			if %s starts with "http" then
				open location %s
			else
				display notification "Not a valid URL" with title "QR Reader Pro"
			end if
		end if
	end tell
	`, escapedText, escapedText, escapedText, escapedText)
	
	// Execute AppleScript
	cmd := exec.Command("osascript", "-e", script)
	go func() {
		err := cmd.Run()
		if err != nil {
			fmt.Printf("Dialog error: %v\n", err)
		}
	}()
}

func (qr *QRReader) showStatus() {
	status := "QR Reader Pro v1.0\n\nEngine: ZXing\nPlatform: macOS\n\nReady to scan!"
	qr.showNotification("Status", status)
	fmt.Println("📊 Status: Ready")
}

func (qr *QRReader) showNotification(title, message string) {
	// macOS notification
	cmd := exec.Command("osascript", "-e", 
		fmt.Sprintf(`display notification "%s" with title "%s"`, message, title))
	cmd.Run()
	
	fmt.Printf("📢 %s: %s\n", title, message)
}

func (qr *QRReader) startHotkeyListener() {
	fmt.Println("🎹 Setting up Q+R hotkey...")
	
	qPressed := false
	
	// Register key events
	hook.Register(hook.KeyDown, []string{"q"}, func(e hook.Event) {
		qPressed = true
	})
	
	hook.Register(hook.KeyUp, []string{"q"}, func(e hook.Event) {
		qPressed = false
	})
	
	hook.Register(hook.KeyDown, []string{"r"}, func(e hook.Event) {
		if qPressed {
			fmt.Println("🔥 Q+R triggered!")
			qr.performScan()
		}
	})
	
	// Start hook
	s := hook.Start()
	<-hook.Process(s)
}

func (qr *QRReader) onExit() {
	fmt.Println("👋 QR Reader Pro shutting down")
	hook.End()
}

func main() {
	fmt.Println("🚀 QR Reader Pro starting...")
	
	// Initialize QR scanner
	scanner := NewQRScanner()
	
	// Create app
	qrApp := &QRReader{
		scanner: scanner,
	}
	
	// Run system tray
	systray.Run(qrApp.onReady, qrApp.onExit)
}