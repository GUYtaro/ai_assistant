# core/llm_client.py
# -------------------------
# LLMClient: ตัวเชื่อมต่อกับ LLM server (เช่น LM Studio / Ollama / custom HTTP API)
# - มีเมธอดหลัก ๆ:
#   - ask(text, history)          : ส่งข้อความ (chat) แล้วรับข้อความตอบ
#   - ask_with_image(prompt, image_data_uri, history): ส่ง prompt + image (data URI) ให้ multimodal model
#   - ask_multimodal(messages)     : ส่ง payload แบบ multimodal/custom (ให้ความยืดหยุ่น)
# -------------------------

import json
import requests
from typing import List, Any, Dict, Optional

# ดึงค่าตั้งค่าจาก config.py (ต้องมีไฟล์ config.py ใน root project)
try:
    from config import LLM_SERVER_URL, LLM_MODEL, TEMPERATURE, MAX_TOKENS, LLM_TIMEOUT
except Exception:
    # ค่าดีฟอลต์ถ้าไม่พบ config
    LLM_SERVER_URL = "http://localhost:1234/v1/chat/completions"
    LLM_MODEL = "google/gemma-3-4b"
    TEMPERATURE = 0.2
    MAX_TOKENS = 1024
    LLM_TIMEOUT = 60

class LLMClient:
    """
    LLMClient สำหรับเรียก HTTP API ของ LLM Server
    - รองรับ chat แบบข้อความ และ multimodal (image embedded as data URI)
    - ควรรันโปรเจกต์จาก root เพื่อให้ import config/core ถูกต้อง
    """

    def __init__(self, server_url: str = None, model: str = None, temperature: float = None, max_tokens: int = None, timeout: int = None):
        self.server_url = server_url or LLM_SERVER_URL
        self.model = model or LLM_MODEL
        self.temperature = TEMPERATURE if temperature is None else temperature
        self.max_tokens = MAX_TOKENS if max_tokens is None else max_tokens
        self.timeout = LLM_TIMEOUT if timeout is None else timeout

    # ------------------------
    # Helper: parse response
    # ------------------------
    def _extract_text_from_response(self, resp_json: Dict[str, Any]) -> str:
        """
        พยายามดึงข้อความจาก response ของ server ให้หลากหลายรูปแบบ
        - รองรับ OpenAI/Chat-like: choices[0].message.content
        - รองรับโครงสร้างอื่น ๆ โดยคืน raw json ถ้าไม่พบ text
        """
        try:
            # ตัวอย่าง: OpenAI-like
            if "choices" in resp_json and isinstance(resp_json["choices"], list) and len(resp_json["choices"]) > 0:
                # หลายระบบเก็บข้อความที่ choices[0].message.content
                first = resp_json["choices"][0]
                # หลาย implementation: first["message"]["content"] or first["text"]
                if isinstance(first, dict):
                    if "message" in first and isinstance(first["message"], dict) and "content" in first["message"]:
                        return first["message"]["content"]
                    if "text" in first:
                        return first["text"]
            # บาง API ก็คืน {"output": "text..."}
            if "output" in resp_json and isinstance(resp_json["output"], str):
                return resp_json["output"]
        except Exception:
            pass
        # fallback: return pretty json
        try:
            return json.dumps(resp_json, ensure_ascii=False)
        except Exception:
            return str(resp_json)

    # ------------------------
    # Basic chat (text only)
    # ------------------------
    def ask(self, text: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        ส่งข้อความ (chat) แบบ simple ไปยัง LLM
        - text: ข้อความ user
        - history: ประวัติการสนทนาในรูปแบบ list of {"role": "...", "content": "..."}
        คืน: string (ข้อความตอบ)
        """
        if history is None:
            history = []

        messages = [{"role": "system", "content": "You are a helpful assistant."}]
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
            return f"[LLM ERROR] ไม่สามารถแปลงผลลัพธ์เป็น JSON: {e} - raw: {resp.text[:200]}"

        return self._extract_text_from_response(data)

    # ------------------------
    # Multimodal: prompt + image (data URI)
    # ------------------------
    def ask_with_image(self, prompt_text: str, image_data_uri: str, history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        ส่ง prompt + image (data URI) ให้ LLM multimodal
        - prompt_text: คำสั่ง/คำถาม (string)
        - image_data_uri: data:image/jpeg;base64,... (string)
        - history: optional conversation history
        NOTE: payload format ตัวอย่างนี้ค่อนข้าง generic — ปรับให้ตรงกับ API ของคุณถ้าจำเป็น
        """
        if history is None:
            history = []

        # สร้าง messages แบบฝัง object image
        messages = [{"role": "system", "content": "You are a helpful multimodal assistant. Answer in Thai when possible."}]
        messages.extend(history)
        # user text
        messages.append({"role": "user", "content": prompt_text})
        # image embedded as a user message with structured content (many multimodal servers accept similar structure)
        # ถ้า server ของคุณต้องการ field อื่น ให้แก้ที่นี่
        messages.append({"role": "user", "content": {"type": "input_image", "image": image_data_uri, "caption": "screenshot"}})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False,
        }

        try:
            resp = requests.post(self.server_url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            return f"[LLM ERROR] ไม่สามารถเชื่อมต่อ LLM server: {e}"

        try:
            data = resp.json()
        except Exception as e:
            return f"[LLM ERROR] ไม่สามารถแปลงผลลัพธ์เป็น JSON: {e} - raw: {resp.text[:200]}"

        return self._extract_text_from_response(data)

    # ------------------------
    # Generic multimodal call (ให้ความยืดหยุ่นสูง)
    # ------------------------
    def ask_multimodal(self, messages: List[Dict[str, Any]]) -> str:
        """
        ส่ง messages แบบ multimodal (caller เตรียม messages มา)
        - messages: list ของ dict ที่อาจมี text/image object ตามต้องการ
        - เหมาะกับการส่งรูปแบบ payload เฉพาะของแต่ละ server
        """
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
            return f"[LLM ERROR] ไม่สามารถแปลงผลลัพธ์เป็น JSON: {e} - raw: {resp.text[:200]}"

        return self._extract_text_from_response(data)
# ------------------------
# ✅ Test block (debug / manual run)
# ------------------------
if __name__ == "__main__":
    print("=== [LLMClient: manual test] ===")
    client = LLMClient()

    # ทดสอบส่งข้อความอย่างง่าย
    print("\n[TEST] ask() with text only")
    reply = client.ask("สวัสดี คุณคือใคร?")
    print("Response:", reply)

    # ทดสอบ multimodal (จำลองด้วย string data URI — ต้องมีจริงถึงจะใช้ได้)
    fake_image = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD..."
    print("\n[TEST] ask_with_image() with fake image data")
    reply2 = client.ask_with_image("นี่คือภาพอะไร?", fake_image)
    print("Response:", reply2)

    # ทดสอบ generic multimodal
    print("\n[TEST] ask_multimodal() with manual messages")
    messages = [
        {"role": "system", "content": "You are a test multimodal assistant."},
        {"role": "user", "content": "ลองตอบว่า 'โอเค' หน่อย"},
    ]
    reply3 = client.ask_multimodal(messages)
    print("Response:", reply3)
