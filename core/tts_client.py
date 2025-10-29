# core/tts_client.py
# -------------------------
# ระบบ Text-to-Speech (TTS)
# ✅ ใช้ pygame แทน playsound เพื่อหยุดได้จริง
# -------------------------

import pyttsx3
from gtts import gTTS
import tempfile
import os
import re
import threading
import queue

# ✅ ใช้ pygame แทน playsound
try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    print("[TTS WARNING] pygame ไม่พบ กำลังใช้ playsound (หยุดไม่ได้)")
    from playsound import playsound
    PYGAME_AVAILABLE = False


class TTSClient:
    def __init__(self, lang="th"):
        self.lang = lang
        self.voice_available = False
        self.fallback_enabled = False
        
        # ✅ ใช้ queue เพื่อควบคุมการพูด
        self.speech_queue = queue.Queue()
        self.stop_flag = threading.Event()
        self.speaking_thread = None
        self.is_speaking = False  # ✅ เพิ่ม flag ติดตาม
        
        # สร้าง engine
        self._init_engine()
        
        # เริ่ม worker thread
        self._start_worker()

    def _init_engine(self):
        """สร้าง pyttsx3 engine ใหม่"""
        try:
            self.engine = pyttsx3.init()
            
            # ลองหาเสียงภาษาไทย
            voices = self.engine.getProperty("voices")
            for voice in voices:
                if "th" in voice.languages or "Thai" in voice.name:
                    self.engine.setProperty("voice", voice.id)
                    self.voice_available = True
                    break

            if not self.voice_available:
                print("[TTS] ⚠️ ไม่พบเสียงไทย → ใช้ Google TTS")
                self.fallback_enabled = True
            else:
                print("[TTS] ✅ ใช้เสียงไทยของระบบ")

            self.engine.setProperty("rate", 180)
            self.engine.setProperty("volume", 1.0)
        except Exception as e:
            print(f"[TTS ERROR] ไม่สามารถสร้าง engine: {e}")
            self.fallback_enabled = True

    def _start_worker(self):
        """เริ่ม worker thread สำหรับพูด"""
        self.speaking_thread = threading.Thread(
            target=self._speech_worker,
            daemon=True
        )
        self.speaking_thread.start()

    def _speech_worker(self):
        """Worker thread ที่คอยพูดข้อความจาก queue"""
        while True:
            try:
                # รอข้อความจาก queue
                text = self.speech_queue.get(timeout=0.1)
                
                if text is None:  # สัญญาณหยุด worker
                    break
                
                # เช็คว่าถูกยกเลิกหรือไม่
                if self.stop_flag.is_set():
                    self.stop_flag.clear()
                    self.is_speaking = False
                    continue
                
                # ตั้ง flag ว่ากำลังพูด
                self.is_speaking = True
                
                # พูดข้อความ
                self._do_speak(text)
                
                # เสร็จแล้ว
                self.is_speaking = False
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[TTS ERROR] _speech_worker: {e}")
                self.is_speaking = False

    def _do_speak(self, text: str):
        """พูดข้อความจริงๆ"""
        try:
            if self.fallback_enabled:
                self._speak_google_pygame(text)
            else:
                # ใช้ pyttsx3
                self.engine.say(text)
                self.engine.runAndWait()
                
        except Exception as e:
            print(f"[TTS ERROR] _do_speak: {e}")

    def speak(self, text: str):
        """พูดข้อความด้วยเสียงไทย"""
        if not text or text.strip() == "":
            return
        
        # ทำความสะอาดข้อความ
        cleaned_text = self._clean_text(text)
        
        if not cleaned_text.strip():
            return

        # ✅ ล้าง queue เดิมและใส่ข้อความใหม่
        try:
            while not self.speech_queue.empty():
                self.speech_queue.get_nowait()
        except:
            pass
        
        # ใส่ข้อความใหม่
        self.speech_queue.put(cleaned_text)
        
        # รีเซ็ต stop flag
        self.stop_flag.clear()

    def stop_speaking(self) -> bool:
        """
        ✅ หยุดการพูดทันที - ใช้ได้จริง
        """
        try:
            print("[TTS] 🛑 กำลังหยุดการพูด...")
            
            # 1. ตั้ง flag
            self.stop_flag.set()
            self.is_speaking = False
            
            # 2. ล้าง queue
            try:
                while not self.speech_queue.empty():
                    self.speech_queue.get_nowait()
            except:
                pass
            
            # 3. หยุด pyttsx3
            try:
                if hasattr(self, 'engine'):
                    self.engine.stop()
            except:
                pass
            
            # 4. ✅ หยุด pygame (สำคัญที่สุด!)
            if PYGAME_AVAILABLE:
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.stop()
                except:
                    pass
            
            print("[TTS] ✅ หยุดการพูดสำเร็จ")
            return True
            
        except Exception as e:
            print(f"[TTS ERROR] stop_speaking: {e}")
            return False

    def _speak_google_pygame(self, text: str):
        """
        ✅ ใช้ Google TTS + pygame (หยุดได้!)
        """
        tmp_path = None
        try:
            # เช็คว่าถูกหยุดหรือไม่
            if self.stop_flag.is_set():
                return
            
            # สร้างไฟล์เสียง
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tts = gTTS(text=text, lang="th")
                tts.save(tmp_file.name)
                tmp_path = tmp_file.name

            # เช็คอีกครั้งก่อนเล่น
            if self.stop_flag.is_set():
                return
            
            # ✅ ใช้ pygame แทน playsound
            if PYGAME_AVAILABLE:
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()
                
                # รอจนเล่นเสร็จ หรือถูกหยุด
                while pygame.mixer.music.get_busy():
                    if self.stop_flag.is_set():
                        pygame.mixer.music.stop()
                        break
                    pygame.time.Clock().tick(10)  # เช็คทุก 0.1 วินาที
            else:
                # fallback ถ้าไม่มี pygame
                playsound(tmp_path)
            
        except Exception as e:
            print(f"[TTS ERROR] Google TTS: {e}")
        finally:
            # ลบไฟล์ชั่วคราว
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except:
                    pass

    def _clean_text(self, text: str) -> str:
        """ทำความสะอาดข้อความ"""
        # ตัดข้อความในวงเล็บ
        text = re.sub(r'\([^)]*\)', '', text)
        text = re.sub(r'\[[^\]]*\]', '', text)
        text = re.sub(r'\{[^}]*\}', '', text)
        
        # ตัด emoji
        text = re.sub(r'[😊🤖📝✅❌🔍🚀💡🎤⏹️🔴⏳🎯🎨🎭🎪🎬🎮🎲🎰🎳]', '', text)
        text = re.sub(r'[👍👎👏👋🙏💪🤝🤞🤟🤘]', '', text)
        text = re.sub(r'[❤️💔💕💖💗💙💚💛💜🖤]', '', text)
        text = re.sub(r'[⭐🌟✨💫⚡🔥💥💢💯]', '', text)
        text = re.sub(r'[►▼▲●○■□◆◇★☆♪♫]', '', text)
        
        # ตัดช่องว่างเกิน
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def __del__(self):
        """ปิด worker thread เมื่อ object ถูกทำลาย"""
        try:
            self.speech_queue.put(None)  # สัญญาณหยุด worker
            if self.speaking_thread:
                self.speaking_thread.join(timeout=1.0)
        except:
            pass


# ✅ Test Mode
if __name__ == "__main__":
    import time
    
    tts = TTSClient(lang="th")
    
    print("\n=== ทดสอบ TTS + pygame Stop ===\n")
    
    # ทดสอบ: พูดยาวๆ แล้วหยุดระหว่างพูด
    print("1. ทดสอบการหยุดระหว่างพูด")
    tts.speak("สวัสดีครับ ผมเป็นผู้ช่วยอัจฉริยะ ที่สามารถช่วยเหลือคุณได้หลากหลายงาน ไม่ว่าจะเป็นการเปิดโปรแกรม การค้นหาข้อมูล หรือการควบคุมคอมพิวเตอร์ด้วยเสียง ผมพร้อมให้บริการคุณตลอดเวลา")
    
    print("   รอ 2 วินาที แล้วหยุด...")
    time.sleep(2)
    
    success = tts.stop_speaking()
    print(f"   {'✅' if success else '❌'} ผลลัพธ์: {success}")
    print(f"   is_speaking = {tts.is_speaking}")
    
    time.sleep(1)
    
    # ทดสอบพูดใหม่หลังหยุด
    print("\n2. ทดสอบพูดใหม่หลังหยุด")
    tts.speak("ทดสอบพูดใหม่ครับ ระบบทำงานปกติ")
    
    time.sleep(3)
    
    print("\n✅ ทดสอบเสร็จสิ้น")