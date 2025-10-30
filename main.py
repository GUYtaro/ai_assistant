# main.py
# ================================
# 🤖 AI Assistant (Complete Version with Copilot Vision)
# ✅ รองรับ Push-to-Talk, Copilot Vision, Screen Sharing
# ================================

import re
import sys
import urllib.parse
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QScrollArea, QFrame
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
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
                # sct.monitors[0] is the combined screen, [1:] are individual monitors
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
    บันทึกเสียงเมื่อกดค้างปุ่มไมค์ และแปลงเป็นข้อมูลดิจิตอล
    """
    
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(object)  # ส่ง audio data กลับ
    
    def __init__(self, stt_client: STTClient):
        super().__init__()
        self.stt = stt_client
        self.is_recording = False
        self.audio_data = []
        self.sample_rate = 16000  # ความถี่ที่เหมาะสมกับ Whisper
        
    def start_recording(self):
        """เริ่มบันทึกเสียง"""
        if self.is_recording:
            return
        
        self.is_recording = True
        self.audio_data = []
        
        print("[VoiceRecorder] 🔴 เริ่มบันทึกเสียง...")
        self.recording_started.emit()
        
        # Callback function สำหรับรับข้อมูลเสียง
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"[VoiceRecorder] Status: {status}")
            if self.is_recording:
                self.audio_data.append(indata.copy())
        
        # เริ่ม stream การบันทึกเสียง
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,  # โมโน
            callback=audio_callback,
            dtype=np.float32  # ใช้ float32 สำหรับ Whisper
        )
        self.stream.start()
    
    def stop_recording(self):
        """หยุดบันทึกเสียง และส่งข้อมูลกลับ"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # หยุด stream
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        print("[VoiceRecorder] ⏹️ หยุดบันทึกเสียง")
        
        # ตรวจสอบว่ามีข้อมูลเสียงหรือไม่
        if len(self.audio_data) == 0:
            print("[VoiceRecorder] ❌ ไม่มีข้อมูลเสียง")
            self.recording_stopped.emit(None)
            return
        
        # รวมข้อมูลเสียงทั้งหมด
        audio_array = np.concatenate(self.audio_data, axis=0)
        audio_float32 = audio_array.flatten().astype(np.float32)
        
        duration = len(audio_float32) / self.sample_rate
        print(f"[VoiceRecorder] ✅ บันทึกเสียงได้ {duration:.2f} วินาที")
        
        # ส่งข้อมูลเสียงกลับ
        self.recording_stopped.emit(audio_float32)


class TranscriptionWorker(QThread):
    """
    🔄 Worker thread สำหรับแปลงเสียงเป็นข้อความ
    ใช้ Whisper model แปลงข้อมูลเสียงเป็นข้อความภาษาไทย
    """
    
    transcription_done = pyqtSignal(str)  # ส่งข้อความที่แปลงได้
    
    def __init__(self, stt_client: STTClient, audio_data):
        super().__init__()
        self.stt = stt_client
        self.audio_data = audio_data
    
    def run(self):
        """แปลงเสียงเป็นข้อความ"""
        try:
            print("[TranscriptionWorker] 🔄 กำลังแปลงเสียงเป็นข้อความ...")
            
            # ใช้ Whisper model แปลงเสียง
            text = self.stt.model.transcribe(
                self.audio_data,
                language="th",  # ภาษาไทย
                fp16=False      # ใช้ float32 เพื่อความแม่นยำ
            )["text"].strip()
            
            print(f"[TranscriptionWorker] ✅ แปลงได้: {text}")
            self.transcription_done.emit(text)
            
        except Exception as e:
            print(f"[TranscriptionWorker] ❌ Error: {e}")
            self.transcription_done.emit("")


class AssistantContext:
    """
    🧠 Context Memory สำหรับผู้ช่วย
    จดจำการใช้งานล่าสุดและความชอบของผู้ใช้
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
        self.max_history = 10  # จำนวนคำสั่งล่าสุดที่เก็บไว้
    
    def record_command(self, command: str, result: str):
        """บันทึกคำสั่งและผลลัพธ์"""
        from datetime import datetime
        self.memory["recent_commands"].append({
            "command": command,
            "result": result,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        # ลบคำสั่งเก่าถ้าเกินจำนวนที่กำหนด
        if len(self.memory["recent_commands"]) > self.max_history:
            self.memory["recent_commands"].pop(0)
    
    def record_app_launch(self, app_name: str, success: bool):
        """บันทึกการเปิดแอปพลิเคชัน"""
        self.memory["last_opened_app"] = app_name
        if app_name not in self.memory["favorite_apps"]:
            self.memory["favorite_apps"][app_name] = {"launch_count": 0, "success_count": 0}
        self.memory["favorite_apps"][app_name]["launch_count"] += 1
        if success:
            self.memory["favorite_apps"][app_name]["success_count"] += 1
    
    def get_smart_suggestion(self, partial_command: str) -> str:
        """ให้คำแนะนำจากประวัติการใช้งาน"""
        partial_lower = partial_command.lower()
        
        # ตรวจสอบคำสั่งล่าสุด
        for cmd in reversed(self.memory["recent_commands"]):
            if partial_lower in cmd["command"].lower():
                return f"เคยทำคำสั่งนี้: '{cmd['command']}' -> {cmd['result']}"
        
        # ตรวจสอบแอปพลิเคชันที่เคยเปิด
        for app_name, stats in self.memory["favorite_apps"].items():
            if partial_lower in app_name.lower():
                success_rate = (stats["success_count"] / stats["launch_count"]) * 100
                return f"เคยเปิด '{app_name}' {stats['launch_count']} ครั้ง (สำเร็จ {success_rate:.0f}%)"
        
        return "ไม่พบประวัติที่เกี่ยวข้อง"
    
    def get_context_summary(self) -> str:
        """สรุปประวัติการใช้งานล่าสุด"""
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
    แปลงคำไทยเป็นภาษาอังกฤษและตรวจจับคำสั่งต่างๆ
    """
    
    def __init__(self, llm_client):
        self.llm = llm_client
        # Mapping คำไทยเป็นภาษาอังกฤษ
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
        """ตรวจสอบว่าเป็นคำสั่งเปิดแอปหรือไม่"""
        return any(word in text.lower() for word in ["เปิด", "open", "launch", "start", "run"])
    
    def extract_app_name_from_command(self, text: str) -> str:
        """แยกชื่อแอปพลิเคชันจากคำสั่ง"""
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
        """แปลคำไทยเป็นภาษาอังกฤษ"""
        thai_text = thai_text.strip()
        if thai_text in self.thai_to_english_map:
            return self.thai_to_english_map[thai_text]
        for thai, english in self.thai_to_english_map.items():
            if thai in thai_text:
                return english
        return thai_text
    
    def extract_url(self, text: str) -> str:
        """แยก URL จากคำสั่ง"""
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
        """แยกคำค้นหาจากคำสั่ง"""
        if "ค้นหา" not in text.lower() and "search" not in text.lower():
            return None
        query = text.lower().replace("เปิด", "").replace("ค้นหา", "").strip()
        if query:
            return f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        return None


class AssistantCore(QObject):
    """
    🧠 Core System ของ AI Assistant
    จัดการการประมวลผลคำสั่งทั้งหมดและประสานงานระหว่าง modules
    """
    
    # สัญญาณต่างๆ สำหรับการสื่อสารกับ GUI
    status_updated = pyqtSignal(str)          # อัพเดทสถานะ
    response_ready = pyqtSignal(str)          # ส่งการตอบกลับ
    voice_input_received = pyqtSignal(str)    # แสดงข้อความจากเสียง
    
    def __init__(self):
        super().__init__()
        self.setup_core_systems()
        
    def setup_core_systems(self):
        """ตั้งค่าระบบทั้งหมด"""
        try:
            # ตั้งค่า core modules
            self.llm = LLMClient()                    # AI Language Model
            self.stt = STTClient(model_size="medium", language="th")  # Speech-to-Text
            self.tts = TTSClient(lang="th")           # Text-to-Speech  
            self.vision = VisionSystem()              # Vision Analysis
            self.parser = CommandParser(llm_client=self.llm)  # Command Parser
            self.executor = AutomationExecutor(monitor=1)     # Automation
            self.launcher = AppLauncher()             # App Launcher
            self.smart_launcher = SmartAppLauncher()  # Smart App Launcher
            
            # ตั้งค่า systems เพิ่มเติม
            self.context = AssistantContext()         # Context Memory
            self.command_parser = SmartCommandParser(llm_client=self.llm)  # Smart Parser
            
            # ตั้งค่า Voice Recorder สำหรับ Push-to-Talk
            self.voice_recorder = VoiceRecorder(self.stt)
            self.voice_recorder.recording_stopped.connect(self.on_audio_recorded)
            
            # ประวัติการสนทนา
            self.chat_history = [{
                "role": "system", 
                "content": "คุณคือผู้ช่วยที่ตอบเป็นภาษาไทยอย่างเป็นมิตรและเป็นธรรมชาติ"
            }]
            
            # ตั้งค่า Hotkey Listener (ปุ่ม F4)
            self.hotkey_listener = HotkeyListener(
                callback_start=self.handle_voice_f4,
                hotkey="f4",
                cooldown=2.0
            )
            
            self.status_updated.emit("ระบบพร้อมใช้งาน ✅")
            print("=== 🤖 AI Assistant (Complete with Copilot Vision) ===")
            
        except Exception as e:
            error_msg = f"ข้อผิดพลาดในการตั้งค่าระบบ: {str(e)}"
            self.status_updated.emit(error_msg)
            print(f"Error setting up systems: {e}")

    # =====================================================
    # 🎤 Voice Recording Methods
    # =====================================================
    
    @pyqtSlot()
    def start_recording(self):
        """เริ่มบันทึกเสียง (เมื่อกดปุ่มไมค์)"""
        print("[AssistantCore] 🎤 เริ่มบันทึกเสียง...")
        self.status_updated.emit("🔴 กำลังฟัง...")
        self.voice_recorder.start_recording()
    
    @pyqtSlot()
    def stop_recording(self):
        """หยุดบันทึกเสียง (เมื่อปล่อยปุ่มไมค์)"""
        print("[AssistantCore] ⏹️ หยุดบันทึกเสียง")
        self.status_updated.emit("⏳ กำลังประมวลผล...")
        self.voice_recorder.stop_recording()
    
    @pyqtSlot(object)
    def on_audio_recorded(self, audio_data):
        """เมื่อได้ข้อมูลเสียงแล้ว → แปลงเป็นข้อความ"""
        if audio_data is None or len(audio_data) == 0:
            self.status_updated.emit("❌ ไม่มีเสียง")
            self.tts.speak("ขอโทษครับ ผมไม่ได้ยินเสียง")
            return
        
        # สร้าง worker thread สำหรับแปลงเสียง
        self.transcription_worker = TranscriptionWorker(self.stt, audio_data)
        self.transcription_worker.transcription_done.connect(self.on_transcription_done)
        self.transcription_worker.start()
    
    @pyqtSlot(str)
    def on_transcription_done(self, text: str):
        """เมื่อแปลงเสียงเป็นข้อความเสร็จแล้ว"""
        if not text or text.strip() == "":
            self.status_updated.emit("❌ ไม่เข้าใจ")
            self.tts.speak("ขอโทษครับ ผมไม่เข้าใจ")
            return
        
        print(f"📝 คุณพูดว่า: {text}")
        
        # แสดงข้อความจากเสียงใน GUI
        self.voice_input_received.emit(text)
        self.response_ready.emit(f"📝 คุณพูดว่า: {text}")
        
        # ประมวลผลคำสั่ง
        self.process_command(text)

    # =====================================================
    # 🛑 Stop Speaking Method
    # =====================================================
    
    @pyqtSlot()
    def stop_speaking(self):
        """
        หยุดการพูดปัจจุบัน
        ทำงานกับ TTS Client ที่รองรับการหยุด
        """
        print("[AssistantCore] ⏹️ กำลังหยุดการพูด...")
        
        # อัพเดท UI ทันที
        self.status_updated.emit("หยุดการพูดแล้ว")
        self.response_ready.emit("⏹️ หยุดการพูดแล้ว")
        
        try:
            # พยายามหยุด TTS
            if hasattr(self.tts, 'stop_speaking'):
                success = self.tts.stop_speaking()
                if success:
                    print("[AssistantCore] ✅ หยุดการพูดสำเร็จ")
                else:
                    print("[AssistantCore] ❌ หยุดการพูดไม่สำเร็จ")
            else:
                # วิธีสำรอง: สร้าง TTS ใหม่
                print("[AssistantCore] 🔄 รีสตาร์ทระบบเสียง...")
                self.tts = TTSClient(lang="th")
                print("[AssistantCore] ✅ หยุดการพูดสำเร็จ (วิธีสำรอง)")
                
        except Exception as e:
            error_msg = f"❌ ข้อผิดพลาดในการหยุดพูด: {str(e)}"
            print(f"[AssistantCore] {error_msg}")

    # =====================================================
    # 🧠 Copilot Vision Methods
    # =====================================================
    
    def open_vision_panel(self, assistant_bar):
        """
        เปิดหน้าต่างเลือกหน้าจอสำหรับ Copilot Vision
        """
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
        """
        จับภาพหน้าจอแล้วให้ AI วิเคราะห์
        """
        assistant_bar.status_label.setText(f"📡 กำลังแชร์ {description} ให้ AI...")
        try:
            # ใช้ vision system วิเคราะห์ภาพ
            reply = self.vision.ask_with_screenshot(
                f"อธิบายสิ่งที่เห็นบน {description} ให้ละเอียดเป็นภาษาไทย",
                monitor=monitor_id
            )
            
            # แสดงผลลัพธ์
            assistant_bar.show_ai_response(f"🤖 [Vision-{monitor_id}]: {reply}")
            self.tts.speak(reply)
            assistant_bar.status_label.setText(f"✅ วิเคราะห์ {description} สำเร็จ")
            
            # บันทึกใน context
            self.context.record_command(f"vision share {description}", "วิเคราะห์ภาพสำเร็จ")
            
        except Exception as e:
            error_msg = f"❌ แชร์ไม่สำเร็จ: {e}"
            assistant_bar.status_label.setText(error_msg)
            self.tts.speak("ขอโทษครับ การวิเคราะห์ภาพมีปัญหา")
            print(f"[Vision Error] {e}")

    # =====================================================
    # 🎯 Command Processing Methods
    # =====================================================
    
    def handle_voice_f4(self):
        """จัดการคำสั่งเสียงจาก F4 (แบบเดิม - อัด 5 วินาที)"""
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
            
            # ตรวจสอบ Context Memory
            context_suggestion = self.context.get_smart_suggestion(user_input)
            if "เคย" in context_suggestion:
                print(f"🧠 [Context] {context_suggestion}")
            
            # แสดงข้อความจากเสียงใน GUI
            self.voice_input_received.emit(user_input)
            
            # ส่งคำสั่งเสียงไปประมวลผล
            self.process_command(user_input)
            
        except Exception as e:
            error_msg = f"ข้อผิดพลาดในการประมวลผลเสียง: {str(e)}"
            self.response_ready.emit(error_msg)
            self.status_updated.emit("ประมวลผลเสียงไม่สำเร็จ")
            print(f"[ERROR] {e}")
    
    @pyqtSlot(str)
    def process_command(self, command: str):
        """ประมวลผลคำสั่งจาก GUI หรือ Voice"""
        try:
            self.status_updated.emit("กำลังประมวลผล...")
            
            # คำสั่งออกจากโปรแกรม
            if command.lower() in ["exit", "quit", "q"]:
                self.tts.speak("ลาก่อนครับ")
                self.status_updated.emit("กำลังปิดโปรแกรม...")
                QApplication.instance().quit()
                return
            
            # แสดง Context Summary
            if command.lower() in ["context", "ประวัติ", "history"]:
                summary = self.context.get_context_summary()
                self.response_ready.emit(f"🧠 [Context Memory] {summary}")
                self.tts.speak(f"สรุปกิจกรรมล่าสุด: {summary}")
                self.status_updated.emit("แสดงประวัติเรียบร้อย")
                return
            
            # ตรวจจับคำสั่งเปิดโปรแกรม
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
            if command.lower().startswith("vision"):
                self.process_vision_command(command)
                return
            
            # ตรวจจับคำสั่ง Automation
            if any(word in command.lower() for word in ["คลิก", "พิมพ์", "กด", "เลื่อน", "ปุ่ม"]):
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
        """ระบบเปิดแอปอัจฉริยะแบบใหม่"""
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
        
        # Fallback ระบบหากเปิดไม่สำเร็จ
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
        
        # บันทึกใน context
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
    """ฟังก์ชันหลักแบบ GUI - รวมทุกฟีเจอร์"""
    app = QApplication(sys.argv)
    
    # สร้าง core system
    assistant_core = AssistantCore()
    
    # สร้าง GUI
    assistant_bar = AssistantBar()
    
    # =====================================================
    # 🔗 การเชื่อมต่อสัญญาณทั้งหมด
    # =====================================================
    
    # การอัพเดทสถานะและแสดงผล
    assistant_core.status_updated.connect(assistant_bar.status_label.setText)
    assistant_core.response_ready.connect(lambda text: print(f"🤖: {text}"))
    assistant_core.voice_input_received.connect(assistant_bar.show_voice_input)
    
    # ป้องกันการพูดซ้ำ
    assistant_core.response_ready.connect(
        lambda text: assistant_bar.show_ai_response(text, speak=False)
    )
    
    # การเชื่อมต่อจาก GUI ไปยัง Core
    assistant_bar.text_submitted.connect(assistant_core.process_command)
    assistant_bar.close_requested.connect(app.quit)
    assistant_bar.mic_pressed.connect(assistant_core.start_recording)
    assistant_bar.mic_released.connect(assistant_core.stop_recording)
    assistant_bar.stop_speaking_requested.connect(assistant_core.stop_speaking)
    
    # ✅ การเชื่อมต่อ Copilot Vision
    # หมายเหตุ: ต้องเพิ่มปุ่มใน GUI เพื่อเรียกใช้ assistant_core.open_vision_panel(assistant_bar)
    
    # เริ่มต้นระบบ
    assistant_core.hotkey_listener.start()
    assistant_bar.show()
    # ✅ เพิ่มปุ่ม Copilot Vision ใน AssistantBar
    assistant_bar.add_extra_button("🧠 Copilot Vision", lambda: assistant_core.open_vision_panel(assistant_bar))

    # แสดงคำแนะนำ
    print("=" * 60)
    print("=== 🤖 AI Assistant (Complete with Copilot Vision) ===")
    print("=" * 60)
    print("✅ กดค้างปุ่มไมค์เพื่อพูด (Push-to-Talk)")
    print("✅ กด F4 เพื่ออัดเสียง 5 วินาที")
    print("✅ พิมพ์คำสั่งแล้วกด Enter")
    print("✅ มีปุ่มหยุดพูดและปิดโปรแกรม")
    if _HAS_MSS:
        print("✅ Copilot Vision พร้อมใช้งาน (ต้องการปุ่มใน GUI)")
    else:
        print("⚠️  ติดตั้ง mss สำหรับ Copilot Vision: pip install mss")
    
    assistant_core.status_updated.emit("พร้อมใช้งาน ✅")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()