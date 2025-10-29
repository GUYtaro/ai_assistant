# gui/assistant_bar.py
# ================================
# 🎨 AssistantBar v3 (Combined Pro Version)
# ✅ รวมจุดเด่นจากทั้งสองเวอร์ชัน
# ================================

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, 
    QLineEdit, QSizeGrip, QProgressBar
)
from PyQt6.QtCore import pyqtSignal, Qt, QPoint, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen


class AssistantBar(QWidget):
    """💬 Modern AI Assistant Bar - Combined Pro Version"""

    text_submitted = pyqtSignal(str)
    mic_pressed = pyqtSignal()
    mic_released = pyqtSignal()
    close_requested = pyqtSignal()
    stop_speaking_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.drag_pos = QPoint()
        self.recording = False
        self.glow_opacity = 0.0
        self.glow_direction = 1
        self.record_progress = 0
        
        self._init_ui()
        self._init_effects()

    def _init_ui(self):
        """ตั้งค่า UI ที่รวมจุดเด่นจากทั้งสองเวอร์ชัน"""
        self.setWindowTitle("AI Assistant Pro")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(480, 100)  # ขนาดกะทัดรัดแต่พอดี

        # =====================================================
        # 🎨 DESIGN: Dark Blue Gradient (จากเวอร์ชันแรก)
        # =====================================================
        self.setStyleSheet("""
            QWidget#main_panel {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                              stop:0 #071428, stop:1 #0b3b61);
                border-radius: 12px;
                color: #E6F0FF;
                font-family: Segoe UI, Roboto, "Tahoma";
                border: 1px solid #1a3b5a;
            }
            QPushButton#mic_button {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ff5f6d, stop:1 #ffc371);
                color: #fff;
                border-radius: 10px;
                padding: 8px;
                font-size: 16px;
                border: 2px solid #ff9966;
            }
            QPushButton#mic_button:pressed {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ff3d4a, stop:1 #ffb347);
            }
            QPushButton#send_button {
                background: rgba(255,255,255,0.1);
                color: #cfe8ff;
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton#send_button:hover {
                background: rgba(255,255,255,0.15);
            }
            QPushButton#stop_button {
                background: rgba(255,100,100,0.2);
                color: #ffdddd;
                border: 1px solid rgba(255,100,100,0.3);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 12px;
            }
            QPushButton#stop_button:hover {
                background: rgba(255,100,100,0.3);
            }
            QPushButton#close_button {
                background: rgba(255,100,100,0.2);
                color: #ffdddd;
                border: 1px solid rgba(255,100,100,0.3);
                border-radius: 10px;
                padding: 4px;
                font-size: 14px;
            }
            QPushButton#close_button:hover {
                background: rgba(255,100,100,0.4);
            }
            QLineEdit {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.15);
                padding: 8px 12px;
                color: #E6F0FF;
                border-radius: 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #00ccff;
                background: rgba(255,255,255,0.12);
            }
            QLineEdit::placeholder {
                color: #88aacc;
            }
            QLabel#status_label {
                color: #aaccff;
                font-weight: bold;
                font-size: 12px;
            }
            QLabel#response_label {
                color: #cfe8ff;
                font-size: 12px;
                padding: 2px 0px;
            }
        """)

        # =====================================================
        # 🏗️ LAYOUT: Combined Structure
        # =====================================================
        main_panel = QWidget()
        main_panel.setObjectName("main_panel")
        
        # Layout หลัก
        main_layout = QVBoxLayout(main_panel)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(6)

        # =====================================================
        # 🔝 แถบบน: Status + Control Buttons (จากเวอร์ชันแรก)
        # =====================================================
        top_bar = QHBoxLayout()
        
        # Status Label
        self.status_label = QLabel("พร้อมใช้งาน ✅")
        self.status_label.setObjectName("status_label")
        self.status_label.setFixedHeight(16)
        
        # Stop Button (จากเวอร์ชันแรก)
        self.stop_button = QPushButton("หยุดพูด")
        self.stop_button.setObjectName("stop_button")
        self.stop_button.setToolTip("หยุดการพูดปัจจุบัน")
        self.stop_button.setFixedSize(60, 24)
        
        # Close Button (จากเวอร์ชันสอง)
        self.close_button = QPushButton("✖")
        self.close_button.setObjectName("close_button")
        self.close_button.setToolTip("ปิดแอป")
        self.close_button.setFixedSize(24, 24)
        
        top_bar.addWidget(self.status_label)
        top_bar.addStretch()
        top_bar.addWidget(self.stop_button)
        top_bar.addWidget(self.close_button)

        # =====================================================
        # 🔄 แถบกลาง: Input + Mic (รวมทั้งสองเวอร์ชัน)
        # =====================================================
        input_bar = QHBoxLayout()
        input_bar.setSpacing(8)
        
        # Text Input
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("พิมพ์คำสั่ง หรือ กดค้างไมค์เพื่อพูด...")
        self.text_input.setMinimumHeight(32)
        
        # Send Button (จากเวอร์ชันแรก)
        self.send_button = QPushButton("ส่ง")
        self.send_button.setObjectName("send_button")
        self.send_button.setFixedSize(50, 32)
        
        # Mic Button (รวมจุดเด่นทั้งสอง)
        self.mic_button = QPushButton("🎤")
        self.mic_button.setObjectName("mic_button")
        self.mic_button.setFixedSize(50, 32)
        
        input_bar.addWidget(self.text_input)
        input_bar.addWidget(self.send_button)
        input_bar.addWidget(self.mic_button)

        # =====================================================
        # 📊 แถบล่าง: Progress + Response (จากเวอร์ชันสอง)
        # =====================================================
        bottom_bar = QVBoxLayout()
        bottom_bar.setSpacing(4)
        
        # Progress Bar สำหรับบันทึกเสียง (จากเวอร์ชันสอง)
        self.record_bar = QProgressBar()
        self.record_bar.setFixedHeight(4)
        self.record_bar.setRange(0, 100)
        self.record_bar.setValue(0)
        self.record_bar.setTextVisible(False)
        self.record_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(0,0,0,0.3);
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #00ffaa;
                border-radius: 2px;
            }
        """)
        
        # Response Label (จากเวอร์ชันสอง)
        self.response_label = QLabel("🤖 รอคำสั่งจากคุณ...")
        self.response_label.setObjectName("response_label")
        self.response_label.setMinimumHeight(16)
        
        bottom_bar.addWidget(self.record_bar)
        bottom_bar.addWidget(self.response_label)

        # =====================================================
        # 🎯 รวมทุกส่วนเข้าด้วยกัน
        # =====================================================
        main_layout.addLayout(top_bar)
        main_layout.addLayout(input_bar)
        main_layout.addLayout(bottom_bar)

        # Size Grip (จากทั้งสองเวอร์ชัน)
        self.size_grip = QSizeGrip(self)
        grip_layout = QHBoxLayout()
        grip_layout.addStretch()
        grip_layout.addWidget(self.size_grip)
        main_layout.addLayout(grip_layout)

        # ตั้งค่า Layout หลัก
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_panel)

        # =====================================================
        # 🔗 การเชื่อมต่อสัญญาณ
        # =====================================================
        self.text_input.returnPressed.connect(self._on_send_clicked)
        self.send_button.clicked.connect(self._on_send_clicked)
        self.mic_button.pressed.connect(self._on_mic_pressed)
        self.mic_button.released.connect(self._on_mic_released)
        self.stop_button.clicked.connect(self.stop_speaking_requested.emit)
        self.close_button.clicked.connect(self.close_requested.emit)

        # ตำแหน่งเริ่มต้น (ปรับจากทั้งสองเวอร์ชัน)
        screen = self.screen().geometry()
        self.move(screen.width() - self.width() - 20, screen.height() - 120)

    def _init_effects(self):
        """เอฟเฟกต์จากเวอร์ชันสอง"""
        # เอฟเฟกต์แสงเรือง
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self._update_glow)
        
        # Progress animation
        self.record_timer = QTimer(self)
        self.record_timer.timeout.connect(self._update_record_bar)

    def _update_glow(self):
        """อัพเดทเอฟเฟกต์แสงเรือง"""
        if not self.recording:
            return
        self.glow_opacity += 0.08 * self.glow_direction
        if self.glow_opacity > 1.0:
            self.glow_direction = -1
            self.glow_opacity = 1.0
        elif self.glow_opacity < 0.3:
            self.glow_direction = 1
            self.glow_opacity = 0.3
        self.update()

    def _update_record_bar(self):
        """อัพเดท progress bar บันทึกเสียง"""
        if not self.recording:
            return
        self.record_progress = (self.record_progress + 3) % 100
        self.record_bar.setValue(self.record_progress)

    def paintEvent(self, event):
        """วาดเอฟเฟกต์แสงเรือง (จากเวอร์ชันสอง)"""
        if self.recording:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # วงเรืองแสงรอบไมค์
            glow_color = QColor(255, 255, 255, int(80 * self.glow_opacity))
            painter.setBrush(QBrush(glow_color))
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            
            # หาตำแหน่งปุ่มไมค์
            mic_center = self.mic_button.geometry().center()
            global_center = self.mapToGlobal(mic_center)
            local_center = self.mapFromGlobal(global_center)
            
            painter.drawEllipse(local_center, 35, 35)

    # =====================================================
    # 🎮 Event Handlers
    # =====================================================
    def _on_send_clicked(self):
        """ส่งข้อความ (จากเวอร์ชันแรก)"""
        text = self.text_input.text().strip()
        if text:
            self.text_submitted.emit(text)
            self.text_input.clear()

    def _on_mic_pressed(self):
        """เริ่มบันทึกเสียง (รวมจุดเด่นทั้งสอง)"""
        self.recording = True
        self.record_bar.setValue(0)
        self.record_timer.start(50)
        self.glow_timer.start(60)
        self.mic_button.setText("🎙️")
        self.status_label.setText("🔴 กำลังฟัง...")
        self.mic_pressed.emit()

    def _on_mic_released(self):
        """หยุดบันทึกเสียง"""
        self.recording = False
        self.glow_timer.stop()
        self.record_timer.stop()
        self.record_bar.setValue(100)
        self.mic_button.setText("🎤")
        self.status_label.setText("⏳ ประมวลผล...")
        self.mic_released.emit()

    # =====================================================
    # 🖱️ Draggable Window (จากทั้งสองเวอร์ชัน)
    # =====================================================
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None
        event.accept()

    # =====================================================
    # 🧠 Public API (รวมทั้งสองเวอร์ชัน)
    # =====================================================
    def show_ai_response(self, text: str, speak: bool = True):
        """แสดงข้อความตอบกลับจาก AI"""
        # แสดงเต็มใน response_label (จากเวอร์ชันสอง)
        self.response_label.setText(text)
        
        # แสดงย่อใน status_label (จากเวอร์ชันแรก)
        display_text = text[:100] + "..." if len(text) > 100 else text
        self.status_label.setText(f"🤖 {display_text}")
        
        if speak:
            print(f"[TTS] 🗣️ {text}")

    def show_voice_input(self, text: str):
        """แสดงข้อความที่ผู้ใช้พูด"""
        self.response_label.setText(f"🎤 {text}")
        self.status_label.setText(f"📝 คุณพูดว่า: {text}")


if __name__ == "__main__":
    # ทดสอบ AssistantBar v3
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    bar = AssistantBar()
    bar.show()
    
    # ทดสอบสัญญาณ
    bar.text_submitted.connect(lambda t: print(f"📤 Text: {t}"))
    bar.mic_pressed.connect(lambda: print("🔴 Mic Pressed"))
    bar.mic_released.connect(lambda: print("⏹️ Mic Released"))
    bar.stop_speaking_requested.connect(lambda: print("⏹️ Stop Speaking"))
    bar.close_requested.connect(lambda: print("❌ Close Requested"))
    
    print("🎯 AssistantBar v3 (Combined) พร้อมใช้งาน!")
    print("📍 ลากเคลื่อนย้ายได้ • 📏 ขยายขนาดได้ • 🎤 กดค้างไมค์ • ⏹️ หยุดพูดได้")
    
    sys.exit(app.exec())