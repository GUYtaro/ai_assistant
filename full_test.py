# full_test.py
from services.assistant import AssistantService

assistant = AssistantService(use_stt=False, use_tts=False)

print("1️⃣ ทดสอบข้อความ")
assistant.handle_text_query("สวัสดีครับ คุณชื่ออะไร?")

print("\n2️⃣ ทดสอบหน้าจอ")
assistant.handle_screen_query("สิ่งที่เห็นในภาพคืออะไร? อธิบายสั้นๆ เป็นภาษาไทย")

print("\n✅ ตรวจสอบโฟลเดอร์ data/ — ควรเห็น chat_history.json ที่อัปเดตแล้ว!")