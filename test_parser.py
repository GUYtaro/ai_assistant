# test_parser.py
# ทดสอบ Command Parser

from core.command_parser import CommandParser
import json

print("=" * 70)
print("🧪 ทดสอบ Command Parser")
print("=" * 70)

parser = CommandParser()

# ทดสอบคำสั่งต่างๆ
test_commands = [
    "คลิกปุ่ม File",
    "พิมพ์ hello world",
    "กด enter",
    "กด ctrl+c",
    "เลื่อนลง 200",
    "คลิกที่พิกัด 100 200",
]

for i, cmd in enumerate(test_commands, 1):
    print(f"\n[{i}] คำสั่ง: '{cmd}'")
    ok, result = parser.parse(cmd)
    
    if ok:
        print(f"✅ แปลงสำเร็จ:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"❌ แปลงล้มเหลว: {result}")

print("\n" + "=" * 70)
print("💡 หมายเหตุ: การแปลงคำสั่งใช้ LLM ดังนั้นอาจต้องรอสักครู่")
print("=" * 70)