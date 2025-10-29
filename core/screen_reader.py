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
    # ทดสอบแค่ screenshot_data_uri (ไม่ต้องใช้ OCR)
    from . import screenshot_data_uri
    uri, _, _ = screenshot_data_uri()
    print("📸 จับภาพหน้าจอสำเร็จ!")
    print("ตัวอย่าง data URI:", uri[:60] + "...")
    
    # หากต้องการทดสอบ OCR → ให้ติดตั้ง Tesseract ก่อน
    # sr = ScreenReader(lang="tha+eng")
    # print("OCR Result:", sr.read_text())

# =============== เพิ่มส่วนนี้ที่ท้ายไฟล์ ===============
import io
import base64

def screenshot_data_uri(resize_to=(1024, 768), fmt="JPEG", quality=80):
    """
    จับภาพหน้าจอ → แปลงเป็น data URI (สำหรับส่งให้ LLM Vision)
    Returns:
        tuple: (data_uri: str, raw_bytes: bytes, pil_image: Image)
    """
    from core.screen_capturer import screenshot_pil
    
    # จับภาพหน้าจอ
    img = screenshot_pil()
    
    # resize ถ้าต้องการ
    if resize_to:
        from PIL import Image
        img = img.resize(resize_to, Image.LANCZOS)
    
    # แปลงเป็น bytes
    img_byte_arr = io.BytesIO()
    if fmt.upper() == "PNG":
        img.save(img_byte_arr, format="PNG")
    else:
        img.save(img_byte_arr, format="JPEG", quality=quality)
    img_bytes = img_byte_arr.getvalue()
    
    # แปลงเป็น base64
    base64_str = base64.b64encode(img_bytes).decode('utf-8')
    mime_type = "image/jpeg" if fmt.upper() != "PNG" else "image/png"
    data_uri = f"data:{mime_type};base64,{base64_str}"
    
    return data_uri, img_bytes, img