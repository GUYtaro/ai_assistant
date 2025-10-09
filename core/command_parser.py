# core/command_parser.py
# -------------------------
# แปลงคำสั่ง (จาก STT หรือ text) เป็น action JSON สำหรับ executor
# ใช้ LLM (ผ่าน core.llm_client.LLMClient) เป็น parser/semantic interpreter
# -------------------------

import json
import re
from typing import Optional, Tuple, Any

from core.llm_client import LLMClient

# System prompt template สำหรับการขอ JSON output แบบเคร่งครัด
PARSER_SYSTEM_PROMPT = """
You are a command parser for a desktop automation assistant.
Input: a user's natural language command (Thai or English) and optional context (ocr_text or screenshot).
Output: a single JSON object (no extra text) that follows this schema:

{
  "type": "click|type|press|scroll|move|multi",
  "target": {"by": "text|image|coords", "value": "<string or [x,y]>"},
  "button": "left|right|middle",
  "content": "<text to type>",
  "keys": ["ctrl","shift","a"],
  "amount": <integer>,  // for scroll
  "confirm": true|false,
  "steps": [ /* list of action objects if multi-step */ ]
}

Rules:
- Return ONLY valid JSON (no explanation).
- If you are uncertain about a target on screen, set "confirm": true.
- If user's command requires multiple actions, use "type":"multi" and fill "steps" with an array of actions.
- Keep fields minimal; omit fields that are not needed.
- If you cannot parse, return {"error":"cannot_parse"}.
"""

class CommandParser:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def _build_prompt(self, utterance: str, ocr_text: Optional[str]=None, hint_image_data_uri: Optional[str]=None) -> str:
        """
        สร้างข้อความสำหรับส่งให้ LLM
        ส่งข้อมูล context ถ้ามี (ocr_text หรือ data_uri)
        """
        ctx = ""
        if ocr_text:
            ctx += f"\nOCR_TEXT:\n{ocr_text}\n"
        if hint_image_data_uri:
            ctx += "\nIMAGE: data_uri included (base64). Use it for locating UI when necessary.\n"

        user_msg = f"COMMAND:\n{utterance}\n{ctx}\nReturn JSON action according to schema."
        return user_msg

    def parse(self, utterance: str, ocr_text: Optional[str]=None, hint_image_data_uri: Optional[str]=None) -> Tuple[bool, Any]:
        """
        ส่ง utterance + context ไปให้ LLM และพยายาม parse เป็น JSON
        คืน (ok:bool, parsed:dict or error string)
        """
        system = PARSER_SYSTEM_PROMPT
        user = self._build_prompt(utterance, ocr_text, hint_image_data_uri)

        # เรียก LLM (llm.ask): โดยส่ง system prompt และ user message ผ่าน history
        history = [
            {"role":"system","content": system},
            {"role":"user","content": user}
        ]

        try:
            # ใช้ llm.ask (ที่โปรเจ็กต์ของคุณมี) - แนะนำให้รับ history arg
            raw = self.llm.ask(user, history=history)
        except Exception as e:
            return False, {"error": f"llm_error: {e}"}

        # ดึง JSON จาก output (พยายามหา block ที่เป็น JSON)
        json_text = self._extract_json(raw)
        if not json_text:
            return False, {"error":"no_json_in_response", "raw": raw}

        try:
            parsed = json.loads(json_text)
        except Exception as e:
            return False, {"error": f"invalid_json: {e}", "raw": json_text}

        # basic validation: must have type
        if "type" not in parsed:
            return False, {"error":"missing_type", "parsed": parsed}

        return True, parsed

    def _extract_json(self, text: str) -> Optional[str]:
        """พยายามดึง JSON block จาก text (รองรับกรณีที่ LLM แทรก whitespace)"""
        # หา first { ... } block using naive bracket matching
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
