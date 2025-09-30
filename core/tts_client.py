# core/tts_client.py
# -------------------------
# โมดูลสำหรับ Text-to-Speech (TTS)
# ใช้ pyttsx3 ซึ่งใช้เสียงสังเคราะห์ในระบบปฏิบัติการ (Offline 100%)
# -------------------------

import pyttsx3
import logging

# ปิด warning ของ pyttsx3 ที่อาจจะรบกวน console
logging.getLogger('pyttsx3.engine').setLevel(logging.WARNING)

class TTSClient:
    def __init__(self, rate=170, lang="th"):
        """
        rate: ความเร็วในการพูด (คำต่อนาที, ค่าปกติคือ 170)
        lang: กำหนดภาษาที่จะให้พูด (เช่น "th" = ไทย)
        """
        print("[TTS] กำลังเตรียมระบบสังเคราะห์เสียง (Offline)...")
        self.engine = None
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', rate)

            # 1. ค้นหาและตั้งค่าเสียงภาษาไทยที่เหมาะสมที่สุด
            voice = self._get_thai_voice(lang)
            if voice:
                self.engine.setProperty('voice', voice.id)
                print(f"[TTS] ใช้เสียงภาษาไทย: {voice.name} (ID: {voice.id})")
            else:
                print("[TTS WARNING] ไม่พบเสียงภาษาไทยในระบบ ใช้เสียงเริ่มต้นแทน")
        except Exception as e:
            # การเตรียมระบบ pyttsx3 ล้มเหลว มักเกิดจากไลบรารีระบบปฏิบัติการ
            print(f"[TTS ERROR] การเตรียมระบบสังเคราะห์เสียงล้มเหลว: {e}")
            print("--- 💡 ตรวจสอบว่าคุณได้ติดตั้ง pyttsx3 และ dependencies ของระบบปฏิบัติการ (เช่น espeak บน Linux) ---")


    def _get_thai_voice(self, lang="th"):
        """
        ค้นหาเสียงในระบบที่ตรงกับภาษาที่กำหนด
        """
        if not self.engine:
            return None
            
        voices = self.engine.getProperty('voices')
        
        # ตรวจสอบ voice id หรือชื่อที่มีคำว่า 'thai', 'th-th', หรือ 'pattara'
        for voice in voices:
            # .languages อาจมีหรือไม่ก็ได้
            is_thai_language = any(lang.lower() in l.lower() for l in voice.languages)
            
            if is_thai_language or lang.lower() in voice.id.lower() or 'pattara' in voice.name.lower():
                return voice
        return None

    def speak(self, text):
        """
        ฟังก์ชันแปลงข้อความเป็นเสียง แล้วเล่นออกลำโพง (Offline)
        """
        if self.engine is None:
            print("[TTS] ระบบสังเคราะห์เสียงไม่พร้อมใช้งาน")
            return
            
        try:
            self.engine.say(text)
            # runAndWait() เป็นตัวที่ทำให้โปรแกรมรอจนกว่าการพูดจะเสร็จ
            self.engine.runAndWait() 
        except Exception as e:
            print(f"[TTS ERROR] เกิดข้อผิดพลาดขณะพูด: {e}")

    def list_voices(self):
        """
        แสดงรายการ ID และชื่อของ Voice ทั้งหมดที่ติดตั้งอยู่ในระบบ
        """
        if self.engine is None:
            return []
            
        voices = self.engine.getProperty('voices')
        return [(v.id, v.name) for v in voices]

    def stop(self):
        """
        หยุดการพูดที่กำลังดำเนินอยู่
        """
        if self.engine:
            self.engine.stop()
