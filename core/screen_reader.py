# core/screen_reader.py
# -------------------------
# ถ่ายภาพหน้าจอ (full-screen หรือ region) และแปลงเป็นข้อความด้วย pytesseract
# ใช้ mss สำหรับ screenshot ที่เร็ว และ PIL (Pillow) สำหรับแปลงภาพ
# ต้องติดตั้ง tesseract และตั้งค่า TESSERACT_CMD ใน config.py
# -------------------------

import mss
from PIL import Image
import pytesseract
import io
import os
from config import TESSERACT_CMD

# ให้ pytesseract รู้พาธ tesseract.exe (ถ้ามี)
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

def screenshot(region=None):
    """
    ถ่าย screenshot
    - region: (left, top, width, height) หรือ None = full screen
    คืนค่า PIL.Image
    """
    with mss.mss() as sct:
        if region:
            left, top, width, height = region
            monitor = {"left": left, "top": top, "width": width, "height": height}
        else:
            monitor = sct.monitors[0]  # full screen
        sct_img = sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
        return img

def read_screen(region=None, lang='tha+eng'):
    """
    อ่านข้อความจากจอด้วย pytesseract
    - region: ถ้าให้เฉพาะพื้นที่ ให้ส่ง tuple (left, top, width, height)
    - lang: ภาษาเพื่อเพิ่มความแม่นยำ (เช่น 'tha+eng')
    คืนค่า: string (text)
    """
    try:
        img = screenshot(region)
        # ก่อน OCR อาจปรับขาวดำ / ขนาดเพื่อความแม่นยำ (ไม่บังคับ)
        text = pytesseract.image_to_string(img, lang=lang)
        return text.strip()
    except Exception as e:
        return f"[OCR ERROR] {e}"

def save_screenshot(path='screenshot.png', region=None):
    img = screenshot(region)
    img.save(path)
    return path
