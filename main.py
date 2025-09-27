# main.py
# -------------------------
# โปรแกรมหลักของ Assistant
# - เรียกใช้งาน LLMClient เพื่อคุยกับโมเดล
# - รับข้อความจากผู้ใช้ แล้วพิมพ์คำตอบออกมา
# -------------------------

from core.llm_client import LLMClient

def main():
    # สร้าง object ของ LLMClient สำหรับติดต่อ LM Studio
    llm = LLMClient()

    print("=== AI Assistant (Gemma3 4B Q6_K via LM Studio) ===")
    print("พิมพ์ exit หรือ quit เพื่อออกจากโปรแกรม\n")

    while True:
        try:
            # รับข้อความจากผู้ใช้
            user_input = input("คุณ: ")

            # ถ้าผู้ใช้พิมพ์ exit/quit/q ให้ออกจาก loop
            if user_input.lower() in ["exit", "quit", "q"]:
                break

            # ส่งข้อความไปยังโมเดลแล้วรับคำตอบ
            reply = llm.ask(user_input)

            # แสดงคำตอบ
            print("ผู้ช่วย:", reply)

        # กด Ctrl+C เพื่อหยุดโปรแกรม
        except KeyboardInterrupt:
            print("\n[หยุดการทำงาน]")
            break

# เริ่มโปรแกรม
if __name__ == "__main__":
    main()
