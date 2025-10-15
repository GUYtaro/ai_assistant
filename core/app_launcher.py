# core/app_launcher.py
# -------------------------
# AppLauncher v3 (Integrated with SmartAppLauncher v6)
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
        # ใช้ SmartAppLauncher v6 (Pro)
        self.smart = SmartAppLauncher(enable_background_validation=True)
        print("[AppLauncher] ✅ SmartAppLauncher v6 Loaded")

    def launch(self, app_name: str, args=None):
        """
        เปิดโปรแกรมโดยใช้ SmartAppLauncher ก่อน
        ถ้าไม่เจอ → fallback subprocess shell
        """
        try:
            result = self.smart.launch(app_name, args=args)
            if result.get("ok"):
                return result
            # fallback subprocess เผื่อบางกรณี SmartLauncher หาไม่เจอ
            print("[AppLauncher] ⚠️ SmartLauncher ไม่พบ, ลอง subprocess fallback...")
            cmd = app_name if args is None else f'"{app_name}" {args}'
            subprocess.Popen(cmd, shell=True)
            return {"ok": True, "message": f"เปิด {app_name} (fallback subprocess)"}
        except Exception as e:
            return {"ok": False, "message": f"AppLauncher error: {e}"}
