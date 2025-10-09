# main.py
# -------------------------
# โปรแกรมหลักของ AI Assistant
# - รองรับหลายโหมด: แชต, เสียง, Vision, และ Full Voice Automation
# -------------------------

import re
from core.llm_client import LLMClient
from core.stt_client import STTClient
from core.tts_client import TTSClient
from core.vision_system import VisionSystem
from core.command_parser import CommandParser
from core.automation_executor import AutomationExecutor
from core.screen_capturer import screenshot_data_uri, screenshot_pil
from core.screen_reader import ScreenReader

def main():
    # --------------------------
    # 🔧 เตรียมระบบทั้งหมด
    # --------------------------
    llm = LLMClient()
    stt = STTClient(model_size="medium", language="th")
    tts = TTSClient(lang="th")
    vision = VisionSystem()
    parser = CommandParser(llm_client=llm)
    executor = AutomationExecutor()

    chat_history = [{"role": "system", "content": "คุณคือผู้ช่วยที่ตอบเป็นภาษาไทยอย่างเป็นมิตร"}]

    print("=========================================================")
    print("=== 🤖 AI Assistant (Full Voice Automation Mode) ===")
    print("=========================================================")
    print("โหมดพิมพ์: พิมพ์ข้อความ แล้วกด Enter")
    print("โหมดเสียง: กด Enter ว่าง ๆ เพื่อพูด (อัด 5 วินาที)")
    print("โหมด Vision: พิมพ์ 'vision: คำถาม...' เพื่อถามจากภาพหน้าจอ")
    print("โหมด Voice Automation: พูดเช่น 'คลิกปุ่มบันทึก' หรือ 'พิมพ์ hello world'")
    print("พิมพ์ exit/quit/q เพื่อออก\n")

    while True:
        try:
            user_input = input("คุณ (พิมพ์/Enter/vision): ")

            # 1️⃣ ออกจากโปรแกรม
            if user_input.lower() in ["exit", "quit", "q"]:
                tts.speak("ลาก่อนค่ะ ขอให้มีวันที่ดีนะคะ")
                break

            # 2️⃣ Vision Mode
            if user_input.lower().startswith("vision"):
                match = re.match(r'vision:?(\d*)\s*(.*)', user_input, re.IGNORECASE)
                if match:
                    monitor_str = match.group(1)
                    vision_prompt = match.group(2).strip()
                    monitor = int(monitor_str) if monitor_str else 1
                    if not vision_prompt:
                        vision_prompt = "อธิบายสิ่งที่เห็นบนหน้าจอนี้เป็นภาษาไทย"
                    print(f"📸 กำลังจับภาพจอที่ {monitor} และส่งให้ LLM ...")
                    try:
                        reply_text = vision.analyze(vision_prompt, monitor=monitor)
                        print(f"🤖 ผู้ช่วย (Vision-{monitor}): {reply_text}")
                        tts.speak(reply_text)
                    except Exception as e:
                        print(f"❌ เกิดข้อผิดพลาด Vision: {e}")
                        tts.speak("ขอโทษค่ะ มีปัญหาในการประมวลผลภาพ")
                    continue

            # 3️⃣ Voice Mode (Enter เปล่า)
            if user_input.strip() == "":
                print("🎤 กำลังอัดเสียง 5 วินาที... พูดได้เลยครับ")
                user_input = stt.listen_once(duration=5)
                if not user_input:
                    print("[STT] ไม่พบเสียง หรือเสียงไม่ชัด")
                    continue
                print(f"🗣️ คุณพูดว่า: {user_input}")

            # 4️⃣ ตรวจจับว่าเป็นคำสั่ง Automation หรือไม่
            if any(word in user_input.lower() for word in ["คลิก", "พิมพ์", "กด", "เลื่อน", "หน้าจอ", "เมาส์", "เคอร์เซอร์"]):
                print("⚙️ ตรวจจับได้ว่าเป็นคำสั่ง Automation → กำลังวิเคราะห์...")
                ocr_text = None
                data_uri = None
                needs_vision = any(w in user_input.lower() for w in ["หน้าจอ", "ปุ่ม", "ไอคอน", "window"])
                if needs_vision:
                    try:
                        data_uri, _, _ = screenshot_data_uri(monitor=1, resize_to=(1200,800))
                        sr = ScreenReader()
                        img = screenshot_pil(monitor=1, resize_to=(1200,800))
                        ocr_text = sr.read_text(img)
                    except Exception as e:
                        print(f"[WARN] OCR หรือ Vision ใช้งานไม่ได้: {e}")

                ok, parsed = parser.parse(user_input, ocr_text=ocr_text, hint_image_data_uri=data_uri)
                if not ok:
                    print("❌ ไม่สามารถแปลงคำสั่งเป็น action ได้:", parsed)
                    tts.speak("ขอโทษค่ะ ฉันยังไม่เข้าใจคำสั่งนี้ ลองพูดใหม่อีกครั้งนะคะ")
                    continue

                result = executor.execute(parsed)
                if result.get("ok"):
                    print("✅ สำเร็จ:", result.get("message"))
                    tts.speak("เรียบร้อยค่ะ")
                else:
                    print("❌ ไม่สำเร็จ:", result.get("message"))
                    tts.speak("ขอโทษค่ะ คำสั่งนี้ไม่สำเร็จ")
                continue

            # 5️⃣ ถ้าไม่ใช่ Automation → ส่งเข้า LLM ปกติ
            reply_text = llm.ask(user_input, history=chat_history)
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": reply_text})
            print(f"🤖 ผู้ช่วย: {reply_text}")
            tts.speak(reply_text)

        except KeyboardInterrupt:
            print("\n[หยุดโดยผู้ใช้]")
            break
        except Exception as e:
            print(f"[CRITICAL ERROR] {e}")
            print("💡 โปรดตรวจสอบว่า LM Studio Server เปิดอยู่บน http://localhost:1234/")
            break


if __name__ == "__main__":
    main()
