# config.py
# -------------------------
# ไฟล์นี้เก็บค่าการตั้งค่าพื้นฐาน
# เช่น URL ของ LM Studio และชื่อโมเดลที่ใช้
# -------------------------

# URL ของ LM Studio Local Server
LMSTUDIO_URL = "http://localhost:1234/v1"

# ชื่อโมเดลที่ต้องตรงกับที่ LM Studio เปิดอยู่
MODEL_NAME = "gemma-3-4b-q6_k"

# การตั้งค่า LLM (สำหรับใช้ใน llm_client.py)
# MAX_TOKENS: จำกัดความยาวสูงสุดของคำตอบ (2048 token)
MAX_TOKENS = 2048 
# TEMPERATURE: ค่าความสร้างสรรค์ของคำตอบ (0.0 = ตอบเหมือนเดิมตลอด, 1.0 = สร้างสรรค์มาก)
TEMPERATURE = 0.7 
