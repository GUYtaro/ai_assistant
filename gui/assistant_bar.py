import sys
from PyQt6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QLineEdit, QPushButton, QVBoxLayout, QLabel, QFrame
)
from PyQt6.QtGui import QIcon, QFont, QColor, QPainter, QBrush, QPalette

class AssistantBar(QWidget):
    """
    🔹 Floating Assistant Bar (Copilot-style)
    - แสดงด้านล่างจอ
    - มีช่องพิมพ์ + ปุ่มเสียง + ปุ่มฟังก์ชัน
    - สามารถขยาย/ย่อได้อัตโนมัติ
    """

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedHeight(70)

        # 🌈 Layout หลัก
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(10)

        # 📝 ช่องพิมพ์ข้อความ
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("พิมพ์ข้อความ หรือพูดผ่านไมค์...")
        self.input_box.setFont(QFont("Segoe UI", 11))
        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: rgba(30, 30, 30, 230);
                color: white;
                border: 1px solid rgba(255, 255, 255, 60);
                border-radius: 25px;
                padding: 10px 20px;
            }
        """)

        # 🎤 ปุ่มไมค์
        self.mic_button = QPushButton("🎤")
        self.mic_button.setFixedSize(40, 40)
        self.mic_button.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border-radius: 20px;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #4e4e4e;
            }
        """)

        # ⚙️ ปุ่มเมนู (ฟังก์ชัน)
        self.menu_button = QPushButton("⋮")
        self.menu_button.setFixedSize(40, 40)
        self.menu_button.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border-radius: 20px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #4e4e4e;
            }
        """)

        # 🧠 ป้ายสถานะเล็ก (AI กำลังคิด)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ✅ รวมทั้งหมด
        main_layout.addWidget(self.menu_button)
        main_layout.addWidget(self.input_box, 1)
        main_layout.addWidget(self.mic_button)

        # 🔲 เฟรมหลัก
        self.setLayout(main_layout)
        self.resize(500, 70)

        # 🔧 ตั้งตำแหน่งล่างจอ (center bottom)
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = screen.height() - self.height() - 40
        self.move(x, y)

        # 🎬 Animation เข้า-ออก
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(500)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.fade_in()

        # 🧩 Connect signals
        self.mic_button.clicked.connect(self.on_mic_clicked)
        self.menu_button.clicked.connect(self.on_menu_clicked)

    def fade_in(self):
        self.setWindowOpacity(0)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.start()

    def fade_out(self):
        self.anim.setStartValue(1)
        self.anim.setEndValue(0)
        self.anim.start()

    def on_mic_clicked(self):
        print("[AssistantBar] 🎤 Voice mode triggered")

    def on_menu_clicked(self):
        print("[AssistantBar] ⚙️ Menu clicked")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    bar = AssistantBar()
    bar.show()
    sys.exit(app.exec())
