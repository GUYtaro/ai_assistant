# main.py
# -------------------------
# โปรแกรมหลักของ Assistant
# - เรียกใช้งาน LLMClient เพื่อคุยกับโมเดล
# - รับข้อความจากผู้ใช้ แล้วพิมพ์คำตอบออกมา
# -------------------------

from core.llm_client import LLMClient
from core.stt_client import STTClient

def main():
    llm = LLMClient()
    stt = STTClient(model_size="tiny", language="th")

    print("=== AI Assistant (Gemma3 4B Q6_K via LM Studio) ===")
    print("พิมพ์ข้อความ หรือกด Enter ว่าง ๆ เพื่อพูด (พูด 5 วิ)")
    print("พิมพ์ exit/quit/q เพื่อออก\n")

    while True:
        try:
            user_input = input("คุณ (พิมพ์ข้อความหรือกด Enter เพื่อพูด): ")

            # ออกจากโปรแกรม
            if user_input.lower() in ["exit", "quit", "q"]:
                break

            # ถ้า user ไม่พิมพ์ → ใช้เสียงแทน
            if user_input.strip() == "":
                user_input = stt.listen_once(duration=5)

            if not user_input:
                continue

            reply = llm.ask(user_input)
            print("ผู้ช่วย:", reply)

        except KeyboardInterrupt:
            print("\n[หยุดการทำงาน]")
            break

# เริ่มโปรแกรม
if __name__ == "__main__":
    main()
