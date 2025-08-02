import pystray
from PIL import Image, ImageGrab, ImageDraw, ImageEnhance
import cv2
import numpy as np
import pyperclip
import tkinter as tk
from tkinter import messagebox
import keyboard
import threading
import sys
import time
import mss
import win32gui
import win32con

# QR okuma kütüphaneleri - HEPSİNİ KULLAN
try:
    from qreader import QReader
    qreader_instance = QReader()
    QREADER = True
except:
    QREADER = False

try:
    from pyzbar import pyzbar
    PYZBAR = True
except:
    PYZBAR = False

try:
    import easyocr
    ocr_reader = easyocr.Reader(['en'])
    EASYOCR = True
except:
    EASYOCR = False
    print("EasyOCR yüklü değil - pip install easyocr")

class QRReaderPro:
    def __init__(self):
        self.icon = None
        self.whatsapp_monitor_active = False
        self.last_qr_data = None
        
    def create_icon(self):
        # Icon oluştur
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        
        # QR pattern
        for i in range(0, 64, 8):
            for j in range(0, 64, 8):
                if (i + j) % 16 == 0:
                    draw.rectangle([i, j, i+6, j+6], fill='black')
        
        menu = pystray.Menu(
            pystray.MenuItem("✋ Manuel QR Oku (Win+Z)", self.manual_capture),
            pystray.MenuItem("📱 WhatsApp İzle", self.toggle_whatsapp_monitor, checked=lambda item: self.whatsapp_monitor_active),
            pystray.MenuItem("ℹ️ Durum", self.show_status),
            pystray.MenuItem("❌ Çıkış", self.quit_app)
        )
        
        self.icon = pystray.Icon("QR Pro", image, menu=menu)
        
    def show_status(self, icon, item):
        status = "QR Reader Pro - Durum\n\n"
        status += f"✓ qreader: {'Aktif' if QREADER else 'Yok'}\n"
        status += f"✓ pyzbar: {'Aktif' if PYZBAR else 'Yok'}\n"
        status += f"✓ easyocr: {'Aktif' if EASYOCR else 'Yok'}\n"
        status += f"✓ WhatsApp İzleme: {'Aktif' if self.whatsapp_monitor_active else 'Kapalı'}\n\n"
        status += "Kısayollar:\n"
        status += "Win+Z: Manuel QR okuma\n"
        status += "Win+X: WhatsApp'tan otomatik oku"
        
        messagebox.showinfo("Durum", status)
        
    def toggle_whatsapp_monitor(self, icon, item):
        self.whatsapp_monitor_active = not self.whatsapp_monitor_active
        if self.whatsapp_monitor_active:
            threading.Thread(target=self.monitor_whatsapp, daemon=True).start()
            self.show_notification("WhatsApp izleme başladı")
        else:
            self.show_notification("WhatsApp izleme durduruldu")
            
    def show_notification(self, message):
        """Bildirim göster"""
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            messagebox.showinfo("QR Reader", message)
            root.destroy()
        except:
            pass
            
    def monitor_whatsapp(self):
        """WhatsApp Web'i izle ve QR algıla"""
        with mss.mss() as sct:
            while self.whatsapp_monitor_active:
                try:
                    # WhatsApp penceresi bul
                    whatsapp_window = self.find_window("WhatsApp")
                    if whatsapp_window:
                        # Pencere koordinatlarını al
                        rect = win32gui.GetWindowRect(whatsapp_window)
                        monitor = {"top": rect[1], "left": rect[0], 
                                 "width": rect[2] - rect[0], "height": rect[3] - rect[1]}
                        
                        # Ekran görüntüsü al
                        screenshot = sct.grab(monitor)
                        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                        
                        # QR ara
                        result = self.ultimate_qr_scan(img)
                        
                        if result and result != self.last_qr_data:
                            self.last_qr_data = result
                            self.show_popup(result)
                            
                except Exception as e:
                    print(f"WhatsApp monitor hatası: {e}")
                    
                time.sleep(2)  # 2 saniyede bir kontrol et
                
    def find_window(self, title):
        """Pencere bul"""
        def callback(hwnd, windows):
            if title.lower() in win32gui.GetWindowText(hwnd).lower():
                windows.append(hwnd)
            return True
            
        windows = []
        win32gui.EnumWindows(callback, windows)
        return windows[0] if windows else None
        
    def manual_capture(self, icon=None, item=None):
        """Manuel QR okuma - geliştirilmiş"""
        # Küçük bir bekleme (menü kapansın)
        time.sleep(0.1)
        
        # Tüm ekran görüntüsü al
        with mss.mss() as sct:
            monitor = sct.monitors[0]  # Tüm ekran
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
        # QR ara - TÜM EKRANDA
        result = self.full_screen_qr_scan(img)
        
        if result:
            self.show_popup(result)
        else:
            # Alan seçimi başlat
            self.start_area_selection()
            
    def full_screen_qr_scan(self, image):
        """Tüm ekranda QR ara"""
        # Önce direkt dene
        result = self.ultimate_qr_scan(image)
        if result:
            return result
            
        # Grid bazlı tarama
        width, height = image.size
        grid_size = 400  # 400x400 piksel bloklar halinde tara
        
        for y in range(0, height - grid_size + 1, 200):  # 200 piksel overlap
            for x in range(0, width - grid_size + 1, 200):
                # Bölgeyi kes
                region = image.crop((x, y, x + grid_size, y + grid_size))
                result = self.ultimate_qr_scan(region)
                if result:
                    return result
                    
        return None
        
    def start_area_selection(self):
        """Alan seçimi başlat"""
        selection_window = tk.Tk()
        selection_window.attributes('-fullscreen', True)
        selection_window.attributes('-alpha', 0.3)
        selection_window.attributes('-topmost', True)
        selection_window.configure(background='black')
        
        canvas = tk.Canvas(selection_window, highlightthickness=0, bg='black')
        canvas.pack(fill='both', expand=True)
        
        # Bilgi metni
        canvas.create_text(
            selection_window.winfo_screenwidth() // 2,
            50,
            text="QR KODU SEÇİN (veya ESC ile çık)",
            font=('Arial', 24, 'bold'),
            fill='yellow'
        )
        
        self.start_x = None
        self.start_y = None
        rect = None
        
        def on_mouse_down(event):
            self.start_x = selection_window.winfo_pointerx()
            self.start_y = selection_window.winfo_pointery()
            
        def on_mouse_move(event):
            nonlocal rect
            if self.start_x:
                if rect:
                    canvas.delete(rect)
                    
                current_x = selection_window.winfo_pointerx()
                current_y = selection_window.winfo_pointery()
                
                x1 = min(self.start_x, current_x) - selection_window.winfo_rootx()
                y1 = min(self.start_y, current_y) - selection_window.winfo_rooty()
                x2 = max(self.start_x, current_x) - selection_window.winfo_rootx()
                y2 = max(self.start_y, current_y) - selection_window.winfo_rooty()
                
                rect = canvas.create_rectangle(x1, y1, x2, y2,
                                             outline='lime', width=3)
                                             
        def on_mouse_up(event):
            if self.start_x:
                end_x = selection_window.winfo_pointerx()
                end_y = selection_window.winfo_pointery()
                
                # Alan hesapla
                x1 = min(self.start_x, end_x) - 50  # 50px padding
                y1 = min(self.start_y, end_y) - 50
                x2 = max(self.start_x, end_x) + 50
                y2 = max(self.start_y, end_y) + 50
                
                selection_window.destroy()
                
                # Görüntü al ve işle
                screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                result = self.ultimate_qr_scan(screenshot)
                
                if result:
                    self.show_popup(result)
                else:
                    messagebox.showwarning("QR Bulunamadı", 
                                         "QR kod okunamadı!\n\n"
                                         "Öneriler:\n"
                                         "• Daha yakından çekin\n"
                                         "• Ekranı temizleyin\n"
                                         "• QR'ın tamamı görünsün")
                                         
        def on_escape(event):
            selection_window.destroy()
            
        selection_window.bind("<Button-1>", on_mouse_down)
        selection_window.bind("<B1-Motion>", on_mouse_move)
        selection_window.bind("<ButtonRelease-1>", on_mouse_up)
        selection_window.bind("<Escape>", on_escape)
        
        selection_window.mainloop()
        
    def ultimate_qr_scan(self, image):
        """Tüm QR okuma yöntemlerini kullan"""
        img_array = np.array(image)
        
        # 1. QREADER (EN GÜÇLÜ)
        if QREADER:
            try:
                decoded = qreader_instance.detect_and_decode(image=img_array)
                if decoded and decoded[0]:
                    return decoded[0]
            except:
                pass
                
        # 2. OpenCV
        try:
            detector = cv2.QRCodeDetector()
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            data, _, _ = detector.detectAndDecode(gray)
            if data:
                return data
        except:
            pass
            
        # 3. PYZBAR - Çoklu preprocessing
        if PYZBAR:
            preprocessors = [
                lambda img: cv2.cvtColor(img, cv2.COLOR_RGB2GRAY),
                lambda img: cv2.threshold(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), 
                                        0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
                lambda img: cv2.adaptiveThreshold(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY),
                                                255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                cv2.THRESH_BINARY, 11, 2),
            ]
            
            for preprocess in preprocessors:
                try:
                    processed = preprocess(img_array)
                    codes = pyzbar.decode(processed)
                    if codes:
                        return codes[0].data.decode('utf-8', errors='ignore')
                except:
                    pass
                    
        # 4. Görüntü iyileştirme ve tekrar dene
        try:
            # Kontrast artır
            enhancer = ImageEnhance.Contrast(image)
            enhanced = enhancer.enhance(2.0)
            
            # Keskinlik artır
            sharpener = ImageEnhance.Sharpness(enhanced)
            sharpened = sharpener.enhance(2.0)
            
            # Tekrar dene
            return self.basic_qr_scan(np.array(sharpened))
        except:
            pass
            
        return None
        
    def basic_qr_scan(self, img_array):
        """Basit QR tarama"""
        if PYZBAR:
            try:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                codes = pyzbar.decode(gray)
                if codes:
                    return codes[0].data.decode('utf-8', errors='ignore')
            except:
                pass
        return None
        
    def show_popup(self, text):
        """Sonuç popup'ı"""
        popup = tk.Tk()
        popup.title("📱 QR Kod Okundu!")
        popup.geometry("500x300")
        popup.attributes('-topmost', True)
        
        # Ortala
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - 250
        y = (popup.winfo_screenheight() // 2) - 150
        popup.geometry(f'+{x}+{y}')
        
        # Frame
        main_frame = tk.Frame(popup, bg='#1a1a1a', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Başlık
        title_label = tk.Label(main_frame, text="✅ QR Kod Başarıyla Okundu", 
                             font=('Arial', 16, 'bold'), bg='#1a1a1a', fg='#00ff00')
        title_label.pack(pady=(0, 15))
        
        # Metin alanı
        text_frame = tk.Frame(main_frame, bg='#2a2a2a', relief='solid', borderwidth=2)
        text_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 11),
                            bg='#2a2a2a', fg='white', relief='flat', padx=10, pady=10,
                            insertbackground='white')
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', text)
        text_widget.config(state='disabled')
        
        # Kopyala butonu
        def copy_and_close():
            pyperclip.copy(text)
            popup.destroy()
            self.show_notification("✅ Metin kopyalandı!")
            
        copy_btn = tk.Button(main_frame, text="📋 KOPYALA VE KAPAT", 
                           command=copy_and_close,
                           bg='#00ff00', fg='black', font=('Arial', 14, 'bold'),
                           padx=30, pady=15, relief='flat', cursor='hand2')
        copy_btn.pack()
        
        # Enter = kopyala
        popup.bind('<Return>', lambda e: copy_and_close())
        popup.bind('<Escape>', lambda e: popup.destroy())
        
        popup.focus_force()
        popup.mainloop()
        
    def whatsapp_quick_scan(self, icon=None, item=None):
        """WhatsApp'tan hızlı QR okuma"""
        # WhatsApp penceresi bul
        whatsapp = self.find_window("WhatsApp")
        if not whatsapp:
            messagebox.showwarning("Uyarı", "WhatsApp penceresi bulunamadı!")
            return
            
        # Pencere görüntüsü al
        rect = win32gui.GetWindowRect(whatsapp)
        screenshot = ImageGrab.grab(bbox=rect)
        
        # QR ara
        result = self.ultimate_qr_scan(screenshot)
        
        if result:
            self.show_popup(result)
        else:
            messagebox.showinfo("Bilgi", "WhatsApp'ta QR kod bulunamadı.\n"
                                        "QR kodun ekranda görünür olduğundan emin olun.")
                                        
    def quit_app(self, icon, item):
        self.icon.stop()
        sys.exit()
        
    def run(self):
        self.create_icon()
        
        # Icon thread
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        
        # Kısayollar
        keyboard.add_hotkey('win+z', self.manual_capture)
        keyboard.add_hotkey('win+x', self.whatsapp_quick_scan)
        
        print("QR Reader Pro başlatıldı!")
        print("Win+Z: Manuel QR okuma")
        print("Win+X: WhatsApp'tan QR okuma")
        
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            self.icon.stop()
            sys.exit()

if __name__ == "__main__":
    app = QRReaderPro()
    app.run()