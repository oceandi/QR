# qr_reader_opencv.py - OpenCV'nin QR dedektörü ile alternatif versiyon
import pystray
from PIL import Image, ImageGrab, ImageDraw
import cv2
import numpy as np
import pyperclip
import tkinter as tk
from tkinter import messagebox
import keyboard
import threading
import sys

class QRReaderTray:
    def __init__(self):
        self.icon = None
        self.selecting = False
        self.selection_window = None
        
        # OpenCV QR dedektörü
        self.qr_detector = cv2.QRCodeDetector()
        
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
        
        # İpucu metni
        hint_text = self.canvas.create_text(
            self.selection_window.winfo_screenwidth() // 2,
            50,
            text="QR kodun etrafını seçin ve bırakın",
            font=('Arial', 16, 'bold'),
            fill='white'
        )
        
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
                                                       outline='#00ff00', width=3)
            
        def on_mouse_up(event):
            if self.start_x is None:
                self.selection_window.destroy()
                self.selecting = False
                return
                
            # Ekran koordinatlarını al
            end_x = self.selection_window.winfo_pointerx()
            end_y = self.selection_window.winfo_pointery()
            
            # Seçim alanını hesapla (biraz genişlet)
            margin = 20  # Kenar boşluğu
            x1 = min(self.start_x, end_x) - margin
            y1 = min(self.start_y, end_y) - margin
            x2 = max(self.start_x, end_x) + margin
            y2 = max(self.start_y, end_y) + margin
            
            # Ekran sınırlarını kontrol et
            x1 = max(0, x1)
            y1 = max(0, y1)
            
            # Pencereyi kapat
            self.selection_window.destroy()
            self.selecting = False
            
            # En az 50x50 piksel seçim yapılmış mı kontrol et
            if abs(x2 - x1) > 50 and abs(y2 - y1) > 50:
                try:
                    # Ekran görüntüsü al
                    screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                    self.process_qr_opencv(screenshot)
                except Exception as e:
                    messagebox.showerror("Hata", f"Ekran görüntüsü alınamadı: {str(e)}")
            else:
                messagebox.showwarning("Uyarı", "Lütfen QR kodun etrafında daha büyük bir alan seçin!")
        
        def on_escape(event):
            self.selection_window.destroy()
            self.selecting = False
            
        self.selection_window.bind("<Button-1>", on_mouse_down)
        self.selection_window.bind("<B1-Motion>", on_mouse_move)
        self.selection_window.bind("<ButtonRelease-1>", on_mouse_up)
        self.selection_window.bind("<Escape>", on_escape)
        
        self.selection_window.mainloop()
        
    def process_qr_opencv(self, image):
        """OpenCV QR dedektörü ile işle"""
        try:
            # PIL'den numpy array'e çevir
            img_array = np.array(image)
            
            # BGR'ye çevir (OpenCV formatı)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            # Direkt decode dene
            data, points, _ = self.qr_detector.detectAndDecode(img_bgr)
            
            if data:
                self.show_popup(data)
                return
            
            # Gri tonlama ile dene
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            data, points, _ = self.qr_detector.detectAndDecode(gray)
            
            if data:
                self.show_popup(data)
                return
            
            # Görüntü iyileştirmeleri ile dene
            enhanced_results = self.try_enhanced_detection(img_bgr)
            
            if enhanced_results:
                self.show_popup(enhanced_results)
            else:
                # pyzbar ile son deneme
                self.fallback_pyzbar_detection(img_array)
                
        except Exception as e:
            messagebox.showerror("Hata", f"QR kod işlenirken hata: {str(e)}")
    
    def try_enhanced_detection(self, img):
        """Gelişmiş algılama teknikleri"""
        # 1. Keskinleştirme
        kernel = np.array([[-1,-1,-1],
                          [-1, 9,-1],
                          [-1,-1,-1]])
        sharpened = cv2.filter2D(img, -1, kernel)
        data, _, _ = self.qr_detector.detectAndDecode(sharpened)
        if data:
            return data
        
        # 2. Histogram eşitleme
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        equalized = cv2.equalizeHist(gray)
        data, _, _ = self.qr_detector.detectAndDecode(equalized)
        if data:
            return data
        
        # 3. Büyütme
        scaled = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        data, _, _ = self.qr_detector.detectAndDecode(scaled)
        if data:
            return data
        
        # 4. Otsu threshold
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        data, _, _ = self.qr_detector.detectAndDecode(binary)
        if data:
            return data
        
        return None
    
    def fallback_pyzbar_detection(self, img_array):
        """pyzbar ile yedek algılama"""
        try:
            from pyzbar import pyzbar
            
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            
            # Farklı threshold değerleri dene
            for thresh_val in [100, 127, 150, 180, 200]:
                _, binary = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
                qr_codes = pyzbar.decode(binary)
                if qr_codes:
                    data = qr_codes[0].data.decode('utf-8', errors='ignore')
                    self.show_popup(data)
                    return
            
            messagebox.showwarning("QR Bulunamadı", 
                                 "QR kod okunamadı!\n\n"
                                 "Öneriler:\n"
                                 "• QR kodun TAMAMI görünecek şekilde seçin\n"
                                 "• Biraz daha geniş alan seçin\n"
                                 "• Ekranı yakınlaştırın (Ctrl + +)\n"
                                 "• Daha net/kontrast bir görüntü deneyin")
                                 
        except ImportError:
            messagebox.showwarning("QR Bulunamadı", "QR kod okunamadı!")
            
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