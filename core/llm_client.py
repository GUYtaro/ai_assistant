# core/llm_client.py
# -------------------------
# โมดูลนี้ใช้สำหรับติดต่อกับ LLM Server (เช่น LM Studio หรือ OpenAI API ที่โฮสต์เอง)
# โดยใช้ requests ส่งข้อความไปยังโมเดล LLM พร้อมรองรับประวัติการสนทนา (history)
# จุดเด่น:
#   - มี System Prompt เพื่อควบคุมบุคลิก/บทบาทของ AI
#   - ตรวจสอบโครงสร้าง history ป้องกัน format error
#   - มี Error Handling ครอบคลุม เช่น ต่อ server ไม่ติด, response เพี้ยน
#   - user friendly: ข้อความ error อ่านง่าย, มีคำแนะนำ
# -------------------------

import requests
from config import (
    LLM_SERVER_URL,   # URL ของ LLM Server เช่น "http://localhost:1234/v1/chat/completions"
    LLM_MODEL,        # ชื่อโมเดล เช่น "google/gemma-3-4b"
    LLM_TEMPERATURE,  # ค่าการสุ่ม (0=คาดเดาแม่น, 1=สร้างสรรค์)
    LLM_MAX_TOKENS,   # จำนวน token สูงสุดที่ตอบกลับได้ (-1 = ไม่จำกัด)
)

class LLMClient:
    def __init__(self, server_url=LLM_SERVER_URL, model=LLM_MODEL, system_prompt=None):
        """
        Constructor สำหรับ LLMClient
        - server_url    : URL ที่ใช้เรียก API ของ LLM
        - model         : โมเดลที่จะใช้งาน
        - system_prompt : system message (กำหนดบุคลิก, บทบาทของ AI)
        """
        self.server_url = server_url
        self.model = model
        # ถ้าไม่ได้ส่ง system_prompt มา → ใช้ default ว่าเป็น assistant ภาษาไทย
        self.system_prompt = system_prompt or "You are a helpful assistant. Please answer in Thai when possible."

    def _validate_history(self, history):
        """
        ตรวจสอบว่า history ถูกต้องหรือไม่
        - ต้องเป็น list
        - แต่ละ element ต้องเป็น dict
        - dict ต้องมี key: role, content
        """
        if not isinstance(history, list):
            raise ValueError("❌ History ต้องเป็น list เช่น [{'role': 'user', 'content': 'ข้อความ'}]")

        for i, msg in enumerate(history):
            if not isinstance(msg, dict):
                raise ValueError(f"❌ history[{i}] ต้องเป็น dict เช่น {{'role': 'user', 'content': 'ข้อความ'}}")
            if "role" not in msg or "content" not in msg:
                raise ValueError(f"❌ history[{i}] ไม่มี key 'role' หรือ 'content'")

    def ask(self, prompt, history=None, temperature=LLM_TEMPERATURE, max_tokens=LLM_MAX_TOKENS):
        """
        ฟังก์ชันหลัก → ใช้ส่งข้อความไปยัง LLM Server
        - prompt   : ข้อความใหม่ที่ user ป้อน
        - history  : list ของการสนทนาที่ผ่านมา
        - temperature : ระดับความสร้างสรรค์ของโมเดล
        - max_tokens  : จำนวน token ที่อนุญาตให้ตอบกลับ
        """

        # ถ้าไม่มี history ส่งเข้ามา → กำหนดให้เป็น list ว่าง
        if history is None:
            history = []

        # ตรวจสอบ history format
        try:
            self._validate_history(history)
        except ValueError as e:
            # ถ้า format ผิด → คืนค่า error message (ไม่ทำให้โปรแกรม crash)
            return f"[LLMClient Error] {e}"

        # สร้าง payload ของข้อความที่จะส่งไปยัง API
        # เริ่มด้วย system prompt เพื่อควบคุมบุคลิก
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(history)  # เติมประวัติการสนทนาเก่า
        messages.append({"role": "user", "content": prompt})  # เพิ่มข้อความใหม่

        # เตรียมข้อมูลที่จะส่งไป API
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,  # stream = False → รอคำตอบทีเดียว
        }

        # ---------------------
        # เริ่มการเชื่อมต่อ API
        # ---------------------
        try:
            response = requests.post(self.server_url, json=payload, timeout=30)
        except requests.exceptions.RequestException as e:
            # ถ้าเชื่อมต่อไม่ได้ เช่น server ไม่เปิด
            return f"❌ ไม่สามารถเชื่อมต่อ LLM Server ได้: {e}"

        # ตรวจสอบ HTTP status code (ถ้าไม่ใช่ 200 → error)
        if response.status_code != 200:
            return f"❌ LLM API error {response.status_code}: {response.text}"

        # แปลง response เป็น JSON
        try:
            data = response.json()
        except Exception:
            return "❌ ไม่สามารถแปลง response จากเซิร์ฟเวอร์เป็น JSON ได้"

        # ดึงข้อความออกจาก response
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return f"❌ Response จาก LLM ไม่ถูกต้อง: {data}"
