# main.py
# -------------------------
# โปรแกรมหลักของ AI Assistant
# รองรับ:
#   🗣️ พูด-ฟัง (F4 เปิด/ปิด)
#   🖼️ Vision Mode (จับภาพหน้าจอ)
#   💬 สนทนา (พิมพ์ข้อความ)
# -------------------------

from core.llm_client import LLMClient
from core.stt_client import STTClient
from core.tts_client import TTSClient
from core.vision_system import VisionSystem
from core.hotkey_listener import HotkeyListener
import re
import threading
import time


def main():
    # --- สร้าง Clients ---
    llm = LLMClient()
    stt = STTClient(model_size="medium", language="th")
    tts = TTSClient(lang="th")
    vision = VisionSystem()

    chat_history = [{"role": "system", "content": "คุณคือผู้ช่วยที่ตอบเป็นภาษาไทยอย่างเป็นมิตร"}]

    print("=========================================================")
    print("=== 🤖 AI Assistant (Offline Mode) ===")
    print("=========================================================")
    print("โหมดพิมพ์: พิมพ์ข้อความ แล้วกด Enter")
    print("โหมด Vision:")
    print("  - vision: คำถาม... (จับจอหลัก)")
    print("  - vision:1 คำถาม... (จับจอที่ 1)")
    print("  - vision:2 คำถาม... (จับจอที่ 2)")
    print("  - vision:3 คำถาม... (จับจอที่ 3)")
    print("โหมดเสียง (Voice): กด F4 เพื่อเริ่มพูด / F4 อีกครั้งเพื่อหยุด")
    print("พิมพ์ exit/quit/q เพื่อออก\n")

    # --- ฟังก์ชันหลักสำหรับพูด (เมื่อกด F4) ---
    def handle_voice():
        try:
            print("🎤 [HOTKEY] กำลังอัดเสียง 5 วินาที... พูดได้เลยครับ")
            tts.speak("เริ่มฟังแล้วครับ")  # ✅ ตอบเสียงเหมือน Google Assistant
            user_input = stt.listen_once(duration=5)
            if not user_input or user_input.strip() == "":
                print("[STT] ไม่ได้ยินเสียง หรือเสียงไม่ชัดเจน")
                tts.speak("ขอโทษครับ ผมไม่ได้ยิน ลองใหม่อีกครั้งนะครับ")
                return

            print(f"📝 คุณพูดว่า: {user_input}")
            reply_text = llm.ask(user_input, history=chat_history)

            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": reply_text})

            print(f"🤖 ผู้ช่วย: {reply_text}")
            tts.speak(reply_text)

        except Exception as e:
            print(f"[ERROR] โหมดเสียงล้มเหลว: {e}")
            tts.speak("เกิดข้อผิดพลาดในระบบเสียงครับ")

    # --- เมื่อกด F4 ซ้ำ เพื่อหยุด ---
    def handle_stop_voice():
        print("[Hotkey] 🚫 หยุดโหมดผู้ช่วยเสียงแล้ว")
        tts.speak("หยุดฟังแล้วครับ")

    # --- เริ่มระบบ Hotkey ---
    hotkey_listener = HotkeyListener(
        callback_start=handle_voice,
        callback_stop=handle_stop_voice,
        hotkey="f4"
    )
    hotkey_listener.start()

    # --- วนลูปรับ input ---
    while True:
        try:
            user_input = input("คุณ (พิมพ์/vision/F4): ")

            # ออกจากโปรแกรม
            if user_input.lower() in ["exit", "quit", "q"]:
                tts.speak("ลาก่อนครับ ขอให้มีวันที่ดีนะครับ")
                break

            # Vision Mode
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
                        print(f"🤖 ผู้ช่วย (Vision - จอที่ {monitor}): {reply_text}")
                        tts.speak(reply_text)
                    except Exception as e:
                        error_msg = f"เกิดข้อผิดพลาดในการจับภาพจอที่ {monitor}: {e}"
                        print(f"❌ {error_msg}")
                        tts.speak("ขอโทษครับ เกิดข้อผิดพลาดในการจับภาพหน้าจอ")
                    continue

            # โหมดพิมพ์ (ทั่วไป)
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


if __name__ == "__main__":
    main()
