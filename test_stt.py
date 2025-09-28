from core.tts_client import TTSClient

tts = TTSClient(rate=170, volume=1.0)

# แสดง voices ที่มีในระบบ
voices = tts.list_voices()
print("== Voice ที่มีในระบบ ==")
for vid, vname in voices:
    print(f"{vid} -> {vname}")

# ลองให้พูด
tts.speak("สวัสดีครับ ยินดีที่ได้รู้จัก")
tts.speak("Hello! This is a test for text to speech.")
