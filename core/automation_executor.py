# core/automation_executor.py
# -------------------------
# รับ action JSON แล้วสั่งให้ KeyboardMouseController ทำงาน
# มี safety check และ confirm flow (ใช้ TTS/STT)
# -------------------------

import time
from typing import Dict, Any
from core.keyboard_mouse_controller import KeyboardMouseController
from core.tts_client import TTSClient
from core.stt_client import STTClient
from core.app_launcher import AppLauncher


class AutomationExecutor:
    def __init__(self, km_controller: KeyboardMouseController = None, monitor=1):
        """ตัวจัดการคำสั่ง Automation ทั้งหมด"""
        self.km = km_controller or KeyboardMouseController(monitor=monitor)
        self.tts = TTSClient(lang="th")
        self.stt = STTClient(model_size="small", language="th")
        self.launcher = AppLauncher()  # ✅ ระบบเปิดโปรแกรม

    def _ask_confirm(self, prompt_text: str, timeout=6) -> bool:
        """ถามผู้ใช้เพื่อยืนยันคำสั่งก่อนทำงาน"""
        self.tts.speak(prompt_text + " พูดว่า 'ใช่' เพื่อยืนยัน หรือ 'ไม่' เพื่อยกเลิก")
        try:
            reply = self.stt.listen_once(duration=4)
            if not reply:
                return False
            r = reply.strip().lower()
            return any(w in r for w in ["ใช่", "ยืนยัน", "yes", "ok", "โอเค"])
        except Exception:
            return False

    def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        รับ action JSON จาก LLM แล้วสั่งให้ระบบ Automation ทำงาน
        เช่น {"type":"click","target":{"by":"text","value":"File"}}
        """
        try:
            # multi-step
            if action.get("type") == "multi":
                results = []
                for step in action.get("steps", []):
                    res = self.execute(step)
                    results.append(res)
                    if not res.get("ok", False):
                        return {"ok": False, "message": "step_failed", "details": results}
                return {"ok": True, "message": "multi_steps_done", "details": results}

            # ถ้าต้องยืนยัน
            if action.get("confirm", False):
                ok = self._ask_confirm("คำสั่งนี้ต้องยืนยันก่อน ทำเลยหรือไม่")
                if not ok:
                    return {"ok": False, "message": "cancelled_by_user"}

            t = action.get("type")

            # ---------------------- Click ----------------------
            if t == "click":
                target = action.get("target")
                if not target:
                    return {"ok": False, "message": "missing_target"}
                if target["by"] == "coords":
                    x, y = target["value"]
                elif target["by"] == "text":
                    element = self.km.detector.find_element_by_text(target["value"])
                    if not element:
                        return {"ok": False, "message": "target_not_found"}
                    x, y = self.km.detector.get_element_center(element)
                else:
                    return {"ok": False, "message": "unknown_target_type"}
                self.km.mouse.click(x, y, button=action.get("button", "left"))
                time.sleep(0.2)
                return {"ok": True, "message": f"clicked {x},{y}"}

            # ---------------------- Type ----------------------
            elif t == "type":
                txt = action.get("content", "")
                target = action.get("target")
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

            # ---------------------- Press Keys ----------------------
            elif t == "press":
                keys = action.get("keys", [])
                self.km.keyboard.press_keys(keys)
                return {"ok": True, "message": f"pressed {'+'.join(keys)}"}

            # ---------------------- Scroll ----------------------
            elif t == "scroll":
                amt = action.get("amount", 100)
                self.km.mouse.scroll(amt)
                return {"ok": True, "message": f"scrolled {amt}"}

            # ---------------------- Move ----------------------
            elif t == "move":
                target = action.get("target")
                if not target:
                    return {"ok": False, "message": "missing_target"}
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

            # ---------------------- Launch App / URL ----------------------
            elif t == "launch":
                app = action.get("app", "")
                url = action.get("url", None)
                self.tts.speak(f"กำลังเปิด {app}")
                if url:
                    result = self.launcher.open_url(url, app)
                else:
                    result = self.launcher.launch(app)
                return {"ok": result["ok"], "message": result["message"]}

            # ---------------------- Unsupported ----------------------
            else:
                return {"ok": False, "message": "unsupported_action_type"}

        except Exception as e:
            return {"ok": False, "message": f"executor_exception: {e}"}
