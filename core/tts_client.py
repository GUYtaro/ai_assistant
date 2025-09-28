# core/tts_client.py
# -------------------------
# โมดูลสำหรับ Text-to-Speech (TTS)
# ใช้ pyttsx3 ซึ่งทำงานแบบ Offline ได้
# รองรับภาษาไทย/อังกฤษ (ขึ้นกับ voice ที่ติดตั้งใน Windows)
# -------------------------

import pyttsx3

class TTSClient:
    def __init__(self, rate=180, volume=1.0, voice=None):
        """
        rate   : ความเร็วในการพูด (ค่าปกติ ~200 คำ/นาที)
        volume : ระดับเสียง (0.0 = เบาสุด, 1.0 = ดังสุด)
        voice  : เลือก voice ID (เช่น ภาษาไทย / ภาษาอังกฤษ)
        """
        self.engine = pyttsx3.init()

        # ตั้งค่าความเร็วในการพูด
        self.engine.setProperty('rate', rate)

        # ตั้งค่าระดับเสียง
        self.engine.setProperty('volume', volume)

        # ถ้ามีการเลือก voice เฉพาะ → ใช้อันนั้น
        if voice:
            self.engine.setProperty('voice', voice)

    def list_voices(self):
        """
        แสดงรายการ voice ที่มีในระบบ
        (ใช้สำหรับเลือกว่าจะใช้เสียงผู้ชาย/ผู้หญิง หรือ ภาษาไทย/อังกฤษ)
        """
        voices = self.engine.getProperty('voices')
        result = []
        for v in voices:
            result.append((v.id, v.name))
        return result

    def speak(self, text):
        """
        พูดข้อความที่ส่งเข้ามา
        """
        if not text:
            return
        print(f"[TTS] กำลังพูด: {text}")
        self.engine.say(text)
        self.engine.runAndWait()
