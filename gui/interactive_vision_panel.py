# gui/interactive_vision_panel.py
# ================================
# 🖱️ Interactive Vision Panel
# โต้ตอบกับหน้าจอ - คลิก/ลากเพื่อถาม AI
# ================================

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QComboBox
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont
import sys


class InteractiveVisionPanel(QWidget):
    """
    🖱️ หน้าต่างโต้ตอบกับหน้าจอ
    
    ฟีเจอร์:
    - คลิกเพื่อถามเกี่ยวกับตำแหน่งนั้น
    - ลากกรอบเพื่อเลือกพื้นที่สนใจ
    - เลือกโหมดคำถาม (อธิบาย/วิเคราะห์/แนะนำ)
    """
    
    # สัญญาณต่างๆ
    point_selected = pyqtSignal(int, int, str)  # x, y, mode
    region_selected = pyqtSignal(int, int, int, int, str)  # x, y, w, h, mode
    close_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
        # สถานะการลาก
        self.dragging = False
        self.start_point = None
        self.current_point = None
        
    def setup_ui(self):
        """ตั้งค่า UI"""
        self.setWindowTitle("🖱️ Interactive Vision Mode")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # ขยายเต็มจอ
        screen = self.screen().geometry()
        self.setGeometry(screen)
        
        # Layout หลัก
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # แถบควบคุมที่มุมขวาบน
        self.control_panel = self._create_control_panel()
        self.control_panel.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.85);
                border-radius: 12px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton {
                background: rgba(255, 255, 255, 0.15);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.25);
            }
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                padding: 4px 8px;
            }
        """)
        
        # วางแถบควบคุมที่มุมขวาบน
        top_layout = QHBoxLayout()
        top_layout.addStretch()
        top_layout.addWidget(self.control_panel)
        top_layout.setContentsMargins(20, 20, 20, 0)
        
        main_layout.addLayout(top_layout)
        main_layout.addStretch()
        
        print("[InteractiveVision] ✅ Panel พร้อมใช้งาน")
    
    def _create_control_panel(self):
        """สร้างแถบควบคุม"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # หัวข้อ
        title = QLabel("🖱️ Interactive Vision Mode")
        layout.addWidget(title)
        
        # คำแนะนำ
        help_text = QLabel("🎯 คลิก: ถามเกี่ยวกับจุดนั้น\n📦 ลาก: เลือกพื้นที่")
        help_text.setStyleSheet("color: #aaaaaa; font-size: 11px; font-weight: normal;")
        layout.addWidget(help_text)
        
        # เลือกโหมดคำถาม
        mode_layout = QHBoxLayout()
        mode_label = QLabel("โหมด:")
        mode_label.setStyleSheet("font-size: 12px;")
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "📝 อธิบาย (What)",
            "🔍 วิเคราะห์ (Why)",
            "💡 แนะนำ (How)",
            "🎯 หา Element",
            "⚙️ ทำงาน (Action)"
        ])
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)
        layout.addLayout(mode_layout)
        
        # ปุ่มปิด
        close_btn = QPushButton("✖ ปิด")
        close_btn.clicked.connect(self.close_requested.emit)
        layout.addWidget(close_btn)
        
        return panel
    
    def paintEvent(self, event):
        """วาดกรอบเลือกพื้นที่"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # พื้นหลังโปร่งใสเล็กน้อย
        painter.fillRect(self.rect(), QColor(0, 0, 0, 30))
        
        # ถ้ากำลังลาก → วาดกรอบ
        if self.dragging and self.start_point and self.current_point:
            # กรอบสีเขียว
            pen = QPen(QColor(100, 255, 100, 200), 3, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            
            # พื้นหลังโปร่งใส
            brush = QBrush(QColor(100, 255, 100, 50))
            painter.setBrush(brush)
            
            # วาดกรอบ
            rect = QRect(self.start_point, self.current_point).normalized()
            painter.drawRect(rect)
            
            # แสดงขนาด
            font = QFont("Arial", 12, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(255, 255, 255))
            size_text = f"{rect.width()} x {rect.height()} px"
            painter.drawText(rect.bottomRight() + QPoint(5, 15), size_text)
    
    def mousePressEvent(self, event):
        """จับการกดเมาส์"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.start_point = event.position().toPoint()
            self.current_point = self.start_point
            print(f"[InteractiveVision] 🖱️ เริ่มลากจาก ({self.start_point.x()}, {self.start_point.y()})")
    
    def mouseMoveEvent(self, event):
        """จับการเคลื่อนที่เมาส์ขณะลาก"""
        if self.dragging:
            self.current_point = event.position().toPoint()
            self.update()  # วาดใหม่
    
    def mouseReleaseEvent(self, event):
        """จับการปล่อยเมาส์"""
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            end_point = event.position().toPoint()
            
            # ดึงโหมดที่เลือก
            mode_text = self.mode_combo.currentText()
            mode = mode_text.split(" ", 1)[1] if " " in mode_text else "อธิบาย"
            
            # ตรวจสอบว่าคลิกหรือลาก
            distance = (end_point - self.start_point).manhattanLength()
            
            if distance < 10:
                # คลิก (ไม่ลาก)
                print(f"[InteractiveVision] 👆 คลิกที่ ({end_point.x()}, {end_point.y()}) - {mode}")
                self.point_selected.emit(end_point.x(), end_point.y(), mode)
            else:
                # ลาก (เลือกพื้นที่)
                rect = QRect(self.start_point, end_point).normalized()
                print(f"[InteractiveVision] 📦 เลือกพื้นที่ {rect.width()}x{rect.height()} - {mode}")
                self.region_selected.emit(
                    rect.x(), rect.y(), rect.width(), rect.height(), mode
                )
            
            # รีเซ็ต
            self.start_point = None
            self.current_point = None
            self.update()
    
    def keyPressEvent(self, event):
        """จับการกดปุ่มคีย์บอร์ด"""
        if event.key() == Qt.Key.Key_Escape:
            print("[InteractiveVision] ❌ กด ESC → ปิด")
            self.close_requested.emit()


# ✅ Test Mode
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    panel = InteractiveVisionPanel()
    
    # เชื่อมต่อสัญญาณ
    panel.point_selected.connect(
        lambda x, y, m: print(f"✅ Point: ({x}, {y}) - Mode: {m}")
    )
    panel.region_selected.connect(
        lambda x, y, w, h, m: print(f"✅ Region: ({x}, {y}, {w}, {h}) - Mode: {m}")
    )
    panel.close_requested.connect(app.quit)
    
    panel.show()
    
    print("🧪 [Test] Interactive Vision Panel")
    print("📍 คลิกหรือลากบนหน้าจอเพื่อทดสอบ")
    print("🔑 กด ESC เพื่อปิด")
    
    sys.exit(app.exec())