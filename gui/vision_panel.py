# gui/vision_panel.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit, QComboBox
from PyQt6.QtCore import Qt
from core.vision_system import VisionSystem

class VisionPanel(QWidget):
    def __init__(self, vision_system: VisionSystem):
        super().__init__()
        self.setWindowTitle("🧠 Copilot Vision")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(400, 250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self.label = QLabel("เลือกหน้าจอที่ต้องการแชร์ให้ AI วิเคราะห์:")
        layout.addWidget(self.label)

        self.monitor_select = QComboBox()
        self.monitor_select.addItems(["Monitor 1", "Monitor 2"])
        layout.addWidget(self.monitor_select)

        self.capture_btn = QPushButton("📸 ถ่ายภาพหน้าจอและวิเคราะห์")
        layout.addWidget(self.capture_btn)

        self.ask_box = QTextEdit()
        self.ask_box.setPlaceholderText("พิมพ์คำถาม เช่น 'อ่านข้อความบนหน้าจอให้หน่อย'")
        layout.addWidget(self.ask_box)

        self.ask_btn = QPushButton("🧠 ถาม AI")
        layout.addWidget(self.ask_btn)

        self.result_label = QLabel("ผลลัพธ์จะแสดงที่นี่...")
        layout.addWidget(self.result_label)

        # Vision System (เชื่อมกับ AI)
        self.vision = vision_system

        self.capture_btn.clicked.connect(self._on_capture)
        self.ask_btn.clicked.connect(self._on_ask)

    def _on_capture(self):
        reply = self.vision.analyze("อธิบายสิ่งที่เห็นบนหน้าจอ", monitor=0)
        self.result_label.setText(reply)

    def _on_ask(self):
        user_prompt = self.ask_box.toPlainText().strip()
        if not user_prompt:
            self.result_label.setText("⚠️ โปรดพิมพ์คำถามก่อน")
            return
        reply = self.vision.ask_with_screenshot(user_prompt, monitor=0)
        self.result_label.setText(reply)
