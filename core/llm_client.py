# core/llm_client.py
# -------------------------
# โมดูลนี้ใช้สำหรับติดต่อกับ LM Studio ผ่าน API
# โดยใช้ requests ส่งข้อความไปยังโมเดล LLM
# และดึงคำตอบกลับมา
# -------------------------

import requests
from config import LMSTUDIO_URL, MODEL_NAME

class LLMClient:
    def __init__(self, url=LMSTUDIO_URL, model=MODEL_NAME):
        # เก็บค่า URL และชื่อโมเดล
        self.url = url
        self.model = model

    def ask(self, prompt, temperature=0.7, max_tokens=256):
        """
        ส่งข้อความ (prompt) ไปยังโมเดลที่รันบน LM Studio
        แล้วคืนค่าข้อความตอบกลับจากโมเดล
        """
        # endpoint ของ LM Studio ที่ใช้ chat-completions
        endpoint = f"{self.url}/chat/completions"
        headers = {"Content-Type": "application/json"}

        # payload ที่จะส่งไปยังโมเดล
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "คุณคือผู้ช่วยที่ตอบเป็นภาษาไทย"},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,  # ค่าการสุ่ม (0 = เดาแน่นอน, 1 = สร้างสรรค์)
            "max_tokens": max_tokens     # จำกัดจำนวน token ที่โมเดลตอบ
        }

        # ส่ง request ไปยัง LM Studio
        resp = requests.post(endpoint, headers=headers, json=payload)

        # ถ้าเกิด error ให้คืนข้อความ error กลับมา
        if resp.status_code != 200:
            return f"[ERROR] {resp.status_code}: {resp.text}"

        # แปลง response ที่ได้เป็น JSON
        data = resp.json()

        # คืนค่าข้อความที่โมเดลตอบกลับ
        return data["choices"][0]["message"]["content"]
