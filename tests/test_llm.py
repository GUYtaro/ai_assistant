# test_llm.py
# -------------------------
# ไฟล์นี้ใช้สำหรับ "ทดสอบการทำงานของ LLMClient"
# โดยจะส่งข้อความ (prompt) ไปที่ LLM Server ผ่าน llm_client.py
# เพื่อเช็คว่า:
#   1. การเชื่อมต่อ API ใช้งานได้
#   2. โมเดลตอบกลับมาได้จริง
#   3. System Prompt, Error Handling, และ History ทำงานถูกต้อง
# -------------------------

from core.llm_client import LLMClient   # นำเข้า class LLMClient ที่เขียนไว้ใน core/llm_client.py

# สร้าง LLMClient ขึ้นมา
# - กำหนด system_prompt ว่าเป็น "ผู้ช่วยภาษาไทย" เพื่อบังคับให้ตอบเป็นภาษาไทย
llm_client = LLMClient(
    system_prompt="คุณคือผู้ช่วย AI ที่ตอบเป็นภาษาไทย อธิบายสั้น กระชับ และเข้าใจง่าย"
)

# ข้อความที่ผู้ใช้จะถาม AI
user_prompt = "ทำไมท้องฟ้าถึงเป็นสีฟ้า อธิบายสำหรับเด็กเล็ก"

# แสดงข้อความที่ผู้ใช้ถาม (จำลองเหมือน chat UI)
print(f"\n🧠 คำถาม: {user_prompt}")

# เรียกใช้งาน LLMClient.ask() เพื่อส่งข้อความไปยัง API
# - user_prompt คือข้อความใหม่ที่เราถาม
# - history ไม่ได้ส่งไป → จะเป็น [] อัตโนมัติ
response = llm_client.ask(user_prompt)

# แสดงผลลัพธ์ที่ได้จากโมเดล
print("\n🤖 คำตอบจาก LLM:")
print("---------------------------------")
print(response)  # พิมพ์ข้อความที่ AI ตอบกลับมา
print("---------------------------------")
