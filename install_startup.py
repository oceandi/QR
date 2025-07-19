# Windows startup'a ekle
import os
import shutil

startup_path = os.path.join(
    os.environ['APPDATA'], 
    'Microsoft', 'Windows', 'Start Menu', 
    'Programs', 'Startup'
)
shutil.copy('qr_reader.pyw', startup_path)