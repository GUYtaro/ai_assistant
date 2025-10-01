from core.tts_client import TTSClient

# สร้าง Client เป็นภาษาไทย
# สอดคล้องกับ main.py: ใช้แค่ lang="th" ใน Constructor
tts = TTSClient(lang="th")

# แสดงเสียงที่มี
print("== Voices ที่ตรวจพบ ==")
for vid, vname in tts.list_voices():
    print(f"{vid} -> {vname}")

# ปรับความเร็วและความดัง ด้วย Methods ที่เราได้เพิ่มเข้ามาใน TTSClient
# ตอนนี้ methods เหล่านี้ใช้งานได้แล้ว
tts.set_rate(180)     # ปรับความเร็ว
tts.set_volume(0.8)   # ปรับความดัง

# พูดข้อความต่างๆ
# การเรียก tts.speak() จะเป็นแบบ Blocking โดยอัตโนมัติ (จะรอพูดจบทีละประโยค)
print("[TTS] พูดประโยค 1: สวัสดีครับ...")
# *** แก้ไข: ลบ block=True/False ออก ***
tts.speak("สวัสดีครับ ตอนนี้ผมพูดภาษาไทยได้แล้ว") 
print("[TTS] พูดประโยค 2: นี่คือการทดสอบ...")
tts.speak("นี่คือการทดสอบระบบสังเคราะห์เสียง")

# เนื่องจาก speak() เป็น Blocking ทุกประโยคจะถูกพูดตามลำดับ
print("[TTS] พูดประโยค 3: ระบบนี้ทำงาน...")
tts.speak("ระบบนี้ทำงานแบบออฟไลน์ 100 เปอร์เซ็นต์")

# หยุดการพูด (ถึงแม้จะไม่จำเป็นเพราะ speak() เป็น Blocking แต่ก็ใส่ไว้เพื่อทดสอบ method stop() ที่เพิ่มเข้ามา)
tts.stop() 
print("[TTS] การพูดทั้งหมดเสร็จสมบูรณ์")
