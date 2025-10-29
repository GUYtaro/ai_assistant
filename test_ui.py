# test_ui.py
# ทดสอบ UI Detector
# วาง file นี้ที่ root ของโปรเจกต์ (ไม่ใช่ใน core/)

from core.ui_detector import UIDetector

print("=" * 70)
print("🧪 ทดสอบ UI Detector")
print("=" * 70)

detector = UIDetector(monitor=1)

print("\n=== ทดสอบค้นหาข้อความ 'File' ===")
element = detector.find_element_by_text("File")
if element:
    print(f"✅ พบ 'File' ที่ตำแหน่ง:")
    print(f"   x={element['x']}, y={element['y']}")
    print(f"   w={element['w']}, h={element['h']}")
    print(f"   confidence={element['confidence']}")
    
    center = detector.get_element_center(element)
    print(f"📍 จุดศูนย์กลาง: {center}")
else:
    print("❌ ไม่พบ 'File' บนหน้าจอ")

print("\n=== ข้อความทั้งหมดบนหน้าจอ (10 อันแรก) ===")
all_text = detector.find_all_text()
print(f"พบ {len(all_text)} ข้อความ")
for i, t in enumerate(all_text[:10]):
    print(f"{i+1}. '{t['text']}' @ ({t['x']}, {t['y']})")

print("\n✅ ทดสอบเสร็จสิ้น")