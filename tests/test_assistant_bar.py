# test_assistant_bar.py
# ================================
# 🧪 Test Script for AssistantBar v2
# ================================

import sys
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QTextEdit
from PyQt6.QtCore import QTimer
from gui.assistant_bar import AssistantBar


class TestWindow(QMainWindow):
    """หน้าต่างทดสอบ AssistantBar"""
    
    def __init__(self):
        super().__init__()
        self.assistant_bar = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("🧪 AssistantBar v2 Test Suite")
        self.setGeometry(100, 100, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        # ปุ่มทดสอบต่างๆ
        self.btn_show_bar = QPushButton("🚀 แสดง AssistantBar")
        self.btn_show_bar.clicked.connect(self.show_assistant_bar)
        
        self.btn_test_voice = QPushButton("🎤 ทดสอบแสดงข้อความเสียง")
        self.btn_test_voice.clicked.connect(self.test_voice_input)
        
        self.btn_test_ai_response = QPushButton("🤖 ทดสอบแสดงข้อความ AI")
        self.btn_test_ai_response.clicked.connect(self.test_ai_response)
        
        self.btn_test_recording = QPushButton("🔴 ทดสอบสถานะบันทึกเสียง")
        self.btn_test_recording.clicked.connect(self.test_recording_state)
        
        self.btn_hide_bar = QPushButton("👻 ซ่อน AssistantBar")
        self.btn_hide_bar.clicked.connect(self.hide_assistant_bar)
        
        self.log_text = QTextEdit()
        self.log_text.setPlaceholderText("Log จะแสดงที่นี่...")
        
        layout.addWidget(self.btn_show_bar)
        layout.addWidget(self.btn_test_voice)
        layout.addWidget(self.btn_test_ai_response)
        layout.addWidget(self.btn_test_recording)
        layout.addWidget(self.btn_hide_bar)
        layout.addWidget(self.log_text)
        
        central_widget.setLayout(layout)
        
        # เชื่อมต่อสัญญาณจาก AssistantBar
        self.connect_assistant_signals()
        
    def connect_assistant_signals(self):
        """เชื่อมต่อสัญญาณจาก AssistantBar"""
        if self.assistant_bar:
            self.assistant_bar.text_submitted.connect(self.on_text_submitted)
            self.assistant_bar.mic_pressed.connect(self.on_mic_pressed)
            self.assistant_bar.mic_released.connect(self.on_mic_released)
            self.assistant_bar.close_requested.connect(self.on_close_requested)
    
    def log_message(self, message):
        """เพิ่มข้อความลงใน log"""
        self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {message}")
    
    def show_assistant_bar(self):
        """แสดง AssistantBar"""
        if not self.assistant_bar:
            self.assistant_bar = AssistantBar()
            self.connect_assistant_signals()
        
        self.assistant_bar.show()
        self.log_message("✅ แสดง AssistantBar แล้ว")
        self.log_message("📍 ลากเมาส์บนแถบเพื่อเคลื่อนย้าย")
        self.log_message("📝 พิมพ์ข้อความแล้วกด Enter เพื่อทดสอบ")
        self.log_message("🎤 กดค้างปุ่มไมค์เพื่อทดสอบ Push-to-Talk")
    
    def hide_assistant_bar(self):
        """ซ่อน AssistantBar"""
        if self.assistant_bar:
            self.assistant_bar.hide()
            self.log_message("❌ ซ่อน AssistantBar แล้ว")
    
    def test_voice_input(self):
        """ทดสอบแสดงข้อความจากเสียง"""
        if self.assistant_bar:
            test_phrases = [
                "เปิด YouTube",
                "สภาพอากาศวันนี้เป็นอย่างไร",
                "ตั้ง้ตัวจับเวลา 5 นาที",
                "เล่นเพลงสตริงใหม่ล่าสุด"
            ]
            import random
            phrase = random.choice(test_phrases)
            self.assistant_bar.show_voice_input(phrase)
            self.log_message(f"🎤 แสดงข้อความเสียง: '{phrase}'")
    
    def test_ai_response(self):
        """ทดสอบแสดงข้อความตอบกลับจาก AI"""
        if self.assistant_bar:
            test_responses = [
                "เปิด YouTube ให้แล้วครับ!",
                "วันนี้อากาศแจ่มใส อุณหภูมิ 32°C",
                "ตั้งเวลาจับเวลา 5 นาทีเรียบร้อยแล้ว",
                "กำลังเล่นเพลงสตริงใหม่ล่าสุดให้คุณ..."
            ]
            import random
            response = random.choice(test_responses)
            self.assistant_bar.show_ai_response(response)
            self.log_message(f"🤖 แสดงข้อความ AI: '{response}'")
    
    def test_recording_state(self):
        """ทดสอบสถานะบันทึกเสียง"""
        if self.assistant_bar:
            self.log_message("🔴 เริ่มทดสอบสถานะบันทึกเสียง...")
            
            # จำลองการกดไมค์
            self.assistant_bar._on_mic_pressed()
            self.log_message("🎤 สถานะ: กำลังบันทึกเสียง")
            
            # จำลองการปล่อยไมค์หลังจาก 2 วินาที
            QTimer.singleShot(2000, lambda: self.assistant_bar._on_mic_released())
            QTimer.singleShot(2000, lambda: self.log_message("⏹️ สถานะ: หยุดบันทึกเสียง"))
            
            # แสดงข้อความเสียงหลังจากประมวลผล
            QTimer.singleShot(2500, self.test_voice_input)
    
    def on_text_submitted(self, text):
        """เมื่อมีข้อความถูกส่งจาก GUI"""
        self.log_message(f"📤 ได้รับข้อความจาก AssistantBar: '{text}'")
    
    def on_mic_pressed(self):
        """เมื่อกดปุ่มไมค์"""
        self.log_message("🔴 ปุ่มไมค์ถูกกด (เริ่มบันทึกเสียง)")
    
    def on_mic_released(self):
        """เมื่อปล่อยปุ่มไมค์"""
        self.log_message("⏹️ ปุ่มไมค์ถูกปล่อย (หยุดบันทึกเสียง)")
    
    def on_close_requested(self):
        """เมื่อขอปิด AssistantBar"""
        self.log_message("❌ ผู้ใช้ขอปิด AssistantBar")
        self.assistant_bar.hide()


def run_standalone_test():
    """ทดสอบ AssistantBar แบบ standalone"""
    print("🧪 เริ่มต้นทดสอบ AssistantBar v2 (Pro GUI)...")
    
    app = QApplication(sys.argv)
    
    # สร้าง AssistantBar โดยตรง
    assistant = AssistantBar()
    assistant.show()
    
    # เชื่อมต่อสัญญาณเพื่อดูการทำงาน
    assistant.text_submitted.connect(lambda text: print(f"📤 Text Submitted: {text}"))
    assistant.mic_pressed.connect(lambda: print("🔴 Mic Pressed"))
    assistant.mic_released.connect(lambda: print("⏹️ Mic Released"))
    assistant.close_requested.connect(lambda: print("❌ Close Requested"))
    
    # ทดสอบอัตโนมัติหลังจากแสดง GUI
    def auto_test():
        print("🚀 เริ่มทดสอบอัตโนมัติ...")
        
        # ทดสอบแสดงข้อความเสียง
        assistant.show_voice_input("นี่คือข้อความทดสอบจากเสียง")
        print("🎤 ทดสอบแสดงข้อความเสียง")
        
        # ทดสอบแสดงข้อความ AI หลังจาก 2 วินาที
        QTimer.singleShot(2000, lambda: assistant.show_ai_response("นี่คือการตอบกลับจาก AI สำหรับทดสอบระบบ"))
        QTimer.singleShot(2000, lambda: print("🤖 ทดสอบแสดงข้อความ AI"))
        
        # ทดสอบบันทึกเสียงหลังจาก 4 วินาที
        QTimer.singleShot(4000, assistant._on_mic_pressed)
        QTimer.singleShot(4000, lambda: print("🔴 ทดสอบเริ่มบันทึกเสียง"))
        
        QTimer.singleShot(6000, assistant._on_mic_released)
        QTimer.singleShot(6000, lambda: print("⏹️ ทดสอบหยุดบันทึกเสียง"))
    
    QTimer.singleShot(1000, auto_test)
    
    print("✅ AssistantBar พร้อมใช้งาน!")
    print("📍 ลากเมาส์บนแถบเพื่อเคลื่อนย้าย")
    print("📝 พิมพ์ข้อความแล้วกด Enter เพื่อทดสอบ")
    print("🎤 กดค้างปุ่มไมค์เพื่อทดสอบ Push-to-Talk")
    print("⏳ ทดสอบอัตโนมัติจะเริ่มใน 1 วินาที...")
    
    sys.exit(app.exec())


def run_comprehensive_test():
    """ทดสอบแบบครบถ้วนกับ Test Window"""
    app = QApplication(sys.argv)
    
    test_window = TestWindow()
    test_window.show()
    
    print("🧪 เริ่มต้น Comprehensive Test...")
    print("📍 ใช้ปุ่มในหน้าต่างเพื่อทดสอบฟีเจอร์ต่างๆ")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    # เลือกโหมดทดสอบ
    print("เลือกโหมดทดสอบ:")
    print("1. 🎯 Standalone Test (ทดสอบ AssistantBar โดยตรง)")
    print("2. 📊 Comprehensive Test (ทดสอบแบบครบถ้วน)")
    
    choice = input("ใส่ตัวเลือก (1 หรือ 2): ").strip()
    
    if choice == "1":
        run_standalone_test()
    else:
        run_comprehensive_test()