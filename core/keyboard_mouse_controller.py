# core/keyboard_mouse_controller.py
# -------------------------
# Controller ระดับสูงสำหรับควบคุม Keyboard & Mouse
# รวมกับ UIDetector เพื่อให้สามารถคลิก/พิมพ์ใน UI ที่ตรวจจับได้
# -------------------------

import pyautogui
import time
from typing import List, Tuple, Optional
from core.ui_detector import UIDetector


class KeyboardController:
    """
    ควบคุมคีย์บอร์ด
    """

    def type_text(self, text: str, interval=0.05):
        """
        พิมพ์ข้อความทีละตัวอักษร
        interval: ช่วงเวลาระหว่างการพิมพ์แต่ละตัว (วินาที)
        """
        print(f"[Keyboard] พิมพ์: {text}")
        pyautogui.typewrite(text, interval=interval)

    def press_keys(self, keys: List[str]):
        """
        กดปุ่มหลายตัวพร้อมกัน (hotkey)
        เช่น keys = ["ctrl", "c"]
        """
        print(f"[Keyboard] กด: {'+'.join(keys)}")
        pyautogui.hotkey(*keys)

    def press_key(self, key: str):
        """กดปุ่มเดียว"""
        print(f"[Keyboard] กด: {key}")
        pyautogui.press(key)


class MouseController:
    """
    ควบคุมเมาส์
    """

    def click(self, x: int, y: int, button="left", clicks=1):
        """
        คลิกที่ตำแหน่ง (x, y)
        button: "left", "right", "middle"
        clicks: จำนวนครั้งที่คลิก
        """
        print(f"[Mouse] คลิก {button} ที่ ({x}, {y})")
        pyautogui.click(x, y, button=button, clicks=clicks)

    def move_to(self, x: int, y: int, duration=0.5):
        """
        ขยับเมาส์ไปยังตำแหน่ง (x, y)
        duration: ระยะเวลาในการขยับ (วินาที)
        """
        print(f"[Mouse] ขยับไปที่ ({x}, {y})")
        pyautogui.moveTo(x, y, duration=duration)

    def scroll(self, amount: int):
        """
        เลื่อนหน้าจอ
        amount: บวก = เลื่อนขึ้น, ลบ = เลื่อนลง
        """
        print(f"[Mouse] เลื่อน: {amount}")
        pyautogui.scroll(amount)

    def drag_to(self, x: int, y: int, duration=0.5):
        """ลากเมาส์ไปยังตำแหน่ง (x, y)"""
        print(f"[Mouse] ลากไปที่ ({x}, {y})")
        pyautogui.dragTo(x, y, duration=duration)


class KeyboardMouseController:
    """
    Controller หลักที่รวม Keyboard, Mouse, และ UIDetector
    """

    def __init__(self, monitor=1):
        """
        monitor: จอที่ต้องการควบคุม
        """
        self.keyboard = KeyboardController()
        self.mouse = MouseController()
        self.detector = UIDetector(monitor=monitor)
        print(f"[Controller] ✅ พร้อมใช้งานบนจอที่ {monitor}")

    def click_text(self, text: str, button="left"):
        """
        ค้นหาข้อความแล้วคลิก
        """
        element = self.detector.find_element_by_text(text)
        if not element:
            print(f"[Controller] ❌ ไม่พบข้อความ '{text}'")
            return False
        
        x, y = self.detector.get_element_center(element)
        self.mouse.click(x, y, button=button)
        return True

    def click_image(self, template_path: str, button="left"):
        """
        ค้นหาภาพแล้วคลิก
        """
        element = self.detector.find_element_by_image(template_path)
        if not element:
            print(f"[Controller] ❌ ไม่พบภาพ '{template_path}'")
            return False
        
        x, y = self.detector.get_element_center(element)
        self.mouse.click(x, y, button=button)
        return True

    def type_at_text(self, target_text: str, content: str):
        """
        ค้นหาข้อความ → คลิก → พิมพ์
        """
        if not self.click_text(target_text):
            return False
        time.sleep(0.2)
        self.keyboard.type_text(content)
        return True


# ✅ Test Mode
if __name__ == "__main__":
    controller = KeyboardMouseController(monitor=1)
    
    print("\n=== ทดสอบค้นหาและคลิก ===")
    # ลองค้นหา "File" แล้วคลิก
    result = controller.click_text("File")
    if result:
        print("✅ คลิกสำเร็จ")
    else:
        print("❌ คลิกล้มเหลว")