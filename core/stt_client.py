# core/stt_client.py
# -------------------------\
# โมดูลสำหรับแปลงเสียงจากไมโครโฟนเป็นข้อความ (Speech-to-Text)
# ใช้ Whisper (tiny/base/medium/large) + sounddevice
# -------------------------\

import sounddevice as sd
import soundfile as sf
import whisper
import tempfile
import os

class STTClient:
    def __init__(self, model_size="tiny", language="th"):
        """
        model_size: ขนาดโมเดล whisper (tiny, base, small, medium, large)
        language: กำหนดภาษา (ค่าเริ่มต้น = "th" ภาษาไทย)
        """
        # ปรับปรุงการโหลดโมเดลให้สมบูรณ์ขึ้น
        print(f"[STT] กำลังโหลด Whisper model: {model_size} (อาจใช้เวลาถ้าเป็นครั้งแรก)")
        try:
            self.model = whisper.load_model(model_size)
        except Exception as e:
            print(f"[STT ERROR] ไม่สามารถโหลดโมเดล {model_size} ได้: {e}")
            print("กรุณาตรวจสอบการติดตั้ง Whisper และไลบรารีที่เกี่ยวข้อง")
            self.model = None

        self.language = language

    def listen_once(self, duration=5, samplerate=16000):
        """
        อัดเสียงจากไมค์ (default 5 วินาที) แล้วแปลงเป็นข้อความ

        Returns:
            str: ข้อความที่ถอดเสียงได้ หรือ None หากเกิดข้อผิดพลาด
        """
        if not self.model:
            return None
        
        # ใช้ tempfile.mkstemp() แทน เพื่อให้การจัดการไฟล์ชั่วคราวปลอดภัยขึ้น
        fd, filename = tempfile.mkstemp(suffix=".wav")
        os.close(fd) # ปิด file descriptor ที่ถูกเปิดโดย mkstemp

        try:
            print(f"[STT] เริ่มอัดเสียง {duration} วินาที ...")
            # อัดเสียงจากไมค์
            recording = sd.rec(int(duration * samplerate), samplerate=samplerate,
                               channels=1, dtype='int16')
            sd.wait() # รอจนกว่าการอัดเสียงจะเสร็จสิ้น
            sf.write(filename, recording, samplerate)
            print("[STT] อัดเสียงเสร็จสิ้น กำลังแปลงเป็นข้อความ...")

            # ส่งไปให้ Whisper แปลงเป็นข้อความ
            result = self.model.transcribe(filename, language=self.language, fp16=False) # ใช้ fp16=False เพื่อให้ใช้งานได้ง่ายขึ้นบน CPU ส่วนใหญ่
            
            return result.get('text', '').strip()

        except Exception as e:
            # ใช้ Exception Handling ที่ดีขึ้น
            if 'No input device' in str(e):
                 print(f"[STT ERROR] ไม่พบไมโครโฟน: {e}")
            else:
                 print(f"[STT ERROR] เกิดข้อผิดพลาดในการอัด/ถอดเสียง: {e}")
            return None
        finally:
            # ตรวจสอบและลบไฟล์ชั่วคราวทุกครั้ง
            if os.path.exists(filename):
                os.remove(filename)
