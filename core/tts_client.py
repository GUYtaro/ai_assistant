# core/tts_client.py
# -------------------------
# โมดูลสำหรับ Text-to-Speech (TTS)
# *** ใช้ gTTS (Google TTS) และใช้ FFmpeg (ที่ติดตั้งแล้ว) ในการเล่นเสียง ***
# -------------------------

# ต้องติดตั้ง: pip install gTTS pydub

from gtts import gTTS
import os
import tempfile
import time

# นำเข้าไลบรารีที่จำเป็นสำหรับการเล่นเสียงผ่าน FFmpeg
try:
    from pydub import AudioSegment
    # pydub จะพึ่งพา FFmpeg ที่เราติดตั้งไปแล้วในการจัดการและเล่นไฟล์
    TTS_PLAYBACK_READY = True
except ImportError:
    print("[TTS ERROR] กรุณาติดตั้งไลบรารี: pip install gTTS pydub")
    TTS_PLAYBACK_READY = False
except Exception as e:
    # ข้อผิดพลาดนี้อาจเกิดจากหา FFmpeg ไม่เจอ แม้จะติดตั้ง pydub แล้ว
    print(f"[TTS ERROR] ข้อผิดพลาดในการโหลดไลบรารีเสียง หรือ FFmpeg: {e}")
    TTS_PLAYBACK_READY = False


class TTSClient:
    def __init__(self, rate=180, volume=1.0, preferred_voice_id=None):
        """
        gTTS ใช้ภาษาไทยได้เลยโดยไม่ต้องตั้งค่า voice ID
        """
        print("[TTS Client] ใช้ gTTS: รองรับภาษาไทย (ใช้ FFmpeg เล่นเสียง)")
        self.temp_dir = tempfile.gettempdir()
        # ใช้ชื่อไฟล์ที่ไม่ซ้ำกัน
        self.temp_file = os.path.join(self.temp_dir, f"tts_output_{os.getpid()}.mp3")
        self.wav_file = os.path.join(self.temp_dir, f"tts_output_{os.getpid()}.wav")


    def _set_thai_voice_if_available(self):
        """ฟังก์ชันนี้ถูกข้ามไปเนื่องจาก gTTS จัดการภาษาอัตโนมัติ"""
        pass

    def list_voices(self):
        """
        สำหรับ gTTS จะคืนค่า voice เสมือนเพื่อแสดงว่ารองรับภาษาไทยแล้ว
        """
        return [
            ("gTTS_TH", "Google TTS - Thai (Internet Required)"),
            ("gTTS_EN", "Google TTS - English (Internet Required)")
        ]

    def speak(self, text):
        """
        แปลงข้อความเป็นไฟล์ MP3, แปลงเป็น WAV ด้วย pydub/FFmpeg, และเล่นออกลำโพง
        """
        if not text:
            return
            
        if not TTS_PLAYBACK_READY:
            print("[TTS ERROR] ไม่สามารถเล่นเสียงได้: ไลบรารี pydub ยังไม่พร้อม")
            return

        print(f"[TTS] กำลังสร้างและพูด: {text}")
        
        try:
            # 1. สร้างไฟล์ MP3 ด้วย gTTS
            is_thai = any(c >= '\u0E00' and c <= '\u0E7F' for c in text)
            lang = 'th' if is_thai else 'en'
            
            tts = gTTS(text=text, lang=lang)
            tts.save(self.temp_file)
            
            # 2. โหลดไฟล์ MP3 และแปลงเป็น AudioSegment
            audio = AudioSegment.from_mp3(self.temp_file)
            
            # 3. เล่นไฟล์เสียงโดยใช้ pydub (ซึ่งจะใช้ FFmpeg ที่ติดตั้งใน PATH)
            # เราใช้ play() ของ pydub ซึ่งจะทำการแปลงและเล่นไฟล์
            from pydub.playback import play
            play(audio)
            
            # 4. ลบไฟล์ชั่วคราวหลังเล่นเสร็จ
            os.remove(self.temp_file)
            # หากมีการสร้างไฟล์ WAV ชั่วคราว (บางระบบ) ให้ลบด้วย
            if os.path.exists(self.wav_file):
                 os.remove(self.wav_file)

        except Exception as e:
            # มักเกิดจากไม่มีการเชื่อมต่ออินเทอร์เน็ต หรือ FFmpeg มีปัญหา
            print(f"[TTS ERROR] ไม่สามารถสร้าง/เล่นเสียงได้: {e}")
            print("กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต และการติดตั้ง FFmpeg")
