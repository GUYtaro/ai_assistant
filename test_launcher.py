# test_launcher.py
# ทดสอบ App Launcher

from core.app_launcher import AppLauncher
import time

launcher = AppLauncher()

print("=" * 70)
print("🧪 ทดสอบ App Launcher")
print("=" * 70)

# ทดสอบเปิด Notepad
print("\n[1] ทดสอบเปิด Notepad...")
result = launcher.launch("notepad")
print(f"   ผลลัพธ์: {result['message']}")
time.sleep(2)

# ทดสอบเปิด Calculator
print("\n[2] ทดสอบเปิด Calculator...")
result = launcher.launch("calculator")
print(f"   ผลลัพธ์: {result['message']}")
time.sleep(2)

# ทดสอบเปิด Chrome + YouTube
print("\n[3] ทดสอบเปิด Chrome + YouTube...")
result = launcher.open_url("https://youtube.com", "chrome")
print(f"   ผลลัพธ์: {result['message']}")

print("\n" + "=" * 70)
print("✅ ทดสอบเสร็จสิ้น")
print("=" * 70)