(function() {
  let isActive = false;
  let scanInterval = null;
  
  // QR okuma butonu ekle
  function addQRButton() {
    const button = document.createElement('div');
    button.id = 'qr-reader-button';
    button.innerHTML = '📷 QR Oku';
    button.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      background: #25D366;
      color: white;
      padding: 10px 20px;
      border-radius: 25px;
      cursor: pointer;
      font-weight: bold;
      box-shadow: 0 2px 5px rgba(0,0,0,0.2);
      z-index: 9999;
      transition: all 0.3s;
    `;
    
    button.addEventListener('click', toggleQRScanning);
    document.body.appendChild(button);
  }
  
  // QR tarama aç/kapat
  function toggleQRScanning() {
    isActive = !isActive;
    const button = document.getElementById('qr-reader-button');
    
    if (isActive) {
      button.innerHTML = '⏸️ Durdur';
      button.style.background = '#ff5555';
      startScanning();
    } else {
      button.innerHTML = '📷 QR Oku';
      button.style.background = '#25D366';
      stopScanning();
    }
  }
  
  // Taramayı başlat
  function startScanning() {
    scanInterval = setInterval(() => {
      // Tüm img elementlerini kontrol et
      const images = document.querySelectorAll('img');
      
      images.forEach(img => {
        // QR kod boyutunda mı kontrol et
        if (img.width > 100 && img.width < 500 && 
            img.height > 100 && img.height < 500) {
          
          // Canvas'a çiz
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d');
          
          // CORS problemini aş
          img.crossOrigin = 'anonymous';
          
          try {
            ctx.drawImage(img, 0, 0);
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            
            // jsQR ile oku
            const code = jsQR(imageData.data, imageData.width, imageData.height);
            
            if (code) {
              handleQRCode(code.data);
              highlightImage(img);
            }
          } catch (e) {
            // CORS hatası, yoksay
          }
        }
      });
      
      // Ayrıca canvas elementlerini de kontrol et
      const canvases = document.querySelectorAll('canvas');
      canvases.forEach(canvas => {
        try {
          const ctx = canvas.getContext('2d');
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const code = jsQR(imageData.data, imageData.width, imageData.height);
          
          if (code) {
            handleQRCode(code.data);
            highlightCanvas(canvas);
          }
        } catch (e) {
          // Hata yoksay
        }
      });
      
    }, 1000); // Saniyede bir kontrol
  }
  
  // Taramayı durdur
  function stopScanning() {
    if (scanInterval) {
      clearInterval(scanInterval);
      scanInterval = null;
    }
  }
  
  // QR kod bulundu
  function handleQRCode(data) {
    // Kopyala
    navigator.clipboard.writeText(data).then(() => {
      showNotification('✅ QR kod kopyalandı!', data);
    });
    
    // Taramayı durdur
    toggleQRScanning();
  }
  
  // Görüntüyü vurgula
  function highlightImage(img) {
    img.style.border = '3px solid #00ff00';
    img.style.boxShadow = '0 0 20px #00ff00';
    
    setTimeout(() => {
      img.style.border = '';
      img.style.boxShadow = '';
    }, 2000);
  }
  
  function highlightCanvas(canvas) {
    canvas.style.border = '3px solid #00ff00';
    canvas.style.boxShadow = '0 0 20px #00ff00';
    
    setTimeout(() => {
      canvas.style.border = '';
      canvas.style.boxShadow = '';
    }, 2000);
  }
  
  // Bildirim göster
  function showNotification(title, text) {
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: white;
      padding: 20px;
      border-radius: 10px;
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
      z-index: 10000;
      max-width: 400px;
      animation: slideIn 0.3s ease;
    `;
    
    notification.innerHTML = `
      <h3 style="margin: 0 0 10px 0; color: #25D366;">${title}</h3>
      <p style="margin: 0; word-break: break-all; font-family: monospace;">
        ${text.substring(0, 100)}${text.length > 100 ? '...' : ''}
      </p>
      <button onclick="this.parentElement.remove()" 
              style="margin-top: 10px; padding: 5px 15px; 
                     background: #25D366; color: white; 
                     border: none; border-radius: 5px; 
                     cursor: pointer;">Tamam</button>
    `;
    
    document.body.appendChild(notification);
    
    // 5 saniye sonra kaldır
    setTimeout(() => {
      notification.remove();
    }, 5000);
  }
  
  // jsQR kütüphanesini yükle
  function loadJsQR() {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.js';
    script.onload = () => {
      console.log('jsQR yüklendi');
      addQRButton();
    };
    document.head.appendChild(script);
  }
  
  // CSS animasyonları ekle
  const style = document.createElement('style');
  style.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
  `;
  document.head.appendChild(style);
  
  // Sayfa yüklendiğinde başlat
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadJsQR);
  } else {
    loadJsQR();
  }
})();