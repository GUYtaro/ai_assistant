# main.py
# -------------------------
# โปรแกรมหลักของ AI Assistant
# รองรับ: แชท, เสียง (F4), Vision (หลายจอ), Automation
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
from core.hotkey_listener import HotkeyListener


def main():
    # เตรียมระบบทั้งหมด
    llm = LLMClient()
    stt = STTClient(model_size="medium", language="th")
    tts = TTSClient(lang="th")
    vision = VisionSystem()
    parser = CommandParser(llm_client=llm)
    executor = AutomationExecutor(monitor=1)  # ใช้จอที่ 1

    chat_history = [{"role": "system", "content": "คุณคือผู้ช่วยที่ตอบเป็นภาษาไทยอย่างเป็นมิตร"}]

    print("=========================================================")
    print("=== 🤖 AI Assistant (Full Automation Mode) ===")
    print("=========================================================")
    print("โหมดพิมพ์: พิมพ์ข้อความ แล้วกด Enter")
    print("โหมด Vision: พิมพ์ 'vision:1 คำถาม...'")
    print("โหมดเสียง: กด F4 เพื่อเริ่มพูด")
    print("โหมด Automation: พูดเช่น 'คลิกปุ่ม File' หรือ 'พิมพ์ hello world'")
    print("พิมพ์ exit/quit/q เพื่อออก\n")

    # ฟังก์ชันสำหรับ F4
    def handle_voice():
        try:
            print("🎤 [F4] กำลังอัดเสียง 5 วินาที... พูดได้เลยครับ")
            tts.speak("เริ่มฟังแล้วครับ")
            user_input = stt.listen_once(duration=5)
            if not user_input or user_input.strip() == "":
                print("[STT] ไม่ได้ยินเสียง")
                tts.speak("ขอโทษครับ ผมไม่ได้ยิน")
                return

            print(f"📝 คุณพูดว่า: {user_input}")
            
            # ตรวจสอบว่าเป็นคำสั่ง Automation หรือไม่
            if any(word in user_input.lower() for word in ["คลิก", "พิมพ์", "กด", "เลื่อน"]):
                print("⚙️ ตรวจจับคำสั่ง Automation...")
                ok, parsed = parser.parse(user_input)
                if ok:
                    result = executor.execute(parsed)
                    if result.get("ok"):
                        tts.speak("เรียบร้อยครับ")
                    else:
                        tts.speak("ขอโทษครับ ทำไม่สำเร็จ")
                else:
                    tts.speak("ขอโทษครับ ผมไม่เข้าใจคำสั่ง")
            else:
                # แชทปกติ
                reply_text = llm.ask(user_input, history=chat_history)
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": reply_text})
                print(f"🤖 ผู้ช่วย: {reply_text}")
                tts.speak(reply_text)

        except Exception as e:
            print(f"[ERROR] {e}")
            tts.speak("เกิดข้อผิดพลาด")

    # เริ่มระบบ Hotkey
    hotkey_listener = HotkeyListener(
        callback_start=handle_voice,
        hotkey="f4",
        cooldown=2.0
    )
    hotkey_listener.start()

    # วนลูปรับ input
    while True:
        try:
            user_input = input("คุณ (พิมพ์/vision/F4): ")

            # ออกจากโปรแกรม
            if user_input.lower() in ["exit", "quit", "q"]:
                tts.speak("ลาก่อนครับ")
                break

            # Vision Mode
            if user_input.lower().startswith("vision"):
                match = re.match(r'vision:?(\d*)\s*(.*)', user_input, re.IGNORECASE)
                if match:
                    monitor_str = match.group(1)
                    vision_prompt = match.group(2).strip()
                    monitor = int(monitor_str) if monitor_str else 1
                    if not vision_prompt:
                        vision_prompt = "อธิบายสิ่งที่เห็นบนหน้าจอนี้"

                    print(f"📸 จับภาพจอที่ {monitor}...")
                    try:
                        reply_text = vision.analyze(vision_prompt, monitor=monitor)
                        print(f"🤖 ผู้ช่วย (Vision-{monitor}): {reply_text}")
                        tts.speak(reply_text)
                    except Exception as e:
                        print(f"❌ {e}")
                        tts.speak("เกิดข้อผิดพลาดในการจับภาพ")
                    continue

            # ตรวจจับคำสั่ง Automation
            if any(word in user_input.lower() for word in ["คลิก", "พิมพ์", "กด", "เลื่อน", "ปุ่ม"]):
                print("⚙️ ตรวจจับคำสั่ง Automation → กำลังวิเคราะห์...")
                
                # ดึง OCR ถ้าจำเป็น
                ocr_text = None
                data_uri = None
                if any(w in user_input.lower() for w in ["ปุ่ม", "หน้าจอ", "ไอคอน"]):
                    try:
                        sr = ScreenReader(lang="tha+eng")
                        img = screenshot_pil(monitor=1)
                        ocr_text = sr.read_text(monitor=1)
                        data_uri, _, _ = screenshot_data_uri(monitor=1, resize_to=(1200, 800))
                    except Exception as e:
                        print(f"[WARN] OCR/Vision ไม่พร้อม: {e}")

                ok, parsed = parser.parse(user_input, ocr_text=ocr_text, hint_image_data_uri=data_uri)
                if not ok:
                    print("❌ ไม่สามารถแปลงคำสั่งได้:", parsed)
                    tts.speak("ขอโทษครับ ผมไม่เข้าใจคำสั่ง")
                    continue

                print(f"📋 Action: {parsed}")
                result = executor.execute(parsed)
                if result.get("ok"):
                    print("✅ สำเร็จ:", result.get("message"))
                    tts.speak("เรียบร้อยครับ")
                else:
                    print("❌ ไม่สำเร็จ:", result.get("message"))
                    tts.speak("ขอโทษครับ ทำไม่สำเร็จ")
                continue

            # โหมดพิมพ์ปกติ
            if user_input.strip():
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
            print("💡 ตรวจสอบว่า LM Studio เปิดอยู่")
            break


if __name__ == "__main__":
    main()