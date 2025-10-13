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
from core.app_launcher import AppLauncher  # เพิ่มบรรทัดนี้


def main():
    # เตรียมระบบทั้งหมด
    llm = LLMClient()
    stt = STTClient(model_size="medium", language="th")
    tts = TTSClient(lang="th")
    vision = VisionSystem()
    parser = CommandParser(llm_client=llm)
    executor = AutomationExecutor(monitor=1)
    launcher = AppLauncher()  # เพิ่มบรรทัดนี้

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
            
            # ตรวจสอบว่าเป็นคำสั่งเปิดโปรแกรมหรือไม่
            if any(word in user_input.lower() for word in ["เปิด", "open", "launch", "start"]):
                # แยกชื่อโปรแกรม
                app_name, url = _parse_open_command(user_input)
                if app_name:
                    result = launcher.open_url(url, app_name) if url else launcher.launch(app_name)
                    if result["ok"]:
                        tts.speak(f"เปิด {app_name} แล้วครับ")
                    else:
                        tts.speak("ขอโทษครับ เปิดไม่ได้")
                    return
            
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

    # ฟังก์ชันช่วยแยกคำสั่งเปิดโปรแกรม
    def _parse_open_command(text):
        """แยกชื่อโปรแกรมและ URL จากคำสั่ง"""
        text_lower = text.lower()
        
        # ตรวจจับ URL (เพิ่มเว็บไซต์ยอดนิยม)
        url = None
        if "youtube" in text_lower:
            url = "https://youtube.com"
        elif "google" in text_lower and "search" not in text_lower and "ค้นหา" not in text_lower:
            url = "https://google.com"
        elif "facebook" in text_lower:
            url = "https://facebook.com"
        elif "github" in text_lower:
            url = "https://github.com"
        elif "chatgpt" in text_lower or "chat gpt" in text_lower:
            url = "https://chat.openai.com"
        elif "claude" in text_lower:
            url = "https://claude.ai"
        elif "gemini" in text_lower or "bard" in text_lower:
            url = "https://gemini.google.com"
        elif "twitter" in text_lower or "x.com" in text_lower:
            url = "https://x.com"
        elif "instagram" in text_lower:
            url = "https://instagram.com"
        elif "netflix" in text_lower:
            url = "https://netflix.com"
        elif "spotify" in text_lower:
            url = "https://open.spotify.com"
        
        # ตรวจจับคำค้นหา Google
        if ("ค้นหา" in text_lower or "search" in text_lower) and not url:
            # แยกคำค้นหาออกมา
            query = text_lower.replace("เปิด", "").replace("open", "")
            query = query.replace("ค้นหา", "").replace("search", "")
            query = query.replace("chrome", "").replace("firefox", "").replace("edge", "")
            query = query.replace("ผ่าน", "").replace("ใน", "")
            query = query.strip()
            if query:
                import urllib.parse
                url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        
        # ตรวจจับโปรแกรม (เช็คเบราว์เซอร์ก่อน)
        if "chrome" in text_lower or ("youtube" in text_lower or "google" in text_lower or "facebook" in text_lower or url):
            return "chrome", url
        elif "firefox" in text_lower:
            return "firefox", url
        elif "edge" in text_lower:
            return "edge", url
        elif "notepad" in text_lower or "โน้ตแพด" in text_lower:
            return "notepad", None
        elif "calculator" in text_lower or "เครื่องคิดเลข" in text_lower or "แคลคูเลเตอร์" in text_lower:
            return "calculator", None
        elif "paint" in text_lower or "เพ้นท์" in text_lower:
            return "paint", None
        elif "cmd" in text_lower or "command" in text_lower or "คอมมานด์" in text_lower:
            return "cmd", None
        elif "powershell" in text_lower or "พาวเวอร์เชล" in text_lower:
            return "powershell", None
        elif "explorer" in text_lower or "เอ็กซ์พลอเรอร์" in text_lower or "file explorer" in text_lower:
            return "explorer", None
        
        # ถ้าไม่มีเบราว์เซอร์แต่มี URL → ใช้ Chrome เป็นค่าเริ่มต้น
        if url:
            return "chrome", url
        
        return None, None

    # วนลูปรับ input
    while True:
        try:
            user_input = input("คุณ (พิมพ์/vision/F4): ")

            # ออกจากโปรแกรม
            if user_input.lower() in ["exit", "quit", "q"]:
                tts.speak("ลาก่อนครับ")
                break

            # ตรวจจับคำสั่งเปิดโปรแกรม (ต้องอยู่ก่อน Vision และ Automation)
            if any(word in user_input.lower() for word in ["เปิด", "open", "launch", "start"]):
                print(f"[DEBUG] ตรวจพบคำสั่งเปิดโปรแกรม: '{user_input}'")
                app_name, url = _parse_open_command(user_input)
                print(f"[DEBUG] แปลงได้: app_name={app_name}, url={url}")
                
                if app_name:
                    print(f"🚀 กำลังเปิด {app_name}..." + (f" ({url})" if url else ""))
                    result = launcher.open_url(url, app_name) if url else launcher.launch(app_name)
                    if result["ok"]:
                        print(f"✅ {result['message']}")
                        tts.speak(f"เปิด {app_name} แล้วครับ")
                    else:
                        print(f"❌ {result['message']}")
                        tts.speak("ขอโทษครับ เปิดไม่ได้")
                else:
                    print("[DEBUG] ไม่สามารถแยกชื่อโปรแกรมได้")
                    tts.speak("ขอโทษครับ ผมไม่แน่ใจว่าจะเปิดอะไร")
                continue

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

            # ตรวจจับคำสั่ง Automation (คลิก, พิมพ์, กด, เลื่อน)
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