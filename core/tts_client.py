# core/tts_client.py
# -------------------------
# ระบบ Text-to-Speech (TTS)
# รองรับภาษาไทย
# ✅ แก้ไขปัญหาพูดซ้ำ - ตัดข้อความในวงเล็บออก
# -------------------------

import pyttsx3
from gtts import gTTS
import tempfile
import os
import re
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
        """
        พูดข้อความด้วยเสียงไทย
        ✅ ตัดข้อความในวงเล็บและ emoji ออกก่อนพูด
        """
        if not text or text.strip() == "":
            return
        
        # ✅ ทำความสะอาดข้อความก่อนพูด
        cleaned_text = self._clean_text(text)
        
        if not cleaned_text.strip():
            return

        try:
            if self.fallback_enabled:
                # --- ใช้ Google TTS ---
                self._speak_google(cleaned_text)
            else:
                # --- ใช้เสียงของระบบ Windows ---
                self.engine.say(cleaned_text)
                self.engine.runAndWait()

        except Exception as e:
            print(f"[TTS ERROR] ระบบเสียงหลักล้มเหลว: {e}")
            print("👉 กำลังสลับไปใช้ Google TTS (สำรอง)")
            self._speak_google(cleaned_text)
    
    def _clean_text(self, text: str) -> str:
        """
        ✅ ทำความสะอาดข้อความ
        - ตัดข้อความในวงเล็บ () ออก
        - ตัดข้อความในวงเล็บเหลี่ยม [] ออก
        - ตัดข้อความในปีกกา {} ออก
        - ตัด emoji และสัญลักษณ์พิเศษออก
        - ตัดช่องว่างเกินออก
        """
        # ตัดข้อความในวงเล็บทั้งหมด
        text = re.sub(r'\([^)]*\)', '', text)  # ตัด (...)
        text = re.sub(r'\[[^\]]*\]', '', text)  # ตัด [...]
        text = re.sub(r'\{[^}]*\}', '', text)  # ตัด {...}
        
        # ตัด emoji และสัญลักษณ์พิเศษทั่วไป
        text = re.sub(r'[😊🤖📝✅❌🔍🚀💡🎤⏹️🔴⏳🎯🎨🎭🎪🎬🎮🎲🎰🎳]', '', text)
        text = re.sub(r'[👍👎👏👋🙏💪🤝🤞🤟🤘]', '', text)
        text = re.sub(r'[❤️💔💕💖💗💙💚💛💜🖤]', '', text)
        text = re.sub(r'[⭐🌟✨💫⚡🔥💥💢💯]', '', text)
        
        # ตัดสัญลักษณ์อื่นๆ ที่ไม่ต้องการ
        text = re.sub(r'[►▼▲●○■□◆◇★☆♪♫]', '', text)
        
        # ตัดช่องว่างเกิน
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text

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


# ✅ Test Mode
if __name__ == "__main__":
    tts = TTSClient(lang="th")
    
    print("\n=== ทดสอบ TTS ===\n")
    
    # ทดสอบข้อความปกติ
    print("1. ทดสอบข้อความปกติ")
    tts.speak("สวัสดีครับ ผมเป็นผู้ช่วยอัจฉริยะ")
    print("   ✅ เสร็จสิ้น\n")
    
    # ทดสอบข้อความที่มีวงเล็บ (ควรจะไม่พูดส่วนในวงเล็บ)
    print("2. ทดสอบข้อความที่มีวงเล็บ")
    print("   Input: 'สวัสดีครับ (Hello in English)'")
    tts.speak("สวัสดีครับ (Hello in English)")
    print("   ✅ ควรพูดแค่ 'สวัสดีครับ'\n")
    
    # ทดสอบข้อความที่มี emoji
    print("3. ทดสอบข้อความที่มี emoji")
    print("   Input: 'เปิดโปรแกรมสำเร็จ ✅ (Program opened successfully)'")
    tts.speak("เปิดโปรแกรมสำเร็จ ✅ (Program opened successfully)")
    print("   ✅ ควรพูดแค่ 'เปิดโปรแกรมสำเร็จ'\n")
    
    # ทดสอบข้อความที่มีทั้ง emoji และวงเล็บ
    print("4. ทดสอบข้อความแบบผู้ช่วย AI")
    print("   Input: '🤖 ผู้ช่วย: สวัสดีค่ะ! ฉันคือแบบจำลอง (I am a model)'")
    tts.speak("🤖 ผู้ช่วย: สวัสดีค่ะ! ฉันคือแบบจำลอง (I am a model)")
    print("   ✅ ควรพูดแค่ 'ผู้ช่วย: สวัสดีค่ะ! ฉันคือแบบจำลอง'\n")
    
    print("✅ ทดสอบเสร็จสิ้น")