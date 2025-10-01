# core/keyboard_mouse.py
# -------------------------
# โมดูลนี้ใช้ควบคุมคีย์บอร์ดและเมาส์
# ใช้ pyautogui ทำงาน เช่น กดปุ่ม, พิมพ์, คลิก, ขยับเมาส์
# -------------------------

import pyautogui

class KeyboardMouse:
    """
    คลาสสำหรับควบคุม Keyboard & Mouse
    รองรับ:
    - พิมพ์ข้อความ (type_text)
    - กดปุ่ม (press_key)
    - คลิก (click)
    - ขยับเมาส์ (move_mouse)
    - กดปุ่มหลายตัวพร้อมกัน (hotkey)
    """

    def type_text(self, text: str):
        """พิมพ์ข้อความลงในหน้าต่างปัจจุบัน"""
        print(f"[KeyboardMouse] กำลังพิมพ์: {text}")
        pyautogui.typewrite(text)

    def press_key(self, key: str):
        """กดปุ่มคีย์บอร์ด เช่น 'enter', 'esc'"""
        print(f"[KeyboardMouse] กดปุ่ม: {key}")
        pyautogui.press(key)

    def click(self, x: int, y: int, button="left"):
        """คลิกเมาส์ที่ตำแหน่ง (x, y)"""
        print(f"[KeyboardMouse] คลิกที่ ({x}, {y}) ปุ่ม: {button}")
        pyautogui.click(x, y, button=button)

    def move_mouse(self, x: int, y: int):
        """ขยับเมาส์ไปยังตำแหน่ง (x, y)"""
        print(f"[KeyboardMouse] ย้ายเมาส์ไปที่ ({x}, {y})")
        pyautogui.moveTo(x, y)

    def hotkey(self, *keys):
        """กดปุ่มหลายตัวพร้อมกัน เช่น hotkey('ctrl', 'c')"""
        print(f"[KeyboardMouse] กดปุ่มลัด: {keys}")
        pyautogui.hotkey(*keys)
