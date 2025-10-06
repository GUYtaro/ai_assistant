# test_vision_debug.py
# -------------------------
# ทดสอบ Vision Mode แบบละเอียด
# -------------------------

from core.vision_system import VisionSystem
from core.screen_capturer import screenshot_data_uri
import json

print("=" * 60)
print("🔍 Vision System Debug Test")
print("=" * 60)

# 1. ทดสอบจับภาพหน้าจอ
print("\n[1] กำลังจับภาพหน้าจอ...")
try:
    data_uri, raw_bytes, img = screenshot_data_uri(resize_to=(512, 384), fmt="JPEG", quality=70)
    print(f"✅ จับภาพสำเร็จ! ขนาด: {img.size}")
    print(f"📦 ขนาดไฟล์: {len(raw_bytes):,} bytes")
    print(f"📊 Data URI length: {len(data_uri):,} chars")
    print(f"🔍 Data URI preview: {data_uri[:80]}...")
except Exception as e:
    print(f"❌ จับภาพล้มเหลว: {e}")
    exit(1)

# 2. ทดสอบส่งไปยัง LLM
print("\n[2] กำลังส่งภาพไปยัง LM Studio...")
vision = VisionSystem()

try:
    result = vision.analyze(
        user_prompt="อธิบายสิ่งที่เห็นในภาพนี้เป็นภาษาไทยสั้นๆ",
        monitor=0
    )
    print("\n" + "=" * 60)
    print("📝 คำตอบจาก LLM:")
    print("=" * 60)
    print(result)
    print("=" * 60)
    
    # ตรวจสอบว่าเป็น error หรือไม่
    if "[ERROR]" in result or "[LLM ERROR]" in result or "[VISION ERROR]" in result:
        print("\n⚠️ พบ error ในคำตอบ - โปรดตรวจสอบ LM Studio")
    else:
        print("\n✅ Vision System ทำงานได้ปกติ!")
        
except Exception as e:
    print(f"\n❌ เกิดข้อผิดพลาด: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("💡 Tips:")
print("- ถ้าเห็น error 'model not found': ตรวจสอบว่าโมเดลโหลดแล้วใน LM Studio")
print("- ถ้าเห็น error 'connection refused': ตรวจสอบว่า Server เปิดอยู่")
print("- ถ้า LLM ตอบแต่ไม่เกี่ยวกับภาพ: โมเดลอาจไม่รองรับ Vision จริง")
print("=" * 60)