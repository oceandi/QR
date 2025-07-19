import pystray
from PIL import Image, ImageGrab, ImageDraw, ImageEnhance
import cv2
import numpy as np
from pyzbar import pyzbar
import pyperclip
import tkinter as tk
from tkinter import messagebox
import keyboard
import threading
import sys
import time

# QR okuma için ek kütüphaneler
try:
    import qrcode
    from pyzbar.pyzbar import ZBarSymbol
    ENHANCED_QR = True
except:
    ENHANCED_QR = False

class QRReaderTray:
    def __init__(self):
        self.icon = None
        self.selecting = False
        self.selection_window = None
        
    def create_icon(self):
        # QR kod şeklinde icon oluştur
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        
        # Basit QR kod görünümü
        for i in range(0, 64, 8):
            for j in range(0, 64, 8):
                if (i + j) % 16 == 0:
                    draw.rectangle([i, j, i+6, j+6], fill='black')
        
        menu = pystray.Menu(
            pystray.MenuItem("QR Oku (Win+Q)", self.start_selection),
            pystray.MenuItem("Çıkış", self.quit_app)
        )
        
        self.icon = pystray.Icon("QR Reader", image, menu=menu)
        
    def start_selection(self, icon=None, item=None):
        if self.selecting:
            return
            
        self.selecting = True
        
        # Seçim penceresi
        self.selection_window = tk.Tk()
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-alpha', 0.3)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.configure(background='gray')
        
        # Canvas oluştur
        self.canvas = tk.Canvas(self.selection_window, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        def on_mouse_down(event):
            # Ekran koordinatlarını al
            self.start_x = self.selection_window.winfo_pointerx()
            self.start_y = self.selection_window.winfo_pointery()
            
        def on_mouse_move(event):
            if self.start_x is not None:
                # Mevcut rect'i sil
                if self.rect:
                    self.canvas.delete(self.rect)
                
                # Yeni rect çiz
                current_x = self.selection_window.winfo_pointerx()
                current_y = self.selection_window.winfo_pointery()
                
                x1 = min(self.start_x, current_x) - self.selection_window.winfo_rootx()
                y1 = min(self.start_y, current_y) - self.selection_window.winfo_rooty()
                x2 = max(self.start_x, current_x) - self.selection_window.winfo_rootx()
                y2 = max(self.start_y, current_y) - self.selection_window.winfo_rooty()
                
                self.rect = self.canvas.create_rectangle(x1, y1, x2, y2, 
                                                       outline='red', width=2)
            
        def on_mouse_up(event):
            if self.start_x is None:
                self.selection_window.destroy()
                self.selecting = False
                return
                
            # Ekran koordinatlarını al
            end_x = self.selection_window.winfo_pointerx()
            end_y = self.selection_window.winfo_pointery()
            
            # Seçim alanını hesapla
            x1 = min(self.start_x, end_x)
            y1 = min(self.start_y, end_y)
            x2 = max(self.start_x, end_x)
            y2 = max(self.start_y, end_y)
            
            # Pencereyi kapat
            self.selection_window.destroy()
            self.selecting = False
            
            # En az 10x10 piksel seçim yapılmış mı kontrol et
            if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
                try:
                    # Ekran görüntüsü al
                    screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                    
                    # Progress popup göster
                    self.show_progress_popup(screenshot)
                    
                except Exception as e:
                    messagebox.showerror("Hata", f"Ekran görüntüsü alınamadı: {str(e)}")
            else:
                messagebox.showwarning("Uyarı", "Lütfen daha büyük bir alan seçin!")
        
        def on_escape(event):
            self.selection_window.destroy()
            self.selecting = False
            
        self.selection_window.bind("<Button-1>", on_mouse_down)
        self.selection_window.bind("<B1-Motion>", on_mouse_move)
        self.selection_window.bind("<ButtonRelease-1>", on_mouse_up)
        self.selection_window.bind("<Escape>", on_escape)
        
        self.selection_window.mainloop()
        
    def show_progress_popup(self, screenshot):
        """QR okuma sırasında progress göster"""
        progress_window = tk.Tk()
        progress_window.title("QR Kod Okunuyor...")
        progress_window.geometry("300x100")
        progress_window.attributes('-topmost', True)
        
        # Ortala
        progress_window.update_idletasks()
        x = (progress_window.winfo_screenwidth() // 2) - 150
        y = (progress_window.winfo_screenheight() // 2) - 50
        progress_window.geometry(f'+{x}+{y}')
        
        label = tk.Label(progress_window, text="QR kod aranıyor...", font=('Arial', 12))
        label.pack(pady=20)
        
        progress_bar = tk.Canvas(progress_window, width=250, height=20, bg='white', highlightthickness=1)
        progress_bar.pack()
        
        # Thread'de QR okuma işlemi
        result = {'data': None}
        
        def process_in_thread():
            result['data'] = self.enhanced_qr_process(screenshot)
        
        thread = threading.Thread(target=process_in_thread)
        thread.start()
        
        # Progress animasyonu
        progress = 0
        while thread.is_alive() and progress < 250:
            progress += 5
            progress_bar.create_rectangle(0, 0, progress, 20, fill='#2196F3', outline='')
            progress_window.update()
            time.sleep(0.05)
        
        progress_window.destroy()
        
        # Sonucu göster
        if result['data']:
            self.show_popup(result['data'])
        else:
            messagebox.showwarning("QR Bulunamadı", 
                                 "Seçilen alanda QR kod bulunamadı!\n\n"
                                 "İpuçları:\n"
                                 "• QR kodun tamamını ve biraz kenar boşluğu ile seçin\n"
                                 "• Ekranı yakınlaştırın (Ctrl++)\n"
                                 "• QR kodun net görünmesini sağlayın")
    
    def enhanced_qr_process(self, image):
        """Gelişmiş QR kod okuma algoritması"""
        try:
            # Orijinal görüntüyü numpy array'e çevir
            img_array = np.array(image)
            
            # Farklı preprocessing teknikleri dene
            preprocessing_methods = [
                # 1. Orijinal
                lambda img: cv2.cvtColor(img, cv2.COLOR_RGB2GRAY),
                
                # 2. Yüksek kontrast
                lambda img: self.apply_high_contrast(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)),
                
                # 3. Adaptive threshold
                lambda img: cv2.adaptiveThreshold(
                    cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), 255,
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                ),
                
                # 4. Otsu threshold
                lambda img: cv2.threshold(
                    cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), 0, 255,
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )[1],
                
                # 5. Morfolojik işlemler
                lambda img: self.apply_morphology(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)),
                
                # 6. Gaussian blur + threshold
                lambda img: cv2.threshold(
                    cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), (5, 5), 0),
                    0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )[1],
                
                # 7. Büyütme ve küçültme kombinasyonu
                lambda img: self.multi_scale_process(img),
            ]
            
            # Her preprocessing metodunu dene
            for i, preprocess in enumerate(preprocessing_methods):
                try:
                    processed = preprocess(img_array)
                    
                    # pyzbar ile decode et
                    if ENHANCED_QR:
                        # Sadece QR kodları ara
                        qr_codes = pyzbar.decode(processed, symbols=[ZBarSymbol.QRCODE])
                    else:
                        qr_codes = pyzbar.decode(processed)
                    
                    if qr_codes:
                        return qr_codes[0].data.decode('utf-8', errors='ignore')
                        
                except Exception as e:
                    continue
            
            # Son çare: görüntüyü büyüt ve tekrar dene
            enlarged = cv2.resize(img_array, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            gray_enlarged = cv2.cvtColor(enlarged, cv2.COLOR_RGB2GRAY)
            qr_codes = pyzbar.decode(gray_enlarged)
            
            if qr_codes:
                return qr_codes[0].data.decode('utf-8', errors='ignore')
                
            return None
            
        except Exception as e:
            print(f"QR işleme hatası: {str(e)}")
            return None
    
    def apply_high_contrast(self, gray):
        """Yüksek kontrast uygula"""
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        return clahe.apply(gray)
    
    def apply_morphology(self, gray):
        """Morfolojik işlemler uygula"""
        # Gürültü temizleme
        kernel = np.ones((3,3), np.uint8)
        morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
        return morph
    
    def multi_scale_process(self, img):
        """Farklı ölçeklerde işle"""
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        
        # Büyütme
        scale_up = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        _, binary = cv2.threshold(scale_up, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Orijinal boyuta geri getir
        return cv2.resize(binary, (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_AREA)
            
    def show_popup(self, text):
        # Pop-up pencere
        popup = tk.Tk()
        popup.title("📱 QR Kod İçeriği")
        popup.geometry("500x300")
        popup.attributes('-topmost', True)
        
        # Pencereyi ortala
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
        y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
        popup.geometry(f'+{x}+{y}')
        
        # Ana frame
        main_frame = tk.Frame(popup, bg='white', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Başlık
        title_label = tk.Label(main_frame, text="Metin QR Kodu", 
                             font=('Arial', 14, 'bold'), bg='white')
        title_label.pack(pady=(0, 10))
        
        # Alt başlık
        subtitle_label = tk.Label(main_frame, text="İçerik:", 
                                font=('Arial', 10), bg='white', fg='gray')
        subtitle_label.pack(anchor='w')
        
        # Metin alanı
        text_frame = tk.Frame(main_frame, bg='#f0f0f0', relief='solid', borderwidth=1)
        text_frame.pack(fill='both', expand=True, pady=(5, 15))
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10),
                            bg='#f9f9f9', relief='flat', padx=10, pady=10)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', text)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(text_widget)
        scrollbar.pack(side='right', fill='y')
        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)
        
        # Butonlar
        button_frame = tk.Frame(main_frame, bg='white')
        button_frame.pack(fill='x')
        
        def copy_text():
            pyperclip.copy(text)
            copy_btn.config(text="✓ Kopyalandı!", bg='#4CAF50')
            popup.after(1500, popup.destroy)
            
        copy_btn = tk.Button(button_frame, text="📋 Kopyala", command=copy_text,
                           bg='#2196F3', fg='white', font=('Arial', 11, 'bold'),
                           padx=20, pady=8, relief='flat', cursor='hand2')
        copy_btn.pack(side='left', padx=(0, 10))
        
        close_btn = tk.Button(button_frame, text="Kapat", command=popup.destroy,
                            bg='#f0f0f0', font=('Arial', 11), padx=20, pady=8,
                            relief='flat', cursor='hand2')
        close_btn.pack(side='left')
        
        # Enter tuşu ile kopyala
        popup.bind('<Return>', lambda e: copy_text())
        popup.bind('<Escape>', lambda e: popup.destroy())
        
        # Metin seçilebilir yap ama düzenlenemez
        text_widget.config(state='normal')
        text_widget.bind("<Key>", lambda e: "break")
        
        popup.mainloop()
        
    def quit_app(self, icon, item):
        self.icon.stop()
        sys.exit()
        
    def run(self):
        self.create_icon()
        
        # Ana thread'de icon'u başlat
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        
        # Global hotkey'i kaydet
        keyboard.add_hotkey('win+q', self.start_selection)
        
        # Program kapatılana kadar bekle
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            self.icon.stop()
            sys.exit()

if __name__ == "__main__":
    app = QRReaderTray()
    app.run()