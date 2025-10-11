# core/command_parser.py
# -------------------------
# แปลงคำสั่ง (จาก STT หรือ text) เป็น action JSON สำหรับ executor
# ใช้ Hybrid Mode: Rule-based ก่อน, ถ้าไม่เข้าใจค่อยใช้ AI
# -------------------------

import json
import re
from typing import Optional, Tuple, Any, Dict  # 🔥 เพิ่ม Dict ตรงนี้
from core.llm_client import LLMClient

# 🔥 AI-powered System Prompt (เข้าใจทั้งคำสั่งเปิด app และ automation)
PARSER_SYSTEM_PROMPT = """
You are an intelligent command parser for a desktop automation assistant (AI-powered).
Your job is to convert user's natural language (Thai or English) into a structured JSON command.
Output must be valid JSON only, following this schema:

{
  "type": "click|type|press|scroll|move|multi|launch",
  "target": {"by": "text|image|coords", "value": "<string or [x,y]>"},
  "app": "<application name>",
  "url": "<https://...>",
  "button": "left|right|middle",
  "content": "<text to type>",
  "keys": ["ctrl","shift","a"],
  "amount": <integer>,
  "confirm": true|false,
  "steps": [ /* list of action objects if multi-step */ ]
}

Rules:
- Always output JSON only (no explanation or text outside the JSON).
- If the command asks to **open / go to / launch / start / เปิด / ไปที่ / เรียกใช้**, use `"type":"launch"`.
- If the thing to open is a **website** (like YouTube, Facebook), add `"url"` and set `"app":"chrome"`.
  Example: "เปิด YouTube ผ่าน Chrome" → {"type":"launch","app":"chrome","url":"https://youtube.com"}
- If the thing to open is an **application** (like Notepad, Excel, Discord), use `"app":"notepad"` etc.
- If user command involves typing, clicking, or pressing keys, map to proper type.
- If the command has multiple steps, use `"type":"multi"` with `"steps": []"`.
- If unsure about something, set `"confirm": true`.
- If you cannot understand, output: {"error":"cannot_parse"}
"""

class CommandParser:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()
        self.hybrid_mode = True  # เปิดใช้งาน Hybrid Mode

    def _try_rule_based_parse(self, utterance: str) -> Optional[Dict[str, Any]]:
        """
        🔥 Hybrid Mode: ลองใช้ Rule-based ก่อนสำหรับคำสั่งพื้นฐาน
        ถ้าสำเร็จจะเร็วกว่าและไม่ต้องเรียก LLM
        """
        if not self.hybrid_mode:
            return None

        text_lower = utterance.lower().strip()
        
        # 1. คำสั่งคลิกพื้นฐาน
        if "คลิก" in text_lower:
            match = re.search(r'คลิก(ปุ่ม)?\s*(.+)', text_lower)
            if match:
                target_text = match.group(2).strip()
                return {
                    "type": "click",
                    "target": {"by": "text", "value": target_text},
                    "button": "left",
                    "method": "rule-based"
                }
        
        # 2. คำสั่งพิมพ์พื้นฐาน
        if "พิมพ์" in text_lower:
            match = re.search(r'พิมพ์(ว่า)?\s*(.+)', text_lower)
            if match:
                content = match.group(2).strip()
                return {
                    "type": "type",
                    "content": content,
                    "method": "rule-based"
                }
        
        # 3. คำสั่งกดปุ่มลัด
        if "กด" in text_lower:
            if "enter" in text_lower or "เอ็นเทอร์" in text_lower:
                return {
                    "type": "press",
                    "keys": ["enter"],
                    "method": "rule-based"
                }
            elif "ctrl" in text_lower or "คอนโทรล" in text_lower:
                return {
                    "type": "press", 
                    "keys": ["ctrl"],
                    "method": "rule-based"
                }
            elif "alt" in text_lower or "อัลท์" in text_lower:
                return {
                    "type": "press",
                    "keys": ["alt"],
                    "method": "rule-based"
                }
        
        # 4. คำสั่งเลื่อน
        if "เลื่อน" in text_lower:
            if "ลง" in text_lower or "ล่าง" in text_lower:
                return {
                    "type": "scroll",
                    "amount": 200,
                    "method": "rule-based"
                }
            elif "ขึ้น" in text_lower or "บน" in text_lower:
                return {
                    "type": "scroll", 
                    "amount": -200,
                    "method": "rule-based"
                }
        
        return None  # ไม่เข้าใจด้วย rule-based

    def _build_prompt(self, utterance: str, ocr_text: Optional[str]=None, hint_image_data_uri: Optional[str]=None) -> str:
        """
        สร้างข้อความสำหรับส่งให้ LLM
        รวมข้อมูล context เช่น OCR หรือภาพหน้าจอถ้ามี
        """
        ctx = ""
        if ocr_text:
            ctx += f"\nOCR_TEXT:\n{ocr_text}\n"
        if hint_image_data_uri:
            ctx += "\nIMAGE: data_uri included (base64). Use it for locating UI if needed.\n"

        user_msg = f"COMMAND:\n{utterance}\n{ctx}\nReturn JSON action according to schema."
        return user_msg

    def parse(self, utterance: str, ocr_text: Optional[str]=None, hint_image_data_uri: Optional[str]=None) -> Tuple[bool, Any]:
        """
        🔥 HYBRID MODE: ลองใช้ Rule-based ก่อน, ถ้าไม่เข้าใจค่อยใช้ AI
        """
        # 1. ลองใช้ Rule-based ก่อน (เร็วและประหยัด)
        rule_based_result = self._try_rule_based_parse(utterance)
        if rule_based_result:
            print(f"⚡ [Hybrid] ใช้ Rule-Based สำหรับ: {utterance}")
            return True, rule_based_result
        
        # 2. ถ้า Rule-based ไม่เข้าใจ → ใช้ AI (ช้าแต่ฉลาด)
        print(f"🤖 [Hybrid] ใช้ AI สำหรับ: {utterance}")
        return self._parse_with_ai(utterance, ocr_text, hint_image_data_uri)

    def _parse_with_ai(self, utterance: str, ocr_text: Optional[str]=None, hint_image_data_uri: Optional[str]=None) -> Tuple[bool, Any]:
        """
        ใช้ AI สำหรับคำสั่งที่ซับซ้อน
        """
        system = PARSER_SYSTEM_PROMPT
        user = self._build_prompt(utterance, ocr_text, hint_image_data_uri)

        history = [
            {"role": "system", "content": system},
            {"role": "user", "content": user}
        ]

        try:
            raw = self.llm.ask(user, history=history)
        except Exception as e:
            return False, {"error": f"llm_error: {e}"}

        # 🔍 ดึงเฉพาะ JSON ออกมาจากข้อความตอบกลับ
        json_text = self._extract_json(raw)
        if not json_text:
            return False, {"error": "no_json_in_response", "raw": raw}

        try:
            parsed = json.loads(json_text)
        except Exception as e:
            return False, {"error": f"invalid_json: {e}", "raw": json_text}

        if "type" not in parsed:
            return False, {"error": "missing_type", "parsed": parsed}

        return True, parsed

    def _extract_json(self, text: str) -> Optional[str]:
        """
        พยายามดึง JSON block จากข้อความ (กรณี LLM มีข้อความส่วนเกิน)
        """
        start = text.find("{")
        if start == -1:
            return None
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
        return None

    def enable_hybrid_mode(self, enabled: bool = True):
        """เปิด/ปิด Hybrid Mode"""
        self.hybrid_mode = enabled
        print(f"🔧 [CommandParser] Hybrid Mode: {'เปิด' if enabled else 'ปิด'}")