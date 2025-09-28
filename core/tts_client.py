# core/tts_client.py
# -------------------------
# โมดูลสำหรับ Text-to-Speech (TTS)
# ใช้ gTTS (Google Text-to-Speech) สร้างไฟล์เสียง .mp3
# แล้วใช้ ffplay (จาก ffmpeg) เล่นไฟล์เสียง
# -------------------------

import os
import tempfile
from gtts import gTTS   # ไลบรารี gTTS ใช้สร้างไฟล์เสียงจากข้อความ
import subprocess       # ใช้รันคำสั่งภายนอก (เรียก ffplay เล่นเสียง)
"" ""
class TTSClient:
    def __init__(self, lang="th", slow=False):
        """
        lang: กำหนดภาษาที่จะให้พูด (เช่น "th" = ไทย, "en" = อังกฤษ)
        slow: ถ้า True จะพูดช้าลง
        """
        self.lang = lang
        self.slow = slow

    def speak(self, text):
        """
        ฟังก์ชันแปลงข้อความเป็นเสียง แล้วเล่นออกลำโพง
        """
        try:
            # สร้างไฟล์ชั่วคราว (.mp3)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
                # ใช้ gTTS สร้างไฟล์เสียงจากข้อความ
                tts = gTTS(text=text, lang=self.lang, slow=self.slow)
                tts.save(tmpfile.name)  # บันทึกไฟล์เสียงลงไฟล์ชั่วคราว
                tmpfile.close()

                # ใช้ ffplay (จาก ffmpeg) เล่นไฟล์เสียง
                # -nodisp   : ไม่เปิดหน้าต่างวิดีโอ
                # -autoexit : เล่นจบแล้วออกทันที
                subprocess.run(
                    ["ffplay", "-nodisp", "-autoexit", tmpfile.name],
                    stdout=subprocess.DEVNULL,   # ซ่อน output ของ ffplay
                    stderr=subprocess.DEVNULL
                )

                # ลบไฟล์ชั่วคราวทิ้ง
                os.remove(tmpfile.name)

        except Exception as e:
            # ถ้ามี error ให้พิมพ์ออกมา
            print(f"[TTS ERROR] {e}")

    def list_voices(self):
        """
        ฟังก์ชันจำลอง (mock) สำหรับ list voices
        จริง ๆ gTTS ไม่รองรับ voice หลายแบบ → return เฉพาะ th/en
        """
        return [
            ("gTTS_TH", "Google TTS - Thai (Internet Required)"),
            ("gTTS_EN", "Google TTS - English (Internet Required)")
        ]
