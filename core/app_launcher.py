# core/app_launcher.py
# -------------------------
# AppLauncher v3 (Integrated with SmartAppLauncher)
# -------------------------
# หน้าที่:
# - ใช้ SmartAppLauncher เป็นระบบหลัก
# - หากไม่พบโปรแกรม จะ fallback ไปใช้ method เดิม (subprocess)
# -------------------------

import os
import subprocess
from core.smart_app_launcher import SmartAppLauncher

class AppLauncher:
    def __init__(self):
        # ✅ แก้ไข: ไม่ส่ง parameter enable_background_validation
        self.smart = SmartAppLauncher()
        print("[AppLauncher] ✅ SmartAppLauncher Loaded")

    def launch(self, app_name: str, args=None):
        """
        เปิดโปรแกรมโดยใช้ SmartAppLauncher ก่อน
        ถ้าไม่เจอ → ไม่ fallback (เพราะจะ error)
        """
        try:
            result = self.smart.launch(app_name, args=args)
            if result.get("ok"):
                return result
            
            # ✅ ไม่ fallback subprocess อีกต่อไป (เพราะจะทำให้เกิด error)
            print(f"[AppLauncher] ❌ ไม่พบโปรแกรม '{app_name}'")
            return {"ok": False, "message": f"ไม่พบโปรแกรม '{app_name}' ในระบบ"}
            
        except Exception as e:
            return {"ok": False, "message": f"AppLauncher error: {e}"}
    
    def open_url(self, url: str, browser="chrome"):
        """เปิด URL ในเบราว์เซอร์"""
        return self.smart.open_url(url, browser)
    
    def open_url(self, url: str, browser="chrome"):
        """เปิด URL ในเบราว์เซอร์"""
        return self.smart.open_url(url, browser)