# main.py
# -------------------------
# โปรแกรมหลักของ AI Assistant (Enhanced Version)
# เพิ่ม SmartAppLauncher + Context Memory + Smart Search
# ✅ แก้ไขปัญหา "ไม่สามารถแยกชื่อโปรแกรม" โดยส่งคำสั่งทั้งหมดไป SmartAppLauncher
# -------------------------

import re
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
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


class AssistantCore(QObject):
    """คลาสหลักสำหรับประมวลผลคำสั่ง"""
    
    # สัญญาณสำหรับอัพเดทสถานะใน GUI
    status_updated = pyqtSignal(str)
    response_ready = pyqtSignal(str)
    
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
            
            self.chat_history = [{"role": "system", "content": "คุณคือผู้ช่วยที่ตอบเป็นภาษาไทยอย่างเป็นมิตร"}]
            
            # ตั้งค่า hotkey listener
            self.hotkey_listener = HotkeyListener(
                callback_start=self.handle_voice,
                hotkey="f4",
                cooldown=2.0
            )
            
            self.status_updated.emit("ระบบพร้อมใช้งาน")
            print("=== 🤖 AI Assistant (Enhanced with Smart Features) ===")
            
        except Exception as e:
            self.status_updated.emit(f"ข้อผิดพลาดในการตั้งค่าระบบ: {str(e)}")
            print(f"Error setting up systems: {e}")
    
    @pyqtSlot(str)
    def process_command(self, command: str):
        """ประมวลผลคำสั่งจาก GUI"""
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
        
        # แยกชื่อโปรแกรมจากคำสั่ง (ตัดคำที่ไม่ต้องการ)
        app_name = self.command_parser.extract_app_name_from_command(raw_command)
        
        # เช็ค URL หรือ search query
        url = self.command_parser.extract_url(raw_command)
        search_query = self.command_parser.extract_search_query(raw_command)
        
        print(f"📝 ชื่อโปรแกรม: '{app_name}'")
        if url:
            print(f"🔗 URL: {url}")
        if search_query:
            print(f"🔍 ค้นหา: {search_query}")
        
        # 1. ✅ ส่งชื่อโปรแกรมไป SmartAppLauncher ค้นหา
        result = self.smart_launcher.launch(app_name)
        
        # 2. ถ้าไม่สำเร็จ และมี URL → เปิดผ่านเบราว์เซอร์
        if not result["ok"] and (url or search_query):
            print(f"[Smart Fallback] เปิด URL ผ่านเบราว์เซอร์...")
            browser = "chrome"  # ใช้ Chrome เป็นค่าเริ่มต้น
            
            # ลองเปิดเบราว์เซอร์พร้อม URL
            final_url = url or search_query
            result = self.smart_launcher.launch(browser, final_url)
            
            # ถ้ายังไม่ได้ → ใช้ AppLauncher
            if not result["ok"]:
                result = self.launcher.open_url(final_url, browser)
        
        # 3. ถ้ายังไม่สำเร็จ → ใช้ AppLauncher ลองค้นหาอีกครั้ง
        if not result["ok"]:
            print(f"[Smart Fallback] ใช้ AppLauncher ลองอีกครั้ง...")
            result = self.launcher.launch(app_name)
        
        # บันทึกผลลัพธ์ลง Context Memory
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
    
    def handle_voice(self):
        """จัดการคำสั่งเสียง"""
        try:
            self.status_updated.emit("กำลังฟัง...")
            print("🎤 [F4] กำลังอัดเสียง 5 วินาที... พูดได้เลยครับ")
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
            
            # ส่งคำสั่งเสียงไปประมวลผล
            self.process_command(user_input)
            
        except Exception as e:
            error_msg = f"ข้อผิดพลาดในการประมวลผลเสียง: {str(e)}"
            self.response_ready.emit(error_msg)
            self.status_updated.emit("ประมวลผลเสียงไม่สำเร็จ")
            print(f"[ERROR] {e}")


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
        """บันทึกคำสั่งและผลลัพธ์"""
        self.memory["recent_commands"].append({
            "command": command,
            "result": result,
            "timestamp": self._get_timestamp()
        })
        if len(self.memory["recent_commands"]) > self.max_history:
            self.memory["recent_commands"].pop(0)
    
    def record_app_launch(self, app_name: str, success: bool):
        """บันทึกการเปิดแอปพลิเคชัน"""
        self.memory["last_opened_app"] = app_name
        
        if app_name not in self.memory["favorite_apps"]:
            self.memory["favorite_apps"][app_name] = {
                "launch_count": 0,
                "success_count": 0
            }
        
        self.memory["favorite_apps"][app_name]["launch_count"] += 1
        if success:
            self.memory["favorite_apps"][app_name]["success_count"] += 1
    
    def get_smart_suggestion(self, partial_command: str) -> str:
        """ให้คำแนะนำอัจฉริยะจากประวัติ"""
        partial_lower = partial_command.lower()
        
        for cmd in reversed(self.memory["recent_commands"]):
            if partial_lower in cmd["command"].lower():
                return f"เคยทำคำสั่งนี้: '{cmd['command']}' -> {cmd['result']}"
        
        for app_name, stats in self.memory["favorite_apps"].items():
            if partial_lower in app_name.lower():
                success_rate = (stats["success_count"] / stats["launch_count"]) * 100
                return f"เคยเปิด '{app_name}' {stats['launch_count']} ครั้ง (สำเร็จ {success_rate:.0f}%)"
        
        return "ไม่พบประวัติที่เกี่ยวข้อง"
    
    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def get_context_summary(self) -> str:
        """สรุป context ปัจจุบัน"""
        summary = []
        if self.memory["last_opened_app"]:
            summary.append(f"เปิดล่าสุด: {self.memory['last_opened_app']}")
        
        if self.memory["recent_commands"]:
            recent_count = len(self.memory["recent_commands"])
            summary.append(f"คำสั่งล่าสุด: {recent_count} รายการ")
        
        if self.memory["favorite_apps"]:
            top_app = max(self.memory["favorite_apps"].items(), 
                         key=lambda x: x[1]["launch_count"], 
                         default=(None, None))
            if top_app[0]:
                summary.append(f"แอปยอดนิยม: {top_app[0]}")
        
        return " | ".join(summary) if summary else "ไม่มีประวัติล่าสุด"


class SmartCommandParser:
    """✅ ตัวแยกคำสั่งอัจฉริยะด้วย AI - ส่งต่อให้ SmartAppLauncher จัดการ"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def is_open_command(self, text: str) -> bool:
        """ตรวจสอบว่าเป็นคำสั่งเปิดโปรแกรมหรือไม่"""
        text_lower = text.lower()
        return any(word in text_lower for word in ["เปิด", "open", "launch", "start", "run"])
    
    def extract_app_name_from_command(self, text: str) -> str:
        """
        ✅ แยกชื่อโปรแกรมจากคำสั่ง - ตัดคำที่ไม่ต้องการออก
        แต่เก็บชื่อโปรแกรมไว้ให้ครบถ้วน
        """
        text_lower = text.lower()
        
        # ตัดคำสั่งออก
        remove_words = ["เปิด", "open", "launch", "start", "run", "ผ่าน", "ใน", "ด้วย", "หน่อย", "ให้หน่อย"]
        
        app_name = text_lower
        for word in remove_words:
            app_name = app_name.replace(word, "").strip()
        
        return app_name
    
    def extract_url(self, text: str) -> str:
        """ดึง URL ที่รู้จักจากคำสั่ง"""
        text_lower = text.lower()
        url_map = {
            "youtube": "https://youtube.com",
            "google": "https://google.com",
            "facebook": "https://facebook.com",
            "github": "https://github.com",
            "chatgpt": "https://chat.openai.com",
            "chat gpt": "https://chat.openai.com",
            "claude": "https://claude.ai",
            "gemini": "https://gemini.google.com",
            "bard": "https://gemini.google.com",
            "twitter": "https://x.com",
            "x.com": "https://x.com",
            "instagram": "https://instagram.com",
            "netflix": "https://netflix.com",
            "spotify": "https://open.spotify.com"
        }
        
        for keyword, url in url_map.items():
            if keyword in text_lower:
                return url
        return None
    
    def extract_search_query(self, text: str) -> str:
        """แยก search query จากคำสั่ง"""
        text_lower = text.lower()
        if "ค้นหา" not in text_lower and "search" not in text_lower:
            return None
        
        # ตัดคำที่ไม่ต้องการ
        query = text_lower.replace("เปิด", "").replace("open", "")
        query = query.replace("ค้นหา", "").replace("search", "")
        query = query.replace("chrome", "").replace("firefox", "").replace("edge", "")
        query = query.replace("ผ่าน", "").replace("ใน", "").replace("google", "")
        query = query.strip()
        
        if query:
            import urllib.parse
            return f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        
        return None


def main():
    """ฟังก์ชันหลักแบบ GUI"""
    app = QApplication(sys.argv)
    
    # สร้าง core system
    assistant_core = AssistantCore()
    
    # สร้าง GUI
    assistant_bar = AssistantBar()
    
    # เชื่อมต่อสัญญาณระหว่าง GUI และ Core
    assistant_bar.text_submitted.connect(assistant_core.process_command)
    assistant_bar.close_requested.connect(app.quit)
    assistant_core.status_updated.connect(assistant_bar.status_label.setText)
    assistant_core.response_ready.connect(lambda text: print(f"🤖: {text}"))
    
    # เริ่มต้น hotkey listener
    assistant_core.hotkey_listener.start()
    
    # แสดง GUI
    assistant_bar.show()
    
    print("=========================================================")
    print("=== 🤖 AI Assistant (Enhanced with Smart Features) ===")
    print("=========================================================")
    print("โหมดพิมพ์: พิมพ์ข้อความในแถบผู้ช่วย แล้วกด Enter")
    print("โหมด Vision: พิมพ์ 'vision:1 คำถาม...'")
    print("โหมดเสียง: กด F4 เพื่อเริ่มพูด")
    print("โหมด Automation: พูดเช่น 'คลิกปุ่ม File' หรือ 'พิมพ์ hello world'")
    print("🧠 ฟีเจอร์ใหม่: Smart App Search + Context Memory + AI Command Parser")
    print("พิมพ์ exit/quit/q ในแถบผู้ช่วยเพื่อออก\n")
    
    # เริ่มต้น event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()