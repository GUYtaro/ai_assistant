# services/assistant.py
# -------------------------
# โมดูลนี้เป็น "ตัวกลาง" (Service Layer) ที่ผูกการทำงานของ:
# - STTClient (ฟังเสียงจากไมค์ → ข้อความ)
# - LLMClient (ส่งข้อความ/ภาพไปยัง LLM → คำตอบ)
# - TTSClient (อ่านข้อความ → พูดออกเสียง)
# - ScreenReader (จับภาพหน้าจอ → ส่งให้ LLM วิเคราะห์)
# -------------------------

import sys
from pathlib import Path

# เพิ่ม root ของโปรเจกต์ลงใน Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# ตอนนี้ import จาก core ได้แล้ว!
from core.llm_client import LLMClient
from core.stt_client import STTClient
from core.tts_client import TTSClient
from core.screen_reader import screenshot_data_uri

import json


class AssistantService:
    def __init__(self, use_stt=True, use_tts=True, lang="th", history_file="data/chat_history.json"):
        """
        - history_file: ที่อยู่ไฟล์ JSON สำหรับบันทึกประวัติ
        """
        self.history_file = Path(history_file)
        self._ensure_history_dir()

        # โหลดประวัติเดิม ถ้ามี
        self.history = self._load_history()
        
        # ถ้าไม่มีประวัติ (หรือไฟล์ว่าง) → ใช้ค่าเริ่มต้น
        if not self.history:
            self.history = [
                {"role": "system", "content": "คุณคือผู้ช่วย AI ที่ตอบเป็นภาษาไทยอย่างสุภาพ เป็นมิตร และอธิบายเข้าใจง่าย"}
            ]

        # โมดูลอื่นๆ
        self.llm = LLMClient()
        self.stt = STTClient(model_size="medium", language=lang) if use_stt else None
        self.tts = TTSClient(lang=lang) if use_tts else None

    def _ensure_history_dir(self):
        """สร้างโฟลเดอร์ data/ ถ้ายังไม่มี"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)

    def _load_history(self):
        """โหลดประวัติจากไฟล์ JSON"""
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # ตรวจสอบว่าเป็น list ของ dict ที่มี role/content
                    if isinstance(data, list) and all(
                        isinstance(msg, dict) and "role" in msg and "content" in msg
                        for msg in data
                    ):
                        return data
            except (json.JSONDecodeError, IOError) as e:
                print(f"[⚠️] โหลดประวัติไม่ได้: {e} — ใช้ประวัติใหม่")
        return []

    def _save_history(self):
        """บันทึกประวัติลงไฟล์ JSON"""
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"[❌] บันทึกประวัติไม่ได้: {e}")

    # -------------------------
    # แก้ไขเมธอดให้บันทึกหลังตอบ
    # -------------------------
    def handle_text_query(self, user_text: str):
        if not user_text or not user_text.strip():
            return "[Assistant] ไม่พบข้อความ กรุณาลองใหม่"

        reply = self.llm.ask(user_text, history=self.history)

        # อัปเดตประวัติ
        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": reply})

        # 🔥 บันทึกทันทีหลังอัปเดต!
        self._save_history()

        print(f"🤖 ผู้ช่วย: {reply}")
        if self.tts:
            self.tts.speak(reply)

        return reply

    def handle_voice_query(self, duration=5):
        if not self.stt:
            return "[Assistant] STT ไม่พร้อมใช้งาน"

        print(f"🎤 กำลังอัดเสียง {duration} วินาที... พูดได้เลยครับ")
        user_text = self.stt.listen_once(duration=duration)

        if not user_text or not user_text.strip():
            return "[Assistant] ไม่สามารถฟังเสียงได้ กรุณาลองใหม่"

        print(f"📝 คุณพูดว่า: {user_text}")
        return self.handle_text_query(user_text)  # ← จะบันทึกอัตโนมัติ

    def handle_screen_query(self, user_instruction="โปรดอธิบายสิ่งที่เห็นบนหน้าจอเป็นภาษาไทยสั้นๆ"):
        data_uri, _, _ = screenshot_data_uri(resize_to=(1024, 768), fmt="JPEG", quality=80)
        prompt = user_instruction + "\n\nหมายเหตุ: โปรดตอบเป็นภาษาไทย"
        reply = self.llm.ask_with_image(prompt, data_uri, history=self.history)

        # อัปเดตประวัติ
        self.history.append({"role": "user", "content": user_instruction + " [SCREENSHOT]"})
        self.history.append({"role": "assistant", "content": reply})

        # 🔥 บันทึกทันที!
        self._save_history()

        print("=== 🖥️ คำตอบจาก LLM (ScreenReader) ===")
        print(reply)
        if self.tts:
            self.tts.speak(reply)

        return reply