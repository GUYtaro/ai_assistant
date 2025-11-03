# main.py
# ================================
# 🤖 AI Assistant (Full Version with Complete Copilot Vision)
# ✅ รองรับ Push-to-Talk, Copilot Vision, Continuous Vision, Interactive Vision
# ================================

import re
import sys
import urllib.parse
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QScrollArea, QFrame
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from PyQt6.QtGui import QColor
import sounddevice as sd
import numpy as np

# Import core modules
from core.llm_client import LLMClient
from core.stt_client import STTClient
from core.tts_client import TTSClient
from core.vision_system import VisionSystem
from core.command_parser import CommandParser
from core.automation_executor import AutomationExecutor
from core.screen_capturer import screenshot_data_uri, screenshot_pil
from core.screen_reader import ScreenReader
from core.hotkey_listener import HotkeyListener
from core.app_launcher import AppLauncher
from core.smart_app_launcher import SmartAppLauncher 
from gui.assistant_bar import AssistantBar

# Import Vision Systems
try:
    from core.vision_overlay import VisionOverlay
    from core.continuous_vision_system import ContinuousVisionSystem
    from gui.interactive_vision_panel import InteractiveVisionPanel
    from core.live_vision_stream import LiveVisionStream
    from gui.live_vision_panel import LiveVisionPanel
    _HAS_VISION_SYSTEMS = True
except ImportError as e:
    print(f"[WARNING] ไม่พบ Vision Systems: {e}")
    _HAS_VISION_SYSTEMS = False

# Import for Copilot Vision
try:
    import mss
    _HAS_MSS = True
except ImportError:
    print("[WARNING] ไม่พบ mss, Copilot Vision อาจไม่ทำงาน")
    _HAS_MSS = False


class ScreenSharePanel(QWidget):
    """
    🖥️ หน้าต่างเลือกจอสำหรับ Copilot Vision
    ให้ผู้ใช้เลือกหน้าจอที่ต้องการแชร์ให้ AI วิเคราะห์
    """
    
    share_requested = pyqtSignal(int, str)  # monitor_id, description

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🧠 Copilot Vision - Share Screen")
        self.setFixedSize(400, 400)
        self.layout = QVBoxLayout(self)

        # Title
        title = QLabel("🧠 Copilot Vision")
        title.setStyleSheet("font-size:18px; font-weight:bold; margin:10px;")
        self.layout.addWidget(title)

        # Description
        desc = QLabel("เลือกหน้าจอที่ต้องการแชร์ให้ AI วิเคราะห์:")
        desc.setStyleSheet("margin:5px; color:#888;")
        self.layout.addWidget(desc)

        # Scroll area for monitors list
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.layout.addWidget(self.scroll)

        # Content for scroll area
        content = QWidget()
        self.scroll.setWidget(content)
        vbox = QVBoxLayout(content)

        # Display available monitors
        if _HAS_MSS:
            with mss.mss() as sct:
                for i, mon in enumerate(sct.monitors[1:], start=1):
                    self._add_monitor_frame(vbox, i, mon)
        else:
            error_label = QLabel("❌ ไม่สามารถเข้าถึงข้อมูลหน้าจอได้\nติดตั้ง: pip install mss")
            error_label.setStyleSheet("color:red; margin:10px;")
            vbox.addWidget(error_label)

        vbox.addStretch()

        # Close button
        close_btn = QPushButton("ปิด")
        close_btn.setStyleSheet("padding:8px; margin:10px;")
        close_btn.clicked.connect(self.close)
        self.layout.addWidget(close_btn)

    def _add_monitor_frame(self, layout, monitor_id, monitor_info):
        """เพิ่มเฟรมแสดงข้อมูลหน้าจอ"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                border: 1px solid #555; 
                border-radius: 8px; 
                padding: 10px;
                margin: 5px;
                background: #2a2a2a;
            }
            QFrame:hover {
                background: #333333;
                border-color: #777;
            }
        """)
        
        frame_layout = QHBoxLayout(frame)

        # Monitor info
        info_text = f"🖥️ หน้าจอ {monitor_id}\n{monitor_info['width']} x {monitor_info['height']} pixels"
        label = QLabel(info_text)
        label.setStyleSheet("font-size:12px;")
        frame_layout.addWidget(label)
        
        frame_layout.addStretch()
        
        # Share button
        btn = QPushButton("แชร์")
        btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #45a049;
            }
        """)
        btn.clicked.connect(lambda _, m=monitor_id: self._on_share_clicked(m))
        frame_layout.addWidget(btn)
        
        layout.addWidget(frame)

    def _on_share_clicked(self, monitor_id):
        """เมื่อกดปุ่มแชร์หน้าจอ"""
        description = f"หน้าจอ {monitor_id}"
        print(f"[Vision] แชร์หน้าจอ {monitor_id} ให้ AI")
        self.share_requested.emit(monitor_id, description)
        self.close()


class VoiceRecorder(QObject):
    """
    🎤 ตัวบันทึกเสียงแบบ Push-to-Talk
    """
    
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(object)
    
    def __init__(self, stt_client: STTClient):
        super().__init__()
        self.stt = stt_client
        self.is_recording = False
        self.audio_data = []
        self.sample_rate = 16000
        
    def start_recording(self):
        if self.is_recording:
            return
        
        self.is_recording = True
        self.audio_data = []
        
        print("[VoiceRecorder] 🔴 เริ่มบันทึกเสียง...")
        self.recording_started.emit()
        
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"[VoiceRecorder] Status: {status}")
            if self.is_recording:
                self.audio_data.append(indata.copy())
        
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=audio_callback,
            dtype=np.float32
        )
        self.stream.start()
    
    def stop_recording(self):
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        print("[VoiceRecorder] ⏹️ หยุดบันทึกเสียง")
        
        if len(self.audio_data) == 0:
            print("[VoiceRecorder] ❌ ไม่มีข้อมูลเสียง")
            self.recording_stopped.emit(None)
            return
        
        audio_array = np.concatenate(self.audio_data, axis=0)
        audio_float32 = audio_array.flatten().astype(np.float32)
        
        duration = len(audio_float32) / self.sample_rate
        print(f"[VoiceRecorder] ✅ บันทึกเสียงได้ {duration:.2f} วินาที")
        
        self.recording_stopped.emit(audio_float32)


class TranscriptionWorker(QThread):
    """
    🔄 Worker thread สำหรับแปลงเสียงเป็นข้อความ
    """
    
    transcription_done = pyqtSignal(str)
    
    def __init__(self, stt_client: STTClient, audio_data):
        super().__init__()
        self.stt = stt_client
        self.audio_data = audio_data
    
    def run(self):
        try:
            print("[TranscriptionWorker] 🔄 กำลังแปลงเสียงเป็นข้อความ...")
            
            text = self.stt.model.transcribe(
                self.audio_data,
                language="th",
                fp16=False
            )["text"].strip()
            
            print(f"[TranscriptionWorker] ✅ แปลงได้: {text}")
            self.transcription_done.emit(text)
            
        except Exception as e:
            print(f"[TranscriptionWorker] ❌ Error: {e}")
            self.transcription_done.emit("")


class AssistantContext:
    """
    🧠 Context Memory สำหรับผู้ช่วย
    """
    
    def __init__(self):
        self.memory = {
            "last_opened_app": None,
            "recent_commands": [],
            "favorite_apps": {},
            "user_preferences": {
                "preferred_browser": "chrome",
                "language": "th"
            }
        }
        self.max_history = 10
    
    def record_command(self, command: str, result: str):
        from datetime import datetime
        self.memory["recent_commands"].append({
            "command": command,
            "result": result,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        if len(self.memory["recent_commands"]) > self.max_history:
            self.memory["recent_commands"].pop(0)
    
    def record_app_launch(self, app_name: str, success: bool):
        self.memory["last_opened_app"] = app_name
        if app_name not in self.memory["favorite_apps"]:
            self.memory["favorite_apps"][app_name] = {"launch_count": 0, "success_count": 0}
        self.memory["favorite_apps"][app_name]["launch_count"] += 1
        if success:
            self.memory["favorite_apps"][app_name]["success_count"] += 1
    
    def get_smart_suggestion(self, partial_command: str) -> str:
        partial_lower = partial_command.lower()
        
        for cmd in reversed(self.memory["recent_commands"]):
            if partial_lower in cmd["command"].lower():
                return f"เคยทำคำสั่งนี้: '{cmd['command']}' -> {cmd['result']}"
        
        for app_name, stats in self.memory["favorite_apps"].items():
            if partial_lower in app_name.lower():
                success_rate = (stats["success_count"] / stats["launch_count"]) * 100
                return f"เคยเปิด '{app_name}' {stats['launch_count']} ครั้ง (สำเร็จ {success_rate:.0f}%)"
        
        return "ไม่พบประวัติที่เกี่ยวข้อง"
    
    def get_context_summary(self) -> str:
        summary = []
        if self.memory["last_opened_app"]:
            summary.append(f"เปิดล่าสุด: {self.memory['last_opened_app']}")
        if self.memory["recent_commands"]:
            summary.append(f"คำสั่งล่าสุด: {len(self.memory['recent_commands'])} รายการ")
        if self.memory["favorite_apps"]:
            top_app = max(self.memory["favorite_apps"].items(), 
                         key=lambda x: x[1]["launch_count"], default=(None, None))
            if top_app[0]:
                summary.append(f"แอปยอดนิยม: {top_app[0]}")
        return " | ".join(summary) if summary else "ไม่มีประวัติล่าสุด"


class SmartCommandParser:
    """
    🧩 ตัวแยกคำสั่งอัจฉริยะ
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
        self.thai_to_english_map = {
            "ดิสคอร์ต": "discord", "ดิสคอร์ด": "discord", "ดิสคอด": "discord",
            "ไลน์": "line", "ลาย": "line",
            "สปอติไฟ": "spotify", "สปอตติฟาย": "spotify",
            "โครม": "chrome", "ไครม์": "chrome",
            "เอ็ดจ์": "edge", "ฟายร์ฟอกซ์": "firefox",
            "สตีม": "steam", "วีเอสโค้ด": "vscode",
            "โน้ตแพด": "notepad", "แคลคูเลเตอร์": "calculator",
            "เครื่องคิดเลข": "calculator", "เพ้นท์": "paint",
            "โรบล็อกซ์": "roblox", "มายคราฟท์": "minecraft",
            "วอร์ธันเดอร์": "war thunder", "วีเอ็มแวร์": "vmware",
            "เวิร์ด": "word", "เอ็กเซล": "excel",
            "พาวเวอร์พอยท์": "powerpoint", "เอาท์ลุค": "outlook",
            "ทีมส์": "teams", "ซูม": "zoom", "สแล็ก": "slack",
            "มายเอซุส": "my asus", "อาร์มูรี่เครท": "armoury crate"
        }
    
    def is_open_command(self, text: str) -> bool:
        return any(word in text.lower() for word in ["เปิด", "open", "launch", "start", "run"])
    
    def extract_app_name_from_command(self, text: str) -> str:
        text_lower = text.lower()
        remove_words = ["เปิด", "open", "launch", "start", "run", "ผ่าน", "ใน", "ด้วย", "หน่อย"]
        app_name = text_lower
        for word in remove_words:
            app_name = app_name.replace(word, "").strip()
        app_name_english = self._translate_thai_to_english(app_name)
        if app_name_english != app_name:
            print(f"🔄 [Translation] '{app_name}' → '{app_name_english}'")
        return app_name_english
    
    def _translate_thai_to_english(self, thai_text: str) -> str:
        thai_text = thai_text.strip()
        if thai_text in self.thai_to_english_map:
            return self.thai_to_english_map[thai_text]
        for thai, english in self.thai_to_english_map.items():
            if thai in thai_text:
                return english
        return thai_text
    
    def extract_url(self, text: str) -> str:
        url_map = {
            "youtube": "https://youtube.com", "ยูทูป": "https://youtube.com",
            "google": "https://google.com", "facebook": "https://facebook.com",
            "chatgpt": "https://chat.openai.com", "claude": "https://claude.ai"
        }
        for keyword, url in url_map.items():
            if keyword in text.lower():
                return url
        return None
    
    def extract_search_query(self, text: str) -> str:
        if "ค้นหา" not in text.lower() and "search" not in text.lower():
            return None
        query = text.lower().replace("เปิด", "").replace("ค้นหา", "").strip()
        if query:
            return f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        return None


class AssistantCore(QObject):
    """
    🧠 Core System ของ AI Assistant (Full Version with Complete Vision)
    """
    
    status_updated = pyqtSignal(str)
    response_ready = pyqtSignal(str)
    voice_input_received = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_core_systems()
        
    def setup_core_systems(self):
        """ตั้งค่าระบบทั้งหมด"""
        try:
            # Core modules
            self.llm = LLMClient()
            self.stt = STTClient(model_size="medium", language="th")
            self.tts = TTSClient(lang="th")
            self.vision = VisionSystem()
            self.parser = CommandParser(llm_client=self.llm)
            self.executor = AutomationExecutor(monitor=1)
            self.launcher = AppLauncher()
            self.smart_launcher = SmartAppLauncher()
            
            # Additional systems
            self.context = AssistantContext()
            self.command_parser = SmartCommandParser(llm_client=self.llm)
            
            # Voice Recorder
            self.voice_recorder = VoiceRecorder(self.stt)
            self.voice_recorder.recording_stopped.connect(self.on_audio_recorded)
            
            # Chat history
            self.chat_history = [{
                "role": "system", 
                "content": "คุณคือผู้ช่วยที่ตอบเป็นภาษาไทยอย่างเป็นมิตรและเป็นธรรมชาติ"
            }]
            
            # Hotkey Listener
            self.hotkey_listener = HotkeyListener(
                callback_start=self.handle_voice_f4,
                hotkey="f4",
                cooldown=2.0
            )
            
            # ✅ Setup Vision Systems
            self.setup_vision_systems()
            
            self.status_updated.emit("ระบบพร้อมใช้งาน ✅")
            print("=== 🤖 AI Assistant (Complete with Full Copilot Vision) ===")
            
        except Exception as e:
            error_msg = f"ข้อผิดพลาดในการตั้งค่าระบบ: {str(e)}"
            self.status_updated.emit(error_msg)
            print(f"Error setting up systems: {e}")

    def setup_vision_systems(self):
        """ตั้งค่าระบบ Vision ครบชุด"""
        if not _HAS_VISION_SYSTEMS:
            print("[Vision] ⚠️ Vision Systems ไม่พร้อม - ข้าม")
            self.vision_overlay = None
            self.continuous_vision = None
            self.interactive_panel = None
            return
            
        try:
            # 1️⃣ Vision Overlay
            self.vision_overlay = VisionOverlay()
            self.vision_overlay.clicked.connect(self.on_overlay_clicked)
            print("[Vision] ✅ Overlay System")
            
            # 2️⃣ Continuous Vision
            self.continuous_vision = ContinuousVisionSystem(
                llm_client=self.llm,
                monitor=1
            )
            self.continuous_vision.analysis_ready.connect(self.on_continuous_analysis)
            self.continuous_vision.change_detected.connect(self.on_screen_change)
            print("[Vision] ✅ Continuous System")
            
            # 3️⃣ Interactive Vision Panel
            self.interactive_panel = None  # สร้างตอนใช้งาน
            print("[Vision] ✅ Interactive System (standby)")
            
        except Exception as e:
            print(f"[Vision] ❌ Setup Error: {e}")
            self.vision_overlay = None
            self.continuous_vision = None
            self.interactive_panel = None

    # =====================================================
    # 🎤 Voice Recording Methods
    # =====================================================
    
    @pyqtSlot()
    def start_recording(self):
        print("[AssistantCore] 🎤 เริ่มบันทึกเสียง...")
        self.status_updated.emit("🔴 กำลังฟัง...")
        self.voice_recorder.start_recording()
    
    @pyqtSlot()
    def stop_recording(self):
        print("[AssistantCore] ⏹️ หยุดบันทึกเสียง")
        self.status_updated.emit("⏳ กำลังประมวลผล...")
        self.voice_recorder.stop_recording()
    
    @pyqtSlot(object)
    def on_audio_recorded(self, audio_data):
        if audio_data is None or len(audio_data) == 0:
            self.status_updated.emit("❌ ไม่มีเสียง")
            self.tts.speak("ขอโทษครับ ผมไม่ได้ยินเสียง")
            return
        
        self.transcription_worker = TranscriptionWorker(self.stt, audio_data)
        self.transcription_worker.transcription_done.connect(self.on_transcription_done)
        self.transcription_worker.start()
    
    @pyqtSlot(str)
    def on_transcription_done(self, text: str):
        if not text or text.strip() == "":
            self.status_updated.emit("❌ ไม่เข้าใจ")
            self.tts.speak("ขอโทษครับ ผมไม่เข้าใจ")
            return
        
        print(f"📝 คุณพูดว่า: {text}")
        self.voice_input_received.emit(text)
        self.response_ready.emit(f"📝 คุณพูดว่า: {text}")
        self.process_command(text)

    # =====================================================
    # 🛑 Stop Speaking
    # =====================================================
    
    @pyqtSlot()
    def stop_speaking(self):
        print("[AssistantCore] ⏹️ กำลังหยุดการพูด...")
        self.status_updated.emit("หยุดการพูดแล้ว")
        self.response_ready.emit("⏹️ หยุดการพูดแล้ว")
        
        try:
            if hasattr(self.tts, 'stop_speaking'):
                self.tts.stop_speaking()
            else:
                self.tts = TTSClient(lang="th")
        except Exception as e:
            print(f"[AssistantCore] ❌ Stop Error: {e}")

    # =====================================================
    # 🎨 Vision Overlay Methods
    # =====================================================
    
    def show_ui_hints(self, elements):
        """แสดงกรอบชี้ UI elements"""
        if not self.vision_overlay:
            print("[Vision] ⚠️ Vision Overlay ไม่พร้อม")
            return
            
        self.vision_overlay.clear_annotations()
        
        for elem in elements:
            self.vision_overlay.add_box(
                elem["x"], elem["y"], elem["w"], elem["h"],
                label=elem.get("label", ""),
                color=QColor(100, 255, 100, 200)
            )
        
        self.vision_overlay.show_temporary(duration_ms=5000)
        print(f"[Vision] 🎨 แสดง {len(elements)} elements")
    
    @pyqtSlot(int, int)
    def on_overlay_clicked(self, x, y):
        print(f"[Vision] 👆 คลิกที่ ({x}, {y})")
        self.response_ready.emit(f"🖱️ คลิกที่ตำแหน่ง ({x}, {y})")

    # =====================================================
    # 👁️ Continuous Vision Methods
    # =====================================================
    
    def start_continuous_vision(self, interval=5):
        if not self.continuous_vision:
            print("[Vision] ⚠️ Continuous Vision ไม่พร้อม")
            self.status_updated.emit("❌ Continuous Vision ไม่พร้อม")
            return
            
        self.continuous_vision.start(interval_seconds=interval)
        self.status_updated.emit(f"🔄 Continuous Vision (ทุก {interval}s)")
        self.tts.speak(f"เริ่มวิเคราะห์หน้าจอทุก {interval} วินาที")
    
    def stop_continuous_vision(self):
        if not self.continuous_vision:
            return
            
        self.continuous_vision.stop()
        self.status_updated.emit("⏸️ หยุด Continuous Vision")
        self.tts.speak("หยุดการวิเคราะห์แล้ว")
    
    @pyqtSlot(str)
    def on_continuous_analysis(self, analysis):
        print(f"[ContinuousVision] 🤖 {analysis[:100]}...")
        self.response_ready.emit(f"🔄 {analysis}")
    
    @pyqtSlot(float, str)
    def on_screen_change(self, percent, description):
        print(f"[ContinuousVision] 🔔 เปลี่ยนแปลง {percent:.1f}%")
        self.response_ready.emit(f"🔔 หน้าจอเปลี่ยนแปลง {percent:.1f}%")

    # =====================================================
    # 🖱️ Interactive Vision Methods
    # =====================================================
    
    def open_interactive_vision(self):
        if not _HAS_VISION_SYSTEMS:
            print("[Vision] ⚠️ Interactive Vision ไม่พร้อม")
            self.status_updated.emit("❌ Interactive Vision ไม่พร้อม")
            return
            
        if self.interactive_panel is None:
            self.interactive_panel = InteractiveVisionPanel()
            self.interactive_panel.point_selected.connect(self.on_point_selected)
            self.interactive_panel.region_selected.connect(self.on_region_selected)
            self.interactive_panel.close_requested.connect(
                lambda: self.interactive_panel.hide()
            )
        
        self.interactive_panel.show()
        self.status_updated.emit("🖱️ Interactive Vision Mode")
        print("[Vision] 🖱️ เปิดโหมด Interactive")
    
    @pyqtSlot(int, int, str)
    def on_point_selected(self, x, y, mode):
        print(f"[InteractiveVision] 👆 ({x}, {y}) - {mode}")
        
        data_uri, _, img = screenshot_data_uri(monitor=1)
        
        prompts = {
            "อธิบาย": f"อธิบายสิ่งที่อยู่รอบๆ ตำแหน่ง ({x}, {y}) บนหน้าจอนี้",
            "วิเคราะห์": f"วิเคราะห์ว่าสิ่งที่อยู่ตำแหน่ง ({x}, {y}) มีความหมายอย่างไร",
            "แนะนำ": f"แนะนำว่าควรทำอะไรกับสิ่งที่อยู่ตำแหน่ง ({x}, {y})",
            "หา Element": f"ระบุว่าสิ่งที่อยู่ตำแหน่ง ({x}, {y}) คือ UI element ประเภทใด",
            "ทำงาน": f"แนะนำคำสั่งที่ใช้โต้ตอบกับสิ่งที่อยู่ตำแหน่ง ({x}, {y})"
        }
        
        prompt = prompts.get(mode, prompts["อธิบาย"])
        
        self.status_updated.emit(f"🔍 กำลังวิเคราะห์ ({x}, {y})...")
        reply = self.llm.ask_with_image(prompt, data_uri)
        
        self.response_ready.emit(f"🤖 [{mode}] {reply}")
        self.tts.speak(reply)
        
        if self.vision_overlay:
            self.vision_overlay.clear_annotations()
            self.vision_overlay.add_text(x + 10, y - 10, "👆 คุณคลิกที่นี่")
            self.vision_overlay.show_temporary(3000)
    
    @pyqtSlot(int, int, int, int, str)
    def on_region_selected(self, x, y, w, h, mode):
        print(f"[InteractiveVision] 📦 ({x}, {y}, {w}, {h}) - {mode}")
        
        region = (x, y, w, h)
        data_uri, _, img = screenshot_data_uri(region=region, monitor=1)
        
        prompts = {
            "อธิบาย": "อธิบายสิ่งที่เห็นในภาพนี้อย่างละเอียด",
            "วิเคราะห์": "วิเคราะห์เนื้อหาในภาพนี้ และบอกความหมาย",
            "แนะนำ": "แนะนำว่าควรทำอะไรกับสิ่งที่เห็นในภาพนี้",
            "หา Element": "ระบุ UI elements ทั้งหมดที่เห็นในภาพนี้",
            "ทำงาน": "แนะนำขั้นตอนการทำงานกับสิ่งที่เห็นในภาพนี้"
        }
        
        prompt = prompts.get(mode, prompts["อธิบาย"])
        
        self.status_updated.emit(f"🔍 กำลังวิเคราะห์พื้นที่ {w}x{h}px...")
        reply = self.llm.ask_with_image(prompt, data_uri)
        
        self.response_ready.emit(f"🤖 [{mode}] {reply}")
        self.tts.speak(reply)
        
        if self.vision_overlay:
            self.vision_overlay.clear_annotations()
            self.vision_overlay.add_box(x, y, w, h, f"{w}x{h}px")
            self.vision_overlay.show_temporary(5000)

    # =====================================================
    # 🧠 Copilot Vision (Original)
    # =====================================================
    
    def open_vision_panel(self, assistant_bar):
        """เปิดหน้าต่างเลือกหน้าจอสำหรับ Copilot Vision"""
        if not _HAS_MSS:
            self.status_updated.emit("❌ ต้องการติดตั้ง mss: pip install mss")
            self.tts.speak("ขอโทษครับ ระบบวิเคราะห์ภาพยังไม่พร้อมใช้งาน")
            return
            
        self.vision_panel = ScreenSharePanel()
        self.vision_panel.share_requested.connect(
            lambda m, d: self.share_screen_to_ai(m, d, assistant_bar)
        )
        self.vision_panel.show()
        print("[Vision] เปิดหน้าต่างเลือกหน้าจอ")

    def share_screen_to_ai(self, monitor_id, description, assistant_bar):
        """จับภาพหน้าจอแล้วให้ AI วิเคราะห์"""
        assistant_bar.status_label.setText(f"📡 กำลังแชร์ {description} ให้ AI...")
        try:
            reply = self.vision.ask_with_screenshot(
                f"อธิบายสิ่งที่เห็นบน {description} ให้ละเอียดเป็นภาษาไทย",
                monitor=monitor_id
            )
            
            assistant_bar.show_ai_response(f"🤖 [Vision-{monitor_id}]: {reply}")
            self.tts.speak(reply)
            assistant_bar.status_label.setText(f"✅ วิเคราะห์ {description} สำเร็จ")
            
            self.context.record_command(f"vision share {description}", "วิเคราะห์ภาพสำเร็จ")
            
        except Exception as e:
            error_msg = f"❌ แชร์ไม่สำเร็จ: {e}"
            assistant_bar.status_label.setText(error_msg)
            self.tts.speak("ขอโทษครับ การวิเคราะห์ภาพมีปัญหา")
            print(f"[Vision Error] {e}")

    # =====================================================
    # 🎯 Command Processing
    # =====================================================
    
    def handle_voice_f4(self):
        """จัดการคำสั่งเสียงจาก F4"""
        try:
            self.status_updated.emit("กำลังฟัง...")
            print("🎤 [F4] กำลังอัดเสียง 5 วินาที...")
            self.tts.speak("เริ่มฟังแล้วครับ")
            user_input = self.stt.listen_once(duration=5)
            
            if not user_input or user_input.strip() == "":
                self.status_updated.emit("ไม่ได้ยินเสียง")
                self.tts.speak("ขอโทษครับ ผมไม่ได้ยิน")
                return

            print(f"📝 คุณพูดว่า: {user_input}")
            
            context_suggestion = self.context.get_smart_suggestion(user_input)
            if "เคย" in context_suggestion:
                print(f"🧠 [Context] {context_suggestion}")
            
            self.voice_input_received.emit(user_input)
            self.process_command(user_input)
            
        except Exception as e:
            error_msg = f"ข้อผิดพลาดในการประมวลผลเสียง: {str(e)}"
            self.response_ready.emit(error_msg)
            self.status_updated.emit("ประมวลผลเสียงไม่สำเร็จ")
            print(f"[ERROR] {e}")
    
    @pyqtSlot(str)
    def process_command(self, command: str):
        """ประมวลผลคำสั่งทั้งหมด"""
        try:
            self.status_updated.emit("กำลังประมวลผล...")
            cmd_lower = command.lower()
            
            # คำสั่งออกจากโปรแกรม
            if cmd_lower in ["exit", "quit", "q"]:
                self.tts.speak("ลาก่อนครับ")
                self.status_updated.emit("กำลังปิดโปรแกรม...")
                QApplication.instance().quit()
                return
            
            # แสดง Context
            if cmd_lower in ["context", "ประวัติ", "history"]:
                summary = self.context.get_context_summary()
                self.response_ready.emit(f"🧠 [Context Memory] {summary}")
                self.tts.speak(f"สรุปกิจกรรมล่าสุด: {summary}")
                self.status_updated.emit("แสดงประวัติเรียบร้อย")
                return
            
            # ✅ คำสั่ง Vision Systems
            if "continuous vision" in cmd_lower or "วิเคราะห์ต่อเนื่อง" in cmd_lower:
                if "start" in cmd_lower or "เริ่ม" in cmd_lower:
                    self.start_continuous_vision(interval=5)
                elif "stop" in cmd_lower or "หยุด" in cmd_lower:
                    self.stop_continuous_vision()
                return
            
            if "interactive vision" in cmd_lower or "โหมดโต้ตอบ" in cmd_lower:
                self.open_interactive_vision()
                return
            
            if "show hints" in cmd_lower or "แสดงคำแนะนำ" in cmd_lower:
                from core.ui_detector import UIDetector
                detector = UIDetector(monitor=1)
                elements = detector.find_all_text()[:10]
                
                hints = []
                for elem in elements:
                    hints.append({
                        "x": elem["x"],
                        "y": elem["y"],
                        "w": elem["w"],
                        "h": elem["h"],
                        "label": elem["text"][:20]
                    })
                
                self.show_ui_hints(hints)
                self.response_ready.emit(f"✅ แสดง {len(hints)} UI elements")
                return
            
            # คำสั่งเปิดโปรแกรม
            if self.command_parser.is_open_command(command):
                result = self.smart_app_launch(command)
                
                if result["ok"]:
                    app_name = self.command_parser.extract_app_name_from_command(command)
                    self.response_ready.emit(f"✅ {result['message']}")
                    self.tts.speak(f"เปิด {app_name} แล้วครับ")
                else:
                    self.response_ready.emit(f"❌ {result['message']}")
                    self.tts.speak("ขอโทษครับ ไม่พบโปรแกรมนี้")
                self.status_updated.emit("พร้อมใช้งาน")
                return
            
            # Vision Mode
            if cmd_lower.startswith("vision"):
                self.process_vision_command(command)
                return
            
            # Automation
            if any(word in cmd_lower for word in ["คลิก", "พิมพ์", "กด", "เลื่อน", "ปุ่ม"]):
                self.process_automation_command(command)
                return
            
            # โหมดแชทปกติ
            if command.strip():
                self.process_chat_command(command)
                
        except Exception as e:
            error_msg = f"ข้อผิดพลาด: {str(e)}"
            self.response_ready.emit(error_msg)
            self.status_updated.emit("เกิดข้อผิดพลาด")
            print(f"[ERROR] {e}")
    
    def smart_app_launch(self, raw_command: str) -> dict:
        """ระบบเปิดแอปอัจฉริยะ"""
        print(f"🚀 กำลังประมวลผล: '{raw_command}'")
        
        app_name = self.command_parser.extract_app_name_from_command(raw_command)
        url = self.command_parser.extract_url(raw_command)
        search_query = self.command_parser.extract_search_query(raw_command)
        
        print(f"📝 ชื่อโปรแกรม: '{app_name}'")
        if url:
            print(f"🔗 URL: {url}")
        if search_query:
            print(f"🔍 ค้นหา: {search_query}")
        
        result = self.smart_launcher.launch(app_name)
        
        if not result["ok"] and (url or search_query):
            print(f"[Smart Fallback] เปิด URL ผ่านเบราว์เซอร์...")
            browser = "chrome"
            final_url = url or search_query
            result = self.smart_launcher.launch(browser, final_url)
            
            if not result["ok"]:
                result = self.launcher.open_url(final_url, browser)
        
        if not result["ok"]:
            print(f"[Smart Fallback] ใช้ AppLauncher ลองอีกครั้ง...")
            result = self.launcher.launch(app_name)
        
        self.context.record_app_launch(app_name, result["ok"])
        self.context.record_command(f"เปิด {app_name}", 
                                 "สำเร็จ" if result["ok"] else "ล้มเหลว")
        
        return result
    
    def process_vision_command(self, command: str):
        """ประมวลผลคำสั่ง Vision"""
        match = re.match(r'vision:?(\d*)\s*(.*)', command, re.IGNORECASE)
        if match:
            monitor_str = match.group(1)
            vision_prompt = match.group(2).strip()
            monitor = int(monitor_str) if monitor_str else 1
            if not vision_prompt:
                vision_prompt = "อธิบายสิ่งที่เห็นบนหน้าจอนี้"

            self.status_updated.emit(f"กำลังวิเคราะห์ภาพจอที่ {monitor}...")
            
            try:
                reply_text = self.vision.analyze(vision_prompt, monitor=monitor)
                self.context.record_command(f"vision: {vision_prompt}", "วิเคราะห์ภาพ")
                self.response_ready.emit(f"🤖 ผู้ช่วย (Vision-{monitor}): {reply_text}")
                self.tts.speak(reply_text)
                self.status_updated.emit("วิเคราะห์ภาพเรียบร้อย")
            except Exception as e:
                error_msg = f"❌ {e}"
                self.response_ready.emit(error_msg)
                self.tts.speak("เกิดข้อผิดพลาดในการจับภาพ")
                self.status_updated.emit("วิเคราะห์ภาพไม่สำเร็จ")
    
    def process_automation_command(self, command: str):
        """ประมวลผลคำสั่ง Automation"""
        self.status_updated.emit("กำลังดำเนินการ Automation...")
        
        ocr_text = None
        data_uri = None
        if any(w in command.lower() for w in ["ปุ่ม", "หน้าจอ", "ไอคอน"]):
            try:
                sr = ScreenReader(lang="tha+eng")
                img = screenshot_pil(monitor=1)
                ocr_text = sr.read_text(monitor=1)
                data_uri, _, _ = screenshot_data_uri(monitor=1, resize_to=(1200, 800))
            except Exception as e:
                print(f"[WARN] OCR/Vision ไม่พร้อม: {e}")

        ok, parsed = self.parser.parse(command, ocr_text=ocr_text, hint_image_data_uri=data_uri)
        if not ok:
            self.response_ready.emit("❌ ไม่สามารถแปลงคำสั่งได้")
            self.tts.speak("ขอโทษครับ ผมไม่เข้าใจคำสั่ง")
            self.status_updated.emit("แปลงคำสั่งไม่สำเร็จ")
            return

        result = self.executor.execute(parsed)
        self.context.record_command(command, 
                                 "สำเร็จ" if result.get("ok") else "ล้มเหลว")
        
        if result.get("ok"):
            self.response_ready.emit(f"✅ สำเร็จ: {result.get('message')}")
            self.tts.speak("เรียบร้อยครับ")
            self.status_updated.emit("Automation สำเร็จ")
        else:
            self.response_ready.emit(f"❌ ไม่สำเร็จ: {result.get('message')}")
            self.tts.speak("ขอโทษครับ ทำไม่สำเร็จ")
            self.status_updated.emit("Automation ไม่สำเร็จ")
    
    def process_chat_command(self, command: str):
        """ประมวลผลคำสั่งแชทปกติ"""
        self.status_updated.emit("กำลังคิดคำตอบ...")
        
        reply_text = self.llm.ask(command, history=self.chat_history)
        self.chat_history.append({"role": "user", "content": command})
        self.chat_history.append({"role": "assistant", "content": reply_text})
        self.context.record_command(command, "แชทปกติ")
        
        self.response_ready.emit(f"🤖 ผู้ช่วย: {reply_text}")
        self.tts.speak(reply_text)
        self.status_updated.emit("พร้อมใช้งาน")


def main():
    """ฟังก์ชันหลัก - Full Version"""
    app = QApplication(sys.argv)
    
    # สร้าง core system
    assistant_core = AssistantCore()
    
    # สร้าง GUI
    assistant_bar = AssistantBar()
    
    # เชื่อมต่อสัญญาณ
    assistant_core.status_updated.connect(assistant_bar.status_label.setText)
    assistant_core.response_ready.connect(lambda text: print(f"🤖: {text}"))
    assistant_core.voice_input_received.connect(assistant_bar.show_voice_input)
    assistant_core.response_ready.connect(
        lambda text: assistant_bar.show_ai_response(text, speak=False)
    )
    
    assistant_bar.text_submitted.connect(assistant_core.process_command)
    assistant_bar.close_requested.connect(app.quit)
    assistant_bar.mic_pressed.connect(assistant_core.start_recording)
    assistant_bar.mic_released.connect(assistant_core.stop_recording)
    assistant_bar.stop_speaking_requested.connect(assistant_core.stop_speaking)
    
    # ✅ เพิ่มปุ่ม Vision ครบชุด
    assistant_bar.add_extra_button(
        "🧠 Copilot",
        lambda: assistant_core.open_vision_panel(assistant_bar)
    )
    
    if _HAS_VISION_SYSTEMS:
        assistant_bar.add_extra_button(
            "🔄 Continuous",
            lambda: assistant_core.start_continuous_vision(5)
        )
        
        assistant_bar.add_extra_button(
            "🖱️ Interactive",
            lambda: assistant_core.open_interactive_vision()
        )
        
        assistant_bar.add_extra_button(
            "🎨 Hints",
            lambda: assistant_core.process_command("show hints")
        )
    
    # เริ่มต้นระบบ
    assistant_core.hotkey_listener.start()
    assistant_bar.show()
    
    # แสดงคำแนะนำ
    print("=" * 70)
    print("=== 🤖 AI Assistant with Full Copilot Vision ===")
    print("=" * 70)
    print("✅ 🧠 Copilot - เลือกหน้าจอเพื่อวิเคราะห์")
    if _HAS_VISION_SYSTEMS:
        print("✅ 🔄 Continuous - วิเคราะห์หน้าจอต่อเนื่อง")
        print("✅ 🖱️ Interactive - คลิก/ลากเพื่อถาม AI")
        print("✅ 🎨 Hints - แสดงกรอบ UI elements")
    print("✅ 🎤 Push-to-Talk - กดค้างไมค์เพื่อพูด")
    print("✅ ⌨️ F4 - อัดเสียง 5 วินาที")
    print("=" * 70)
    
    assistant_core.status_updated.emit("พร้อมใช้งาน ✅")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()