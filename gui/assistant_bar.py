# gui/assistant_bar.py
# -------------------------
# Floating Assistant Bar - แถบผู้ช่วยลอยได้
# -------------------------

import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, 
                             QLineEdit, QPushButton, QLabel, QVBoxLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon


class AssistantBar(QWidget):
    """
    Floating Assistant Bar - แถบผู้ช่วยลอยได้
    """
    
    # สัญญาณสำหรับสั่งปิดโปรแกรม
    close_requested = pyqtSignal()
    # เพิ่มสัญญาณสำหรับส่งข้อความจาก input
    text_submitted = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # ตั้งค่าต่างๆ ของ window
        self.setWindowTitle("AI Assistant")
        self.setFixedSize(500, 80)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                           Qt.WindowType.WindowStaysOnTopHint |
                           Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # สร้าง layout หลัก
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # สร้าง widget หลักที่มีพื้นหลังสีดำ
        self.main_widget = QWidget()
        self.main_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.95);
                border: 2px solid #555555;
                border-radius: 20px;
            }
        """)
        
        # สร้าง layout สำหรับเนื้อหา
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        # สร้างปุ่มเมนู
        self.menu_button = QPushButton("☰")
        self.menu_button.setFixedSize(40, 40)
        self.menu_button.setStyleSheet("""
            QPushButton {
                background-color: #666666;
                border: none;
                border-radius: 20px;
                color: white;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #777777;
            }
            QPushButton:pressed {
                background-color: #555555;
            }
        """)
        
        # สร้างช่องป้อนข้อความ
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("พิมพ์คำสั่งหรือกดไมค์...")
        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: #333333;
                border: 2px solid #444444;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 14px;
                color: white;
                selection-background-color: #666666;
            }
            QLineEdit:focus {
                border-color: #666666;
            }
            QLineEdit::placeholder {
                color: #888888;
            }
        """)
        
        # เชื่อมต่อการกด Enter กับฟังก์ชันส่งข้อความ
        self.input_box.returnPressed.connect(self.on_text_submitted)
        
        # สร้างปุ่มไมค์
        self.mic_button = QPushButton("🎤")
        self.mic_button.setFixedSize(40, 40)
        self.mic_button.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                border: none;
                border-radius: 20px;
                color: white;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #333333;
            }
        """)
        
        # สร้าง label สำหรับแสดงสถานะ
        self.status_label = QLabel("พร้อมใช้งาน")
        self.status_label.setFixedSize(120, 30)
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #222222;
                border: 1px solid #333333;
                border-radius: 15px;
                padding: 5px 10px;
                font-size: 11px;
                color: #cccccc;
                qproperty-alignment: AlignCenter;
            }
        """)
        self.status_label.setFont(QFont("Segoe UI", 9))
        
        # สร้างปุ่มปิดโปรแกรม
        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                border: none;
                border-radius: 15px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #ff5555;
            }
            QPushButton:pressed {
                background-color: #cc0000;
            }
        """)
        self.close_button.clicked.connect(self.request_close)
        
        # เพิ่มวิดเจ็ตลงใน layout
        layout.addWidget(self.menu_button)
        layout.addWidget(self.input_box)
        layout.addWidget(self.mic_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.close_button)
        
        # ตั้งค่า layout
        self.main_widget.setLayout(layout)
        main_layout.addWidget(self.main_widget)
        self.setLayout(main_layout)
        
        # ตั้งค่าให้สามารถลากได้
        self.dragging = False
        self.offset = None
        
        # ตั้งค่าเริ่มต้นให้อยู่มุมล่างขวา
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        self.move(screen_geometry.width() - self.width() - 20, 
                 screen_geometry.height() - self.height() - 20)
    
    def on_text_submitted(self):
        """เมื่อผู้ใช้กด Enter ในช่องป้อนข้อความ"""
        text = self.input_box.text().strip()
        if text:
            print(f"📤 ส่งข้อความจาก GUI: {text}")
            self.text_submitted.emit(text)
            self.input_box.clear()
    
    def request_close(self):
        """ส่งสัญญาณขอปิดโปรแกรม"""
        self.close_requested.emit()
    
    def mousePressEvent(self, event):
        """เมื่อกดเมาส์เพื่อลาก"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.position().toPoint()
    
    def mouseMoveEvent(self, event):
        """เมื่อลากเมาส์"""
        if self.dragging and self.offset is not None:
            new_pos = event.globalPosition().toPoint() - self.offset
            self.move(new_pos)
    
    def mouseReleaseEvent(self, event):
        """เมื่อปล่อยเมาส์"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.offset = None
    
    def enterEvent(self, event):
        """เมื่อเมาส์เข้ามาในพื้นที่"""
        self.main_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.98);
                border: 2px solid #666666;
                border-radius: 20px;
            }
        """)
    
    def leaveEvent(self, event):
        """เมื่อเมาส์ออกจากพื้นที่"""
        self.main_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.95);
                border: 2px solid #555555;
                border-radius: 20px;
            }
        """)


if __name__ == "__main__":
    # ทดสอบ Assistant Bar
    app = QApplication(sys.argv)
    
    bar = AssistantBar()
    bar.show()
    
    # เชื่อมต่อสัญญาณปิดโปรแกรม
    bar.close_requested.connect(app.quit)
    
    # เชื่อมต่อสัญญาณส่งข้อความ (สำหรับทดสอบ)
    bar.text_submitted.connect(lambda text: print(f"📨 ข้อความที่ส่ง: {text}"))
    
    print("Assistant Bar พร้อมใช้งาน - ลากไปวางตำแหน่งใดก็ได้บนหน้าจอ")
    print("กดปุ่ม X เพื่อปิดโปรแกรม")
    print("พิมพ์ข้อความในช่องแล้วกด Enter เพื่อส่งคำสั่ง")
    
    sys.exit(app.exec())