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
    def __init__(self, rate=170, volume=1.0, lang="th"):
        """
        rate: ความเร็วในการพูด (คำต่อนาที, ค่าปกติคือ 170)
        volume: ความดังของเสียง (0.0 ถึง 1.0, ค่าปกติคือ 1.0)
        lang: กำหนดภาษาที่จะให้พูด (เช่น "th" = ไทย)
        """
        print("[TTS] กำลังเตรียมระบบสังเคราะห์เสียง (Offline)...")
        self.engine = None
        try:
            self.engine = pyttsx3.init()
            # ตั้งค่าเริ่มต้น
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            
            voices = self.engine.getProperty('voices')
            
            # 1. ค้นหาและตั้งค่าเสียงภาษาไทยที่เหมาะสมที่สุด
            voice = self._get_thai_voice(lang, voices)
            
            if voice:
                self.engine.setProperty('voice', voice.id)
                print(f"[TTS] ใช้เสียงภาษาไทย: {voice.name} (ID: {voice.id})")
            elif voices:
                # 2. ถ้าไม่พบเสียงไทย ให้ใช้เสียงแรกที่พบแทน (เพื่อให้ยังคงมีเสียงพูดได้)
                self.engine.setProperty('voice', voices[0].id)
                print(f"[TTS WARNING] ไม่พบเสียงภาษาไทยในระบบ ใช้เสียงเริ่มต้นแทน: {voices[0].name}")
            else:
                print("[TTS CRITICAL ERROR] ไม่พบเสียงใดๆ ในระบบปฏิบัติการ")

        except Exception as e:
            # การเตรียมระบบ pyttsx3 ล้มเหลว มักเกิดจากปัญหาการติดตั้ง OS
            print(f"[TTS CRITICAL ERROR] ไม่สามารถเตรียมระบบ TTS ได้: {e}")
            self.engine = None

    def _get_thai_voice(self, lang, voices):
        """
        ค้นหาเสียงภาษาไทยที่เหมาะสมที่สุด
        """
        # ตรวจสอบ voice id หรือชื่อที่มีคำว่า 'thai', 'th-th', หรือ 'pattara'
        for voice in voices:
            # .languages อาจมีหรือไม่ก็ได้
            is_thai_language = False
            if hasattr(voice, 'languages') and voice.languages:
                 is_thai_language = any(lang.lower() in l.lower() for l in voice.languages)
            
            # ใช้เงื่อนไขที่ครอบคลุม: ภาษาตรง หรือ ID/ชื่อ มีคำว่า 'thai'/'pattara'
            if is_thai_language or lang.lower() in voice.id.lower() or 'pattara' in voice.name.lower():
                return voice
        return None

    def speak(self, text):
        """
        ฟังก์ชันแปลงข้อความเป็นเสียง แล้วเล่นออกลำโพง (Offline)
        *ทำงานแบบ Blocking: จะรอจนกว่าการพูดจะเสร็จ*
        """
        if self.engine is None:
            print("[TTS] ระบบสังเคราะห์เสียงไม่พร้อมใช้งาน")
            return
            
        try:
            self.engine.say(text)
            # runAndWait() เป็นตัวที่ทำให้โปรแกรมรอจนกว่าการพูดจะเสร็จ (Blocking)
            self.engine.runAndWait() 
        except Exception as e:
            print(f"[TTS ERROR] เกิดข้อผิดพลาดขณะพูด: {e}")

    def set_rate(self, rate: int):
        """กำหนดความเร็วในการพูด (คำต่อนาที)"""
        if self.engine:
            self.engine.setProperty('rate', rate)

    def set_volume(self, volume: float):
        """กำหนดความดังของเสียง (0.0 ถึง 1.0)"""
        if self.engine:
            self.engine.setProperty('volume', volume)

    def stop(self):
        """หยุดการพูดปัจจุบันทันที (ใช้สำหรับโหมด Non-blocking ในอนาคต)"""
        if self.engine:
            self.engine.stop()
            
    def list_voices(self):
        """
        แสดงรายการ ID และชื่อของ Voice ทั้งหมดที่ติดตั้งอยู่ในระบบ
        """
        if self.engine is None:
            return []
            
        voices = self.engine.getProperty('voices')
        return [(v.id, v.name) for v in voices]
