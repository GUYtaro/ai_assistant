from core.stt_client import STTClient

# ใช้ Whisper medium ภาษาไทย
stt = STTClient(model_size="medium", language="th")

print("🎤 กำลังอัดเสียง 5 วินาที... พูดได้เลยครับ")

text = stt.listen_once(duration=5)

print("📝 คุณพูดว่า:", text)
