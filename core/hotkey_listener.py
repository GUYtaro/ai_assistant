# core/hotkey_listener.py
# -------------------------
# ระบบฟัง Hotkey (เช่น F4) เพื่อเปิดโหมดเสียง
# โหมด: Press-to-Talk (กดทีเดียว = เริ่มฟัง ไม่ต้องกดปิด)
# -------------------------

from pynput import keyboard
import threading
import time


class HotkeyListener:
    """
    ฟัง Hotkey แบบ Global (ทำงานแม้โปรแกรมไม่ได้ Focus)
    โหมด Press-to-Talk: กด F4 ครั้งเดียว → เริ่มฟัง (ไม่ต้องกดปิด)
    """

    def __init__(self, callback_start, callback_stop=None, hotkey="f4", cooldown=2.0):
        """
        Parameters
        ----------
        callback_start : function
            ฟังก์ชันที่จะเรียกเมื่อกด hotkey
        callback_stop : function, optional
            (ไม่ใช้ในโหมดนี้ แต่เก็บไว้เพื่อ compatibility)
        hotkey : str
            ปุ่มที่ต้องการฟัง เช่น "f4", "f5"
        cooldown : float
            ระยะเวลา cooldown (วินาที) เพื่อป้องกันกดซ้ำเร็วเกินไป
        """
        self.callback_start = callback_start
        self.callback_stop = callback_stop
        self.hotkey = hotkey.lower()
        self.cooldown = cooldown
        self.last_trigger_time = 0
        self.listener = None

    def _on_press(self, key):
        """
        เมื่อมีการกดปุ่ม → ตรวจสอบว่าเป็น hotkey หรือไม่
        """
        try:
            # แปลง key เป็น string
            key_name = None
            if hasattr(key, 'name'):
                key_name = key.name.lower()
            elif hasattr(key, 'char') and key.char:
                key_name = key.char.lower()

            # ตรวจสอบว่าตรงกับ hotkey หรือไม่
            if key_name and key_name == self.hotkey:
                self._trigger_voice_mode()

        except AttributeError:
            pass

    def _trigger_voice_mode(self):
        """
        เรียก callback_start (พร้อม cooldown เพื่อป้องกันกดซ้ำ)
        """
        current_time = time.time()
        
        # ตรวจสอบ cooldown
        if current_time - self.last_trigger_time < self.cooldown:
            print(f"[Hotkey] ⏳ กรุณารอ {self.cooldown:.1f} วินาทีก่อนกดใหม่")
            return
        
        self.last_trigger_time = current_time
        
        if self.callback_start:
            # รัน callback ใน thread แยก เพื่อไม่ให้บล็อก listener
            threading.Thread(target=self.callback_start, daemon=True).start()

    def start(self):
        """
        เริ่มฟัง hotkey (รันใน background thread)
        """
        print(f"[Hotkey] 🎹 เริ่มฟังปุ่ม '{self.hotkey.upper()}' (Press-to-Talk Mode)")
        print(f"[Hotkey] 💡 กด {self.hotkey.upper()} เพื่อเริ่มพูดทุกครั้ง")
        self.listener = keyboard.Listener(on_press=self._on_press)
        self.listener.start()

    def stop(self):
        """
        หยุดฟัง hotkey
        """
        if self.listener:
            self.listener.stop()
            print("[Hotkey] 🛑 หยุดฟังปุ่มแล้ว")


# ✅ Test Mode
if __name__ == "__main__":
    import time

    def test_start():
        print("✅ [TEST] กด F4 แล้ว → เริ่มโหมดเสียง")
        time.sleep(2)  # จำลองการทำงาน 2 วินาที
        print("✅ [TEST] เสร็จแล้ว สามารถกด F4 ใหม่ได้")

    listener = HotkeyListener(
        callback_start=test_start,
        hotkey="f4",
        cooldown=1.0  # cooldown 1 วินาที
    )
    listener.start()

    print("กด F4 เพื่อทดสอบ (กด Ctrl+C เพื่อออก)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        listener.stop()
        print("\n[Test] จบการทดสอบ")