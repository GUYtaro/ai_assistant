from core.stt_client import STTClient

# สร้าง STTClient ใช้โมเดล Whisper (tiny) ภาษาไทย
stt = STTClient(model_size="tiny", language="th")

print("🎤 กำลังอัดเสียง 5 วินาที... พูดได้เลยครับ")

# อัดเสียงแล้วแปลงเป็นข้อความ
text = stt.listen_once(duration=5)

print("📝 คุณพูดว่า:", text)
