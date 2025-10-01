# core/screen_reader.py
# -------------------------
# โมดูลนี้ทำหน้าที่เป็น "Screen Reader" เบื้องต้น
# ใช้ pytesseract + Pillow (PIL) เพื่อจับภาพหน้าจอ (screenshot)
# แล้วแปลงภาพเป็นข้อความ (OCR = Optical Character Recognition)
# -------------------------

import pytesseract
import pyautogui
from PIL import Image

class ScreenReader:
    """
    คลาส ScreenReader
    -----------------
    ความสามารถ:
    - จับภาพหน้าจอ (Screenshot)
    - ใช้ OCR (pytesseract) เพื่ออ่านข้อความจากภาพ
    - รองรับการอ่านข้อความทั้งจอ หรือเฉพาะบางส่วน (Crop)
    """

    def __init__(self, lang="tha+eng"):
        """
        lang: กำหนดภาษาที่จะใช้ OCR เช่น
            - "tha"   = ภาษาไทย
            - "eng"   = ภาษาอังกฤษ
            - "tha+eng" = อ่านได้ทั้งไทยและอังกฤษ
        """
        self.lang = lang
        print(f"[ScreenReader] ✅ Initialised OCR language = {self.lang}")

    def read_screen(self):
        """
        จับภาพทั้งหน้าจอ → แปลงเป็นข้อความด้วย OCR
        return: string (ข้อความที่อ่านได้)
        """
        print("[ScreenReader] 🖼 กำลังจับภาพหน้าจอทั้งจอ...")
        screenshot = pyautogui.screenshot()   # ถ่ายภาพทั้งจอ
        text = pytesseract.image_to_string(screenshot, lang=self.lang)  # OCR
        print("[ScreenReader] 📖 ข้อความที่อ่านได้:", text.strip()[:50], "...")
        return text.strip()

    def read_region(self, x, y, width, height):
        """
        จับภาพเฉพาะพื้นที่ (x, y, w, h) → OCR
        เช่น อ่านกล่องข้อความ, ปุ่ม, หรือส่วนหนึ่งของหน้าจอ
        return: string (ข้อความที่อ่านได้)
        """
        print(f"[ScreenReader] 🖼 จับภาพบางส่วน: x={x}, y={y}, w={width}, h={height}")
        screenshot = pyautogui.screenshot(region=(x, y, width, height))  # Crop
        text = pytesseract.image_to_string(screenshot, lang=self.lang)
        print("[ScreenReader] 📖 ข้อความที่อ่านได้:", text.strip()[:50], "...")
        return text.strip()

    def save_screenshot(self, filepath="screenshot.png"):
        """
        จับภาพหน้าจอแล้วบันทึกเป็นไฟล์ .png
        เหมาะกับการ debug หรือเก็บ log
        """
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        print(f"[ScreenReader] 💾 บันทึกภาพหน้าจอที่ {filepath}")
