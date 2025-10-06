# core/llm_client.py
# -------------------------
# LLMClient: ตัวเชื่อมต่อกับ LM Studio (รองรับ Vision/Multimodal)
# Format ที่ LM Studio ต้องการ:
# - ส่ง image เป็น data URI ภายใน content array
# - structure: {"type": "image_url", "image_url": {"url": "data:..."}}
# -------------------------

import json
import requests
from typing import List, Any, Dict, Optional

try:
    from config import LLM_SERVER_URL, LLM_MODEL, TEMPERATURE, MAX_TOKENS, LLM_TIMEOUT
except Exception:
    LLM_SERVER_URL = "http://localhost:1234/v1/chat/completions"
    LLM_MODEL = "google/gemma-3-4b"
    TEMPERATURE = 0.7
    MAX_TOKENS = 1024
    LLM_TIMEOUT = 60

class LLMClient:
    def __init__(self, server_url: str = None, model: str = None, temperature: float = None, max_tokens: int = None, timeout: int = None):
        self.server_url = server_url or LLM_SERVER_URL
        self.model = model or LLM_MODEL
        self.temperature = TEMPERATURE if temperature is None else temperature
        self.max_tokens = MAX_TOKENS if max_tokens is None else max_tokens
        self.timeout = LLM_TIMEOUT if timeout is None else timeout

    def _extract_text_from_response(self, resp_json: Dict[str, Any]) -> str:
        """ดึงข้อความจาก response ของ LM Studio"""
        try:
            if "choices" in resp_json and isinstance(resp_json["choices"], list) and len(resp_json["choices"]) > 0:
                first = resp_json["choices"][0]
                if isinstance(first, dict):
                    if "message" in first and isinstance(first["message"], dict) and "content" in first["message"]:
                        return first["message"]["content"]
                    if "text" in first:
                        return first["text"]
            if "output" in resp_json and isinstance(resp_json["output"], str):
                return resp_json["output"]
        except Exception:
            pass
        try:
            return json.dumps(resp_json, ensure_ascii=False)
        except Exception:
            return str(resp_json)

    def ask(self, text: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """ส่งข้อความแบบ text-only"""
        if history is None:
            history = []

        messages = [{"role": "system", "content": "You are a helpful assistant. Please answer in Thai when possible."}]
        messages.extend(history)
        messages.append({"role": "user", "content": text})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False
        }

        try:
            resp = requests.post(self.server_url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            return f"[LLM ERROR] ไม่สามารถเชื่อมต่อ LLM server: {e}"

        try:
            data = resp.json()
        except Exception as e:
            return f"[LLM ERROR] ไม่สามารถแปลงผลลัพธ์เป็น JSON: {e}"

        return self._extract_text_from_response(data)

    def ask_with_image(self, prompt_text: str, image_data_uri: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        ส่ง prompt + image ให้ LM Studio Vision Model
        Format ที่ LM Studio ต้องการ:
        - content เป็น array ของ objects
        - แต่ละ object มี type: "text" หรือ "image_url"
        """
        if history is None:
            history = []

        # สร้าง messages
        messages = [
            {"role": "system", "content": "You are a helpful multimodal assistant. Answer in Thai when possible."}
        ]
        messages.extend(history)
        
        # สร้าง user message แบบ multimodal
        # LM Studio ต้องการ format นี้:
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt_text
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_data_uri
                    }
                }
            ]
        }
        messages.append(user_message)

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        try:
            print(f"[LLM] 📤 ส่ง payload ไปยัง {self.server_url}")
            resp = requests.post(self.server_url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            return f"[LLM ERROR] ไม่สามารถเชื่อมต่อ LLM server: {e}\n💡 ตรวจสอบว่า LM Studio เปิดอยู่และโหลดโมเดลที่รองรับ Vision แล้ว"

        try:
            data = resp.json()
        except Exception as e:
            return f"[LLM ERROR] ไม่สามารถแปลง response เป็น JSON: {e}\nRaw: {resp.text[:200]}"

        return self._extract_text_from_response(data)

    def ask_multimodal(self, messages: List[Dict[str, Any]]) -> str:
        """ส่ง messages แบบ custom (ยืดหยุ่นสูง)"""
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False
        }
        try:
            resp = requests.post(self.server_url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            return f"[LLM ERROR] ไม่สามารถเชื่อมต่อ LLM server: {e}"

        try:
            data = resp.json()
        except Exception as e:
            return f"[LLM ERROR] ไม่สามารถแปลง response เป็น JSON: {e}"

        return self._extract_text_from_response(data)


if __name__ == "__main__":
    print("=== [LLMClient: manual test] ===")
    client = LLMClient()

    print("\n[TEST 1] Text-only query")
    reply = client.ask("สวัสดี คุณคือใครครับ?")
    print("Response:", reply)

    print("\n[TEST 2] Vision test (requires real image data URI)")
    # ทดสอบด้วย fake data URI
    fake_image = "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
    reply2 = client.ask_with_image("นี่คือภาพอะไร?", fake_image)
    print("Response:", reply2)