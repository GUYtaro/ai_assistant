# core/live_vision_stream.py
# ================================
# 🎥 Live Vision Stream System
# แชร์หน้าจอแบบ Real-time + AI วิเคราะห์ต่อเนื่อง (เหมือน Gemini Live)
# ================================

import cv2
import numpy as np
import time
from threading import Thread, Event
from queue import Queue
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from core.screen_capturer import screenshot_pil
from core.llm_client import LLMClient
from datetime import datetime


class LiveVisionStream(QObject):
    """
    🎥 Live Vision Stream - แชร์หน้าจอแบบ real-time
    
    ฟีเจอร์:
    - จับภาพหน้าจอต่อเนื่อง (10-15 FPS)
    - แสดง preview window แบบ real-time
    - AI วิเคราะห์ทุก N วินาที (ไม่บล็อก stream)
    - รับคำถามจากผู้ใช้ขณะ streaming
    """
    
    # สัญญาณต่างๆ
    frame_captured = pyqtSignal(object)      # ส่งเฟรมภาพ
    analysis_ready = pyqtSignal(str)         # ส่งผลการวิเคราะห์
    status_updated = pyqtSignal(str)         # อัพเดทสถานะ
    stream_started = pyqtSignal()            # เริ่ม stream
    stream_stopped = pyqtSignal()            # หยุด stream
    
    def __init__(self, llm_client: LLMClient = None, monitor=1):
        super().__init__()
        self.llm = llm_client or LLMClient()
        self.monitor = monitor
        
        # Stream settings
        self.is_streaming = False
        self.fps = 10  # 10 เฟรมต่อวินาที (ปรับได้)
        self.frame_interval = 1.0 / self.fps
        
        # AI analysis settings
        self.analysis_interval = 3.0  # วิเคราะห์ทุก 3 วินาที
        self.last_analysis_time = 0
        self.auto_analysis = True  # วิเคราะห์อัตโนมัติ
        
        # Threading
        self.stream_thread = None
        self.analysis_thread = None
        self.stop_event = Event()
        
        # Frame queue สำหรับ AI analysis
        self.frame_queue = Queue(maxsize=2)
        
        # Latest frame และ analysis
        self.latest_frame = None
        self.latest_analysis = ""
        
        # Statistics
        self.frame_count = 0
        self.analysis_count = 0
        self.start_time = None
        
        print("[LiveVision] ✅ เตรียมระบบ Live Vision Stream")
    
    def start_stream(self, fps=10, analysis_interval=3.0):
        """
        เริ่ม Live Vision Stream
        
        Parameters:
            fps: เฟรมต่อวินาที (แนะนำ 5-15)
            analysis_interval: ระยะเวลาระหว่างการวิเคราะห์ (วินาที)
        """
        if self.is_streaming:
            print("[LiveVision] ⚠️ Stream กำลังทำงานอยู่แล้ว")
            return
        
        self.is_streaming = True
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.analysis_interval = analysis_interval
        self.stop_event.clear()
        
        self.frame_count = 0
        self.analysis_count = 0
        self.start_time = time.time()
        
        # เริ่ม capture thread
        self.stream_thread = Thread(target=self._capture_loop, daemon=True)
        self.stream_thread.start()
        
        # เริ่ม analysis thread
        if self.auto_analysis:
            self.analysis_thread = Thread(target=self._analysis_loop, daemon=True)
            self.analysis_thread.start()
        
        self.stream_started.emit()
        self.status_updated.emit(f"🎥 Live Stream เริ่มแล้ว ({fps} FPS)")
        print(f"[LiveVision] 🟢 เริ่ม Stream @ {fps} FPS, วิเคราะห์ทุก {analysis_interval}s")
    
    def stop_stream(self):
        """หยุด Live Vision Stream"""
        if not self.is_streaming:
            return
        
        self.is_streaming = False
        self.stop_event.set()
        
        # รอให้ threads จบ
        if self.stream_thread:
            self.stream_thread.join(timeout=2.0)
        if self.analysis_thread:
            self.analysis_thread.join(timeout=2.0)
        
        # แสดงสถิติ
        duration = time.time() - self.start_time if self.start_time else 0
        avg_fps = self.frame_count / duration if duration > 0 else 0
        
        self.stream_stopped.emit()
        self.status_updated.emit(f"⏸️ หยุด Stream (จับได้ {self.frame_count} เฟรม, {avg_fps:.1f} FPS)")
        print(f"[LiveVision] 🔴 หยุด Stream")
        print(f"  📊 เฟรมทั้งหมด: {self.frame_count}")
        print(f"  📊 วิเคราะห์: {self.analysis_count} ครั้ง")
        print(f"  📊 FPS เฉลี่ย: {avg_fps:.1f}")
    
    def _capture_loop(self):
        """
        Loop สำหรับจับภาพหน้าจอต่อเนื่อง
        รันใน background thread
        """
        print("[LiveVision] 🎥 เริ่ม Capture Loop")
        
        while not self.stop_event.is_set():
            try:
                frame_start = time.time()
                
                # จับภาพหน้าจอ
                img = screenshot_pil(monitor=self.monitor)
                
                # แปลงเป็น numpy array (สำหรับ OpenCV)
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                
                # ย่อขนาดเพื่อประสิทธิภาพ
                height, width = frame.shape[:2]
                if width > 1280:
                    scale = 1280 / width
                    new_width = 1280
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # เพิ่ม overlay ข้อมูล
                self._add_overlay_info(frame)
                
                # บันทึกเฟรมล่าสุด
                self.latest_frame = frame.copy()
                self.frame_count += 1
                
                # ส่งสัญญาณ
                self.frame_captured.emit(frame)
                
                # ใส่เข้า queue สำหรับ AI analysis (ถ้าว่าง)
                if self.auto_analysis and not self.frame_queue.full():
                    try:
                        self.frame_queue.put_nowait(img)
                    except:
                        pass
                
                # รอให้ครบช่วงเวลาต่อเฟรม
                elapsed = time.time() - frame_start
                sleep_time = max(0, self.frame_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                print(f"[LiveVision] ❌ Capture Error: {e}")
                time.sleep(0.1)
        
        print("[LiveVision] 🛑 Capture Loop หยุด")
    
    def _analysis_loop(self):
        """
        Loop สำหรับวิเคราะห์ภาพด้วย AI
        รันใน background thread แยกจาก capture
        """
        print("[LiveVision] 🤖 เริ่ม Analysis Loop")
        
        while not self.stop_event.is_set():
            try:
                current_time = time.time()
                
                # ตรวจสอบว่าถึงเวลาวิเคราะห์หรือยัง
                if current_time - self.last_analysis_time < self.analysis_interval:
                    time.sleep(0.5)
                    continue
                
                # ดึงเฟรมจาก queue
                if self.frame_queue.empty():
                    time.sleep(0.5)
                    continue
                
                img = self.frame_queue.get()
                
                # วิเคราะห์ด้วย AI
                self._analyze_frame(img)
                
                self.last_analysis_time = current_time
                
            except Exception as e:
                print(f"[LiveVision] ❌ Analysis Error: {e}")
                time.sleep(1.0)
        
        print("[LiveVision] 🛑 Analysis Loop หยุด")
    
    def _analyze_frame(self, img):
        """วิเคราะห์เฟรมด้วย AI"""
        try:
            self.analysis_count += 1
            print(f"[LiveVision] 🤖 กำลังวิเคราะห์ (ครั้งที่ {self.analysis_count})...")
            
            # แปลงเป็น data URI
            from core.screen_capturer import image_to_data_uri
            data_uri, _ = image_to_data_uri(img, fmt="JPEG", quality=70)
            
            # ถาม AI
            prompt = "อธิบายสิ่งที่เห็นบนหน้าจอนี้อย่างสั้นๆ ภาษาไทย (ไม่เกิน 100 คำ)"
            analysis = self.llm.ask_with_image(prompt, data_uri)
            
            # บันทึกผลลัพธ์
            self.latest_analysis = analysis
            
            # ส่งสัญญาณ
            timestamp = datetime.now().strftime("%H:%M:%S")
            result = f"[{timestamp}] {analysis}"
            self.analysis_ready.emit(result)
            
            print(f"[LiveVision] ✅ วิเคราะห์เสร็จ: {analysis[:50]}...")
            
        except Exception as e:
            print(f"[LiveVision] ❌ AI Error: {e}")
    
    def _add_overlay_info(self, frame):
        """เพิ่มข้อมูล overlay บนเฟรม"""
        # วาดพื้นหลังโปร่งใส
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # ข้อมูลสถิติ
        duration = time.time() - self.start_time if self.start_time else 0
        avg_fps = self.frame_count / duration if duration > 0 else 0
        
        # วาดข้อความ
        y = 30
        cv2.putText(frame, f"🎥 Live Vision Stream", (15, y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        y += 25
        cv2.putText(frame, f"FPS: {avg_fps:.1f} | Frames: {self.frame_count}", (15, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y += 20
        cv2.putText(frame, f"AI Analysis: {self.analysis_count} times", (15, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def ask_about_screen(self, question: str):
        """
        ถามคำถามเกี่ยวกับหน้าจอปัจจุบัน
        ใช้เฟรมล่าสุดที่จับได้
        """
        if self.latest_frame is None:
            return "❌ ยังไม่มีภาพหน้าจอ"
        
        try:
            print(f"[LiveVision] 💬 คำถาม: {question}")
            
            # แปลง frame เป็น PIL Image
            from PIL import Image
            frame_rgb = cv2.cvtColor(self.latest_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            
            # แปลงเป็น data URI
            from core.screen_capturer import image_to_data_uri
            data_uri, _ = image_to_data_uri(img, fmt="JPEG", quality=80)
            
            # ถาม AI
            answer = self.llm.ask_with_image(question, data_uri)
            
            print(f"[LiveVision] 🤖 คำตอบ: {answer[:100]}...")
            return answer
            
        except Exception as e:
            print(f"[LiveVision] ❌ Ask Error: {e}")
            return f"❌ เกิดข้อผิดพลาด: {e}"
    
    def set_auto_analysis(self, enabled: bool):
        """เปิด/ปิด การวิเคราะห์อัตโนมัติ"""
        self.auto_analysis = enabled
        status = "เปิด" if enabled else "ปิด"
        print(f"[LiveVision] ⚙️ การวิเคราะห์อัตโนมัติ: {status}")
    
    def set_fps(self, fps: int):
        """ปรับ FPS ขณะ streaming"""
        self.fps = max(1, min(fps, 30))  # จำกัด 1-30 FPS
        self.frame_interval = 1.0 / self.fps
        print(f"[LiveVision] ⚙️ ตั้ง FPS: {self.fps}")
    
    def set_analysis_interval(self, seconds: float):
        """ปรับระยะเวลาระหว่างการวิเคราะห์"""
        self.analysis_interval = max(1.0, seconds)
        print(f"[LiveVision] ⚙️ ตั้งช่วงวิเคราะห์: {self.analysis_interval}s")
    
    def get_stats(self) -> dict:
        """ดึงสถิติการทำงาน"""
        duration = time.time() - self.start_time if self.start_time else 0
        avg_fps = self.frame_count / duration if duration > 0 else 0
        
        return {
            "is_streaming": self.is_streaming,
            "frame_count": self.frame_count,
            "analysis_count": self.analysis_count,
            "duration": duration,
            "avg_fps": avg_fps,
            "target_fps": self.fps,
            "analysis_interval": self.analysis_interval
        }


# ✅ Test Mode
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
    from PyQt6.QtWidgets import QPushButton, QLabel, QTextEdit, QLineEdit
    from PyQt6.QtGui import QImage, QPixmap
    
    class LiveVisionTestWindow(QMainWindow):
        """หน้าต่างทดสอบ Live Vision Stream"""
        
        def __init__(self):
            super().__init__()
            self.setWindowTitle("🎥 Live Vision Stream Test")
            self.setGeometry(100, 100, 1000, 700)
            
            # สร้างระบบ
            self.live_vision = LiveVisionStream()
            self.live_vision.frame_captured.connect(self.on_frame)
            self.live_vision.analysis_ready.connect(self.on_analysis)
            self.live_vision.status_updated.connect(self.on_status)
            
            self.setup_ui()
        
        def setup_ui(self):
            central = QWidget()
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            
            # แถบควบคุม
            control_layout = QHBoxLayout()
            
            self.start_btn = QPushButton("🟢 Start Stream")
            self.start_btn.clicked.connect(self.start_stream)
            
            self.stop_btn = QPushButton("🔴 Stop Stream")
            self.stop_btn.clicked.connect(self.stop_stream)
            self.stop_btn.setEnabled(False)
            
            self.status_label = QLabel("พร้อมใช้งาน")
            
            control_layout.addWidget(self.start_btn)
            control_layout.addWidget(self.stop_btn)
            control_layout.addWidget(self.status_label)
            control_layout.addStretch()
            
            layout.addLayout(control_layout)
            
            # Preview video
            self.video_label = QLabel("📸 Video Preview")
            self.video_label.setStyleSheet("border: 2px solid #555; background: #000;")
            self.video_label.setFixedSize(800, 450)
            layout.addWidget(self.video_label)
            
            # ช่องคำถาม
            question_layout = QHBoxLayout()
            self.question_input = QLineEdit()
            self.question_input.setPlaceholderText("ถามคำถามเกี่ยวกับหน้าจอ...")
            self.ask_btn = QPushButton("🤔 ถาม")
            self.ask_btn.clicked.connect(self.ask_question)
            
            question_layout.addWidget(self.question_input)
            question_layout.addWidget(self.ask_btn)
            layout.addLayout(question_layout)
            
            # Analysis output
            self.analysis_text = QTextEdit()
            self.analysis_text.setReadOnly(True)
            self.analysis_text.setMaximumHeight(150)
            layout.addWidget(self.analysis_text)
        
        def on_frame(self, frame):
            """แสดงเฟรมบน video preview"""
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_BGR888)
            
            # ย่อขนาดเพื่อแสดงใน label
            pixmap = QPixmap.fromImage(q_image)
            scaled = pixmap.scaled(800, 450, aspectRatioMode=1)
            self.video_label.setPixmap(scaled)
        
        def on_analysis(self, text):
            """แสดงผลการวิเคราะห์"""
            self.analysis_text.append(f"\n{text}\n{'-'*50}")
        
        def on_status(self, text):
            """อัพเดทสถานะ"""
            self.status_label.setText(text)
        
        def start_stream(self):
            self.live_vision.start_stream(fps=10, analysis_interval=5.0)
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
        
        def stop_stream(self):
            self.live_vision.stop_stream()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
        
        def ask_question(self):
            question = self.question_input.text().strip()
            if not question:
                return
            
            self.question_input.clear()
            self.analysis_text.append(f"\n💬 คุณ: {question}")
            
            answer = self.live_vision.ask_about_screen(question)
            self.analysis_text.append(f"🤖 AI: {answer}\n{'-'*50}")
    
    app = QApplication(sys.argv)
    window = LiveVisionTestWindow()
    window.show()
    
    print("🧪 [Test] Live Vision Stream")
    print("📍 กด Start Stream เพื่อเริ่มแชร์หน้าจอ")
    print("💬 พิมพ์คำถามเพื่อถาม AI เกี่ยวกับหน้าจอ")
    
    sys.exit(app.exec())