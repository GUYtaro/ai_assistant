# 🤖 AI Assistant (Gemma3 4B Q6_K via LM Studio)

โปรเจกต์นี้เป็น **AI Assistant แบบรันบนเครื่อง (Offline)**  
ใช้โมเดล **Gemma3 4B Q6_K** ผ่าน **LM Studio**  
สามารถขยายต่อยอดให้รองรับ **Speech-to-Text (STT)**, **Text-to-Speech (TTS)**, **ควบคุม Keyboard/Mouse**, และ **อ่านหน้าจอ (OCR)** ได้ในอนาคต

---

## 🚀 ฟีเจอร์ปัจจุบัน
- คุยกับ AI Assistant ผ่าน CLI (พิมพ์ข้อความ → ได้คำตอบกลับ)
- ใช้โมเดล **Gemma3 4B Q6_K** ที่รันบน LM Studio
- รองรับภาษาไทยและภาษาอังกฤษ

---

## 📂 โครงสร้างไฟล์
ai_assistant/
│── main.py # entry point ของโปรแกรม
│── config.py # config ต่าง ๆ เช่น LM Studio URL และชื่อโมเดล
│── requirements.txt # dependencies
│── .gitignore # กันไฟล์ไม่จำเป็น (เช่น โมเดล, log)
│
└── core/
└── llm_client.py # ติดต่อ LM Studio API

---

## 🔧 การติดตั้ง
### 1. ติดตั้ง Python (แนะนำ 3.10+)
ตรวจสอบว่า Python ติดตั้งแล้ว:
```bash
python --version



pip install -r requirements.txt
ดาวน์โหลด LM Studio: https://lmstudio.ai

โหลดโมเดล Gemma3 4B Q6_K

ไปที่ Settings → เปิด Local Inference Server

ตรวจสอบว่า server ทำงานที่:

http://localhost:1234/v1

การใช้งาน

รันโปรแกรมด้วยคำสั่ง: python main.py

ตัวอย่าง: === AI Assistant (Gemma3 4B Q6_K via LM Studio) ===
พิมพ์ exit หรือ quit เพื่อออกจากโปรแกรม

คุณ: สวัสดี
ผู้ช่วย: สวัสดีครับ! มีอะไรให้ช่วยไหม?
