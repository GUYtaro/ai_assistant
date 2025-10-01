# main.py
# -------------------------
# โปรแกรมหลักของ AI Assistant
# - ผนวก STT (หู), LLM (สมอง), และ TTS (ปาก) เข้าด้วยกัน
# - รองรับการสนทนาแบบพิมพ์และแบบเสียง (Offline)
# - สามารถควบคุม Keyboard/Mouse และอ่านข้อความบนหน้าจอได้
# -------------------------

from core.llm_client import LLMClient
from core.stt_client import STTClient
from core.tts_client import TTSClient
from core.keyboard_mouse import KeyboardMouse
from core.screen_reader import ScreenReader
from config import LLM_SERVER_URL, LLM_MODEL

def main():
    # 1. สร้าง Clients สำหรับทุกส่วน
    llm = LLMClient(server_url=LLM_SERVER_URL, model=LLM_MODEL)
    stt = STTClient(model_size="medium", language="th")  # Whisper medium
    tts = TTSClient(lang="th")  # Offline TTS
    kb = KeyboardMouse()  # ควบคุม keyboard/mouse
    reader = ScreenReader(lang="tha+eng")  # OCR ไทย+อังกฤษ
    
    # เก็บประวัติการสนทนา
    chat_history = [
        {"role": "system", "content": "คุณคือผู้ช่วยที่ตอบเป็นภาษาไทยอย่างเป็นมิตร และใช้คำที่เหมาะสมกับวัย"}
    ]

    print("=========================================================")
    print("=== 🤖 AI Assistant (Offline Mode: LM Studio, Whisper, pyttsx3) ===")
    print("=========================================================")
    print("📝 คำสั่งพิเศษ:")
    print("   help   → แสดงวิธีใช้งาน")
    print("   screen → อ่านหน้าจอ (OCR)")
    print("   type   → ให้ผู้ช่วยพิมพ์แทน")
    print("   exit   → ออกจากโปรแกรม\n")

    while True:
        try:
            # 2. รับ Input
            user_input = input("คุณ (พิมพ์/Enter เพื่อพูด): ")

            # ออกจากโปรแกรม
            if user_input.lower() in ["exit", "quit", "q"]:
                tts.speak("ลาก่อนค่ะ ขอให้มีวันที่ดีนะคะ")
                break

            # โหมดช่วยเหลือ
            if user_input.lower() == "help":
                print("=== วิธีใช้งาน ===")
                print("- กด Enter ว่าง ๆ เพื่อพูด (5 วินาที)")
                print("- พิมพ์ข้อความเพื่อคุยกับผู้ช่วย")
                print("- คำสั่งพิเศษ: screen / type / exit")
                continue

            # โหมดอ่านหน้าจอ
            if user_input.lower() == "screen":
                text = reader.read_screen()
                print("📖 ข้อความบนหน้าจอ:", text)
                tts.speak("นี่คือข้อความบนหน้าจอ " + text[:50])
                continue

            # โหมดให้ผู้ช่วยพิมพ์แทน
            if user_input.lower() == "type":
                msg = input("🖊️ พิมพ์ข้อความที่ต้องการให้ผู้ช่วยพิมพ์แทน: ")
                kb.type_text(msg)
                print("[Keyboard] ผู้ช่วยพิมพ์ให้แล้ว")
                continue

            # ถ้า user กด Enter ว่าง → ใช้โหมดเสียง
            if user_input.strip() == "":
                print("🎤 กำลังอัดเสียง 5 วินาที... พูดได้เลยครับ")
                user_input = stt.listen_once(duration=5)
                if not user_input.strip():
                    print("[Assistant] ไม่พบเสียง หรือเสียงไม่ชัดเจน กรุณาลองใหม่")
                    continue
                print(f"📝 คุณพูดว่า: {user_input}")

            # ส่งคำถามไปยัง LLM
            reply_text = llm.ask(user_input, history=chat_history)
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": reply_text})

            # แสดงและพูดคำตอบ
            print(f"🤖 ผู้ช่วย: {reply_text}")
            tts.speak(reply_text)

        except KeyboardInterrupt:
            print("\n[หยุดการทำงานโดยผู้ใช้]")
            break
        except Exception as e:
            print(f"\n[CRITICAL ERROR] เกิดข้อผิดพลาด: {e}")
            print("--- 💡 โปรดตรวจสอบว่า LM Studio Server เปิดอยู่บน http://localhost:1234/ ---")
            break

# เริ่มโปรแกรม
if __name__ == "__main__":
    main()
