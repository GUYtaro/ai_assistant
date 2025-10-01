# services/assistant.py
# -------------------------
# โมดูลนี้ทำหน้าที่เป็น "ตัวกลาง" (Orchestrator) 
# รวม LLM (ถามตอบ) + STT (ฟังเสียง) + TTS (ตอบกลับด้วยเสียง) + Actions (keyboard/mouse/screen reader)
# โดยใช้ class AssistantService เป็นตัวจัดการ
# -------------------------

from core.llm_client import LLMClient
from core.stt_client import STTClient
from core.tts_client import TTSClient
from core.keyboard_mouse import KeyboardMouse
from core.screen_reader import ScreenReader
from config import ACTION_REQUIRE_CONFIRM

class AssistantService:
    """
    AssistantService = ผู้ช่วยหลัก
    รวมความสามารถต่าง ๆ:
    - ฟังเสียงผู้ใช้ (STT)
    - เข้าใจข้อความ/คำสั่ง ด้วย LLM
    - วางแผน Action Plan
    - ยืนยัน (confirm) ก่อนลงมือทำ
    - ทำงานจริง เช่น พิมพ์, คลิก, อ่านจอ
    - พูดตอบกลับ (TTS)
    """

    def __init__(self):
        # สร้าง instances ของ client/service ที่ต้องใช้
        self.llm = LLMClient()
        self.stt = STTClient(language="th")
        self.tts = TTSClient(lang="th")
        self.kb = KeyboardMouse()
        self.screen = ScreenReader()
        self.history = []  # เก็บประวัติการสนทนา (list ของ dict)

    def listen_and_understand(self):
        """
        ฟังเสียงจากไมค์ → แปลงเป็นข้อความ → ส่งไปยัง LLM
        """
        print("[Assistant] 🎤 กำลังฟัง...")
        user_text = self.stt.listen_once(duration=5)
        if not user_text:
            return None

        # เก็บไว้ใน history
        self.history.append({"role": "user", "content": user_text})

        # ให้ LLM ตอบ
        response = self.llm.ask(user_text, self.history)

        # เก็บ history
        self.history.append({"role": "assistant", "content": response})
        return response

    def execute_action(self, action: str):
        """
        รัน Action ที่ได้จาก LLM เช่น:
        - type("ข้อความ")
        - press("enter")
        - click(x, y)
        - read_screen()
        """
        try:
            if action.startswith("type"):
                _, text = action.split(" ", 1)
                self.kb.type_text(text)
            elif action.startswith("press"):
                _, key = action.split(" ", 1)
                self.kb.press_key(key)
            elif action.startswith("click"):
                _, x, y = action.split(" ")
                self.kb.click(int(x), int(y))
            elif action.startswith("read_screen"):
                return self.screen.read_screen()
            else:
                print(f"[Assistant] ❓ ไม่รู้จัก action: {action}")
        except Exception as e:
            print(f"[Assistant ERROR] ทำ action ไม่สำเร็จ: {e}")

    def respond(self, text: str):
        """
        พูดข้อความตอบกลับผู้ใช้
        """
        print(f"[Assistant] 🤖 พูด: {text}")
        self.tts.speak(text)

    def interactive_loop(self):
        """
        Loop หลัก:
        1. ฟังเสียงผู้ใช้
        2. เข้าใจ → ได้คำตอบ + Action Plan
        3. ถ้ามี Action → ขอ confirm
        4. ทำ Action
        5. พูดตอบกลับ
        """
        while True:
            response = self.listen_and_understand()
            if not response:
                continue

            # ตรวจสอบว่า LLM แนะนำ action หรือไม่
            if "[ACTION]" in response:
                action = response.split("[ACTION]")[-1].strip()

                if ACTION_REQUIRE_CONFIRM:
                    confirm = input(f"[Assistant] ยืนยันจะทำ action '{action}' ? (y/n): ")
                    if confirm.lower() != "y":
                        continue

                result = self.execute_action(action)
                if result:
                    self.respond(result)
            else:
                self.respond(response)
