# test_assistant.py
from services.assistant import AssistantService

if __name__ == "__main__":
    assistant = AssistantService(use_stt=False, use_tts=False)
    reply = assistant.handle_text_query("สวัสดีครับ คุณชื่ออะไร?")
    print("✅ คำตอบ:", reply)
    print("📁 ไฟล์ประวัติควรถูกสร้างในโฟลเดอร์ data/")