# test_controller.py
# ทดสอบ Keyboard Mouse Controller

from core.keyboard_mouse_controller import KeyboardMouseController
import time

print("=" * 70)
print("🧪 ทดสอบ Controller")
print("=" * 70)

controller = KeyboardMouseController(monitor=1)

print("\n=== ทดสอบค้นหาและขยับเมาส์ไปที่ 'File' ===")
print("⏰ จะเริ่มใน 3 วินาที...")
time.sleep(3)

element = controller.detector.find_element_by_text("File")
if element:
    center = controller.detector.get_element_center(element)
    print(f"✅ พบ 'File' ที่ {center}")
    print("🖱️ กำลังขยับเมาส์...")
    controller.mouse.move_to(center[0], center[1], duration=1)
    print("✅ เสร็จสิ้น!")
else:
    print("❌ ไม่พบ 'File' บนหน้าจอ")

print("\n💡 ถ้าต้องการทดสอบคลิก ให้แก้โค้ดเป็น:")
print("   controller.mouse.click(center[0], center[1])")