# qr_reader_pro.py - Microsoft Store Version
import pystray
from PIL import Image, ImageGrab, ImageDraw, ImageEnhance
import cv2
import numpy as np
import pyperclip
import tkinter as tk
from tkinter import messagebox, ttk
import keyboard
import threading
import sys
import time
import mss
import win32gui
import win32con
import os
import json
from pathlib import Path

# QR okuma kütüphaneleri
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

# Uygulama ayarları
APP_NAME = "QR Reader Pro"
APP_VERSION = "1.0.0"
SETTINGS_FILE = Path.home() / ".qrreaderpro" / "settings.json"

class Settings:
    def __init__(self):
        self.settings_dir = SETTINGS_FILE.parent
        self.settings_dir.mkdir(exist_ok=True)
        self.load()
        
    def load(self):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                self.hotkey = data.get('hotkey', 'win+z')
                self.auto_start = data.get('auto_start', True)
                self.show_notifications = data.get('show_notifications', True)
                self.whatsapp_monitor = data.get('whatsapp_monitor', False)
        except:
            self.hotkey = 'win+z'
            self.auto_start = True
            self.show_notifications = True
            self.whatsapp_monitor = False
            self.save()
            
    def save(self):
        data = {
            'hotkey': self.hotkey,
            'auto_start': self.auto_start,
            'show_notifications': self.show_notifications,
            'whatsapp_monitor': self.whatsapp_monitor
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(data, f, indent=2)

class QRReaderPro:
    def __init__(self):
        self.icon = None
        self.settings = Settings()
        self.whatsapp_monitor_active = False
        self.last_qr_data = None
        self.selecting = False
        
    def create_icon(self):
        # Modern icon oluştur
        icon_size = 64
        image = Image.new('RGBA', (icon_size, icon_size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        
        # QR kod pattern
        block_size = 8
        for i in range(0, icon_size, block_size):
            for j in range(0, icon_size, block_size):
                if (i//block_size + j//block_size) % 2 == 0:
                    draw.rectangle([i, j, i+block_size-1, j+block_size-1], 
                                 fill=(33, 150, 243, 255))  # Material Blue
        
        # Köşe işaretleri
        corner_size = 20
        corner_color = (33, 150, 243, 255)
        # Sol üst
        draw.rectangle([0, 0, corner_size, 4], fill=corner_color)
        draw.rectangle([0, 0, 4, corner_size], fill=corner_color)
        # Sağ üst
        draw.rectangle([icon_size-corner_size, 0, icon_size, 4], fill=corner_color)
        draw.rectangle([icon_size-4, 0, icon_size, corner_size], fill=corner_color)
        # Sol alt
        draw.rectangle([0, icon_size-4, corner_size, icon_size], fill=corner_color)
        draw.rectangle([0, icon_size-corner_size, 4, icon_size], fill=corner_color)
        
        menu = pystray.Menu(
            pystray.MenuItem(f"📷 QR Oku ({self.settings.hotkey})", self.manual_capture),
            pystray.MenuItem("📱 WhatsApp İzle", self.toggle_whatsapp_monitor, 
                           checked=lambda item: self.whatsapp_monitor_active),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("⚙️ Ayarlar", self.show_settings),
            pystray.MenuItem("ℹ️ Hakkında", self.show_about),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Çıkış", self.quit_app)
        )
        
        self.icon = pystray.Icon(APP_NAME, image, menu=menu, title=APP_NAME)
        
    def show_settings(self, icon, item):
        """Ayarlar penceresi"""
        settings_window = tk.Tk()
        settings_window.title(f"{APP_NAME} - Ayarlar")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        
        # Icon
        settings_window.iconbitmap(default=self.get_icon_path())
        
        # Ortala
        settings_window.update_idletasks()
        x = (settings_window.winfo_screenwidth() // 2) - 200
        y = (settings_window.winfo_screenheight() // 2) - 150
        settings_window.geometry(f'+{x}+{y}')
        
        # Notebook (sekmeler)
        notebook = ttk.Notebook(settings_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Genel sekmesi
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text='Genel')
        
        # Kısayol
        ttk.Label(general_frame, text="Kısayol Tuşu:").grid(row=0, column=0, sticky='w', padx=10, pady=10)
        hotkey_var = tk.StringVar(value=self.settings.hotkey)
        hotkey_combo = ttk.Combobox(general_frame, textvariable=hotkey_var, width=20)
        hotkey_combo['values'] = ('win+z', 'win+q', 'ctrl+shift+q', 'alt+q')
        hotkey_combo.grid(row=0, column=1, padx=10, pady=10)
        
        # Otomatik başlat
        auto_start_var = tk.BooleanVar(value=self.settings.auto_start)
        ttk.Checkbutton(general_frame, text="Windows ile başlat", 
                       variable=auto_start_var).grid(row=1, column=0, columnspan=2, 
                                                    sticky='w', padx=10, pady=5)
        
        # Bildirimler
        notifications_var = tk.BooleanVar(value=self.settings.show_notifications)
        ttk.Checkbutton(general_frame, text="Bildirimleri göster", 
                       variable=notifications_var).grid(row=2, column=0, columnspan=2, 
                                                      sticky='w', padx=10, pady=5)
        
        # WhatsApp
        whatsapp_var = tk.BooleanVar(value=self.settings.whatsapp_monitor)
        ttk.Checkbutton(general_frame, text="WhatsApp'ı otomatik izle", 
                       variable=whatsapp_var).grid(row=3, column=0, columnspan=2, 
                                                 sticky='w', padx=10, pady=5)
        
        # Performans sekmesi
        perf_frame = ttk.Frame(notebook)
        notebook.add(perf_frame, text='Performans')
        
        # QR motorları durumu
        ttk.Label(perf_frame, text="QR Okuma Motorları:", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='w', padx=10, pady=10)
        
        engines = [
            ("qreader (AI-tabanlı)", QREADER, "✅" if QREADER else "❌"),
            ("pyzbar", PYZBAR, "✅" if PYZBAR else "❌"),
            ("OpenCV", True, "✅")
        ]
        
        for i, (name, status, icon) in enumerate(engines, 1):
            ttk.Label(perf_frame, text=f"{icon} {name}").grid(row=i, column=0, 
                                                             sticky='w', padx=20, pady=2)
        
        # Kaydet butonu
        def save_settings():
            self.settings.hotkey = hotkey_var.get()
            self.settings.auto_start = auto_start_var.get()
            self.settings.show_notifications = notifications_var.get()
            self.settings.whatsapp_monitor = whatsapp_var.get()
            self.settings.save()
            
            # Kısayolu yeniden kaydet
            keyboard.clear_all_hotkeys()
            keyboard.add_hotkey(self.settings.hotkey, self.manual_capture)
            
            # Otomatik başlatmayı ayarla
            self.setup_autostart(self.settings.auto_start)
            
            messagebox.showinfo("Başarılı", "Ayarlar kaydedildi!")
            settings_window.destroy()
            
        ttk.Button(settings_window, text="Kaydet", 
                  command=save_settings).pack(side='bottom', pady=10)
        
        settings_window.mainloop()
        
    def show_about(self, icon, item):
        """Hakkında penceresi"""
        about_text = f"""{APP_NAME} v{APP_VERSION}

Profesyonel QR kod okuyucu

Özellikler:
• Ekrandan QR kod okuma
• WhatsApp otomatik izleme
• Çoklu QR motor desteği
• Otomatik kopyalama

Geliştirici: Ahmet Emirhan Korkmaz
© 2024 - Tüm hakları saklıdır

QR Motorları:
• qreader: {'✅ Yüklü' if QREADER else '❌ Yüklü değil'}
• pyzbar: {'✅ Yüklü' if PYZBAR else '❌ Yüklü değil'}
• OpenCV: ✅ Yüklü
"""
        messagebox.showinfo(f"{APP_NAME} Hakkında", about_text)
        
    def get_icon_path(self):
        """Icon dosya yolu"""
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller bundle
            return os.path.join(sys._MEIPASS, 'icon.ico')
        return 'icon.ico'
        
    def setup_autostart(self, enable):
        """Windows başlangıcına ekle/kaldır"""
        import winreg
        
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_path = sys.executable if hasattr(sys, 'frozen') else f'"{sys.executable}" "{__file__}"'
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
            
            if enable:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except:
                    pass
                    
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Autostart hatası: {e}")
            
    def show_notification(self, title, message):
        """Windows bildirimi göster"""
        if not self.settings.show_notifications:
            return
            
        try:
            # Windows 10 toast notification
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message, icon_path=self.get_icon_path(), 
                             duration=3, threaded=True)
        except:
            # Fallback - basit popup
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(title, message)
            root.destroy()
            
    def toggle_whatsapp_monitor(self, icon, item):
        """WhatsApp izlemeyi aç/kapat"""
        self.whatsapp_monitor_active = not self.whatsapp_monitor_active
        
        if self.whatsapp_monitor_active:
            self.show_notification(APP_NAME, "WhatsApp izleme başladı")
            threading.Thread(target=self.monitor_whatsapp, daemon=True).start()
        else:
            self.show_notification(APP_NAME, "WhatsApp izleme durduruldu")
            
    def monitor_whatsapp(self):
        """WhatsApp Web'i izle"""
        with mss.mss() as sct:
            while self.whatsapp_monitor_active:
                try:
                    # WhatsApp penceresi bul
                    whatsapp_window = self.find_window("WhatsApp")
                    if whatsapp_window:
                        rect = win32gui.GetWindowRect(whatsapp_window)
                        monitor = {"top": rect[1], "left": rect[0], 
                                 "width": rect[2] - rect[0], "height": rect[3] - rect[1]}
                        
                        screenshot = sct.grab(monitor)
                        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                        
                        result = self.ultimate_qr_scan(img)
                        
                        if result and result != self.last_qr_data:
                            self.last_qr_data = result
                            self.show_popup(result)
                            
                except Exception as e:
                    print(f"WhatsApp monitor hatası: {e}")
                    
                time.sleep(2)
                
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
        """Manuel QR okuma"""
        if self.selecting:
            return
            
        self.selecting = True
        time.sleep(0.1)
        
        # Önce tüm ekranı tara
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
        result = self.full_screen_qr_scan(img)
        
        if result:
            self.show_popup(result)
            self.selecting = False
        else:
            self.start_area_selection()
            
    def full_screen_qr_scan(self, image):
        """Tüm ekranda QR ara"""
        result = self.ultimate_qr_scan(image)
        if result:
            return result
            
        # Grid tarama
        width, height = image.size
        grid_size = 400
        
        for y in range(0, height - grid_size + 1, 200):
            for x in range(0, width - grid_size + 1, 200):
                region = image.crop((x, y, x + grid_size, y + grid_size))
                result = self.ultimate_qr_scan(region)
                if result:
                    return result
                    
        return None
        
    def start_area_selection(self):
        """Alan seçimi"""
        selection_window = tk.Tk()
        selection_window.attributes('-fullscreen', True)
        selection_window.attributes('-alpha', 0.3)
        selection_window.attributes('-topmost', True)
        selection_window.configure(background='black')
        
        canvas = tk.Canvas(selection_window, highlightthickness=0, bg='black')
        canvas.pack(fill='both', expand=True)
        
        # Bilgi
        canvas.create_text(
            selection_window.winfo_screenwidth() // 2, 50,
            text="QR KODUN ÜZERİNE TIKLA VE SÜRÜKLE",
            font=('Arial', 24, 'bold'), fill='yellow'
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
                
                x1 = min(self.start_x, end_x) - 50
                y1 = min(self.start_y, end_y) - 50
                x2 = max(self.start_x, end_x) + 50
                y2 = max(self.start_y, end_y) + 50
                
                selection_window.destroy()
                self.selecting = False
                
                screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                result = self.ultimate_qr_scan(screenshot)
                
                if result:
                    self.show_popup(result)
                else:
                    self.show_notification("QR Bulunamadı", 
                                         "QR kod okunamadı! Daha yakından deneyin.")
                                         
        def on_escape(event):
            selection_window.destroy()
            self.selecting = False
            
        selection_window.bind("<Button-1>", on_mouse_down)
        selection_window.bind("<B1-Motion>", on_mouse_move)
        selection_window.bind("<ButtonRelease-1>", on_mouse_up)
        selection_window.bind("<Escape>", on_escape)
        
        selection_window.mainloop()
        
    def ultimate_qr_scan(self, image):
        """Tüm QR okuma yöntemleri"""
        img_array = np.array(image)
        
        # 1. QREADER
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
            
        # 3. PYZBAR
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
                    
        return None
        
    def show_popup(self, text):
        """Sonuç popup'ı"""
        pyperclip.copy(text)
        
        popup = tk.Tk()
        popup.title(f"✅ {APP_NAME}")
        popup.geometry("500x300")
        popup.attributes('-topmost', True)
        popup.iconbitmap(default=self.get_icon_path())
        
        # Ortala
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - 250
        y = (popup.winfo_screenheight() // 2) - 150
        popup.geometry(f'+{x}+{y}')
        
        # Modern tasarım
        main_frame = tk.Frame(popup, bg='#ffffff')
        main_frame.pack(fill='both', expand=True)
        
        # Başlık
        header_frame = tk.Frame(main_frame, bg='#2196F3', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="✅ QR Kod Başarıyla Okundu!", 
                font=('Segoe UI', 16, 'bold'), bg='#2196F3', 
                fg='white').pack(expand=True)
        
        # İçerik
        content_frame = tk.Frame(main_frame, bg='white', padx=20, pady=20)
        content_frame.pack(fill='both', expand=True)
        
        tk.Label(content_frame, text="Metin otomatik olarak kopyalandı:", 
                font=('Segoe UI', 10), bg='white', fg='gray').pack(anchor='w')
        
        # Metin alanı
        text_frame = tk.Frame(content_frame, bg='#f5f5f5', relief='solid', bd=1)
        text_frame.pack(fill='both', expand=True, pady=(10, 15))
        
        text_widget = tk.Text(text_frame, wrap='word', font=('Consolas', 11),
                            bg='#f5f5f5', relief='flat', padx=10, pady=10)
        text_widget.pack(fill='both', expand=True)
        text_widget.insert('1.0', text)
        text_widget.config(state='disabled')
        
        # Butonlar
        button_frame = tk.Frame(content_frame, bg='white')
        button_frame.pack(fill='x')
        
        tk.Button(button_frame, text="Tamam", command=popup.destroy,
                 bg='#2196F3', fg='white', font=('Segoe UI', 11, 'bold'),
                 bd=0, padx=30, pady=10, cursor='hand2').pack()
        
        # 3 saniye sonra otomatik kapat
        popup.after(3000, popup.destroy)
        
        popup.bind('<Return>', lambda e: popup.destroy())
        popup.bind('<Escape>', lambda e: popup.destroy())
        
        popup.mainloop()
        
    def quit_app(self, icon, item):
        keyboard.clear_all_hotkeys()
        self.icon.stop()
        sys.exit()
        
    def run(self):
        self.create_icon()
        
        # Icon thread
        icon_thread = threading.Thread(target=self.icon.run, daemon=True)
        icon_thread.start()
        
        # Kısayol
        keyboard.add_hotkey(self.settings.hotkey, self.manual_capture)
        
        # WhatsApp izleme
        if self.settings.whatsapp_monitor:
            self.whatsapp_monitor_active = True
            threading.Thread(target=self.monitor_whatsapp, daemon=True).start()
        
        # Başlangıç bildirimi
        self.show_notification(APP_NAME, f"Hazır! {self.settings.hotkey} ile QR okuyun")
        
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            self.quit_app(None, None)

if __name__ == "__main__":
    app = QRReaderPro()
    app.run()