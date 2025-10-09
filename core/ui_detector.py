# core/ui_detector.py
# -------------------------
# ตรวจจับ UI Elements บนหน้าจอ
# รองรับ:
# - หาตำแหน่งข้อความด้วย OCR
# - หาภาพด้วย Template Matching
# - คำนวณ Bounding Box และจุดศูนย์กลาง
# -------------------------

import cv2
import numpy as np
import pytesseract
from PIL import Image
from core.screen_capturer import screenshot_pil
from typing import Optional, Tuple, List, Dict


class UIDetector:
    """
    ตรวจจับ UI Elements บนหน้าจอ
    """

    def __init__(self, monitor=1):
        """
        monitor: เลือกจอที่ต้องการตรวจจับ (1 = จอหลัก)
        """
        self.monitor = monitor
        print(f"[UIDetector] ✅ เตรียมระบบตรวจจับ UI บนจอที่ {monitor}")

    def find_element_by_text(self, text: str, screenshot=None) -> Optional[Dict]:
        """
        หา element บนหน้าจอด้วยข้อความ (OCR)
        
        Returns:
            Dict หรือ None
            {"x": int, "y": int, "w": int, "h": int, "confidence": float}
        """
        if screenshot is None:
            screenshot = screenshot_pil(monitor=self.monitor)

        # แปลงเป็น numpy array สำหรับ pytesseract
        img_np = np.array(screenshot)

        # ใช้ pytesseract หาข้อความและตำแหน่ง
        try:
            data = pytesseract.image_to_data(img_np, lang="tha+eng", output_type=pytesseract.Output.DICT)
        except Exception as e:
            print(f"[UIDetector ERROR] OCR ล้มเหลว: {e}")
            return None

        # ค้นหาข้อความที่ตรงกัน
        text_lower = text.lower()
        for i, word in enumerate(data['text']):
            if word and text_lower in word.lower():
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                conf = data['conf'][i]
                
                return {
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                    "confidence": conf
                }

        print(f"[UIDetector] ไม่พบข้อความ '{text}' บนหน้าจอ")
        return None

    def find_element_by_image(self, template_path: str, screenshot=None, threshold=0.8) -> Optional[Dict]:
        """
        หา element บนหน้าจอด้วย template matching
        
        Parameters:
            template_path: path ไปยังภาพ template
            screenshot: PIL Image (ถ้าไม่ระบุจะจับภาพใหม่)
            threshold: ความแม่นยำขั้นต่ำ (0-1)
        
        Returns:
            Dict หรือ None
        """
        if screenshot is None:
            screenshot = screenshot_pil(monitor=self.monitor)

        # แปลงเป็น OpenCV format
        screen_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        try:
            template = cv2.imread(template_path)
            if template is None:
                print(f"[UIDetector ERROR] ไม่สามารถโหลดภาพ {template_path}")
                return None
        except Exception as e:
            print(f"[UIDetector ERROR] โหลดภาพล้มเหลว: {e}")
            return None

        # Template matching
        result = cv2.matchTemplate(screen_cv, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = template.shape[:2]
            x, y = max_loc
            return {
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "confidence": max_val
            }

        print(f"[UIDetector] ไม่พบภาพที่ตรงกับ template (max_val={max_val:.2f})")
        return None

    def get_element_center(self, element: Dict) -> Tuple[int, int]:
        """
        คำนวณจุดศูนย์กลางของ element
        
        Returns:
            (center_x, center_y)
        """
        x = element["x"]
        y = element["y"]
        w = element["w"]
        h = element["h"]
        
        center_x = x + w // 2
        center_y = y + h // 2
        
        return (center_x, center_y)

    def find_all_text(self, screenshot=None) -> List[Dict]:
        """
        หาข้อความทั้งหมดบนหน้าจอ
        
        Returns:
            List of Dict
        """
        if screenshot is None:
            screenshot = screenshot_pil(monitor=self.monitor)

        img_np = np.array(screenshot)
        
        try:
            data = pytesseract.image_to_data(img_np, lang="tha+eng", output_type=pytesseract.Output.DICT)
        except Exception as e:
            print(f"[UIDetector ERROR] OCR ล้มเหลว: {e}")
            return []

        results = []
        for i in range(len(data['text'])):
            word = data['text'][i]
            if word.strip():  # ข้ามข้อความว่าง
                results.append({
                    "text": word,
                    "x": data['left'][i],
                    "y": data['top'][i],
                    "w": data['width'][i],
                    "h": data['height'][i],
                    "confidence": data['conf'][i]
                })
        
        return results


# ✅ Test Mode
if __name__ == "__main__":
    detector = UIDetector(monitor=1)
    
    print("\n=== ทดสอบค้นหาข้อความ ===")
    element = detector.find_element_by_text("File")
    if element:
        print(f"✅ พบ 'File' ที่ตำแหน่ง: {element}")
        center = detector.get_element_center(element)
        print(f"📍 จุดศูนย์กลาง: {center}")
    else:
        print("❌ ไม่พบ")

    print("\n=== ข้อความทั้งหมดบนหน้าจอ ===")
    all_text = detector.find_all_text()
    print(f"พบ {len(all_text)} ข้อความ")
    for t in all_text[:10]:  # แสดง 10 อันแรก
        print(f"- {t['text']} @ ({t['x']}, {t['y']})")