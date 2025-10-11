# config.py
# -------------------------
# เก็บค่าการตั้งค่าเกี่ยวกับ LLM

LLM_SERVER_URL = "http://localhost:1234/v1/chat/completions"
LLM_MODEL = "google/gemma-3-4b"

# ค่า default ของการสุ่มข้อความ (temperature)
LLM_TEMPERATURE = 0.7

# จำนวน tokens สูงสุด (-1 = ไม่จำกัด ตาม LM Studio)
LLM_MAX_TOKENS = -1

# เปิด/ปิดการให้ AI ควบคุม Keyboard/Mouse จริง ๆ
ALLOW_INPUT_CONTROL = False       # False = โหมดปลอดภัย (จำลอง/print) / True = อนุญาตให้รันจริง

# ถ้า ALLOW_INPUT_CONTROL == True และนี่เป็นการกระทำจริง ๆ จะยังคง require confirm ถ้าตั้งเป็น True
ACTION_REQUIRE_CONFIRM = True

# พาธไปยัง tesseract.exe (ถ้าติดตั้งไว้ที่อื่นให้แก้ตามจริง)
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 🔥 Hybrid Mode Settings
HYBRID_MODE_ENABLED = True  # เปิดใช้งาน Hybrid Mode
RULE_BASED_CONFIDENCE_THRESHOLD = 0.8  # ความมั่นใจขั้นต่ำสำหรับ Rule-based