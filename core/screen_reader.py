# core/screen_reader.py
# -------------------------
# จัดการ OCR (อ่านข้อความจากหน้าจอ)
# -------------------------

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # ให้เจอ config และ core อื่นๆ

import pytesseract
from PIL import Image
from core.screen_capturer import screenshot_pil

class ScreenReader:
    def __init__(self, lang="eng", default_monitor=0, default_region=None):
        """
        ScreenReader: อ่านข้อความจากหน้าจอด้วย OCR
        - lang: กำหนดภาษาสำหรับ Tesseract เช่น "eng", "tha", หรือ "tha+eng"
        - default_monitor: เลือกจอที่ต้องการ (0 = all, 1 = main, 2+ = จออื่นๆ)
        - default_region: tuple (left, top, width, height) ถ้าอยาก fix พื้นที่ OCR
        """
        self.lang = lang
        self.default_monitor = default_monitor
        self.default_region = default_region

    def read_text(self, region=None, resize_to=None, monitor=None):
        """
        OCR อ่านข้อความจากหน้าจอ
        - region: (x,y,w,h) พื้นที่ OCR ถ้า None ใช้ default_region
        - resize_to: (w,h) ถ้าอยากย่อ/ขยายก่อน OCR
        - monitor: เลือกจอที่จะจับ (override default_monitor)
        """
        monitor = monitor if monitor is not None else self.default_monitor
        region = region if region is not None else self.default_region

        # จับภาพหน้าจอ
        img = screenshot_pil(region=region)

        # OCR
        text = pytesseract.image_to_string(img, lang=self.lang)
        return text.strip()

# ✅ Test Mode
if __name__ == "__main__":
    sr = ScreenReader(lang="tha+eng")  # รองรับทั้งไทยและอังกฤษ
    print("📸 OCR Result:")
    print(sr.read_text())
