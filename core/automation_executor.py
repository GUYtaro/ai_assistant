# ==========================================================
# core/automation_executor.py
# -------------------------
# โมดูลนี้มีหน้าที่ "รับคำสั่ง Automation จาก LLM (JSON)"
# แล้วสั่งให้ KeyboardMouseController ทำงานตามนั้น
# พร้อมระบบ:
#   - ยืนยันด้วยเสียง (TTS/STT)
#   - ทำงานหลายขั้นตอน (multi-step)
#   - ตรวจสอบความปลอดภัย (safety)
#   - รองรับคลิก, พิมพ์, กดปุ่ม, เลื่อน, ย้ายเมาส์
# ==========================================================

import time
from typing import Dict, Any

from core.keyboard_mouse_controller import KeyboardMouseController
from core.tts_client import TTSClient
from core.stt_client import STTClient


class AutomationExecutor:
    """
    คลาส AutomationExecutor
    -------------------------
    ทำหน้าที่เป็นตัวกลางระหว่าง LLM กับระบบควบคุมคีย์บอร์ด/เมาส์

    เช่น action จาก LLM จะมีรูปแบบ:
    {
        "type": "click",
        "target": {"by": "text", "value": "ตกลง"},
        "button": "left"
    }
    """

    def __init__(self, km_controller: KeyboardMouseController = None, monitor=1):
        # ใช้ controller ที่ส่งมาหรือสร้างใหม่
        self.km = km_controller or KeyboardMouseController(monitor=monitor)

        # ระบบเสียง
        self.tts = TTSClient(lang="th")
        self.stt = STTClient(model_size="small", language="th")

    # ----------------------------------------------------------
    def _ask_confirm(self, prompt_text: str, timeout=6) -> bool:
        """
        🔒 ฟังก์ชันถามยืนยันก่อนทำงานจริง
        ใช้ TTS พูดถาม และใช้ STT ฟังคำตอบ
        คืนค่า:
            True  → ถ้าผู้ใช้พูด "ใช่ / ยืนยัน / โอเค"
            False → ถ้าผู้ใช้พูด "ไม่" หรือไม่มีเสียงตอบ
        """
        self.tts.speak(prompt_text + " พูดว่า 'ใช่' เพื่อยืนยัน หรือ 'ไม่' เพื่อยกเลิก")
        try:
            reply = self.stt.listen_once(duration=4)
            if not reply:
                return False
            r = reply.strip().lower()
            return any(w in r for w in ["ใช่", "ยืนยัน", "yes", "ok", "โอเค"])
        except Exception:
            return False

    # ----------------------------------------------------------
    def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        🧩 ฟังก์ชันหลักของ AutomationExecutor
        รับ action JSON และประมวลผลคำสั่ง

        Parameters:
            action (dict): JSON คำสั่งจาก LLM เช่น
                {
                    "type": "click",
                    "target": {"by": "text", "value": "ตกลง"},
                    "button": "left"
                }

        Returns:
            dict: {"ok": bool, "message": str, "details": ...}
        """
        try:
            # ==========================
            # 🔁 Multi-step Automation
            # ==========================
            if action.get("type") == "multi":
                results = []
                for step in action.get("steps", []):
                    res = self.execute(step)
                    results.append(res)
                    if not res.get("ok", False):
                        return {"ok": False, "message": "step_failed", "details": results}
                return {"ok": True, "message": "multi_steps_done", "details": results}

            # ==========================
            # 🔒 ถ้ามี flag confirm → ต้องถามก่อน
            # ==========================
            if action.get("confirm", False):
                ok = self._ask_confirm("คำสั่งนี้ต้องยืนยันก่อน ทำเลยหรือไม่")
                if not ok:
                    return {"ok": False, "message": "cancelled_by_user"}

            # ==========================
            # ⚙️ ประมวลผลคำสั่งหลัก
            # ==========================
            t = action.get("type")

            # ----------------------------------------------------------
            # 🖱️ CLICK ACTION
            # ----------------------------------------------------------
            if t == "click":
                target = action.get("target", {})
                x, y = None, None

                if target.get("by") == "coords":
                    # กรณีระบุตำแหน่งพิกัดโดยตรง
                    x, y = target["value"]

                elif target.get("by") == "text":
                    # ค้นหาข้อความบนหน้าจอแล้วคลิก
                    element = self.km.detector.find_element_by_text(target["value"])
                    if not element:
                        return {"ok": False, "message": "target_not_found"}
                    x, y = self.km.detector.get_element_center(element)

                elif target.get("by") == "image":
                    # ค้นหาด้วยรูปภาพ (template matching)
                    element = self.km.detector.find_element_by_image(target["value"])
                    if not element:
                        return {"ok": False, "message": "target_not_found"}
                    x, y = self.km.detector.get_element_center(element)

                else:
                    return {"ok": False, "message": "unknown_target_type"}

                # สั่งคลิก
                button = action.get("button", "left")
                self.km.mouse.click(x, y, button=button)
                time.sleep(0.2)
                return {"ok": True, "message": f"clicked {x},{y}"}

            # ----------------------------------------------------------
            # ⌨️ TYPE ACTION
            # ----------------------------------------------------------
            elif t == "type":
                txt = action.get("content", "")
                target = action.get("target")

                # ถ้ามี target → โฟกัสก่อนพิมพ์
                if target:
                    if target["by"] == "coords":
                        x, y = target["value"]
                        self.km.mouse.click(x, y)
                    elif target["by"] == "text":
                        element = self.km.detector.find_element_by_text(target["value"])
                        if element:
                            x, y = self.km.detector.get_element_center(element)
                            self.km.mouse.click(x, y)
                    time.sleep(0.2)

                self.km.keyboard.type_text(txt)
                return {"ok": True, "message": f"typed {len(txt)} chars"}

            # ----------------------------------------------------------
            # 🔘 PRESS KEY ACTION
            # ----------------------------------------------------------
            elif t == "press":
                keys = action.get("keys", [])
                self.km.keyboard.press_keys(keys)
                return {"ok": True, "message": f"pressed {'+'.join(keys)}"}

            # ----------------------------------------------------------
            # 🖱️ SCROLL ACTION
            # ----------------------------------------------------------
            elif t == "scroll":
                amt = action.get("amount", 100)
                self.km.mouse.scroll(amt)
                return {"ok": True, "message": f"scrolled {amt}"}

            # ----------------------------------------------------------
            # 🖱️ MOVE ACTION
            # ----------------------------------------------------------
            elif t == "move":
                target = action.get("target")
                if target["by"] == "coords":
                    x, y = target["value"]
                elif target["by"] == "text":
                    element = self.km.detector.find_element_by_text(target["value"])
                    if not element:
                        return {"ok": False, "message": "target_not_found"}
                    x, y = self.km.detector.get_element_center(element)
                else:
                    return {"ok": False, "message": "unknown_target_type"}

                self.km.mouse.move_to(x, y)
                return {"ok": True, "message": f"moved to {x},{y}"}

            # ----------------------------------------------------------
            # ❌ Unknown Type
            # ----------------------------------------------------------
            else:
                return {"ok": False, "message": "unsupported_action_type"}

        except Exception as e:
            # ดัก error ทุกชนิด เพื่อไม่ให้ระบบล่ม
            return {"ok": False, "message": f"executor_exception: {e}"}
