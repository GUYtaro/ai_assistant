# test_screenshot.py
from core.screen_reader import screenshot_data_uri

uri, raw, img = screenshot_data_uri()
print("✅ ได้ data URI แล้ว!")
print("ความยาว:", len(uri))
print("ตัวอย่าง:", uri[:80] + "...")
img.show()  # เปิดภาพเพื่อดู (optional)