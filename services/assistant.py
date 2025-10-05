# services/assistant.py
# -------------------------
# โมดูลนี้เป็น "ตัวกลาง" (Service Layer) ที่ผูกการทำงานของ:
# - STTClient (ฟังเสียงจากไมค์ → ข้อความ)
# - LLMClient (ส่งข้อความ/ภาพไปยัง LLM → คำตอบ)
# - TTSClient (อ่านข้อความ → พูดออกเสียง)
# - ScreenReader (จับภาพหน้าจอ → ส่งให้ LLM วิเคราะห์)
# -------------------------

from core.llm_client import LLMClient
from core.stt_client import STTClient
from core.tts_client import TTSClient
from core.screen_reader import screenshot_data_uri

class AssistantService:
    def __init__(self, use_stt=True, use_tts=True, lang="th"):
        """
        สร้าง Assistant Service โดยเชื่อมต่อทุกโมดูลเข้าด้วยกัน
        - use_stt: เปิด/ปิดการใช้ Speech-to-Text
        - use_tts: เปิด/ปิดการใช้ Text-to-Speech
        - lang: ภาษาหลักของระบบ ("th" = ไทย)
        """
        self.llm = LLMClient()                         # สมอง
        self.stt = STTClient(model_size="medium", language=lang) if use_stt else None   # หู
        self.tts = TTSClient(lang=lang) if use_tts else None                           # ปาก

        # เก็บประวัติการสนทนา (จำบริบทการพูดคุย)
        self.history = [
            {"role": "system", "content": "คุณคือผู้ช่วย AI ที่ตอบเป็นภาษาไทยอย่างสุภาพ เป็นมิตร และอธิบายเข้าใจง่าย"}
        ]

    # -------------------------
    # โหมดข้อความ (User พิมพ์เข้ามา)
    # -------------------------
    def handle_text_query(self, user_text: str):
        """
        รับข้อความจากผู้ใช้ → ส่งไปยัง LLM → ตอบด้วยข้อความ/เสียง
        """
        if not user_text or not user_text.strip():
            return "[Assistant] ไม่พบข้อความ กรุณาลองใหม่"

        # ส่งไปยัง LLM
        reply = self.llm.ask(user_text, history=self.history)

        # บันทึกประวัติการสนทนา
        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": reply})

        # แสดงผล และพูดออกเสียง (ถ้ามี TTS)
        print(f"🤖 ผู้ช่วย: {reply}")
        if self.tts:
            self.tts.speak(reply)

        return reply

    # -------------------------
    # โหมดเสียง (User พูดเข้ามา)
    # -------------------------
    def handle_voice_query(self, duration=5):
        """
        อัดเสียงจากไมค์ (x วินาที) → แปลงเป็นข้อความ → ส่งไป LLM → ตอบ
        """
        if not self.stt:
            return "[Assistant] STT ไม่พร้อมใช้งาน"

        print(f"🎤 กำลังอัดเสียง {duration} วินาที... พูดได้เลยครับ")
        user_text = self.stt.listen_once(duration=duration)

        if not user_text or not user_text.strip():
            return "[Assistant] ไม่สามารถฟังเสียงได้ กรุณาลองใหม่"

        print(f"📝 คุณพูดว่า: {user_text}")
        return self.handle_text_query(user_text)

    # -------------------------
    # โหมดอ่านหน้าจอ (Multimodal)
    # -------------------------
    def handle_screen_query(self, user_instruction="โปรดอธิบายสิ่งที่เห็นบนหน้าจอเป็นภาษาไทยสั้นๆ"):
        """
        จับภาพหน้าจอ → ส่งภาพ + คำสั่ง ไปให้ LLM วิเคราะห์ → ตอบเป็นข้อความ/เสียง
        """
        # 1) ถ่าย screenshot และแปลงเป็น data URI
        data_uri, raw_bytes, img = screenshot_data_uri(resize_to=(1024, 768), fmt="JPEG", quality=80)

        # 2) เตรียม prompt ที่จะส่งพร้อมภาพ
        prompt = user_instruction + "\n\nหมายเหตุ: โปรดตอบเป็นภาษาไทย"

        # 3) ส่งไปยัง LLM
        reply = self.llm.ask_with_image(prompt, data_uri, history=self.history)

        # 4) บันทึกลง history
        self.history.append({"role": "user", "content": user_instruction + " [SCREENSHOT]"})
        self.history.append({"role": "assistant", "content": reply})

        # 5) แสดงผล และพูดออกเสียง (ถ้ามี TTS)
        print("=== 🖥️ คำตอบจาก LLM (ScreenReader) ===")
        print(reply)
        if self.tts:
            self.tts.speak(reply)

        return reply
