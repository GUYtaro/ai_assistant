# config.py
# -------------------------
# เก็บค่าการตั้งค่าเกี่ยวกับ LLM

LLM_SERVER_URL = "http://localhost:1234/v1/chat/completions"
LLM_MODEL = "google/gemma-3-4b"

# ค่า default ของการสุ่มข้อความ (temperature)
LLM_TEMPERATURE = 0.7

# จำนวน tokens สูงสุด (-1 = ไม่จำกัด ตาม LM Studio)
LLM_MAX_TOKENS = -1
