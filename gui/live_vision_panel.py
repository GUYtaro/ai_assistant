# gui/live_vision_panel.py
# ================================
# 🎥 Live Vision Panel
# GUI สำหรับ Live Vision Stream (เหมือน Gemini Live)
# ================================

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTextEdit, QLineEdit, QSlider, QGroupBox, QCheckBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap, QFont
from core.live_vision_stream import LiveVisionStream
from core.llm_client import LLMClient


class LiveVisionPanel(QWidget):
    """
    🎥 Live Vision Panel - แชร์หน้าจอแบบ Real-time
    
    ฟีเจอร์:
    - แสดง video preview ขนาดใหญ่
    - ควบคุม start/stop stream
    - ถามคำถามเกี่ยวกับหน้าจอแบบ real-time
    - ปรับ FPS และความถี่การวิเคราะห์
    - แสดงผลการวิเคราะห์อัตโนมัติ
    """
    
    close_requested = pyqtSignal()
    
    def __init__(self, llm_client: LLMClient = None):
        super().__init__()
        self.llm = llm_client or LLMClient()
        self.live_vision = LiveVisionStream(llm_client=self.llm, monitor=1)
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """ตั้งค่า UI"""
        self.setWindowTitle("🎥 Live Vision Stream (Gemini Live Style)")
        self.setGeometry(100, 100, 1100, 750)
        
        # Style
        self.setStyleSheet("""
            QWidget {
                background: #0a0a0a;
                color: #e0e0e0;
                font-family: "Segoe UI", Arial;
            }
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
            QPushButton#start_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d084, stop:1 #00b36b);
            }
            QPushButton#stop_btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff4444, stop:1 #cc0000);
            }
            QLabel#video_label {
                border: 2px solid #333;
                border-radius: 8px;
                background: #000;
            }
            QLineEdit, QTextEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 8px;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #333;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        # Layout หลัก
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # =====================================================
        # 🎬 แถบหัวข้อ
        # =====================================================
        header_layout = QHBoxLayout()
        
        title = QLabel("🎥 Live Vision Stream")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #00d084;")
        
        self.status_label = QLabel("พร้อมใช้งาน")
        self.status_label.setStyleSheet("color: #888; font-size: 12px;")
        
        close_btn = QPushButton("✖")
        close_btn.setFixedSize(40, 40)
        close_btn.clicked.connect(self.close_requested.emit)
        
        header_layout.addWidget(title)
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        main_layout.addLayout(header_layout)
        
        # =====================================================
        # 📺 Video Preview (ขนาดใหญ่)
        # =====================================================
        self.video_label = QLabel("📸 กด Start Stream เพื่อเริ่มแชร์หน้าจอ")
        self.video_label.setObjectName("video_label")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setFixedSize(1024, 576)  # 16:9 aspect ratio
        main_layout.addWidget(self.video_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # =====================================================
        # 🎛️ ควบคุม Stream
        # =====================================================
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🟢 Start Stream")
        self.start_btn.setObjectName("start_btn")
        self.start_btn.setFixedHeight(45)
        self.start_btn.clicked.connect(self.start_stream)
        
        self.stop_btn = QPushButton("🔴 Stop Stream")
        self.stop_btn.setObjectName("stop_btn")
        self.stop_btn.setFixedHeight(45)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_stream)
        
        # เลือก Monitor
        monitor_label = QLabel("จอที่:")
        self.monitor_combo = QComboBox()
        self.monitor_combo.addItems(["จอ 1", "จอ 2", "จอ 3"])
        self.monitor_combo.setCurrentIndex(0)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(monitor_label)
        control_layout.addWidget(self.monitor_combo)
        control_layout.addStretch()
        
        main_layout.addLayout(control_layout)
        
        # =====================================================
        # ⚙️ การตั้งค่า
        # =====================================================
        settings_group = QGroupBox("⚙️ การตั้งค่า")
        settings_layout = QHBoxLayout()
        
        # FPS Slider
        fps_layout = QVBoxLayout()
        fps_label = QLabel("FPS: 10")
        self.fps_slider = QSlider(Qt.Orientation.Horizontal)
        self.fps_slider.setMinimum(5)
        self.fps_slider.setMaximum(20)
        self.fps_slider.setValue(10)
        self.fps_slider.setTickInterval(5)
        self.fps_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.fps_slider.valueChanged.connect(
            lambda v: fps_label.setText(f"FPS: {v}")
        )
        fps_layout.addWidget(fps_label)
        fps_layout.addWidget(self.fps_slider)
        
        # Analysis Interval Slider
        interval_layout = QVBoxLayout()
        interval_label = QLabel("วิเคราะห์ทุก: 3s")
        self.interval_slider = QSlider(Qt.Orientation.Horizontal)
        self.interval_slider.setMinimum(1)
        self.interval_slider.setMaximum(10)
        self.interval_slider.setValue(3)
        self.interval_slider.setTickInterval(1)
        self.interval_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.interval_slider.valueChanged.connect(
            lambda v: interval_label.setText(f"วิเคราะห์ทุก: {v}s")
        )
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_slider)
        
        # Auto Analysis Checkbox
        self.auto_analysis_cb = QCheckBox("วิเคราะห์อัตโนมัติ")
        self.auto_analysis_cb.setChecked(True)
        
        settings_layout.addLayout(fps_layout)
        settings_layout.addLayout(interval_layout)
        settings_layout.addWidget(self.auto_analysis_cb)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)
        
        # =====================================================
        # 💬 ช่องถามคำถาม
        # =====================================================
        question_layout = QHBoxLayout()
        
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("💬 ถามคำถามเกี่ยวกับหน้าจอที่กำลังแชร์...")
        self.question_input.setFixedHeight(40)
        self.question_input.returnPressed.connect(self.ask_question)
        
        self.ask_btn = QPushButton("🤔 ถาม")
        self.ask_btn.setFixedSize(80, 40)
        self.ask_btn.clicked.connect(self.ask_question)
        
        question_layout.addWidget(self.question_input)
        question_layout.addWidget(self.ask_btn)
        
        main_layout.addLayout(question_layout)
        
        # =====================================================
        # 📄 ผลการวิเคราะห์
        # =====================================================
        analysis_group = QGroupBox("🤖 การวิเคราะห์ของ AI")
        analysis_layout = QVBoxLayout()
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setMaximumHeight(150)
        self.analysis_text.setPlaceholderText("ผลการวิเคราะห์จะแสดงที่นี่...")
        
        analysis_layout.addWidget(self.analysis_text)
        analysis_group.setLayout(analysis_layout)
        main_layout.addWidget(analysis_group)
    
    def connect_signals(self):
        """เชื่อมต่อสัญญาณ"""
        self.live_vision.frame_captured.connect(self.on_frame_captured)
        self.live_vision.analysis_ready.connect(self.on_analysis_ready)
        self.live_vision.status_updated.connect(self.on_status_updated)
        self.live_vision.stream_started.connect(self.on_stream_started)
        self.live_vision.stream_stopped.connect(self.on_stream_stopped)
    
    @pyqtSlot()
    def start_stream(self):
        """เริ่ม Live Stream"""
        monitor = self.monitor_combo.currentIndex() + 1
        fps = self.fps_slider.value()
        interval = self.interval_slider.value()
        
        # อัพเดท settings
        self.live_vision.monitor = monitor
        self.live_vision.set_auto_analysis(self.auto_analysis_cb.isChecked())
        
        # เริ่ม stream
        self.live_vision.start_stream(fps=fps, analysis_interval=interval)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.monitor_combo.setEnabled(False)
    
    @pyqtSlot()
    def stop_stream(self):
        """หยุด Live Stream"""
        self.live_vision.stop_stream()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.monitor_combo.setEnabled(True)
        
        self.video_label.setText("📸 Stream หยุดแล้ว - กด Start เพื่อเริ่มใหม่")
    
    @pyqtSlot()
    def ask_question(self):
        """ถามคำถามเกี่ยวกับหน้าจอ"""
        question = self.question_input.text().strip()
        if not question:
            return
        
        self.question_input.clear()
        
        # แสดงคำถาม
        self.analysis_text.append(f"\n💬 <b>คุณ:</b> {question}")
        self.analysis_text.append("")
        
        # ถาม AI
        answer = self.live_vision.ask_about_screen(question)
        
        # แสดงคำตอบ
        self.analysis_text.append(f"🤖 <b>AI:</b> {answer}")
        self.analysis_text.append("-" * 70)
        
        # เลื่อนลงล่างสุด
        self.analysis_text.verticalScrollBar().setValue(
            self.analysis_text.verticalScrollBar().maximum()
        )
    
    @pyqtSlot(object)
    def on_frame_captured(self, frame):
        """แสดงเฟรมบน video preview"""
        import cv2
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
        
        # ย่อขนาดเพื่อแสดงใน label
        pixmap = QPixmap.fromImage(q_image)
        scaled = pixmap.scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.video_label.setPixmap(scaled)
    
    @pyqtSlot(str)
    def on_analysis_ready(self, text):
        """แสดงผลการวิเคราะห์อัตโนมัติ"""
        self.analysis_text.append(f"<span style='color:#00d084'>🤖 <b>AI (อัตโนมัติ):</b></span> {text}")
        self.analysis_text.append("-" * 70)
        
        # เลื่อนลงล่างสุด
        self.analysis_text.verticalScrollBar().setValue(
            self.analysis_text.verticalScrollBar().maximum()
        )
    
    @pyqtSlot(str)
    def on_status_updated(self, text):
        """อัพเดทสถานะ"""
        self.status_label.setText(text)
    
    @pyqtSlot()
    def on_stream_started(self):
        """เมื่อ stream เริ่มต้น"""
        print("[LiveVisionPanel] ✅ Stream Started")
    
    @pyqtSlot()
    def on_stream_stopped(self):
        """เมื่อ stream หยุด"""
        print("[LiveVisionPanel] ⏸️ Stream Stopped")
        
        # แสดงสถิติ
        stats = self.live_vision.get_stats()
        self.analysis_text.append(f"\n📊 <b>สถิติ:</b>")
        self.analysis_text.append(f"  • เฟรมทั้งหมด: {stats['frame_count']}")
        self.analysis_text.append(f"  • วิเคราะห์: {stats['analysis_count']} ครั้ง")
        self.analysis_text.append(f"  • FPS เฉลี่ย: {stats['avg_fps']:.1f}")
        self.analysis_text.append(f"  • ระยะเวลา: {stats['duration']:.1f} วินาที")
        self.analysis_text.append("-" * 70)
    
    def closeEvent(self, event):
        """เมื่อปิดหน้าต่าง → หยุด stream"""
        if self.live_vision.is_streaming:
            self.live_vision.stop_stream()
        event.accept()


# ✅ Test Mode
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    panel = LiveVisionPanel()
    panel.show()
    
    print("🧪 [Test] Live Vision Panel")
    print("📍 กด Start Stream เพื่อเริ่มแชร์หน้าจอ")
    print("💬 พิมพ์คำถามเพื่อถาม AI")
    print("⚙️ ปรับ FPS และความถี่การวิเคราะห์ได้")
    
    sys.exit(app.exec())