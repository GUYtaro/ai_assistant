# main.py
# -------------------------
# โปรแกรมหลักของ AI Assistant (Enhanced Version)
# ✅ รองรับ Push-to-Talk (กดค้างไมค์)
# -------------------------

import re
import sys
import urllib.parse  # ✅ เพิ่ม import นี้
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
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
import sounddevice as sd
import numpy as np


class VoiceRecorder(QObject):
    """✅ ตัวอัดเสียงแบบ Push-to-Talk"""
    
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(object)  # ส่ง audio data กลับ
    
    def __init__(self, stt_client: STTClient):
        super().__init__()
        self.stt = stt_client
        self.is_recording = False
        self.audio_data = []
        self.sample_rate = 16000
        
    def start_recording(self):
        """เริ่มอัดเสียง"""
        if self.is_recording:
            return
        
        self.is_recording = True
        self.audio_data = []
        
        print("[VoiceRecorder] 🔴 เริ่มอัดเสียง...")
        self.recording_started.emit()
        
        # เริ่ม stream อัดเสียง
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
        """หยุดอัดเสียง และส่งข้อมูลกลับ"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # หยุด stream
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()
        
        print("[VoiceRecorder] ⏹️ หยุดอัดเสียง")
        
        # รวม audio data
        if len(self.audio_data) == 0:
            print("[VoiceRecorder] ❌ ไม่มีข้อมูลเสียง")
            self.recording_stopped.emit(None)
            return
        
        audio_array = np.concatenate(self.audio_data, axis=0)
        
        # ✅ แก้ไข: ใช้ float32 แทน int16 สำหรับ Whisper
        audio_float32 = audio_array.flatten().astype(np.float32)
        
        print(f"[VoiceRecorder] ✅ อัดเสียงได้ {len(audio_float32) / self.sample_rate:.2f} วินาที")
        
        # ส่งข้อมูลกลับ
        self.recording_stopped.emit(audio_float32)


class TranscriptionWorker(QThread):
    """✅ Worker thread สำหรับแปลงเสียงเป็นข้อความ"""
    
    transcription_done = pyqtSignal(str)  # ส่งข้อความที่แปลงได้
    
    def __init__(self, stt_client: STTClient, audio_data):
        super().__init__()
        self.stt = stt_client
        self.audio_data = audio_data
    
    def run(self):
        """แปลงเสียงเป็นข้อความ"""
        try:
            print("[TranscriptionWorker] 🔄 กำลังแปลงเสียงเป็นข้อความ...")
            
            # ใช้ Whisper แปลงเสียง
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


class AssistantCore(QObject):
    """คลาสหลักสำหรับประมวลผลคำสั่ง"""
    
    status_updated = pyqtSignal(str)
    response_ready = pyqtSignal(str)
    # ✅ เพิ่มสัญญาณสำหรับแสดงข้อความจากเสียงใน GUI
    voice_input_received = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setup_core_systems()
        
    def setup_core_systems(self):
        """ตั้งค่าระบบทั้งหมด"""
        try:
            self.llm = LLMClient()
            self.stt = STTClient(model_size="medium", language="th")
            self.tts = TTSClient(lang="th")
            self.vision = VisionSystem()
            self.parser = CommandParser(llm_client=self.llm)
            self.executor = AutomationExecutor(monitor=1)
            self.launcher = AppLauncher()
            self.smart_launcher = SmartAppLauncher()
            self.context = AssistantContext()
            self.command_parser = SmartCommandParser(llm_client=self.llm)
            
            # ✅ สร้าง VoiceRecorder
            self.voice_recorder = VoiceRecorder(self.stt)
            self.voice_recorder.recording_stopped.connect(self.on_audio_recorded)
            
            self.chat_history = [{"role": "system", "content": "คุณคือผู้ช่วยที่ตอบเป็นภาษาไทยอย่างเป็นมิตร"}]
            
            # ตั้งค่า hotkey listener (F4)
            self.hotkey_listener = HotkeyListener(
                callback_start=self.handle_voice_f4,
                hotkey="f4",
                cooldown=2.0
            )
            
            self.status_updated.emit("ระบบพร้อมใช้งาน")
            print("=== 🤖 AI Assistant (Enhanced with Smart Features) ===")
            
        except Exception as e:
            self.status_updated.emit(f"ข้อผิดพลาดในการตั้งค่าระบบ: {str(e)}")
            print(f"Error setting up systems: {e}")
     
    @pyqtSlot()
    def stop_speaking(self):
        """✅ หยุดการพูด - วิธีด่วนที่ไม่บล็อก"""
        print("[AssistantCore] ⏹️ หยุดการพูด...")
        
        # อัพเดท UI ทันที
        self.status_updated.emit("หยุดการพูดแล้ว")
        self.response_ready.emit("⏹️ หยุดการพูดแล้ว")
        
        # พยายามหยุดแบบไม่บล็อก
        try:
            if hasattr(self.tts, 'engine'):
                self.tts.engine.stop()
        except:
            pass
        
        print("[AssistantCore] ✅ ส่งคำสั่งหยุดแล้ว")
        
    @pyqtSlot()
    def stop_speaking(self):
        """✅ หยุดการพูดปัจจุบัน"""
        print("[AssistantCore] ⏹️ กำลังหยุดการพูด...")
        try:
            # ✅ หยุด TTS
            if hasattr(self.tts, 'stop_speaking'):
                success = self.tts.stop_speaking()
                if success:
                    self.status_updated.emit("หยุดการพูดแล้ว")
                    self.response_ready.emit("⏹️ หยุดการพูดแล้ว")
                    print("[AssistantCore] ✅ หยุดการพูดสำเร็จ")
                else:
                    self.status_updated.emit("หยุดการพูดไม่สำเร็จ")
                    print("[AssistantCore] ❌ หยุดการพูดไม่สำเร็จ")
            else:
                # ✅ วิธีสำรอง: สร้าง TTS ใหม่
                print("[AssistantCore] 🔄 รีสตาร์ทระบบเสียง...")
                self.tts = TTSClient(lang="th")
                self.status_updated.emit("หยุดการพูดแล้ว")
                self.response_ready.emit("⏹️ หยุดการพูดแล้ว")
                print("[AssistantCore] ✅ หยุดการพูดสำเร็จ (วิธีสำรอง)")
                
        except Exception as e:
            error_msg = f"❌ ข้อผิดพลาดในการหยุดพูด: {str(e)}"
            print(f"[AssistantCore] {error_msg}")
            self.status_updated.emit("หยุดการพูดไม่สำเร็จ")
    
    @pyqtSlot()
    def start_recording(self):
        """✅ เริ่มอัดเสียง (เมื่อกดปุ่มไมค์)"""
        print("[AssistantCore] 🎤 เริ่มอัดเสียง...")
        self.status_updated.emit("🔴 กำลังฟัง...")
        self.voice_recorder.start_recording()
    
    @pyqtSlot()
    def stop_recording(self):
        """✅ หยุดอัดเสียง (เมื่อปล่อยปุ่มไมค์)"""
        print("[AssistantCore] ⏹️ หยุดอัดเสียง")
        self.status_updated.emit("⏳ กำลังประมวลผล...")
        self.voice_recorder.stop_recording()
    
    @pyqtSlot(object)
    def on_audio_recorded(self, audio_data):
        """✅ เมื่อได้ข้อมูลเสียงแล้ว → แปลงเป็นข้อความ"""
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
        """✅ เมื่อแปลงเสียงเป็นข้อความเสร็จแล้ว"""
        if not text or text.strip() == "":
            self.status_updated.emit("❌ ไม่เข้าใจ")
            self.tts.speak("ขอโทษครับ ผมไม่เข้าใจ")
            return
        
        print(f"📝 คุณพูดว่า: {text}")
        
        # ✅ แสดงข้อความจากเสียงใน GUI
        self.voice_input_received.emit(text)
        self.response_ready.emit(f"📝 คุณพูดว่า: {text}")
        
        # ประมวลผลคำสั่ง
        self.process_command(text)
    
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
            
            # ✅ ตรวจสอบ Context Memory
            context_suggestion = self.context.get_smart_suggestion(user_input)
            if "เคย" in context_suggestion:
                print(f"🧠 [Context] {context_suggestion}")
            
            # ✅ แสดงข้อความจากเสียงใน GUI
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
            
            # ออกจากโปรแกรม
            if command.lower() in ["exit", "quit", "q"]:
                self.tts.speak("ลาก่อนครับ")
                self.status_updated.emit("กำลังปิดโปรแกรม...")
                QApplication.instance().quit()
                return
            
            # ✅ แสดง Context Summary
            if command.lower() in ["context", "ประวัติ", "history"]:
                summary = self.context.get_context_summary()
                self.response_ready.emit(f"🧠 [Context Memory] {summary}")
                self.tts.speak(f"สรุปกิจกรรมล่าสุด: {summary}")
                self.status_updated.emit("แสดงประวัติเรียบร้อย")
                return
            
            # ✅ ตรวจจับคำสั่งเปิดโปรแกรม
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
            
            # โหมดพิมพ์ปกติ
            if command.strip():
                self.process_chat_command(command)
                
        except Exception as e:
            error_msg = f"ข้อผิดพลาด: {str(e)}"
            self.response_ready.emit(error_msg)
            self.status_updated.emit("เกิดข้อผิดพลาด")
            print(f"[ERROR] {e}")
    
    def smart_app_launch(self, raw_command: str) -> dict:
        """✅ ระบบเปิดแอปอัจฉริยะแบบใหม่"""
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


class AssistantContext:
    """คลาสจัดการ Context Memory ของผู้ช่วย"""
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
    """✅ ตัวแยกคำสั่งอัจฉริยะ + แปลงคำไทยเป็นอังกฤษ"""
    
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
            # ✅ ใช้ urllib.parse ที่ import แล้ว
            return f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        return None


def main():
    """ฟังก์ชันหลักแบบ GUI - รวมข้อดีทั้งสองเวอร์ชัน"""
    app = QApplication(sys.argv)
    
    # สร้าง core system
    assistant_core = AssistantCore()
    
    # สร้าง GUI
    assistant_bar = AssistantBar()
    
    # ✅ เชื่อมต่อสัญญาณ (จากเวอร์ชันแรก + เวอร์ชันสอง)
    assistant_core.status_updated.connect(assistant_bar.status_label.setText)
    assistant_core.response_ready.connect(lambda text: print(f"🤖: {text}"))
    assistant_core.voice_input_received.connect(assistant_bar.show_voice_input)
    
    # ✅ ป้องกันการพูดซ้ำ (จากเวอร์ชันแรก)
    assistant_core.response_ready.connect(
        lambda text: assistant_bar.show_ai_response(text, speak=False)
    )
    
    # ✅ การเชื่อมต่ออื่นๆ (จากเวอร์ชันสอง)
    assistant_bar.text_submitted.connect(assistant_core.process_command)
    assistant_bar.close_requested.connect(app.quit)
    assistant_bar.mic_pressed.connect(assistant_core.start_recording)
    assistant_bar.mic_released.connect(assistant_core.stop_recording)
    
    # ✅ ✅ ✅ เพิ่มการเชื่อมต่อสัญญาณหยุดพูด
    assistant_bar.stop_speaking_requested.connect(assistant_core.stop_speaking)
    
    # ✅ เริ่มต้นระบบ (จากเวอร์ชันสอง)
    assistant_core.hotkey_listener.start()
    assistant_bar.show()
    
    # ✅ แสดงคำแนะนำ (จากเวอร์ชันสอง)
    print("=" * 60)
    print("=== 🤖 AI Assistant (GUI + Push-to-Talk) ===")
    print("=" * 60)
    print("✅ กดค้างปุ่มไมค์เพื่อพูด")
    print("✅ กด F4 เพื่ออัดเสียง 5 วินาที")
    print("✅ พิมพ์คำสั่งแล้วกด Enter")
    
    assistant_core.status_updated.emit("พร้อมใช้งาน ✅")
    sys.exit(app.exec())




if __name__ == "__main__":
    main()