# main.py
# -------------------------
# โปรแกรมหลักของ AI Assistant
# - รองรับหลายจอ: vision:1, vision:2, vision:3
# - รองรับการสนทนาแบบพิมพ์, แบบเสียง, และ Vision Mode
# -------------------------

from core.llm_client import LLMClient
from core.stt_client import STTClient
from core.tts_client import TTSClient
from core.vision_system import VisionSystem
import re

def main():
    # 1. สร้าง Clients สำหรับทุกส่วน
    llm = LLMClient()
    stt = STTClient(model_size="medium", language="th")
    tts = TTSClient(lang="th")
    vision = VisionSystem()

    # เก็บประวัติการสนทนา
    chat_history = [{"role": "system", "content": "คุณคือผู้ช่วยที่ตอบเป็นภาษาไทยอย่างเป็นมิตร"}]

    print("=========================================================")
    print("=== 🤖 AI Assistant (Offline Mode) ===")
    print("=========================================================")
    print("โหมดพิมพ์: พิมพ์ข้อความ แล้วกด Enter")
    print("โหมดเสียง: กด Enter ว่าง ๆ เพื่อพูด (อัด 5 วินาที)")
    print("โหมด Vision:")
    print("  - vision: คำถาม... (จับจอหลัก)")
    print("  - vision:1 คำถาม... (จับจอที่ 1)")
    print("  - vision:2 คำถาม... (จับจอที่ 2)")
    print("  - vision:3 คำถาม... (จับจอที่ 3)")
    print("พิมพ์ exit/quit/q เพื่อออก\n")

    while True:
        try:
            # 2. รับ Input
            user_input = input("คุณ (พิมพ์/Enter/vision): ")

            # ออกจากโปรแกรม
            if user_input.lower() in ["exit", "quit", "q"]:
                tts.speak("ลาก่อนค่ะ ขอให้มีวันที่ดีนะคะ")
                break

            # Vision Mode - รองรับการเลือกจอ
            # Format: vision:2 คำถาม... หรือ vision: คำถาม...
            if user_input.lower().startswith("vision"):
                # ใช้ regex เพื่อแยก monitor number และ prompt
                match = re.match(r'vision:?(\d*)\s*(.*)', user_input, re.IGNORECASE)
                
                if match:
                    monitor_str = match.group(1)  # เลขจอ (ถ้ามี)
                    vision_prompt = match.group(2).strip()  # คำถาม
                    
                    # กำหนด monitor (default = 1 ถ้าไม่ระบุ)
                    monitor = int(monitor_str) if monitor_str else 1
                    
                    # ถ้าไม่มีคำถาม ให้ใช้ default
                    if not vision_prompt:
                        vision_prompt = "อธิบายสิ่งที่เห็นบนหน้าจอนี้เป็นภาษาไทย"
                    
                    print(f"📸 กำลังจับภาพจอที่ {monitor} และส่งให้ LLM ...")
                    
                    try:
                        reply_text = vision.analyze(vision_prompt, monitor=monitor)
                        print(f"🤖 ผู้ช่วย (Vision - จอที่ {monitor}): {reply_text}")
                        tts.speak(reply_text)
                    except Exception as e:
                        error_msg = f"เกิดข้อผิดพลาดในการจับภาพจอที่ {monitor}: {e}"
                        print(f"❌ {error_msg}")
                        tts.speak("ขอโทษค่ะ เกิดข้อผิดพลาดในการจับภาพหน้าจอ")
                    
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