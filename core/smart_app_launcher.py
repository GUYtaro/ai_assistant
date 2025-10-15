# core/smart_app_launcher.py
# -------------------------
# AI-Powered App Launcher - Enhanced with Display Name Support
# ค้นหาและเปิดโปรแกรมอัตโนมัติโดยใช้ AI + รองรับ Display Name
# -------------------------

import subprocess
import os
import winreg
import re
from typing import Optional, Dict, List
from pathlib import Path


class SmartAppLauncher:
    """
    App Launcher ที่ฉลาด - รองรับทั้ง Display Name และ Executable Name
    - ค้นหาโปรแกรมอัตโนมัติจาก Registry, Start Menu, Desktop
    - แปลง Display Name เป็น Executable Name อัตโนมัติ
    - เรียนรู้และจดจำ path ของโปรแกรมที่เคยเปิด
    - รองรับภาษาไทยและภาษาอังกฤษ
    """

    def __init__(self, enable_background_validation=False):
        self.known_apps = self._load_default_apps()
        self.learned_apps = {}
        self.cache = {}
        self.blacklist_keywords = ['uninstall', 'uninst', 'setup', 'remove', 'repair']
        self.display_name_map = self._build_display_name_map()
        self.enable_background_validation = enable_background_validation
        
        if enable_background_validation:
            print("[SmartLauncher] ✅ พร้อมค้นหาและเปิดโปรแกรม (รองรับ Display Name + Background Validation)")
        else:
            print("[SmartLauncher] ✅ พร้อมค้นหาและเปิดโปรแกรม (รองรับ Display Name)")

    def _build_display_name_map(self) -> Dict[str, str]:
        """✅ สร้าง mapping ระหว่าง display name กับ executable name"""
        return {
            # ASUS
            "my asus": "myasus",
            "myasus": "myasus",
            "armoury crate": "armoury crate",
            "armourycrate": "armoury crate",
            "asus armoury crate": "armoury crate",
            "asus framework": "asus",
            "aura sync": "lightingservice",
            
            # Microsoft Office
            "microsoft word": "winword",
            "word": "winword",
            "microsoft excel": "excel",
            "excel": "excel",
            "microsoft powerpoint": "powerpnt",
            "powerpoint": "powerpnt",
            "microsoft outlook": "outlook",
            "outlook": "outlook",
            "microsoft teams": "teams",
            "teams": "teams",
            "onenote": "onenote",
            
            # Browsers
            "google chrome": "chrome",
            "chrome": "chrome",
            "microsoft edge": "edge",
            "edge": "edge",
            "mozilla firefox": "firefox",
            "firefox": "firefox",
            "brave": "brave",
            "opera": "opera",
            "opera gx": "opera",
            
            # Development Tools
            "visual studio code": "code",
            "vscode": "code",
            "vs code": "code",
            "code": "code",
            "visual studio": "devenv",
            "pycharm": "pycharm",
            "intellij": "idea",
            "android studio": "studio",
            "git bash": "git-bash",
            "github desktop": "githubdesktop",
            "docker desktop": "docker desktop",
            
            # Communication
            "discord": "discord",
            "slack": "slack",
            "zoom": "zoom",
            "microsoft teams": "teams",
            "skype": "skype",
            "line": "line",
            "telegram": "telegram",
            "whatsapp": "whatsapp",
            
            # Media & Entertainment
            "spotify": "spotify",
            "vlc": "vlc",
            "vlc media player": "vlc",
            "obs": "obs",
            "obs studio": "obs",
            "adobe photoshop": "photoshop",
            "photoshop": "photoshop",
            "adobe premiere": "premiere",
            "premiere": "premiere",
            
            # Gaming
            "steam": "steam",
            "epic games": "epicgameslauncher",
            "epic games launcher": "epicgameslauncher",
            "origin": "origin",
            "battle.net": "battle.net",
            "battlenet": "battle.net",
            "roblox": "roblox",
            "minecraft": "minecraft",
            "war thunder": "warthunder",
            "warthunder": "warthunder",
            
            # Utilities
            "notepad": "notepad",
            "notepad++": "notepad++",
            "calculator": "calculator",
            "paint": "paint",
            "file explorer": "explorer",
            "explorer": "explorer",
            "task manager": "taskmgr",
            "command prompt": "cmd",
            "cmd": "cmd",
            "powershell": "powershell",
            "7-zip": "7zfm",
            "winrar": "winrar",
            
            # System Tools
            "vmware": "vmware",
            "vmware workstation": "vmware",
            "virtualbox": "virtualbox",
            "wireshark": "wireshark",
            "putty": "putty",
            "winscp": "winscp",
            "filezilla": "filezilla",
        }

    def _load_default_apps(self) -> Dict[str, str]:
        """โหลดโปรแกรมที่รู้จักล่วงหน้า"""
        username = os.getenv("USERNAME", "")
        
        return {
            # Browsers
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "brave": rf"C:\Users\{username}\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe",
            
            # Microsoft Office
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
            "taskmgr": "taskmgr.exe",
            "winword": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            "powerpnt": r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
            "outlook": r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",
            "teams": rf"C:\Users\{username}\AppData\Local\Microsoft\Teams\current\Teams.exe",
            
            # Communication
            "discord": rf"C:\Users\{username}\AppData\Local\Discord\Update.exe --processStart Discord.exe",
            "line": rf"C:\Users\{username}\AppData\Local\LINE\bin\LineLauncher.exe",
            "zoom": rf"C:\Users\{username}\AppData\Roaming\Zoom\bin\Zoom.exe",
            
            # Development
            "code": rf"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "vscode": rf"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            
            # Media
            "spotify": rf"C:\Users\{username}\AppData\Roaming\Spotify\Spotify.exe",
            "obs": r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
            "vlc": r"C:\Program Files\VideoLAN\VLC\vlc.exe",
            
            # Gaming
            "steam": r"C:\Program Files (x86)\Steam\steam.exe",
            "epicgameslauncher": r"C:\Program Files (x86)\Epic Games\Launcher\Portal\Binaries\Win64\EpicGamesLauncher.exe",
            
            # ASUS
            "myasus": r"C:\Program Files\ASUS\MyASUS\MyASUS.exe",
            "armoury crate": r"C:\Program Files\ASUS\ArmouryCrate\ArmouryCrate.exe",
            "asus": r"C:\Program Files\ASUS\ASUS Framework\AsusFramework.exe",
        }

    def launch(self, app_name: str, args: Optional[str] = None) -> Dict:
        """
        เปิดโปรแกรมด้วย AI - รองรับทั้ง Display Name และ Executable Name
        """
        app_name_lower = app_name.lower().strip()
        original_name = app_name
        
        # ✅ 1. แปลง Display Name เป็น Executable Name
        executable_name = self._resolve_display_name(app_name_lower)
        if executable_name != app_name_lower:
            print(f"[SmartLauncher] 🔄 แปลง '{app_name}' → '{executable_name}'")
            app_name_lower = executable_name
        
        # 2. เช็ค cache
        if app_name_lower in self.cache:
            print(f"[SmartLauncher] 💨 ใช้ cache: {self.cache[app_name_lower]}")
            return self._execute(self.cache[app_name_lower], args)
        
        # 3. เช็ค known_apps
        if app_name_lower in self.known_apps:
            path = self.known_apps[app_name_lower]
            path = path.replace("{username}", os.getenv("USERNAME", ""))
            
            if os.path.exists(path.split()[0]):
                self.cache[app_name_lower] = path
                return self._execute(path, args)
        
        # 4. ค้นหาด้วย AI
        print(f"[SmartLauncher] 🔍 ค้นหา '{original_name}' อัตโนมัติ...")
        found_path = self._smart_search(app_name_lower)
        
        if found_path:
            print(f"[SmartLauncher] ✅ พบ: {found_path}")
            self.cache[app_name_lower] = found_path
            return self._execute(found_path, args)
        else:
            print(f"[SmartLauncher] ❌ ไม่พบโปรแกรม '{original_name}'")
            return {
                "ok": False,
                "message": f"ไม่พบโปรแกรม '{original_name}' ในระบบ"
            }

    def _resolve_display_name(self, app_name: str) -> str:
        """✅ แปลง Display Name เป็น Executable Name"""
        app_name = app_name.lower().strip()
        
        # เช็คใน display name map (exact match)
        if app_name in self.display_name_map:
            return self.display_name_map[app_name]
        
        # เช็คว่ามีคำใน display name map หรือไม่ (partial match)
        for display_name, executable_name in self.display_name_map.items():
            if display_name in app_name or app_name in display_name:
                return executable_name
        
        # ถ้าไม่เจอใน map ให้ลองหาใน registry
        registry_name = self._find_executable_in_registry(app_name)
        if registry_name:
            # บันทึกลง map เพื่อใช้ครั้งต่อไป
            self.display_name_map[app_name] = registry_name
            return registry_name
        
        return app_name

    def _find_executable_in_registry(self, display_name: str) -> Optional[str]:
        """✅ ค้นหา executable name จาก registry โดยใช้ display name"""
        try:
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
                                reg_display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                if display_name.lower() in reg_display_name.lower():
                                    # พยายามหา executable name จาก DisplayIcon
                                    try:
                                        display_icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                                        if display_icon and ".exe" in display_icon.lower():
                                            exe_name = Path(display_icon.split(',')[0].strip('"')).stem.lower()
                                            print(f"[Registry] 📝 พบ '{reg_display_name}' → '{exe_name}'")
                                            winreg.CloseKey(subkey)
                                            winreg.CloseKey(key)
                                            return exe_name
                                    except:
                                        pass
                                    
                                    # หรือใช้คำแรกของ display name
                                    first_word = reg_display_name.split()[0].lower()
                                    if first_word not in ['microsoft', 'adobe', 'google']:
                                        winreg.CloseKey(subkey)
                                        winreg.CloseKey(key)
                                        return first_word
                                    
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

    def _smart_search(self, app_name: str) -> Optional[str]:
        """ค้นหาโปรแกรมอัตโนมัติ"""
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
        """ตรวจสอบว่า exe ปลอดภัยหรือไม่"""
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
                    if any(kw in lnk_file.stem.lower() for kw in self.blacklist_keywords):
                        continue
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
            
            # ค้นหาแค่ระดับแรก
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
        """ค้นหาใน Windows Registry - Enhanced"""
        try:
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
                                
                                # ตรวจสอบทั้ง executable name และ display name
                                if (app_name.lower() in display_name.lower() or 
                                    app_name.lower() in subkey_name.lower()):
                                    
                                    paths_to_try = []
                                    
                                    # 1. DisplayIcon
                                    try:
                                        display_icon = winreg.QueryValueEx(subkey, "DisplayIcon")[0]
                                        if display_icon and ".exe" in display_icon.lower():
                                            icon_path = display_icon.split(',')[0].strip('"')
                                            if os.path.exists(icon_path):
                                                paths_to_try.append(icon_path)
                                    except:
                                        pass
                                    
                                    # 2. InstallLocation + EXE
                                    try:
                                        install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                        if install_location and os.path.exists(install_location):
                                            install_path = Path(install_location)
                                            for exe in install_path.rglob("*.exe"):
                                                if self._is_safe_exe(exe) and app_name.lower() in exe.stem.lower():
                                                    paths_to_try.append(str(exe))
                                                    break  # เอาตัวแรกที่เจอ
                                    except:
                                        pass
                                    
                                    # ลองใช้ path ที่หาได้
                                    for path in paths_to_try:
                                        if os.path.exists(path) and self._is_safe_exe(Path(path)):
                                            print(f"[Registry] ✅ พบ: {path}")
                                            winreg.CloseKey(subkey)
                                            winreg.CloseKey(key)
                                            return path
                                    
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

    def get_supported_display_names(self) -> List[str]:
        """✅ รับรายการ Display Name ที่รองรับ"""
        return sorted(list(self.display_name_map.keys()))


# ✅ Test Mode
if __name__ == "__main__":
    launcher = SmartAppLauncher()
    
    print("\n=== รายการ Display Name ที่รองรับ ===")
    names = launcher.get_supported_display_names()
    print(f"รองรับทั้งหมด {len(names)} ชื่อ")
    for name in names[:10]:
        print(f"  - {name}")
    print("  ...")
    
    print("\n=== ทดสอบเปิด Armoury Crate ===")
    result = launcher.launch("armoury crate")
    print(result)
    
    print("\n=== ทดสอบเปิด My ASUS ===")
    result = launcher.launch("my asus")
    print(result)
    
    print("\n=== ทดสอบเปิด Microsoft Word ===")
    result = launcher.launch("microsoft word")
    print(result)