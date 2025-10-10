# core/app_launcher.py
# -------------------------
# เปิดโปรแกรม/แอปพลิเคชันบน Windows
# รองรับ: Notepad, Chrome, Calculator, และอื่นๆ
# -------------------------

import subprocess
import os
from typing import Optional, Dict


class AppLauncher:
    """
    คลาสสำหรับเปิดโปรแกรมบน Windows
    """

    # รายการโปรแกรมที่รู้จัก
    KNOWN_APPS = {
        # Browsers
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        
        # Microsoft Apps
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "paint": "mspaint.exe",
        "wordpad": "write.exe",
        "explorer": "explorer.exe",
        
        # System
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "taskmgr": "taskmgr.exe",
        
        # Office (ถ้าติดตั้งไว้)
        "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        "powerpoint": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    }

    def __init__(self):
        print("[AppLauncher] ✅ พร้อมเปิดโปรแกรม")

    def launch(self, app_name: str, args: Optional[str] = None) -> Dict:
        """
        เปิดโปรแกรม
        
        Parameters:
            app_name: ชื่อโปรแกรม เช่น "chrome", "notepad"
            args: argument เพิ่มเติม เช่น "https://youtube.com"
        
        Returns:
            {"ok": bool, "message": str, "process": subprocess.Popen}
        """
        app_name_lower = app_name.lower()
        
        # ค้นหาโปรแกรม
        if app_name_lower in self.KNOWN_APPS:
            path = self.KNOWN_APPS[app_name_lower]
        else:
            # ลองหาจาก PATH
            path = app_name
        
        try:
            # สร้างคำสั่ง
            if args:
                cmd = [path, args]
            else:
                cmd = [path]
            
            print(f"[AppLauncher] 🚀 กำลังเปิด: {' '.join(cmd)}")
            
            # เปิดโปรแกรม
            process = subprocess.Popen(cmd, shell=True)
            
            return {
                "ok": True,
                "message": f"เปิด {app_name} สำเร็จ",
                "process": process
            }
            
        except FileNotFoundError:
            return {
                "ok": False,
                "message": f"ไม่พบโปรแกรม '{app_name}' (path: {path})"
            }
        except Exception as e:
            return {
                "ok": False,
                "message": f"เปิดโปรแกรมล้มเหลว: {e}"
            }

    def open_url(self, url: str, browser="chrome") -> Dict:
        """
        เปิด URL ในเบราว์เซอร์
        
        Parameters:
            url: URL ที่ต้องการเปิด
            browser: เบราว์เซอร์ที่ต้องการใช้
        """
        return self.launch(browser, url)

    def add_app(self, name: str, path: str):
        """
        เพิ่มโปรแกรมใหม่เข้า KNOWN_APPS
        
        Parameters:
            name: ชื่อโปรแกรม
            path: path ไปยัง .exe
        """
        self.KNOWN_APPS[name.lower()] = path
        print(f"[AppLauncher] ✅ เพิ่มโปรแกรม '{name}' -> {path}")


# ✅ Test Mode
if __name__ == "__main__":
    launcher = AppLauncher()
    
    print("\n=== ทดสอบเปิด Notepad ===")
    result = launcher.launch("notepad")
    print(result)
    
    print("\n=== ทดสอบเปิด Chrome + YouTube ===")
    result = launcher.open_url("https://youtube.com", "chrome")
    print(result)