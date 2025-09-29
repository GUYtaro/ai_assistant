# core/llm_client.py
# -------------------------
# โมดูลสำหรับเชื่อมต่อกับ Large Language Model (LLM)
# โดยใช้ LM Studio Server (รันบน localhost:1234) ผ่าน API
# -------------------------

import requests
import json
# อิมพอร์ตการตั้งค่าจาก config.py (ตอนนี้มี MAX_TOKENS, TEMPERATURE)
from config import LMSTUDIO_URL, MODEL_NAME, MAX_TOKENS, TEMPERATURE 

class LLMClient:
    def __init__(self):
        """
        ตั้งค่าไคลเอนต์สำหรับเชื่อมต่อกับ LM Studio
        """
        self.api_url = LMSTUDIO_URL
        self.model_name = MODEL_NAME
        self.max_tokens = MAX_TOKENS
        self.temperature = TEMPERATURE
        
        print(f"[LLM Client] เชื่อมต่อกับ LM Studio ที่ {self.api_url}")
        print(f"[LLM Client] ใช้โมเดล: {self.model_name}")

    def ask(self, prompt, history=[]): # ***ฟังก์ชันที่ถูกต้องคือ ask() และรับ history***
        """
        ส่งข้อความไปให้ LLM ประมวลผลและรับคำตอบกลับมา (รองรับ Chat History)
        
        Args:
            prompt (str): ข้อความล่าสุดจากผู้ใช้
            history (list): ประวัติการสนทนา (list of dictionaries)
            
        Returns:
            str: คำตอบที่สร้างโดยโมเดล หรือข้อความแจ้งเตือนข้อผิดพลาด
        """
        
        # System Message: กำหนดบุคลิกและบทบาทของ Assistant
        messages = [{
            "role": "system", 
            "content": "คุณคือผู้ช่วย AI ที่เป็นมิตรและมีความรู้ ตอบคำถามด้วยภาษาไทยที่สุภาพและเข้าใจง่าย ตอบคำถามให้กระชับที่สุด"
        }]
        
        # เพิ่มประวัติการสนทนาและคำถามล่าสุด
        messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        # สร้าง Payload สำหรับ API
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        # ส่ง Request ไปยัง LM Studio Server
        try:
            headers = {"Content-Type": "application/json"}
            
            # API endpoint สำหรับการสนทนาคือ /v1/chat/completions
            # เพิ่ม timeout เพื่อป้องกันการรอนานเกินไป
            response = requests.post(f"{self.api_url}/chat/completions", headers=headers, json=payload, timeout=60)
            response.raise_for_status() # ตรวจสอบ Error HTTP

            # ประมวลผลคำตอบ
            data = response.json()
            
            if data and data['choices']:
                message = data['choices'][0]['message']
                return message.get('content', '').strip()
            
            return "ขออภัยค่ะ โมเดลไม่ได้ให้คำตอบที่ชัดเจน"

        except requests.exceptions.ConnectionError:
            return "❌ เชื่อมต่อ LM Studio Server ไม่ได้ กรุณาตรวจสอบว่า LM Studio เปิดอยู่และรันโมเดลแล้วที่พอร์ต 1234"
        except requests.exceptions.RequestException as e:
            return f"❌ เกิดข้อผิดพลาดในการเรียก API: {e}"
        except Exception as e:
            return f"❌ เกิดข้อผิดพลาดที่ไม่รู้จัก: {e}"
