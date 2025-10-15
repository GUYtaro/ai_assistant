# gui/main_window.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTextEdit, QLabel
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

class AIAssistantGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant Pro")
        self.setGeometry(400, 200, 700, 500)
        self.setStyleSheet("""
            QWidget { background-color: #0f111a; color: #e0e0e0; font-family: 'Segoe UI'; }
            QLineEdit {
                background-color: #1a1c25; border-radius: 12px; padding: 10px;
                border: 1px solid #333; color: #fff;
            }
            QPushButton {
                background-color: #2b2d3a; border-radius: 10px;
                padding: 8px 15px; color: #ddd;
            }
            QPushButton:hover { background-color: #383b4a; }
            QTextEdit {
                background-color: #161821; border: none;
                border-radius: 12px; padding: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Ask anything...")
        self.send_btn = QPushButton("Send")
        self.mic_btn = QPushButton("🎤")
        self.mic_btn.setToolTip("Voice Mode")

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.mic_btn)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(QLabel("🤖 AI Assistant (Full Voice + Vision Mode)"))
        layout.addWidget(self.output)
        layout.addLayout(input_layout)

        # Connect events
        self.send_btn.clicked.connect(self.send_message)
        self.input_line.returnPressed.connect(self.send_message)
        self.mic_btn.clicked.connect(self.activate_voice_mode)

    def send_message(self):
        text = self.input_line.text().strip()
        if text:
            self.output.append(f"🧑‍💻 คุณ: {text}")
            # TODO: ส่งข้อความไปที่ Core LLMClient / AutomationExecutor
            self.output.append("🤖 ผู้ช่วย: กำลังประมวลผล...\n")
            self.input_line.clear()

    def activate_voice_mode(self):
        self.output.append("🎤 Voice Mode: กำลังฟังเสียง...")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = AIAssistantGUI()
    win.show()
    sys.exit(app.exec())
