# main.py
# -------------------------
# โปรแกรมหลักของ AI Assistant
# - ผนวก STT (หู), LLM (สมอง), และ TTS (ปาก) เข้าด้วยกัน
# - รองรับการสนทนาแบบพิมพ์และแบบเสียง
# -------------------------

from core.llm_client import LLMClient
from core.stt_client import STTClient
from core.tts_client import TTSClient

def main():
    # 1. สร้าง Clients สำหรับทุกส่วน
    llm = LLMClient()
    stt = STTClient(model_size="tiny", language="th")
    tts = TTSClient(lang="th") # ตั้งค่าให้พูดภาษาไทย
    
    # สำหรับการเก็บประวัติการสนทนา (เพื่อให้ LLM จำบทสนทนาเก่าได้)
    chat_history = [] 

    print("=========================================================")
    print("=== AI Assistant (Gemma3 4B Q6_K via LM Studio) ===")
    print("=========================================================")
    print("พิมพ์ข้อความ: พิมพ์คำถาม แล้วกด Enter")
    print("โหมดเสียง: กด Enter ว่าง ๆ เพื่อพูด (พูดได้ 5 วินาที)")
    print("พิมพ์ exit/quit/q เพื่อออก\\n")

    while True:
        try:
            # 2. รับ Input จากผู้ใช้ (พิมพ์ข้อความหรือกด Enter เพื่อพูด)
            user_input = input("คุณ (พิมพ์/Enter เพื่อพูด): ")

            # ออกจากโปรแกรม
            if user_input.lower() in ["exit", "quit", "q"]:
                tts.speak("ลาก่อนค่ะ ขอให้มีวันที่ดีนะคะ")
                break

            # ถ้า user กด Enter ว่าง ๆ → ใช้โหมดเสียงแทน
            if user_input.strip() == "":
                print("🎤 กำลังอัดเสียง 5 วินาที... พูดได้เลยครับ")
                user_input = stt.listen_once(duration=5)
                # ถ้าอัดแล้วไม่เจอข้อความ ให้วนลูปใหม่
                if not user_input or user_input.strip() == "":
                    print("[Assistant] ไม่พบเสียง หรือเสียงไม่ชัดเจน กรุณาลองใหม่")
                    continue
                print(f"📝 คุณพูดว่า: {user_input}")

            # 3. ส่งคำถามไปให้ LLM ประมวลผล
            # LLMClient.generate_response จะจัดการการเชื่อมต่อกับ LM Studio
            reply_text = llm.generate_response(user_input, history=chat_history)
            
            # 4. อัปเดต History สำหรับการสนทนาครั้งต่อไป
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": reply_text})
            
            # 5. แสดงคำตอบและพูดออกเสียง
            print(f"🤖 ผู้ช่วย: {reply_text}")
            tts.speak(reply_text)

        except KeyboardInterrupt:
            print("\n[หยุดการทำงานโดยผู้ใช้]")
            break
        except Exception as e:
            print(f"\n[ERROR] เกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
            break

# เริ่มโปรแกรม
if __name__ == "__main__":
    main()
