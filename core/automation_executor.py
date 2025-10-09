# core/automation_executor.py
# -------------------------
# รับ action JSON แล้วสั่งให้ KeyboardMouseController ทำงาน
# มี safety check และ confirm flow (ใช้ TTS/STT)
# -------------------------

import time
from typing import Dict, Any

from core.keyboard_mouse.controller import KeyboardMouseController  # ตามโครงที่สร้างไว้
from core.tts_client import TTSClient
from core.stt_client import STTClient

class AutomationExecutor:
    def __init__(self, km_controller: KeyboardMouseController = None):
        self.km = km_controller or KeyboardMouseController()
        self.tts = TTSClient(lang="th")
        self.stt = STTClient(model_size="small", language="th")  # ใช้ small สำหรับ confirm ให้ไว

    def _ask_confirm(self, prompt_text: str, timeout=6) -> bool:
        """ถามผู้ใช้ยืนยัน (TTS -> STT) คืน True/False"""
        self.tts.speak(prompt_text + " พูดว่า 'ใช่' เพื่อยืนยัน หรือ 'ไม่' เพื่อยกเลิก")
        # ฟัง 3-6 วินาที
        try:
            reply = self.stt.listen_once(duration=4)
            if not reply:
                return False
            r = reply.strip().lower()
            return any(w in r for w in ["ใช่","ยืนยัน","yes","ok","โอเค"])
        except Exception:
            return False

    def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        action: validated JSON จาก parser
        คืน dict เป็นผลลัพธ์ เช่น {"ok":True,"message":"..."}
        """
        try:
            # multi-step
            if action.get("type") == "multi":
                results = []
                for step in action.get("steps", []):
                    res = self.execute(step)
                    results.append(res)
                    # ถ้าหนึ่งในขั้นตอนไม่ผ่าน ให้หยุดหรือแจ้ง
                    if not res.get("ok", False):
                        return {"ok": False, "message": "step_failed", "details": results}
                return {"ok": True, "message": "multi_steps_done", "details": results}

            # ถ้ต้อง confirm ให้ถาม
            if action.get("confirm", False):
                ok = self._ask_confirm("คำสั่งนี้ต้องยืนยันก่อน ทำเลยหรือไม่")
                if not ok:
                    return {"ok": False, "message":"cancelled_by_user"}

            # แยก type และเรียก controller
            t = action.get("type")
            if t == "click":
                target = action.get("target")
                if target["by"] == "coords":
                    x,y = target["value"]
                else:
                    # ถ้า target by text/image ให้ใช้ UIDetector ผ่าน controller
                    elem = self.km.detector.find_element_by_text(target["value"]) if target["by"]=="text" else self.km.detector.find_element_by_image(target["value"])
                    if not elem:
                        return {"ok": False, "message": "target_not_found"}
                    x,y = self.km.detector.get_element_center(elem)

                button = action.get("button","left")
                self.km.mouse.click(x, y, button=button)
                time.sleep(0.2)
                return {"ok": True, "message": f"clicked {x},{y}"}

            elif t == "type":
                txt = action.get("content","")
                # โฟกัส target ถ้ามี
                target = action.get("target")
                if target:
                    if target["by"]=="coords":
                        x,y = target["value"]
                        self.km.mouse.click(x,y)
                    elif target["by"]=="text":
                        elem = self.km.detector.find_element_by_text(target["value"])
                        if elem:
                            x,y = self.km.detector.get_element_center(elem)
                            self.km.mouse.click(x,y)
                # พิมพ์
                self.km.keyboard.type_text(txt)
                return {"ok": True, "message": f"typed {len(txt)} chars"}

            elif t == "press":
                keys = action.get("keys", [])
                self.km.keyboard.press_keys(keys)
                return {"ok": True, "message": f"pressed {'+'.join(keys)}"}

            elif t == "scroll":
                amt = action.get("amount", 100)
                self.km.mouse.scroll(amt)
                return {"ok": True, "message": f"scrolled {amt}"}

            elif t == "move":
                target = action.get("target")
                if target["by"]=="coords":
                    x,y = target["value"]
                else:
                    elem = self.km.detector.find_element_by_text(target["value"])
                    if not elem:
                        return {"ok": False, "message":"target_not_found"}
                    x,y = self.km.detector.get_element_center(elem)
                self.km.mouse.move_to(x,y)
                return {"ok": True, "message": f"moved to {x},{y}"}

            else:
                return {"ok": False, "message":"unsupported_action_type"}

        except Exception as e:
            return {"ok": False, "message": f"executor_exception: {e}"}
