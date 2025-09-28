from core.tts_client import TTSClient

# ใช้เสียงภาษาไทย
tts = TTSClient(lang="th")

print("== Voice ที่มีในระบบ ==")
for vid, vname in tts.list_voices():
    print(f"{vid} -> {vname}")

# ทดลองพูด
tts.speak("สวัสดีครับ ยินดีที่ได้รู้จัก")
tts.speak("Hello! This is a test for text to speech.")
