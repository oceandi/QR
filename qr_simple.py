# qr_simple.py - En basit QR okuyucu
import tkinter as tk
from PIL import ImageGrab
import keyboard
import pyperclip
from tkinter import messagebox
import cv2
import numpy as np
from pyzbar import pyzbar
import sys
import time

# qreader varsa kullan
try:
    from qreader import QReader
    qreader = QReader()
    USE_QREADER = True
except:
    USE_QREADER = False
    print("qreader için: pip install qreader")

class SimpleQRReader:
    def __init__(self):
        self.selecting = False
        
    def capture_screen(self):
        """Ekran yakalama başlat"""
        if self.selecting:
            return
            
        self.selecting = True
        
        # Overlay pencere
        root = tk.Tk()
        root.attributes('-fullscreen', True)
        root.attributes('-alpha', 0.3)
        root.attributes('-topmost', True)
        root.configure(background='gray')
        root.config(cursor="cross")
        
        self.start_x = None
        self.start_y = None
        
        canvas = tk.Canvas(root, cursor="cross", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bilgi metni
        info = canvas.create_text(
            root.winfo_screenwidth()//2, 30,
            text="QR KODUN ÜZERİNE TIKLA VE SÜRÜKLE",
            font=("Arial", 20, "bold"),
            fill="yellow"
        )
        
        rect = None
        
        def start_select(event):
            self.start_x = root.winfo_pointerx()
            self.start_y = root.winfo_pointery()
            
        def update_select(event):
            nonlocal rect
            if self.start_x:
                # Eski dikdörtgeni sil
                if rect:
                    canvas.delete(rect)
                
                # Yeni dikdörtgen çiz
                cur_x = root.winfo_pointerx()
                cur_y = root.winfo_pointery()
                
                x1 = min(self.start_x, cur_x) - root.winfo_rootx()
                y1 = min(self.start_y, cur_y) - root.winfo_rooty()
                x2 = max(self.start_x, cur_x) - root.winfo_rootx()
                y2 = max(self.start_y, cur_y) - root.winfo_rooty()
                
                rect = canvas.create_rectangle(
                    x1, y1, x2, y2,
                    outline='red', width=2, fill='red', stipple='gray50'
                )
        
        def end_select(event):
            if not self.start_x:
                root.destroy()
                self.selecting = False
                return
                
            cur_x = root.winfo_pointerx()
            cur_y = root.winfo_pointery()
            
            # Koordinatları al
            x1 = min(self.start_x, cur_x)
            y1 = min(self.start_y, cur_y)
            x2 = max(self.start_x, cur_x)
            y2 = max(self.start_y, cur_y)
            
            # Pencereyi kapat
            root.destroy()
            self.selecting = False
            
            # Biraz bekle (pencere kapansın)
            time.sleep(0.1)
            
            # Ekran görüntüsü al
            if abs(x2-x1) > 20 and abs(y2-y1) > 20:
                # Biraz genişlet
                x1 -= 20
                y1 -= 20
                x2 += 20
                y2 += 20
                
                screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                self.process_image(screenshot)
        
        def cancel(event):
            root.destroy()
            self.selecting = False
        
        # Olayları bağla
        canvas.bind("<Button-1>", start_select)
        canvas.bind("<B1-Motion>", update_select)
        canvas.bind("<ButtonRelease-1>", end_select)
        root.bind("<Escape>", cancel)
        
        root.mainloop()
    
    def process_image(self, image):
        """Görüntüyü işle ve QR oku"""
        # Numpy array'e çevir
        img_np = np.array(image)
        
        # 1. qreader ile dene
        if USE_QREADER:
            try:
                result = qreader.detect_and_decode(image=img_np)
                if result and result[0]:
                    self.show_result(result[0])
                    return
            except:
                pass
        
        # 2. OpenCV QR detector
        try:
            qr_detector = cv2.QRCodeDetector()
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            data, _, _ = qr_detector.detectAndDecode(gray)
            if data:
                self.show_result(data)
                return
        except:
            pass
        
        # 3. pyzbar ile dene
        methods = [
            # Direkt gri
            lambda: cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY),
            # Binary
            lambda: cv2.threshold(cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY), 127, 255, cv2.THRESH_BINARY)[1],
            # Otsu
            lambda: cv2.threshold(cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
            # Adaptive
            lambda: cv2.adaptiveThreshold(cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2),
        ]
        
        for method in methods:
            try:
                processed = method()
                codes = pyzbar.decode(processed)
                if codes:
                    data = codes[0].data.decode('utf-8', errors='ignore')
                    self.show_result(data)
                    return
            except:
                continue
        
        # Bulunamadı
        messagebox.showwarning(
            "QR Kod Bulunamadı",
            "QR kod okunamadı!\n\n"
            "Çözümler:\n"
            "• QR kodun TAMAMI görünsün\n"
            "• Daha YAKIN çekin (Ctrl++)\n"
            "• Ekran parlaklığını artırın\n\n"
            f"{'qreader yüklü değil!' if not USE_QREADER else ''}"
        )
    
    def show_result(self, text):
        """Sonucu göster"""
        # Otomatik kopyala
        pyperclip.copy(text)
        
        # Popup
        root = tk.Tk()
        root.title("✅ QR Kod Okundu!")
        root.geometry("400x200")
        root.attributes('-topmost', True)
        
        # Ortala
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - 200
        y = (root.winfo_screenheight() // 2) - 100
        root.geometry(f'+{x}+{y}')
        
        # İçerik
        frame = tk.Frame(root, bg='white', padx=20, pady=20)
        frame.pack(fill='both', expand=True)
        
        # Başarı mesajı
        tk.Label(frame, text="✅ Başarıyla okundu ve kopyalandı!",
                font=('Arial', 14, 'bold'), bg='white', fg='green').pack(pady=(0,10))
        
        # Metin
        text_frame = tk.Frame(frame, bg='#f0f0f0', relief='solid', bd=1)
        text_frame.pack(fill='both', expand=True, pady=10)
        
        text_widget = tk.Text(text_frame, wrap='word', height=5, 
                            font=('Consolas', 10), bg='#f0f0f0')
        text_widget.pack(fill='both', expand=True, padx=5, pady=5)
        text_widget.insert('1.0', text)
        text_widget.config(state='disabled')
        
        # Kapat butonu
        tk.Button(frame, text="Tamam (Enter)", command=root.destroy,
                 bg='#4CAF50', fg='white', font=('Arial', 11, 'bold'),
                 padx=20, pady=8).pack()
        
        root.bind('<Return>', lambda e: root.destroy())
        root.bind('<Escape>', lambda e: root.destroy())
        
        # 3 saniye sonra otomatik kapat
        root.after(3000, root.destroy)
        
        root.mainloop()
    
    def run(self):
        """Ana döngü"""
        print("Simple QR Reader başlatıldı!")
        print("Win+Z: QR okuma")
        print("ESC: İptal")
        
        # Kısayol tanımla
        keyboard.add_hotkey('win+z', self.capture_screen)
        
        # Sonsuz döngü
        try:
            keyboard.wait()
        except KeyboardInterrupt:
            sys.exit()

if __name__ == "__main__":
    app = SimpleQRReader()
    app.run()