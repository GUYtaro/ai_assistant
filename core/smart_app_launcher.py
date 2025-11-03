# core/smart_app_launcher.py
# -------------------------
# SmartAppLauncher (upgraded)
# - รองรับไทย/อังกฤษ/สแลง
# - เรียนรู้ path ที่ใช้งานบ่อย (persistent cache)
# - รองรับ dict { "path": "...", "args": "..." }
# - เรียก subprocess ด้วย list (no shell)
# - หา Discord.exe ใน folder app-<version> ล่าสุด
# -------------------------

import os
import json
import subprocess
import winreg
import fnmatch
import re
from pathlib import Path
from typing import Optional, Dict, List


CACHE_DIR = ".ai_cache"
CACHE_FILE = os.path.join(CACHE_DIR, "launcher_paths.json")


class SmartAppLauncher:
    def __init__(self, enable_background_validation: bool = False):
        # โหลด mapping ที่รู้จัก
        self.known_apps = self._load_default_apps()
        self.learned_apps: Dict[str, object] = {}
        self.cache: Dict[str, object] = {}
        self.blacklist_keywords = ['uninstall', 'uninst', 'setup', 'remove', 'repair', 'update', 'patch']
        self.display_name_map = self._build_display_name_map()
        self.enable_background_validation = enable_background_validation

        # ภาษาไทย / สแลง เพิ่มเติม
        self.thai_name_map = {
            "ดิส": "discord",
            "ดิสคอร์ด": "discord",
            "ดิสคอด": "discord",
            "เปิดดิส": "discord",
            "ไลน์": "line",
            "เปิดไลน์": "line",
            "โครม": "chrome",
            "ครอม": "chrome",
            "โค้ด": "code",
            "วีเอสโค้ด": "code",
            "สตีม": "steam",
        }

        # สร้างโฟลเดอร์ cache และโหลด learned paths
        os.makedirs(CACHE_DIR, exist_ok=True)
        self._load_learned_paths()

        # ผสาน learned into cache (priority)
        self.cache.update(self.learned_apps)

        if enable_background_validation:
            print("[SmartLauncher] ✅ พร้อมค้นหาและเปิดโปรแกรม (with background validation)")
        else:
            print("[SmartLauncher] ✅ SmartAppLauncher พร้อมใช้งาน")

    # ----------------------------
    # Mapping & defaults
    # ----------------------------
    def _build_display_name_map(self) -> Dict[str, str]:
        # ขยาย mapping ตามต้องการ (ย่อให้สั้นที่นี่)
        return {
            "my asus": "myasus",
            "chrome": "chrome",
            "google chrome": "chrome",
            "firefox": "firefox",
            "discord": "discord",
            "line": "line",
            "vscode": "code",
            "code": "code",
            "steam": "steam",
            "notepad": "notepad",
            "spotify": "spotify",
            "obs": "obs",
            "vlc": "vlc",
        }

    def _load_default_apps(self) -> Dict[str, object]:
        username = os.getenv("USERNAME", "")
        # ใช้ dict สำหรับ Discord เพื่อแยก path/args หรือ string สำหรับแอปอื่น
        return {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            "notepad": "notepad.exe",
            "code": os.path.join(os.getenv("LOCALAPPDATA", ""), "Programs", "Microsoft VS Code", "Code.exe"),
            # Discord: เราจะพยายามหา Discord.exe ใน folder app-<version>
            # แต่เก็บ default Update.exe เป็น fallback (ไม่แนะนำ)
            "discord": {
                "path": os.path.join(os.getenv("LOCALAPPDATA", ""), "Discord", "Update.exe"),
                "args": "--processStart Discord.exe"
            },
            "line": os.path.join(os.getenv("LOCALAPPDATA", ""), "LINE", "bin", "LineLauncher.exe"),
            "steam": r"C:\Program Files (x86)\Steam\steam.exe",
            "spotify": os.path.join(os.getenv("APPDATA", ""), "Spotify", "Spotify.exe"),
        }

    # ----------------------------
    # Persistent learned paths
    # ----------------------------
    def _load_learned_paths(self):
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    self.learned_apps = json.load(f)
                    # ensure keys lower-case
                    self.learned_apps = {k.lower(): v for k, v in self.learned_apps.items()}
                    print(f"[SmartLauncher] โหลด learned apps จาก cache ({len(self.learned_apps)})")
        except Exception as e:
            print(f"[SmartLauncher] ไม่สามารถโหลด cache ได้: {e}")
            self.learned_apps = {}

    def _save_learned_path(self, app_name: str, path_obj: object):
        try:
            name = app_name.lower()
            self.learned_apps[name] = path_obj
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.learned_apps, f, ensure_ascii=False, indent=2)
            # update runtime cache too
            self.cache[name] = path_obj
            print(f"[SmartLauncher] บันทึก path ของ '{name}' ลง cache")
        except Exception as e:
            print(f"[SmartLauncher] ไม่สามารถเซฟ learned path: {e}")

    # ----------------------------
    # Public API
    # ----------------------------
    def launch(self, app_name: str, args: Optional[str] = None) -> Dict:
        """
        เปิดโปรแกรม (รองรับชื่อไทย/อังกฤษ/สแลง)
        """
        if not app_name:
            return {"ok": False, "message": "ชื่อโปรแกรมว่างเปล่า"}

        original_name = app_name
        key = self._normalize_name(app_name)

        # 1) ถ้ามีใน cache (learned หรือ cached) ให้ใช้เลย
        if key in self.cache:
            path_obj = self.cache[key]
            print(f"[SmartLauncher] 💨 ใช้ cache สำหรับ '{key}': {path_obj}")
            return self._execute(path_obj, args)

        # 2) ถ้ามีใน known_apps ให้ใช้
        if key in self.known_apps:
            path_obj = self.known_apps[key]
            # ถ้าเป็น string ให้ replace username placeholder ถ้ามี
            if isinstance(path_obj, str):
                # บันทึกลง cache และเรียก
                self._save_learned_path(key, path_obj)
                return self._execute(path_obj, args)
            elif isinstance(path_obj, dict):
                # แก้ path ใน dict (replace placeholder)
                path_obj = dict(path_obj)  # copy
                # บันทึก dict ลง cache และเรียก
                self._save_learned_path(key, path_obj)
                return self._execute(path_obj, args)

        # 3) ค้นหาอัตโนมัติ (Start Menu, Desktop, Program Files, Registry)
        print(f"[SmartLauncher] 🔍 ค้นหา '{original_name}' อัตโนมัติ...")
        found = self._smart_search(key)

        if found:
            print(f"[SmartLauncher] ✅ พบ: {found}")
            self._save_learned_path(key, found)
            return self._execute(found, args)

        return {"ok": False, "message": f"ไม่พบโปรแกรม '{original_name}' ในระบบ"}

    # ----------------------------
    # Name normalization (Thai slang + display map)
    # ----------------------------
    def _normalize_name(self, name: str) -> str:
        n = name.lower().strip()
        # ตัดคำที่ไม่จำเป็น (แบบง่าย)
        n = re.sub(r'[^\w\s\-\.]', "", n)  # เอา punctuation ออก
        # direct thai slang
        if n in self.thai_name_map:
            return self.thai_name_map[n]
        # direct display map
        if n in self.display_name_map:
            return self.display_name_map[n]
        # partial match in display_name_map
        for k, v in self.display_name_map.items():
            if k in n or n in k:
                return v
        return n

    # ----------------------------
    # Smart search helpers
    # ----------------------------
    def _smart_search(self, app_name: str) -> Optional[object]:
        # Order: Start Menu (.lnk) -> Desktop (.lnk / .exe) -> Program Files -> Registry -> special Discord search
        handlers = [
            self._search_start_menu,
            self._search_desktop,
            self._search_program_files,
            self._search_registry,
        ]
        # If searching for discord, try special finder to locate app-<version>\Discord.exe
        if app_name == "discord":
            discord_path = self._find_discord_exe_latest()
            if discord_path:
                return str(discord_path)

        for fn in handlers:
            try:
                res = fn(app_name)
                if res:
                    return res
            except Exception as e:
                print(f"[SmartLauncher] ⚠️ {fn.__name__} ล้มเหลว: {e}")
        return None

    def _search_start_menu(self, app_name: str) -> Optional[str]:
        start_menu_paths = [
            Path(os.getenv("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            Path("C:/ProgramData/Microsoft/Windows/Start Menu/Programs")
        ]
        for base in start_menu_paths:
            if not base.exists():
                continue
            for lnk in base.rglob("*.lnk"):
                lname = lnk.stem.lower()
                if app_name in lname and not any(kw in lname for kw in self.blacklist_keywords):
                    target = self._get_shortcut_target(lnk)
                    if target and os.path.exists(target) and self._is_safe_exe(Path(target)):
                        return target
        return None

    def _search_desktop(self, app_name: str) -> Optional[str]:
        desktop = Path(os.path.join(os.path.expanduser("~"), "Desktop"))
        if not desktop.exists():
            return None
        for item in desktop.iterdir():
            if app_name in item.stem.lower():
                if item.suffix.lower() == ".lnk":
                    target = self._get_shortcut_target(item)
                    if target and self._is_safe_exe(Path(target)):
                        return target
                elif item.suffix.lower() == ".exe" and self._is_safe_exe(item):
                    return str(item)
        return None

    def _search_program_files(self, app_name: str) -> Optional[str]:
        program_dirs = [
            Path("C:/Program Files"),
            Path("C:/Program Files (x86)"),
            Path(os.getenv("LOCALAPPDATA") or "") / "Programs"
        ]
        for base in program_dirs:
            if not base.exists():
                continue
            # ค้นหาโฟลเดอร์ที่มีชื่อ app_name (partial)
            for folder in base.iterdir():
                if not folder.is_dir():
                    continue
                if app_name in folder.name.lower():
                    for exe in folder.rglob("*.exe"):
                        if app_name in exe.stem.lower() and self._is_safe_exe(exe):
                            return str(exe)
        return None

    def _search_registry(self, app_name: str) -> Optional[str]:
        try:
            registry_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            for reg_path in registry_paths:
                try:
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                except Exception:
                    continue
                try:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            sub = winreg.EnumKey(key, i)
                            sk = winreg.OpenKey(key, sub)
                            try:
                                display_name = winreg.QueryValueEx(sk, "DisplayName")[0]
                                if app_name in display_name.lower():
                                    # try DisplayIcon
                                    try:
                                        display_icon = winreg.QueryValueEx(sk, "DisplayIcon")[0]
                                        if display_icon and ".exe" in display_icon.lower():
                                            p = display_icon.split(",")[0].strip('"')
                                            if os.path.exists(p) and self._is_safe_exe(Path(p)):
                                                winreg.CloseKey(sk)
                                                winreg.CloseKey(key)
                                                return p
                                    except Exception:
                                        pass
                                    # try InstallLocation
                                    try:
                                        install_loc = winreg.QueryValueEx(sk, "InstallLocation")[0]
                                        if install_loc and os.path.exists(install_loc):
                                            for exe in Path(install_loc).rglob("*.exe"):
                                                if app_name in exe.stem.lower() and self._is_safe_exe(exe):
                                                    winreg.CloseKey(sk)
                                                    winreg.CloseKey(key)
                                                    return str(exe)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            finally:
                                winreg.CloseKey(sk)
                        except Exception:
                            continue
                finally:
                    winreg.CloseKey(key)
        except Exception as e:
            print(f"[SmartLauncher] Registry search error: {e}")
        return None

    # ----------------------------
    # Helpers
    # ----------------------------
    def _get_shortcut_target(self, lnk_path: Path) -> Optional[str]:
        try:
            import win32com.client  # pywin32 needed
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(lnk_path))
            return shortcut.Targetpath
        except Exception:
            return None

    def _is_safe_exe(self, exe_path: Path) -> bool:
        stem = exe_path.stem.lower()
        return not any(kw in stem for kw in self.blacklist_keywords)

    def _find_discord_exe_latest(self) -> Optional[Path]:
        """
        หา Discord.exe ในโฟลเดอร์ C:\\Users\\<user>\\AppData\\Local\\Discord\\app-*
        เลือกเวอร์ชันล่าสุด (ชื่อโฟลเดอร์ที่เป็น semver หรือมีหมายเลขมากสุด)
        """
        base = Path(os.getenv("LOCALAPPDATA") or "") / "Discord"
        if not base.exists():
            return None
        app_dirs = [d for d in base.iterdir() if d.is_dir() and d.name.startswith("app-")]
        if not app_dirs:
            return None
        # เลือก dir ล่าสุดโดยเรียงชื่อ (ส่วนใหญ่ Discord ใช้ app-<version>)
        try:
            app_dirs_sorted = sorted(app_dirs, key=lambda p: p.name, reverse=True)
            for d in app_dirs_sorted:
                candidate = d / "Discord.exe"
                if candidate.exists():
                    return candidate
        except Exception:
            pass
        return None

    # ----------------------------
    # Execution
    # ----------------------------
    def _execute(self, path_obj: object, args: Optional[str] = None) -> Dict:
        """
        path_obj: สามารถเป็น
          - string path เช่น "C:\\...\\app.exe"
          - dict {"path": "...", "args": "..."}
        """
        try:
            embedded_args = None
            if isinstance(path_obj, dict):
                exe_path = path_obj.get("path")
                embedded_args = path_obj.get("args")
            else:
                exe_path = str(path_obj)

            if not exe_path:
                return {"ok": False, "message": "Invalid executable path"}

            # ถ้า exe_path มี wildcard 'app-*\\Discord.exe' handle ให้หาไฟล์จริง
            # (ผู้ใช้อาจตั้งค่าแบบ pattern)
            if "*" in exe_path or "app-" in exe_path and exe_path.endswith("Discord.exe"):
                # ลองหา Discord executable ล่าสุด
                discord_found = self._find_discord_exe_latest()
                if discord_found:
                    exe_path = str(discord_found)

            # build command list
            cmd = [exe_path]

            if embedded_args:
                if isinstance(embedded_args, str):
                    cmd.extend(embedded_args.split())
                elif isinstance(embedded_args, (list, tuple)):
                    cmd.extend(list(embedded_args))

            if args:
                if isinstance(args, str):
                    cmd.extend(args.split())
                elif isinstance(args, (list, tuple)):
                    cmd.extend(list(args))

            # safety: if exe_path not exist, warn but try to run (some are in PATH)
            if not os.path.exists(exe_path):
                print(f"[SmartLauncher] ⚠️ ไม่พบไฟล์: {exe_path} (จะพยายามรันโดยตรง ถ้าเป็นชื่อใน PATH)")

            print(f"[SmartLauncher] 🚀 เปิด (cmd list): {cmd}")
            # ใช้ shell=False และส่ง list เพื่อป้องกันการ parse ผิดพลาด
            subprocess.Popen(cmd)

            # ถ้ารันสำเร็จ ให้บันทึกเรียนรู้ path (ใช้ stem เป็น key)
            try:
                key = Path(exe_path).stem.lower()
                # ถ้าเราบันทึก dict ให้เก็บ dict เพื่อใช้ args ต่อไป
                stored = path_obj if isinstance(path_obj, dict) else exe_path
                self._save_learned_path(key, stored)
            except Exception:
                pass

            return {"ok": True, "message": f"เปิด {Path(exe_path).stem} สำเร็จ"}

        except Exception as e:
            return {"ok": False, "message": f"เปิดโปรแกรมล้มเหลว: {e}"}

    # ----------------------------
    # Extra
    # ----------------------------
    def open_url(self, url: str, browser: str = "chrome") -> Dict:
        # เปิด URL ผ่าน browser mapping
        return self.launch(browser, url)

    def get_supported_display_names(self) -> List[str]:
        keys = list(self.display_name_map.keys()) + list(self.thai_name_map.keys())
        return sorted(set(keys))


# Test runner
if __name__ == "__main__":
    launcher = SmartAppLauncher()
    tests = ["discord", "ดิส", "line", "chrome", "notepad"]
    for t in tests:
        print("----")
        print(f"launch('{t}') ->", launcher.launch(t))