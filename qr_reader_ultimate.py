# qr_reader_ultimate.py - qreader ile en güçlü versiyon
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

# QR okuma kütüphaneleri
try:
    from qreader import QReader
    qreader_available = True
    qreader_instance = QReader()
except:
    qreader_available = False
    print("qreader yüklü değil, pyzbar kullanılacak")

from pyzbar import pyzbar

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
            pystray.MenuItem("Hakkında", self.show_about),
            pystray.MenuItem("Çıkış", self.quit_app)
        )
        
        self.icon = pystray.Icon("QR Reader", image, menu=menu)
        
    def show_about(self, icon, item):
        about_text = "QR Reader Ultimate\n\n"
        if qreader_available:
            about_text += "✓ qreader (YOLOv8) - Aktif\n"
        else:
            about_text += "✗ qreader - Yüklü değil\n"
        about_text += "✓ pyzbar - Aktif\n"
        about_text += "✓ OpenCV - Aktif\n\n"
        about_text += "En iyi performans için:\npip install qreader"
        
        messagebox.showinfo("Hakkında", about_text)
        
    def start_selection(self, icon=None, item=None):
        if self.selecting:
            return
            
        self.selecting = True
        
        # Seçim penceresi
        self.selection_window = tk.Tk()
        self.selection_window.attributes('-fullscreen', True)
        self.selection_window.attributes('-alpha', 0.2)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.configure(background='black')
        
        # Canvas oluştur
        self.canvas = tk.Canvas(self.selection_window, highlightthickness=0, bg='black')
        self.canvas.pack(fill='both', expand=True)
        
        # Rehber çizgileri
        screen_width = self.selection_window.winfo_screenwidth()
        screen_height = self.selection_window.winfo_screenheight()
        
        # Ortada büyük QR rehberi
        center_x = screen_width // 2
        center_y = screen_height // 2
        guide_size = 300
        
        # QR kare rehberi
        self.canvas.create_rectangle(
            center_x - guide_size//2, center_y - guide_size//2,
            center_x + guide_size//2, center_y + guide_size//2,
            outline='#00ff00', width=2, dash=(5, 5)
        )
        
        # İpucu metni
        self.canvas.create_text(
            center_x, center_y - guide_size//2 - 30,
            text="QR KODU BU ALANA SIĞDIRIN",
            font=('Arial', 20, 'bold'),
            fill='#00ff00'
        )
        
        self.canvas.create_text(
            center_x, center_y + guide_size//2 + 30,
            text="Tıklayın ve sürükleyin veya ESC ile çıkın",
            font=('Arial', 14),
            fill='white'
        )
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
        def on_mouse_down(event):
            self.start_x = self.selection_window.winfo_pointerx()
            self.start_y = self.selection_window.winfo_pointery()
            
        def on_mouse_move(event):
            if self.start_x is not None:
                if self.rect:
                    self.canvas.delete(self.rect)
                
                current_x = self.selection_window.winfo_pointerx()
                current_y = self.selection_window.winfo_pointery()
                
                x1 = min(self.start_x, current_x) - self.selection_window.winfo_rootx()
                y1 = min(self.start_y, current_y) - self.selection_window.winfo_rooty()
                x2 = max(self.start_x, current_x) - self.selection_window.winfo_rootx()
                y2 = max(self.start_y, current_y) - self.selection_window.winfo_rooty()
                
                self.rect = self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline='#ff0000', width=3, fill='white', stipple='gray25'
                )
            
        def on_mouse_up(event):
            if self.start_x is None:
                self.selection_window.destroy()
                self.selecting = False
                return
                
            end_x = self.selection_window.winfo_pointerx()
            end_y = self.selection_window.winfo_pointery()
            
            # Seçim alanını hesapla ve genişlet
            padding = 30  # Daha fazla kenar boşluğu
            x1 = min(self.start_x, end_x) - padding
            y1 = min(self.start_y, end_y) - padding
            x2 = max(self.start_x, end_x) + padding
            y2 = max(self.start_y, end_y) + padding
            
            # Ekran sınırları
            x1 = max(0, x1)
            y1 = max(0, y1)
            
            self.selection_window.destroy()
            self.selecting = False
            
            if abs(x2 - x1) > 30 and abs(y2 - y1) > 30:
                # Biraz bekle (ekranın temizlenmesi için)
                self.selection_window.after(100, lambda: self.capture_and_process(x1, y1, x2, y2))
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
        
    def capture_and_process(self, x1, y1, x2, y2):
        """Ekran görüntüsü al ve işle"""
        try:
            screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            
            # İşleme başla
            result = self.ultimate_qr_process(screenshot)
            
            if result:
                self.show_popup(result)
            else:
                # Daha büyük alan ile tekrar dene
                x1 -= 50
                y1 -= 50
                x2 += 50
                y2 += 50
                x1 = max(0, x1)
                y1 = max(0, y1)
                
                screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                result = self.ultimate_qr_process(screenshot)
                
                if result:
                    self.show_popup(result)
                else:
                    messagebox.showwarning(
                        "QR Kod Bulunamadı",
                        "QR kod okunamadı!\n\n"
                        "Çözüm önerileri:\n"
                        "1. QR kodun TAMAMINI seçin\n"
                        "2. Ekranı YAKLAŞTIRIN (Ctrl++)\n"
                        "3. Ekran parlaklığını artırın\n"
                        "4. QR kod çevresinde boşluk bırakın\n\n"
                        "En iyi sonuç için:\n"
                        "pip install qreader"
                    )
        except Exception as e:
            messagebox.showerror("Hata", f"İşlem hatası: {str(e)}")
    
    def ultimate_qr_process(self, image):
        """Tüm QR okuma yöntemlerini dene"""
        img_array = np.array(image)
        
        # 1. qreader ile dene (en güçlü)
        if qreader_available:
            try:
                # RGB formatında direkt dene
                decoded = qreader_instance.detect_and_decode(image=img_array)
                if decoded and decoded[0]:
                    return decoded[0]
                    
                # Farklı boyutlarda dene
                for scale in [1.5, 2.0, 0.8]:
                    new_size = (int(image.width * scale), int(image.height * scale))
                    resized = image.resize(new_size, Image.Resampling.LANCZOS)
                    decoded = qreader_instance.detect_and_decode(image=np.array(resized))
                    if decoded and decoded[0]:
                        return decoded[0]
            except Exception as e:
                print(f"qreader hatası: {e}")
        
        # 2. OpenCV QR dedektörü
        try:
            qr_detector = cv2.QRCodeDetector()
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            data, points, _ = qr_detector.detectAndDecode(gray)
            if data:
                return data
        except:
            pass
        
        # 3. pyzbar ile gelişmiş algılama
        return self.enhanced_pyzbar_detection(img_array)
    
    def enhanced_pyzbar_detection(self, img_array):
        """Gelişmiş pyzbar algılama"""
        methods = [
            # Orijinal
            lambda img: cv2.cvtColor(img, cv2.COLOR_RGB2GRAY),
            
            # Otsu threshold
            lambda img: cv2.threshold(
                cv2.cvtColor(img, cv2.COLOR_RGB2GRAY),
                0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )[1],
            
            # Adaptive threshold
            lambda img: cv2.adaptiveThreshold(
                cv2.cvtColor(img, cv2.COLOR_RGB2GRAY),
                255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            ),
            
            # CLAHE
            lambda img: cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8)).apply(
                cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            ),
            
            # Sharpen
            lambda img: cv2.filter2D(
                cv2.cvtColor(img, cv2.COLOR_RGB2GRAY),
                -1,
                np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            ),
        ]
        
        for method in methods:
            try:
                processed = method(img_array)
                qr_codes = pyzbar.decode(processed)
                if qr_codes:
                    return qr_codes[0].data.decode('utf-8', errors='ignore')
            except:
                continue
        
        return None
    
    def show_popup(self, text):
        # Pop-up pencere
        popup = tk.Tk()
        popup.title("📱 QR Kod İçeriği")
        popup.geometry("500x350")
        popup.attributes('-topmost', True)
        
        # Ortala
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - 250
        y = (popup.winfo_screenheight() // 2) - 175
        popup.geometry(f'+{x}+{y}')
        
        # Ana frame
        main_frame = tk.Frame(popup, bg='white', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Başlık
        title_label = tk.Label(main_frame, text="Metin QR Kodu", 
                             font=('Arial', 16, 'bold'), bg='white')
        title_label.pack(pady=(0, 5))
        
        # Başarı işareti
        success_label = tk.Label(main_frame, text="✅ Başarıyla okundu", 
                               font=('Arial', 10), bg='white', fg='green')
        success_label.pack(pady=(0, 10))
        
        # Metin alanı
        text_frame = tk.Frame(main_frame, bg='#f0f0f0', relief='solid', borderwidth=1)
        text_frame.pack(fill='both', expand=True, pady=(5, 15))
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 11),
                            bg='#f9f9f9', relief='flat', padx=10, pady=10)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', text)
        text_widget.config(state='disabled')
        
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
            popup.after(1000, popup.destroy)
            
        copy_btn = tk.Button(button_frame, text="📋 Kopyala", command=copy_text,
                           bg='#2196F3', fg='white', font=('Arial', 12, 'bold'),
                           padx=30, pady=10, relief='flat', cursor='hand2')
        copy_btn.pack(pady=10)
        
        # Enter ile kopyala
        popup.bind('<Return>', lambda e: copy_text())
        popup.bind('<Escape>', lambda e: popup.destroy())
        
        # Focus
        popup.focus_force()
        
        popup.mainloop()
        
    def quit_app(self, icon, item):
        self.icon.stop()
        sys.exit()
        
    def run(self):
        self.create_icon()
        
        # Icon thread
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        
        # Global hotkey
        keyboard.add_hotkey('win+q', self.start_selection)
        
        print("QR Reader Ultimate başlatıldı!")
        print("Win+Q ile QR okuma yapabilirsiniz.")
        if not qreader_available:
            print("\n⚠️  Daha iyi performans için: pip install qreader")
        
        # Bekle
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            self.icon.stop()
            sys.exit()

if __name__ == "__main__":
    app = QRReaderTray()
    app.run()