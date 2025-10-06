# core/tts_client.py
# -------------------------
# ระบบ Text-to-Speech (TTS)
# รองรับภาษาไทย
# ถ้าเสียงของ Windows ไม่มี → ใช้ gTTS ของ Google แทน
# -------------------------

import pyttsx3
from gtts import gTTS
import tempfile
import os
import platform
from playsound import playsound


class TTSClient:
    def __init__(self, lang="th"):
        self.lang = lang
        self.engine = pyttsx3.init()
        self.voice_available = False
        self.fallback_enabled = False

        # ลองหาว่าในระบบมีเสียงภาษาไทยไหม
        voices = self.engine.getProperty("voices")
        for voice in voices:
            if "th" in voice.languages or "Thai" in voice.name:
                self.engine.setProperty("voice", voice.id)
                self.voice_available = True
                break

        if not self.voice_available:
            print("[TTS WARNING] ❌ ไม่พบเสียงภาษาไทยในระบบ Windows")
            print("👉 ระบบจะใช้เสียงสำรองจาก Google TTS แทน (ต้องต่ออินเทอร์เน็ต)")
            self.fallback_enabled = True
        else:
            print("[TTS] ✅ พบเสียงภาษาไทยในระบบ พร้อมใช้งาน")

        # ตั้งค่าเสียงและความเร็ว
        self.engine.setProperty("rate", 180)
        self.engine.setProperty("volume", 1.0)

    def speak(self, text: str):
        """พูดข้อความด้วยเสียงไทย"""
        if not text or text.strip() == "":
            return

        try:
            if self.fallback_enabled:
                # --- ใช้ Google TTS ---
                self._speak_google(text)
            else:
                # --- ใช้เสียงของระบบ Windows ---
                self.engine.say(text)
                self.engine.runAndWait()

        except Exception as e:
            print(f"[TTS ERROR] ระบบเสียงหลักล้มเหลว: {e}")
            print("👉 กำลังสลับไปใช้ Google TTS (สำรอง)")
            self._speak_google(text)

    def _speak_google(self, text):
        """ระบบเสียงสำรองจาก Google"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tts = gTTS(text=text, lang="th")
                tts.save(tmp_file.name)
                tmp_path = tmp_file.name

            playsound(tmp_path)
            os.remove(tmp_path)
        except Exception as e:
            print(f"[TTS ERROR] Google TTS ใช้งานไม่ได้: {e}")
            print("⚠️ ไม่สามารถสร้างเสียงพูดได้ในขณะนี้")

