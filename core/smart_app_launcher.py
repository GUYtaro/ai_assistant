# core/smart_app_launcher.py
# -------------------------
# AI-Powered App Launcher
# ค้นหาและเปิดโปรแกรมอัตโนมัติโดยใช้ AI
# -------------------------

import subprocess
import os
import winreg
from typing import Optional, Dict, List
from pathlib import Path


class SmartAppLauncher:
    """
    App Launcher ที่ฉลาด
    - ค้นหาโปรแกรมอัตโนมัติจาก Registry, Start Menu, Desktop
    - เรียนรู้และจดจำ path ของโปรแกรมที่เคยเปิด
    - รองรับภาษาไทยและภาษาอังกฤษ
    - เพิ่มระบบ safety เพื่อหลีกเลี่ยงการเปิดไฟล์ uninstaller หรือไฟล์อันตรายอื่นๆ
    """

    def __init__(self):
        self.known_apps = self._load_default_apps()
        self.learned_apps = {}  # เก็บโปรแกรมที่เรียนรู้มา
        self.cache = {}  # cache path ที่พบแล้ว
        self.blacklist_keywords = ['uninstall', 'uninst', 'setup', 'remove', 'repair']  # คำต้องห้ามในชื่อไฟล์
        print("[SmartLauncher] ✅ พร้อมค้นหาและเปิดโปรแกรม")

    def _load_default_apps(self) -> Dict[str, str]:
        """โหลดโปรแกรมที่รู้จักล่วงหน้า"""
        return {
            # Browsers
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            
            # Microsoft
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            
            # Common Apps
            "discord": r"C:\Users\{username}\AppData\Local\Discord\Update.exe --processStart Discord.exe",
            "spotify": r"C:\Users\{username}\AppData\Roaming\Spotify\Spotify.exe",
            "steam": r"C:\Program Files (x86)\Steam\steam.exe",
            "vscode": r"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        }

    def launch(self, app_name: str, args: Optional[str] = None) -> Dict:
        """
        เปิดโปรแกรมด้วย AI
        1. เช็ค cache ก่อน
        2. ค้นหาใน known_apps
        3. ค้นหาด้วย AI (Registry, Start Menu, Desktop)
        4. บันทึก path ที่พบลง cache
        """
        app_name_lower = app_name.lower()
        
        # 1. เช็ค cache
        if app_name_lower in self.cache:
            print(f"[SmartLauncher] 💨 ใช้ cache: {self.cache[app_name_lower]}")
            return self._execute(self.cache[app_name_lower], args)
        
        # 2. เช็ค known_apps
        if app_name_lower in self.known_apps:
            path = self.known_apps[app_name_lower]
            # แทนที่ {username}
            path = path.replace("{username}", os.getenv("USERNAME", ""))
            
            if os.path.exists(path.split()[0]):  # เช็คว่า path มีจริง
                self.cache[app_name_lower] = path
                return self._execute(path, args)
        
        # 3. ค้นหาด้วย AI
        print(f"[SmartLauncher] 🔍 ค้นหา '{app_name}' อัตโนมัติ...")
        found_path = self._smart_search(app_name)
        
        if found_path:
            print(f"[SmartLauncher] ✅ พบ: {found_path}")
            self.cache[app_name_lower] = found_path
            return self._execute(found_path, args)
        else:
            print(f"[SmartLauncher] ❌ ไม่พบโปรแกรม '{app_name}'")
            return {
                "ok": False,
                "message": f"ไม่พบโปรแกรม '{app_name}' ในระบบ"
            }

    def _smart_search(self, app_name: str) -> Optional[str]:
        """
        ค้นหาโปรแกรมอัตโนมัติ
        1. ค้นหาใน Start Menu
        2. ค้นหาใน Desktop
        3. ค้นหาใน Program Files
        4. ค้นหาใน Registry
        """
        search_methods = [
            self._search_start_menu,
            self._search_desktop,
            self._search_program_files,
            self._search_registry
        ]
        
        for method in search_methods:
            try:
                result = method(app_name)
                if result:
                    return result
            except Exception as e:
                print(f"[SmartLauncher] ⚠️ {method.__name__} ล้มเหลว: {e}")
        
        return None

    def _is_safe_exe(self, exe_path: Path) -> bool:
        """ตรวจสอบว่า exe ปลอดภัยหรือไม่ (ไม่มีคำต้องห้ามในชื่อ)"""
        stem_lower = exe_path.stem.lower()
        return not any(kw in stem_lower for kw in self.blacklist_keywords)

    def _search_start_menu(self, app_name: str) -> Optional[str]:
        """ค้นหาใน Start Menu"""
        start_menu_paths = [
            Path(os.getenv("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs")
        ]
        
        for base_path in start_menu_paths:
            if not base_path.exists():
                continue
            
            # ค้นหา .lnk files
            for lnk_file in base_path.rglob("*.lnk"):
                if app_name.lower() in lnk_file.stem.lower():
                    # เช็คว่าชื่อ shortcut ไม่มีคำต้องห้าม
                    if any(kw in lnk_file.stem.lower() for kw in self.blacklist_keywords):
                        continue
                    # อ่าน shortcut target
                    target = self._get_shortcut_target(lnk_file)
                    if target and os.path.exists(target) and self._is_safe_exe(Path(target)):
                        return target
        
        return None

    def _search_desktop(self, app_name: str) -> Optional[str]:
        """ค้นหาบน Desktop"""
        desktop = Path(os.path.join(os.path.expanduser("~"), "Desktop"))
        
        if not desktop.exists():
            return None
        
        for item in desktop.iterdir():
            if app_name.lower() in item.stem.lower():
                if item.suffix == ".lnk":
                    # เช็คว่าชื่อ shortcut ไม่มีคำต้องห้าม
                    if any(kw in item.stem.lower() for kw in self.blacklist_keywords):
                        continue
                    target = self._get_shortcut_target(item)
                    if target and self._is_safe_exe(Path(target)):
                        return target
                elif item.suffix == ".exe" and self._is_safe_exe(item):
                    return str(item)
        
        return None

    def _search_program_files(self, app_name: str) -> Optional[str]:
        """ค้นหาใน Program Files"""
        program_dirs = [
            Path("C:/Program Files"),
            Path("C:/Program Files (x86)"),
            Path(os.getenv("LOCALAPPDATA")) / "Programs"
        ]
        
        for base_dir in program_dirs:
            if not base_dir.exists():
                continue
            
            # ค้นหาแค่ระดับแรก (ไม่ลงลึก เพื่อความเร็ว)
            for app_dir in base_dir.iterdir():
                if not app_dir.is_dir():
                    continue
                
                if app_name.lower() in app_dir.name.lower():
                    # หา .exe ในโฟลเดอร์นี้
                    for exe_file in app_dir.rglob("*.exe"):
                        if app_name.lower() in exe_file.stem.lower() and self._is_safe_exe(exe_file):
                            return str(exe_file)
        
        return None

    def _search_registry(self, app_name: str) -> Optional[str]:
        """ค้นหาใน Windows Registry"""
        try:
            # ค้นหาใน Uninstall registry
            registry_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            
            for reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            subkey = winreg.OpenKey(key, subkey_name)
                            
                            try:
                                display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if app_name.lower() in display_name.lower():
                                    install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                    
                                    # หา .exe ในโฟลเดอร์ install
                                    install_path = Path(install_location)
                                    for exe in install_path.rglob("*.exe"):
                                        if app_name.lower() in exe.stem.lower() and self._is_safe_exe(exe):
                                            return str(exe)
                            except:
                                pass
                            
                            winreg.CloseKey(subkey)
                        except:
                            continue
                    
                    winreg.CloseKey(key)
                except:
                    continue
        except Exception as e:
            print(f"[Registry Search] Error: {e}")
        
        return None

    def _get_shortcut_target(self, lnk_path: Path) -> Optional[str]:
        """อ่าน target path จาก .lnk file"""
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(lnk_path))
            return shortcut.Targetpath
        except:
            return None

    def _execute(self, path: str, args: Optional[str] = None) -> Dict:
        """เปิดโปรแกรม"""
        try:
            if args:
                cmd = f'"{path}" {args}'
            else:
                cmd = f'"{path}"'
            
            print(f"[SmartLauncher] 🚀 เปิด: {cmd}")
            subprocess.Popen(cmd, shell=True)
            
            return {
                "ok": True,
                "message": f"เปิด {Path(path).stem} สำเร็จ"
            }
        except Exception as e:
            return {
                "ok": False,
                "message": f"เปิดโปรแกรมล้มเหลว: {e}"
            }

    def open_url(self, url: str, browser="chrome") -> Dict:
        """เปิด URL ในเบราว์เซอร์"""
        return self.launch(browser, url)


# ✅ Test Mode
if __name__ == "__main__":
    launcher = SmartAppLauncher()
    
    print("\n=== ทดสอบค้นหา Discord ===")
    result = launcher.launch("discord")
    print(result)
    
    print("\n=== ทดสอบค้นหา LINE ===")
    result = launcher.launch("line")
    print(result)