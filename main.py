# main.py
# -------------------------
# โปรแกรมหลักของ AI Assistant
# - ผนวก STT (หู), LLM (สมอง), และ TTS (ปาก) เข้าด้วยกัน
# - รองรับการสนทนาแบบพิมพ์, แบบเสียง, และ Vision Mode (จับภาพหน้าจอ)
# -------------------------

from core.llm_client import LLMClient
from core.stt_client import STTClient
from core.tts_client import TTSClient
from core.vision_system import VisionSystem  # <<< เพิ่ม Vision Mode

def main():
    # 1. สร้าง Clients สำหรับทุกส่วน
    llm = LLMClient()
    stt = STTClient(model_size="medium", language="th")
    tts = TTSClient(lang="th")
    vision = VisionSystem()  # <<< Vision

    # เก็บประวัติการสนทนา
    chat_history = [{"role": "system", "content": "คุณคือผู้ช่วยที่ตอบเป็นภาษาไทยอย่างเป็นมิตร"}]

    print("=========================================================")
    print("=== 🤖 AI Assistant (Offline Mode) ===")
    print("=========================================================")
    print("โหมดพิมพ์: พิมพ์ข้อความ แล้วกด Enter")
    print("โหมดเสียง: กด Enter ว่าง ๆ เพื่อพูด (อัด 5 วินาที)")
    print("โหมด Vision: พิมพ์ 'vision: คำถาม...' เพื่อถามจากภาพหน้าจอ")
    print("พิมพ์ exit/quit/q เพื่อออก\n")

    while True:
        try:
            # 2. รับ Input
            user_input = input("คุณ (พิมพ์/Enter/vision): ")

            # ออกจากโปรแกรม
            if user_input.lower() in ["exit", "quit", "q"]:
                tts.speak("ลาก่อนค่ะ ขอให้มีวันที่ดีนะคะ")
                break

            # Vision Mode
            if user_input.lower().startswith("vision:"):
                vision_prompt = user_input.replace("vision:", "").strip()
                if not vision_prompt:
                    vision_prompt = "ช่วยวิเคราะห์หน้าจอนี้ให้หน่อย"
                print("📸 กำลังจับภาพหน้าจอและส่งให้ LLM ...")
                reply_text = vision.analyze(vision_prompt, monitor=1)  # คุณเลือก monitor=1,2,3 ได้
                print(f"🤖 ผู้ช่วย (Vision): {reply_text}")
                tts.speak(reply_text)
                continue

            # โหมดเสียง
            if user_input.strip() == "":
                print("🎤 กำลังอัดเสียง 5 วินาที... พูดได้เลยครับ")
                user_input = stt.listen_once(duration=5)
                if not user_input or user_input.strip() == "":
                    print("[Assistant] ไม่พบเสียง หรือเสียงไม่ชัดเจน กรุณาลองใหม่")
                    continue
                print(f"📝 คุณพูดว่า: {user_input}")

            # โหมดพิมพ์
            if user_input.strip():
                reply_text = llm.ask(user_input, history=chat_history)
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": reply_text})

                print(f"🤖 ผู้ช่วย: {reply_text}")
                tts.speak(reply_text)

        except KeyboardInterrupt:
            print("\n[หยุดการทำงานโดยผู้ใช้]")
            break
        except Exception as e:
            print(f"\n[CRITICAL ERROR] เกิดข้อผิดพลาดร้ายแรง: {e}")
            print("--- 💡 โปรดตรวจสอบว่า LM Studio Server เปิดอยู่บน http://localhost:1234/ ---")
            break


# เริ่มโปรแกรม
if __name__ == "__main__":
    main()
