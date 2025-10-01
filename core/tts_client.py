# core/tts_client.py
# -------------------------
# โมดูลสำหรับ Text-to-Speech (TTS)
# ใช้ pyttsx3 ซึ่งอาศัยเสียงสังเคราะห์ที่มีอยู่ในระบบปฏิบัติการ Windows
# ทำงานแบบ Offline 100% (ไม่ต้องใช้อินเทอร์เน็ต)
#
# ฟีเจอร์:
#   - เลือกเสียงภาษาไทย (ถ้ามีในระบบ เช่น Microsoft Pattara, Narisa)
#   - ถ้าไม่มีเสียงไทย → fallback ไปใช้เสียงเริ่มต้น (English)
#   - ผู้ใช้สามารถตั้งค่าความเร็ว (rate) และความดัง (volume) ได้
#   - รองรับการ list เสียงทั้งหมดที่ติดตั้งในระบบ
#   - ใช้งานง่ายผ่าน method speak(), set_rate(), set_volume(), stop()
#
# ข้อจำกัด:
#   - Windows 10/11 ค่าเริ่มต้นมักไม่มีเสียงภาษาไทย ต้องติดตั้งเพิ่ม
#   - pyttsx3 อาศัย Windows SAPI → คุณภาพเสียงขึ้นอยู่กับ voice ที่ติดตั้ง
# -------------------------

import pyttsx3
import logging

# ปิด warning ของ pyttsx3 ที่อาจรบกวน console (ไม่จำเป็น แต่ช่วยให้ log สะอาดขึ้น)
logging.getLogger('pyttsx3.engine').setLevel(logging.WARNING)


class TTSClient:
    """
    คลาสสำหรับจัดการ Text-to-Speech (TTS)
    ทำหน้าที่เป็น abstraction layer ครอบ pyttsx3
    เพื่อให้เรียกใช้งานง่ายขึ้นและมี error handling ที่ชัดเจน
    """

    def __init__(self, rate=170, volume=1.0, lang="th"):
        """
        Constructor
        ----------
        rate : int
            ความเร็วในการพูด (คำต่อนาที) ค่าเริ่มต้น = 170
        volume : float
            ความดังของเสียง (0.0 ถึง 1.0) ค่าเริ่มต้น = 1.0
        lang : str
            ภาษาเป้าหมาย เช่น "th" = ไทย, "en" = อังกฤษ
        """
        print("[TTS] กำลังเตรียมระบบสังเคราะห์เสียง (Offline)...")
        self.engine = None
        try:
            self.engine = pyttsx3.init()  # เริ่มต้น engine
            self.engine.setProperty('rate', rate)     # ตั้งค่า speed
            self.engine.setProperty('volume', volume) # ตั้งค่า volume
            
            voices = self.engine.getProperty('voices')  # ดึงรายการ voice ที่ระบบมี
            
            # ค้นหาเสียงไทย
            voice = self._get_thai_voice(lang, voices)
            
            if voice:
                # ถ้ามีเสียงไทย → ใช้เสียงนั้น
                self.engine.setProperty('voice', voice.id)
                print(f"[TTS] ใช้เสียงภาษาไทย: {voice.name} (ID: {voice.id})")
            elif voices:
                # ถ้าไม่มีเสียงไทย แต่มีเสียงอื่น → fallback ใช้เสียงแรก
                self.engine.setProperty('voice', voices[0].id)
                print(f"[TTS WARNING] ไม่พบเสียงภาษาไทยในระบบ ใช้เสียงเริ่มต้นแทน: {voices[0].name}")
                print("👉 วิธีแก้: ติดตั้งเสียงภาษาไทยใน Windows Settings > Time & Language > Language & Region > Add a language")
                print("   และอย่าลืมติ๊กเลือก Speech ด้วย")
            else:
                # กรณีไม่มีเสียงในระบบเลย
                print("[TTS CRITICAL ERROR] ไม่พบเสียงใดๆ ในระบบปฏิบัติการ")

        except Exception as e:
            # ถ้า pyttsx3 init ล้มเหลว (เช่น registry เสียหาย, OS ไม่รองรับ)
            print(f"[TTS CRITICAL ERROR] ไม่สามารถเตรียมระบบ TTS ได้: {e}")
            self.engine = None

    def _get_thai_voice(self, lang, voices):
        """
        ฟังก์ชันภายใน: ค้นหาเสียงภาษาไทยจาก voices ที่มีอยู่
        ใช้เงื่อนไขหลายแบบ เช่น:
        - voice.languages มี "th"
        - voice.id มีคำว่า "thai"
        - voice.name มีคำว่า "pattara" (Microsoft Pattara)
        
        Returns
        -------
        voice : object | None
            ถ้าพบเสียงไทย → คืนค่า voice object, ถ้าไม่พบ → คืน None
        """
        for voice in voices:
            # ตรวจสอบจาก languages (บางระบบอาจไม่มี field นี้)
            is_thai_language = False
            if hasattr(voice, 'languages') and voice.languages:
                 is_thai_language = any(lang.lower() in l.lower() for l in voice.languages)
            
            if is_thai_language or lang.lower() in voice.id.lower() or 'pattara' in voice.name.lower():
                return voice
        return None

    def speak(self, text):
        """
        แปลงข้อความเป็นเสียงพูด
        การทำงานเป็นแบบ Blocking (รอจนพูดเสร็จ)
        
        Parameters
        ----------
        text : str
            ข้อความที่ต้องการพูด
        """
        if self.engine is None:
            print("[TTS] ระบบสังเคราะห์เสียงไม่พร้อมใช้งาน")
            return
        try:
            self.engine.say(text)
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
        """หยุดการพูดปัจจุบันทันที (ใช้ในโหมด Non-blocking หรือหยุดฉุกเฉิน)"""
        if self.engine:
            self.engine.stop()
            
    def list_voices(self):
        """
        คืนค่ารายการเสียงทั้งหมดที่ติดตั้งอยู่ในระบบ
        
        Returns
        -------
        list of tuple
            [(voice_id, voice_name), ...]
        """
        if self.engine is None:
            return []
        voices = self.engine.getProperty('voices')
        return [(v.id, v.name) for v in voices]
