# core/stt_client.py
# -------------------------
# โมดูลสำหรับแปลงเสียงจากไมโครโฟนเป็นข้อความ (Speech-to-Text)
# ใช้ Whisper (tiny/base) + sounddevice
# -------------------------

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
        print(f"[STT] กำลังโหลด Whisper model: {model_size}")
        self.model = whisper.load_model(model_size)
        self.language = language

    def listen_once(self, duration=5, samplerate=16000):
        """
        อัดเสียงจากไมค์ (default 5 วินาที) แล้วแปลงเป็นข้อความ
        """
        print(f"[STT] เริ่มอัดเสียง {duration} วินาที ...")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            filename = tmp.name

        try:
            # อัดเสียงจากไมค์
            recording = sd.rec(int(duration * samplerate), samplerate=samplerate,
                               channels=1, dtype='int16')
            sd.wait()
            sf.write(filename, recording, samplerate)
            print("[STT] อัดเสียงเสร็จสิ้น")

            # ส่งไปให้ Whisper แปลงเป็นข้อความ
            result = self.model.transcribe(filename, language=self.language)
            text = result.get("text", "").strip()
            print("[STT] ข้อความที่ได้:", text)
            return text

        finally:
            if os.path.exists(filename):
                os.remove(filename)
