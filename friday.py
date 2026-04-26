import argparse
import datetime as dt
import json
import os
import re
import subprocess
import time
import urllib.parse
import webbrowser
from pathlib import Path

import psutil

from audio_utils import load_config, record_wav, recognize_wav

try:
    from friday_api_client import current_user, save_history, save_safety_event, load_session
except Exception:
    current_user = save_history = save_safety_event = load_session = None

BASE_DIR = Path(__file__).resolve().parent
NOTES_DIR = BASE_DIR / "notes"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
CONTACTS_FILE = BASE_DIR / "whatsapp_contacts.json"
NOTES_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR.mkdir(exist_ok=True)

try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    import pygetwindow as gw
except Exception:
    gw = None


def say(message: str):
    print(f"FRIDAY: {message}")
    if pyttsx3 is None:
        return
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 178)
        engine.say(message)
        engine.runAndWait()
    except Exception:
        pass


def require_account_login() -> bool:
    """Require user login before FridayV8 starts saving database history."""
    if current_user is None or load_session is None:
        print("FRIDAY: Account module not available.")
        return True

    if not load_session():
        print("\nFRIDAY V8 ACCOUNT REQUIRED")
        print("Please run LOGIN_SETUP.bat first and login/register your email.")
        print("Your commands will be saved under your own email after login.")
        return False

    try:
        user = current_user()
        print(f"FRIDAY: Logged in as {user.get('email')} ({user.get('role')})")
        return True
    except Exception as e:
        print("FRIDAY: Login check failed:", e)
        print("Please run LOGIN_SETUP.bat again.")
        return False


def save_command_to_database(command_text: str, result_text: str = "", status: str = "completed"):
    if save_history is None:
        return
    try:
        save_history(command_text=command_text, result_text=result_text, status=status)
    except Exception as e:
        print("FRIDAY: Could not save command history:", e)


def save_safety_to_database(command_text: str, risk_type: str = "unsafe_command", severity: str = "high"):
    if save_safety_event is None:
        return
    try:
        save_safety_event(
            risk_type=risk_type,
            severity=severity,
            action_taken="blocked",
            command_preview=command_text[:150],
        )
    except Exception as e:
        print("FRIDAY: Could not save safety event:", e)



def clean_command(text: str) -> str:
    text = text.lower().strip()
    # common speech-recognition spelling mistakes
    replacements = {
        "crome": "chrome",
        "croam": "chrome",
        "google crome": "google chrome",
        "what's app": "whatsapp",
        "whats app": "whatsapp",
        "wats app": "whatsapp",
        "watsapp": "whatsapp",
        "whatapp": "whatsapp",
        "what sup": "whatsapp",
        "visual studio coat": "visual studio code",
        "vs coat": "vs code",
    }
    for wrong, right in replacements.items():
        text = text.replace(wrong, right)
    text = re.sub(r"[^a-z0-9 .:/\\_+@-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    filler_phrases = [
        "hello friday", "hey friday", "ok friday", "okay friday", "friday",
        "hello jarvis", "hey jarvis", "ok jarvis", "okay jarvis", "jarvis",
        "please", "can you", "could you", "would you", "try to", "try", "bro",
        "for me", "now", "just", "please can you",
    ]
    for phrase in filler_phrases:
        text = re.sub(rf"\b{re.escape(phrase)}\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def run_cmd(cmd: str):
    subprocess.Popen(cmd, shell=True)


def start_target(target: str):
    run_cmd(f'start "" {target}')


def open_url(url: str, prefer: str = "default"):
    if prefer == "chrome":
        try:
            subprocess.Popen(f'start "" chrome "{url}"', shell=True)
            return True
        except Exception:
            pass
    if prefer == "edge":
        try:
            subprocess.Popen(f'start "" msedge "{url}"', shell=True)
            return True
        except Exception:
            pass
    webbrowser.open(url)
    return True


def google_search(query: str, prefer: str = "default"):
    query = query.strip()
    if not query:
        say("What should I search?")
        return True
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    say(f"Searching Google for {query}")
    open_url(url, prefer=prefer)
    return True


def youtube_search(query: str):
    query = query.strip()
    if not query:
        say("What should I search on YouTube?")
        return True
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)
    say(f"Searching YouTube for {query}")
    open_url(url)
    return True


def open_folder(name: str):
    home = Path.home()
    folders = {
        "desktop": home / "Desktop",
        "downloads": home / "Downloads",
        "download": home / "Downloads",
        "documents": home / "Documents",
        "document": home / "Documents",
        "pictures": home / "Pictures",
        "picture": home / "Pictures",
        "videos": home / "Videos",
        "video": home / "Videos",
        "music": home / "Music",
        "screenshots": home / "Pictures" / "Screenshots",
        "screenshot": home / "Pictures" / "Screenshots",
        "project": BASE_DIR,
        "friday": BASE_DIR,
    }
    key = name.replace(" folder", "").strip()
    path = folders.get(key)
    if path is None:
        return False
    try:
        os.startfile(str(path))
        say(f"Opening {key} folder.")
    except Exception:
        start_target(f'explorer "{path}"')
        say(f"Opening {key} folder.")
    return True


SETTINGS = {
    "settings": "ms-settings:",
    "windows settings": "ms-settings:",
    "wifi": "ms-settings:network-wifi",
    "wi fi": "ms-settings:network-wifi",
    "bluetooth": "ms-settings:bluetooth",
    "sound": "ms-settings:sound",
    "audio": "ms-settings:sound",
    "display": "ms-settings:display",
    "screen": "ms-settings:display",
    "battery": "ms-settings:batterysaver",
    "power": "ms-settings:powersleep",
    "storage": "ms-settings:storagesense",
    "apps": "ms-settings:appsfeatures",
    "app": "ms-settings:appsfeatures",
    "privacy": "ms-settings:privacy",
    "microphone": "ms-settings:privacy-microphone",
    "mic": "ms-settings:privacy-microphone",
    "camera": "ms-settings:privacy-webcam",
    "windows update": "ms-settings:windowsupdate",
    "update": "ms-settings:windowsupdate",
    "network": "ms-settings:network",
    "personalization": "ms-settings:personalization",
    "theme": "ms-settings:themes",
    "themes": "ms-settings:themes",
    "keyboard": "ms-settings:easeofaccess-keyboard",
    "mouse": "ms-settings:mousetouchpad",
    "touchpad": "ms-settings:mousetouchpad",
    "date": "ms-settings:dateandtime",
    "time": "ms-settings:dateandtime",
    "language": "ms-settings:regionlanguage",
    "gaming": "ms-settings:gaming-gamebar",
    "security": "ms-settings:windowsdefender",
    "defender": "ms-settings:windowsdefender",
    "about": "ms-settings:about",
}


def open_setting(name: str):
    name = name.replace(" settings", "").replace(" setting", "").strip()
    uri = SETTINGS.get(name)
    if not uri:
        for key, value in SETTINGS.items():
            if key in name or name in key:
                uri = value
                break
    if not uri:
        say(f"I don't know that settings page yet. Searching Windows settings for {name}.")
        fallback_windows_search(name + " settings")
        return True
    say(f"Opening {name or 'settings'} settings.")
    start_target(uri)
    return True


APPS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "browser": "chrome",
    "edge": "msedge",
    "microsoft edge": "msedge",
    "brave": "brave",
    "firefox": "firefox",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "paint": "mspaint",
    "camera": "microsoft.windows.camera:",
    "cmd": "cmd",
    "command prompt": "cmd",
    "terminal": "wt",
    "windows terminal": "wt",
    "powershell": "powershell",
    "task manager": "taskmgr",
    "control panel": "control",
    "file explorer": "explorer",
    "explorer": "explorer",
    "vs code": "code",
    "vscode": "code",
    "visual studio code": "code",
    "word": "winword",
    "excel": "excel",
    "powerpoint": "powerpnt",
    "power point": "powerpnt",
    "outlook": "outlook",
    "whatsapp": "WHATSAPP_SPECIAL",
    "telegram": "telegram:",
    "discord": "discord:",
    "spotify": "spotify:",
    "vlc": "vlc",
    "github": "https://github.com",
    "github desktop": "GitHubDesktop",
    "chatgpt": "https://chatgpt.com",
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "drive": "https://drive.google.com",
    "google drive": "https://drive.google.com",
    "linkedin": "https://www.linkedin.com",
}


def normalize_app_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


def shortcut_locations():
    home = Path.home()
    locations = [
        home / "Desktop",
        Path(os.environ.get("PUBLIC", r"C:\Users\Public")) / "Desktop",
        Path(os.environ.get("APPDATA", home / "AppData/Roaming")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
    ]
    return [p for p in locations if p.exists()]


def find_shortcut(app_name: str):
    wanted = normalize_app_name(app_name)
    if not wanted:
        return None
    candidates = []
    for base in shortcut_locations():
        try:
            for path in base.rglob("*.lnk"):
                stem = normalize_app_name(path.stem)
                if wanted == stem:
                    return path
                if wanted in stem or stem in wanted:
                    score = abs(len(stem) - len(wanted))
                    candidates.append((score, path))
        except Exception:
            continue
    if candidates:
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]
    return None


def fallback_windows_search(app_name: str):
    if pyautogui is None:
        say(f"I cannot use Windows search because pyautogui is not installed. Searching Google for {app_name} instead.")
        google_search(app_name)
        return True
    try:
        say(f"Searching Windows for {app_name}.")
        pyautogui.hotkey("win")
        time.sleep(0.8)
        pyautogui.write(app_name, interval=0.02)
        time.sleep(0.7)
        pyautogui.press("enter")
        return True
    except Exception as exc:
        say(f"Windows search failed: {exc}")
        return False


def open_whatsapp():
    say("Opening WhatsApp.")
    # First try direct shortcut, because Microsoft Store WhatsApp often has a shortcut.
    shortcut = find_shortcut("whatsapp")
    if shortcut:
        try:
            os.startfile(str(shortcut))
            return True
        except Exception:
            pass
    # Then try WhatsApp URI protocol.
    try:
        subprocess.Popen('start "" "whatsapp:"', shell=True)
        time.sleep(1)
        return True
    except Exception:
        pass
    # Final fallback: Windows Start search.
    return fallback_windows_search("whatsapp")


def open_app(name: str):
    raw = name.strip().replace(" app", "").replace(" application", "")
    raw = raw.replace("chrome browser", "chrome").strip()
    if not raw:
        say("Which app should I open?")
        return True

    if raw.endswith("folder") or raw in ["desktop", "downloads", "documents", "pictures", "videos", "music", "screenshots"]:
        if open_folder(raw):
            return True

    if raw.endswith("settings") or raw in SETTINGS:
        return open_setting(raw)

    if raw in ["whatsapp", "whats app", "watsapp"]:
        return open_whatsapp()

    target = APPS.get(raw)
    if target:
        if target == "WHATSAPP_SPECIAL":
            return open_whatsapp()
        if target.startswith("http"):
            say(f"Opening {raw}.")
            open_url(target)
        else:
            say(f"Opening {raw}.")
            start_target(target)
        return True

    for key, target in APPS.items():
        if key in raw or raw in key:
            if target == "WHATSAPP_SPECIAL":
                return open_whatsapp()
            if target.startswith("http"):
                say(f"Opening {key}.")
                open_url(target)
            else:
                say(f"Opening {key}.")
                start_target(target)
            return True

    # NEW: Open apps from Desktop / Start Menu shortcuts.
    shortcut = find_shortcut(raw)
    if shortcut:
        say(f"Opening {shortcut.stem}.")
        try:
            os.startfile(str(shortcut))
            return True
        except Exception:
            pass

    # Universal app fallback: Start Menu search.
    return fallback_windows_search(raw)



PROCESS_ALIASES = {
    "chrome": ["chrome.exe"],
    "google chrome": ["chrome.exe"],
    "browser": ["chrome.exe", "msedge.exe", "brave.exe", "firefox.exe"],
    "edge": ["msedge.exe"],
    "microsoft edge": ["msedge.exe"],
    "brave": ["brave.exe"],
    "firefox": ["firefox.exe"],
    "whatsapp": ["WhatsApp.exe", "WhatsAppBeta.exe"],
    "notepad": ["notepad.exe"],
    "calculator": ["CalculatorApp.exe", "Calculator.exe", "calc.exe"],
    "calc": ["CalculatorApp.exe", "Calculator.exe", "calc.exe"],
    "paint": ["mspaint.exe"],
    "cmd": ["cmd.exe"],
    "command prompt": ["cmd.exe"],
    "terminal": ["WindowsTerminal.exe", "wt.exe", "OpenConsole.exe"],
    "powershell": ["powershell.exe", "pwsh.exe"],
    "task manager": ["Taskmgr.exe", "taskmgr.exe"],
    "settings": ["SystemSettings.exe"],
    "vs code": ["Code.exe"],
    "vscode": ["Code.exe"],
    "visual studio code": ["Code.exe"],
    "word": ["WINWORD.EXE", "winword.exe"],
    "excel": ["EXCEL.EXE", "excel.exe"],
    "powerpoint": ["POWERPNT.EXE", "powerpnt.exe"],
    "outlook": ["OUTLOOK.EXE", "outlook.exe"],
    "telegram": ["Telegram.exe"],
    "discord": ["Discord.exe"],
    "spotify": ["Spotify.exe"],
    "vlc": ["vlc.exe"],
}


def close_active_window():
    if pyautogui is None:
        say("Active window close needs pyautogui. Run install again.")
        return True
    try:
        say("Closing active window.")
        pyautogui.hotkey("alt", "f4")
    except Exception as exc:
        say(f"Could not close active window: {exc}")
    return True


def close_app(name: str):
    raw = name.lower().strip()
    raw = raw.replace(" app", "").replace(" application", "").replace(" window", "").strip()
    raw = re.sub(r"^(the|my)\s+", "", raw).strip()

    if not raw:
        say("Which app should I close?")
        return True
    if raw in ["current", "current window", "active", "active window", "this", "this window"]:
        return close_active_window()
    if raw in ["friday", "assistant", "jarvis"]:
        say("To close me, say exit.")
        return True
    if raw in ["all browsers", "all browser", "browsers"]:
        targets = []
        for key in ["chrome", "edge", "brave", "firefox"]:
            targets.extend(PROCESS_ALIASES.get(key, []))
        return terminate_processes("all browsers", targets, fuzzy_names=["chrome", "msedge", "brave", "firefox"])

    aliases = list(PROCESS_ALIASES.get(raw, []))
    fuzzy_names = [raw]
    for key, value in PROCESS_ALIASES.items():
        if key in raw or raw in key:
            aliases.extend(value)
            fuzzy_names.append(key)

    if raw in ["desktop", "folder", "folders", "downloads", "documents"]:
        return close_active_window()

    return terminate_processes(raw, aliases, fuzzy_names=fuzzy_names)


def terminate_processes(label: str, aliases, fuzzy_names=None):
    aliases_lower = {a.lower() for a in aliases}
    fuzzy_norms = {normalize_app_name(x) for x in (fuzzy_names or []) if len(normalize_app_name(x)) >= 3}
    current_pid = os.getpid()
    to_close = []

    for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
        try:
            pid = proc.info.get("pid")
            if pid == current_pid:
                continue
            pname = (proc.info.get("name") or "").strip()
            if not pname:
                continue
            pname_lower = pname.lower()
            pname_norm = normalize_app_name(pname_lower.replace(".exe", ""))
            matched = pname_lower in aliases_lower
            if not matched and fuzzy_norms:
                for f in fuzzy_norms:
                    if f and len(f) >= 3 and (f in pname_norm or pname_norm in f):
                        if pname_lower not in ["python.exe", "pythonw.exe", "cmd.exe", "conhost.exe"]:
                            matched = True
                            break
            if matched:
                to_close.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not to_close:
        say(f"I could not find running {label}. If it is open, say close current window.")
        return True

    for proc in to_close:
        try:
            proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    time.sleep(1.5)
    for proc in to_close:
        try:
            if proc.is_running():
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    say(f"Closed {label}.")
    return True
def load_contacts():
    if not CONTACTS_FILE.exists():
        return {}
    try:
        return json.loads(CONTACTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_contacts(data):
    CONTACTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize_phone(phone: str):
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        # India default. Change manually in whatsapp_contacts.json if needed.
        digits = "91" + digits
    return digits


def add_whatsapp_contact(name: str, phone: str):
    name = name.strip().lower()
    phone = normalize_phone(phone)
    if not name or len(phone) < 10:
        say("Contact name or phone number is not correct.")
        return True
    contacts = load_contacts()
    contacts[name] = phone
    save_contacts(contacts)
    say(f"Saved WhatsApp contact {name}.")
    return True


def send_whatsapp_number(phone: str, message: str):
    phone = normalize_phone(phone)
    message = message.strip()
    if len(phone) < 10:
        say("Phone number is not correct. Say number with country code, like 91 then number.")
        return True
    if not message:
        say("What message should I send?")
        return True
    encoded = urllib.parse.quote(message)
    say(f"Opening WhatsApp chat for {phone}.")
    # Try WhatsApp Desktop URI first.
    try:
        subprocess.Popen(f'start "" "whatsapp://send?phone={phone}&text={encoded}"', shell=True)
        time.sleep(5)
    except Exception:
        open_url(f"https://wa.me/{phone}?text={encoded}")
        time.sleep(5)

    if pyautogui:
        # On most systems, WhatsApp opens with text filled; Enter sends.
        # If it does not, user can press Enter manually.
        try:
            time.sleep(1)
            pyautogui.press("enter")
            say("If WhatsApp opened correctly, the message has been sent. If not, press Enter once.")
        except Exception:
            say("WhatsApp opened. Press Enter to send.")
    else:
        say("WhatsApp opened. Press Enter to send.")
    return True


def send_whatsapp_contact(name: str, message: str):
    contact_key = name.strip().lower()
    contacts = load_contacts()
    if contact_key in contacts:
        return send_whatsapp_number(contacts[contact_key], message)

    # Fuzzy contact match.
    for saved_name, phone in contacts.items():
        if contact_key in saved_name or saved_name in contact_key:
            return send_whatsapp_number(phone, message)

    # Fallback UI automation by contact name. This can work, but depends on WhatsApp UI focus.
    say(f"I do not have a saved number for {name}. I will search the contact name in WhatsApp.")
    open_whatsapp()
    if pyautogui is None:
        say("For reliable messaging, first save contact: add whatsapp contact name number.")
        return True
    try:
        time.sleep(5)
        # New chat shortcut often opens contact search in WhatsApp Desktop.
        pyautogui.hotkey("ctrl", "n")
        time.sleep(1)
        pyautogui.write(name, interval=0.03)
        time.sleep(1.5)
        pyautogui.press("enter")
        time.sleep(1)
        pyautogui.write(message, interval=0.02)
        pyautogui.press("enter")
        say("I tried to send it. If WhatsApp selected the wrong chat, use saved phone number command.")
    except Exception as exc:
        say(f"Could not automate WhatsApp: {exc}")
    return True


def search_whatsapp_contact(name: str):
    name = name.strip()
    if not name:
        say("Which WhatsApp contact should I search?")
        return True
    open_whatsapp()
    if pyautogui is None:
        say("WhatsApp opened. Search the contact manually.")
        return True
    try:
        time.sleep(5)
        pyautogui.hotkey("ctrl", "n")
        time.sleep(0.8)
        pyautogui.write(name, interval=0.03)
        say(f"Searching WhatsApp contact {name}.")
    except Exception:
        say("WhatsApp opened. Search the contact manually.")
    return True


def local_file_search(query: str):
    query = query.strip()
    if not query:
        say("What file should I search?")
        return True
    say(f"Searching files for {query}.")
    encoded = urllib.parse.quote(query)
    try:
        subprocess.Popen(f'explorer "search-ms:query={encoded}"', shell=True)
    except Exception:
        fallback_windows_search(query)
    return True


def take_screenshot():
    if pyautogui is None:
        say("Screenshot needs pyautogui. Run install again.")
        return True
    filename = SCREENSHOTS_DIR / f"screenshot_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    try:
        img = pyautogui.screenshot()
        img.save(filename)
        say("Screenshot saved in screenshots folder.")
        os.startfile(str(SCREENSHOTS_DIR))
    except Exception as exc:
        say(f"Could not take screenshot: {exc}")
    return True


def system_status():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    if battery:
        say(f"CPU {cpu} percent. RAM {ram} percent. Battery {int(battery.percent)} percent.")
    else:
        say(f"CPU {cpu} percent. RAM {ram} percent. Battery information not available.")
    return True


def volume_action(action: str):
    if pyautogui is None:
        say("Volume control needs pyautogui. Run install again.")
        return True
    if action == "up":
        pyautogui.press("volumeup", presses=5)
        say("Volume up.")
    elif action == "down":
        pyautogui.press("volumedown", presses=5)
        say("Volume down.")
    elif action == "mute":
        pyautogui.press("volumemute")
        say("Volume muted.")
    return True


def write_note(text: str):
    text = text.strip()
    if not text:
        say("What should I write in the note?")
        return True
    filename = NOTES_DIR / f"note_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filename.write_text(text, encoding="utf-8")
    say("Note saved.")
    return True


def read_latest_note():
    notes = sorted(NOTES_DIR.glob("note_*.txt"), reverse=True)
    if not notes:
        say("No notes found.")
        return True
    text = notes[0].read_text(encoding="utf-8", errors="ignore")
    say(f"Latest note says: {text[:400]}")
    return True


def type_text(text: str):
    if pyautogui is None:
        say("Typing needs pyautogui. Run install again.")
        return True
    text = text.strip()
    if not text:
        say("What should I type?")
        return True
    say("Typing now.")
    time.sleep(0.5)
    pyautogui.write(text, interval=0.01)
    return True




# ------------------------------
# V8 MULTITASKING / WINDOW CONTROL
# ------------------------------
WINDOW_KEYWORDS = {
    "chrome": ["chrome", "google chrome"],
    "google chrome": ["chrome", "google chrome"],
    "edge": ["edge", "microsoft edge"],
    "microsoft edge": ["edge", "microsoft edge"],
    "brave": ["brave"],
    "firefox": ["firefox"],
    "whatsapp": ["whatsapp"],
    "notepad": ["notepad"],
    "calculator": ["calculator", "calc"],
    "vs code": ["visual studio code", "vs code", "code"],
    "vscode": ["visual studio code", "vs code", "code"],
    "visual studio code": ["visual studio code", "vs code", "code"],
    "file explorer": ["file explorer", "explorer"],
    "explorer": ["file explorer", "explorer"],
    "settings": ["settings"],
    "cmd": ["command prompt", "cmd"],
    "terminal": ["terminal", "windows terminal"],
    "powershell": ["powershell"],
    "youtube": ["youtube", "google chrome", "microsoft edge", "brave", "firefox"],
}


def _need_gui(action_name: str = "This command"):
    if pyautogui is None:
        say(f"{action_name} needs pyautogui. Run INSTALL again.")
        return False
    return True


def get_active_window_title():
    if gw is None:
        return ""
    try:
        win = gw.getActiveWindow()
        return win.title if win else ""
    except Exception:
        return ""


def window_terms(name: str):
    raw = name.lower().strip()
    raw = raw.replace(" app", "").replace(" application", "").replace(" window", "").strip()
    terms = [raw]
    if raw in WINDOW_KEYWORDS:
        terms.extend(WINDOW_KEYWORDS[raw])
    for key, vals in WINDOW_KEYWORDS.items():
        if key in raw or raw in key:
            terms.append(key)
            terms.extend(vals)
    if raw in APPS:
        terms.append(raw)
    # Also support natural website names like youtube, github, gmail.
    for site in ["youtube", "github", "gmail", "google", "chatgpt", "linkedin", "drive"]:
        if site in raw:
            terms.append(site)
    clean_terms = []
    for t in terms:
        t = t.strip()
        if t and t not in clean_terms:
            clean_terms.append(t)
    return clean_terms


def list_open_windows(speak: bool = True):
    if gw is None:
        say("Window listing needs pygetwindow. Run INSTALL again.")
        return []
    windows = []
    try:
        for w in gw.getAllWindows():
            title = (w.title or "").strip()
            if not title:
                continue
            # Skip tiny system/helper windows when possible.
            try:
                if w.width <= 60 or w.height <= 60:
                    continue
            except Exception:
                pass
            windows.append(w)
    except Exception:
        windows = []
    if speak:
        if not windows:
            say("I could not read open windows.")
        else:
            say(f"I found {len(windows)} open windows. Check the command window list.")
            print("\nOPEN WINDOWS:")
            for i, w in enumerate(windows[:30], start=1):
                print(f"{i}. {w.title}")
    return windows


def find_windows_by_name(name: str):
    if gw is None:
        return []
    terms = window_terms(name)
    term_norms = [normalize_app_name(t) for t in terms if normalize_app_name(t)]
    matches = []
    try:
        for w in gw.getAllWindows():
            title = (w.title or "").strip()
            if not title:
                continue
            title_norm = normalize_app_name(title)
            if not title_norm:
                continue
            best_score = None
            for term in term_norms:
                if term in title_norm or title_norm in term:
                    score = abs(len(title_norm) - len(term))
                    # Prefer exact app suffix in browser titles.
                    if title_norm.endswith(term):
                        score -= 25
                    if term in ["chrome", "googlechrome"] and "googlechrome" in title_norm:
                        score -= 30
                    if term in ["edge", "microsoftedge"] and "microsoftedge" in title_norm:
                        score -= 30
                    if term == "whatsapp" and "whatsapp" in title_norm:
                        score -= 40
                    if best_score is None or score < best_score:
                        best_score = score
            if best_score is not None:
                matches.append((best_score, w))
    except Exception:
        return []
    matches.sort(key=lambda x: x[0])
    return [w for _, w in matches]


def focus_window(name: str, also_open: bool = True):
    raw = name.strip()
    if raw in ["current", "active", "this", "this app", "this window", "current window"]:
        title = get_active_window_title()
        say(f"Current window is {title or 'active window'}.")
        return True
    wins = find_windows_by_name(raw)
    if wins:
        w = wins[0]
        try:
            if getattr(w, "isMinimized", False):
                w.restore()
                time.sleep(0.3)
        except Exception:
            pass
        try:
            w.activate()
            time.sleep(0.4)
            say(f"Brought {raw} to front.")
            return True
        except Exception:
            try:
                w.restore()
                time.sleep(0.2)
                w.activate()
                say(f"Brought {raw} to front.")
                return True
            except Exception:
                pass
    if also_open:
        say(f"I could not find an open {raw} window. I will try opening it.")
        return open_app(raw)
    say(f"I could not find an open {raw} window.")
    return True


def minimize_named_window(name: str):
    wins = find_windows_by_name(name)
    if not wins:
        say(f"I could not find {name}. If it is active, say minimize current window.")
        return True
    try:
        wins[0].minimize()
        say(f"Minimized {name}.")
    except Exception:
        say(f"Could not minimize {name}.")
    return True


def maximize_named_window(name: str):
    wins = find_windows_by_name(name)
    if not wins:
        say(f"I could not find {name}. If it is active, say maximize current window.")
        return True
    try:
        wins[0].restore()
        time.sleep(0.2)
        wins[0].maximize()
        wins[0].activate()
        say(f"Maximized {name}.")
    except Exception:
        say(f"Could not maximize {name}.")
    return True


def restore_named_window(name: str):
    wins = find_windows_by_name(name)
    if not wins:
        say(f"I could not find minimized {name}. I will try opening it.")
        return open_app(name)
    try:
        wins[0].restore()
        time.sleep(0.2)
        wins[0].activate()
        say(f"Restored {name}.")
    except Exception:
        say(f"Could not restore {name}.")
    return True


def current_window_action(action: str):
    if action in ["minimize", "minimise"]:
        if gw is not None:
            try:
                win = gw.getActiveWindow()
                if win:
                    win.minimize()
                    say("Minimized current window.")
                    return True
            except Exception:
                pass
        if _need_gui("Minimize current window"):
            pyautogui.hotkey("win", "down")
            time.sleep(0.1)
            pyautogui.hotkey("win", "down")
            say("Minimized current window.")
        return True
    if action == "maximize":
        if gw is not None:
            try:
                win = gw.getActiveWindow()
                if win:
                    win.maximize()
                    say("Maximized current window.")
                    return True
            except Exception:
                pass
        if _need_gui("Maximize current window"):
            pyautogui.hotkey("win", "up")
            say("Maximized current window.")
        return True
    if action == "restore":
        if gw is not None:
            try:
                win = gw.getActiveWindow()
                if win:
                    win.restore()
                    say("Restored current window.")
                    return True
            except Exception:
                pass
        if _need_gui("Restore current window"):
            pyautogui.hotkey("win", "down")
            say("Restored current window.")
        return True
    return True


def shortcut_action(action: str, text: str = ""):
    if not _need_gui("Multitasking command"):
        return True
    try:
        if action == "next_tab":
            pyautogui.hotkey("ctrl", "tab")
            say("Next tab.")
        elif action == "previous_tab":
            pyautogui.hotkey("ctrl", "shift", "tab")
            say("Previous tab.")
        elif action == "new_tab":
            pyautogui.hotkey("ctrl", "t")
            say("New tab.")
        elif action == "close_tab":
            pyautogui.hotkey("ctrl", "w")
            say("Closed tab.")
        elif action == "reopen_tab":
            pyautogui.hotkey("ctrl", "shift", "t")
            say("Reopened closed tab.")
        elif action == "refresh":
            pyautogui.hotkey("ctrl", "r")
            say("Refreshed.")
        elif action == "back":
            pyautogui.hotkey("alt", "left")
            say("Back.")
        elif action == "forward":
            pyautogui.hotkey("alt", "right")
            say("Forward.")
        elif action == "switch_window":
            pyautogui.hotkey("alt", "tab")
            say("Switched window.")
        elif action == "task_view":
            pyautogui.hotkey("win", "tab")
            say("Task view.")
        elif action == "show_desktop":
            pyautogui.hotkey("win", "d")
            say("Showing desktop.")
        elif action == "minimize_all":
            pyautogui.hotkey("win", "m")
            say("Minimized all windows.")
        elif action == "restore_all":
            pyautogui.hotkey("win", "shift", "m")
            say("Restored minimized windows.")
        elif action == "copy":
            pyautogui.hotkey("ctrl", "c")
            say("Copied.")
        elif action == "paste":
            pyautogui.hotkey("ctrl", "v")
            say("Pasted.")
        elif action == "select_all":
            pyautogui.hotkey("ctrl", "a")
            say("Selected all.")
        elif action == "save":
            pyautogui.hotkey("ctrl", "s")
            say("Saved.")
        elif action == "enter":
            pyautogui.press("enter")
            say("Pressed Enter.")
        elif action == "escape":
            pyautogui.press("esc")
            say("Pressed Escape.")
        elif action == "scroll_down":
            pyautogui.scroll(-5)
            say("Scrolled down.")
        elif action == "scroll_up":
            pyautogui.scroll(5)
            say("Scrolled up.")
    except Exception as exc:
        say(f"Could not run multitasking command: {exc}")
    return True


def search_in_current_tab(query: str, new_tab: bool = False):
    if not _need_gui("Browser search"):
        return True
    query = query.strip()
    if not query:
        say("What should I search?")
        return True
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
    try:
        if new_tab:
            pyautogui.hotkey("ctrl", "t")
            time.sleep(0.2)
        else:
            pyautogui.hotkey("ctrl", "l")
            time.sleep(0.2)
        pyautogui.write(url, interval=0.001)
        pyautogui.press("enter")
        say(f"Searching {query} in this tab." if not new_tab else f"Searching {query} in a new tab.")
    except Exception as exc:
        say(f"Could not search in browser: {exc}")
    return True


def find_browser_tab(query: str):
    if not _need_gui("Find browser tab"):
        return True
    query = query.strip()
    if not query:
        say("Which tab should I find?")
        return True
    try:
        # Chrome and Edge support tab search with Ctrl+Shift+A.
        pyautogui.hotkey("ctrl", "shift", "a")
        time.sleep(0.6)
        pyautogui.write(query, interval=0.02)
        time.sleep(0.5)
        pyautogui.press("enter")
        say(f"Trying to switch to tab {query}.")
    except Exception as exc:
        say(f"Could not find tab: {exc}")
    return True


def multitask_help():
    say("Use commands like switch to chrome, restore whatsapp, minimize current window, next tab, previous tab, find tab youtube, restore all windows.")
    print("""
V8 MULTITASKING COMMANDS
------------------------
Active/current app:
- minimize current window
- maximize current window
- close current window
- search this tab python tutorial
- open new tab and search ai projects
- next tab / previous tab / close tab / reopen closed tab
- refresh page / go back / go forward
- copy / paste / select all / save / press enter

Open/minimized apps:
- switch to chrome
- bring whatsapp to front
- restore chrome
- maximize whatsapp
- minimize chrome
- list open windows
- restore all windows
- minimize all windows
- show desktop
- switch window

Browser tabs:
- find tab youtube
- switch to tab github
- next tab
- previous tab
""")
    return True

def _handle_command_core(original: str) -> bool:
    cmd = clean_command(original)
    if not cmd:
        say("I did not hear clearly. Please say it again.")
        return True

    print(f"Clean command: {cmd}")

    if cmd in ["exit", "quit", "stop", "close", "goodbye", "bye"] or "stop friday" in cmd:
        say("Goodbye bro.")
        return False

    # V8 multitasking help.
    if cmd in ["multitasking commands", "multi tasking commands", "window commands", "tab commands", "help multitasking"]:
        return multitask_help()

    # List / focus / restore minimized apps and windows.
    if cmd in ["list windows", "show open windows", "list open windows", "what windows are open"]:
        list_open_windows(speak=True)
        return True

    if cmd in ["switch window", "switch to next window", "next window", "change window", "alt tab"]:
        return shortcut_action("switch_window")
    if cmd in ["task view", "open task view", "show task view"]:
        return shortcut_action("task_view")
    if cmd in ["show desktop", "go to desktop", "desktop"]:
        return shortcut_action("show_desktop")
    if cmd in ["minimize all", "minimise all", "minimize all windows", "hide all windows"]:
        return shortcut_action("minimize_all")
    if cmd in ["restore all", "restore all windows", "open minimized windows", "show minimized windows", "bring back all windows"]:
        return shortcut_action("restore_all")

    m = re.search(r"(?:switch to|bring|bring back|bring to front|focus|activate|open minimized|show) (.+?)(?: window| app)?$", cmd)
    if m:
        return focus_window(m.group(1))
    m = re.search(r"(?:restore|unminimize|unminimise) (.+?)(?: window| app)?$", cmd)
    if m:
        return restore_named_window(m.group(1))
    m = re.search(r"(?:minimize|minimise|hide) (current window|active window|this window|this app|current app)$", cmd)
    if m:
        return current_window_action("minimize")
    m = re.search(r"(?:maximize|maximise|full screen) (current window|active window|this window|this app|current app)$", cmd)
    if m:
        return current_window_action("maximize")
    m = re.search(r"(?:restore) (current window|active window|this window|this app|current app)$", cmd)
    if m:
        return current_window_action("restore")
    m = re.search(r"(?:minimize|minimise|hide) (.+?)(?: window| app)?$", cmd)
    if m:
        return minimize_named_window(m.group(1))
    m = re.search(r"(?:maximize|maximise|full screen) (.+?)(?: window| app)?$", cmd)
    if m:
        return maximize_named_window(m.group(1))

    # Browser tab / current app shortcuts.
    if cmd in ["next tab", "switch tab", "change tab", "go next tab"]:
        return shortcut_action("next_tab")
    if cmd in ["previous tab", "prev tab", "back tab", "go previous tab"]:
        return shortcut_action("previous_tab")
    if cmd in ["new tab", "open new tab"]:
        return shortcut_action("new_tab")
    if cmd in ["close tab", "close current tab", "close this tab"]:
        return shortcut_action("close_tab")
    if cmd in ["reopen tab", "reopen closed tab", "restore closed tab"]:
        return shortcut_action("reopen_tab")
    if cmd in ["refresh", "refresh page", "reload", "reload page"]:
        return shortcut_action("refresh")
    if cmd in ["go back", "back page", "browser back"]:
        return shortcut_action("back")
    if cmd in ["go forward", "forward page", "browser forward"]:
        return shortcut_action("forward")
    if cmd in ["copy", "copy this"]:
        return shortcut_action("copy")
    if cmd in ["paste", "paste here"]:
        return shortcut_action("paste")
    if cmd in ["select all", "select everything"]:
        return shortcut_action("select_all")
    if cmd in ["save", "save file", "save this"]:
        return shortcut_action("save")
    if cmd in ["press enter", "enter"]:
        return shortcut_action("enter")
    if cmd in ["escape", "press escape", "press esc"]:
        return shortcut_action("escape")
    if cmd in ["scroll down", "page down"]:
        return shortcut_action("scroll_down")
    if cmd in ["scroll up", "page up"]:
        return shortcut_action("scroll_up")

    m = re.search(r"(?:search this tab|search in this tab|search current tab|search here)(?: for)? (.+)", cmd)
    if m:
        return search_in_current_tab(m.group(1), new_tab=False)
    m = re.search(r"(?:open new tab and search|new tab search|search in new tab)(?: for)? (.+)", cmd)
    if m:
        return search_in_current_tab(m.group(1), new_tab=True)
    m = re.search(r"(?:find tab|switch to tab|open tab|search tab)(?: named| called)? (.+)", cmd)
    if m:
        return find_browser_tab(m.group(1))

    # Close apps/windows. Examples: close chrome, close whatsapp, close current window.
    if cmd in ["close current window", "close active window", "close window", "close this window"]:
        return close_active_window()
    m = re.search(r"(?:close|quit|exit|stop|kill|turn off) (.+?)(?: app| application| window)?$", cmd)
    if m:
        return close_app(m.group(1))

    # WhatsApp contact saving.
    m = re.search(r"(?:add|save) whatsapp contact (.+?) (?:number )?([+0-9][0-9 +_-]{8,})$", cmd)
    if m:
        return add_whatsapp_contact(m.group(1), m.group(2))

    # WhatsApp by number.
    m = re.search(r"(?:send whatsapp|whatsapp|message whatsapp) (?:to )?([+0-9][0-9 +_-]{8,}) (?:message )?(.+)", cmd)
    if m:
        return send_whatsapp_number(m.group(1), m.group(2))

    # WhatsApp by contact name.
    m = re.search(r"(?:send whatsapp message to|send whatsapp to|message|text) (.+?) (?:on whatsapp|whatsapp)?(?: saying| message| text)? (.+)", cmd)
    if m and "whatsapp" in cmd:
        return send_whatsapp_contact(m.group(1), m.group(2))

    m = re.search(r"(?:search whatsapp|find whatsapp contact|open whatsapp chat with|open whatsapp contact) (.+)", cmd)
    if m:
        return search_whatsapp_contact(m.group(1))

    if cmd in ["open whatsapp", "whatsapp"]:
        return open_whatsapp()

    # Time/date
    if "what time" in cmd or cmd == "time":
        say("The time is " + dt.datetime.now().strftime("%I:%M %p"))
        return True
    if "what date" in cmd or "today date" in cmd or cmd == "date":
        say("Today is " + dt.datetime.now().strftime("%A, %d %B %Y"))
        return True

    # Screenshot/status/volume
    if "screenshot" in cmd or "screen shot" in cmd:
        return take_screenshot()
    if "system status" in cmd or "pc status" in cmd or "battery status" in cmd or cmd == "status":
        return system_status()
    if "volume up" in cmd or "increase volume" in cmd:
        return volume_action("up")
    if "volume down" in cmd or "decrease volume" in cmd:
        return volume_action("down")
    if "mute" in cmd or "silent volume" in cmd:
        return volume_action("mute")

    # Lock/shutdown/restart safety
    if "lock pc" in cmd or "lock computer" in cmd:
        say("Locking PC.")
        run_cmd("rundll32.exe user32.dll,LockWorkStation")
        return True
    if "confirm shutdown" in cmd:
        say("Shutting down PC.")
        run_cmd("shutdown /s /t 5")
        return True
    if "shutdown" in cmd:
        say("For safety say: confirm shutdown pc")
        return True
    if "confirm restart" in cmd:
        say("Restarting PC.")
        run_cmd("shutdown /r /t 5")
        return True
    if "restart" in cmd:
        say("For safety say: confirm restart pc")
        return True

    # Notes and typing
    m = re.search(r"(?:write note|make note|save note|note) (.+)", cmd)
    if m:
        return write_note(m.group(1))
    if "read note" in cmd or "latest note" in cmd:
        return read_latest_note()
    m = re.search(r"(?:type|write this|type this) (.+)", cmd)
    if m:
        return type_text(m.group(1))

    # Open Chrome/Edge/Brave and search query
    m = re.search(r"open (chrome|google chrome|edge|brave|browser) (?:and )?(?:search|find|look up|google search)(?: for)? (.+)", cmd)
    if m:
        browser = m.group(1)
        query = m.group(2)
        prefer = "chrome" if "chrome" in browser or browser == "browser" else "edge" if "edge" in browser else "default"
        return google_search(query, prefer=prefer)

    # YouTube search / play
    m = re.search(r"(?:open )?youtube (?:and )?(?:search|play|find|look up)(?: for)? (.+)", cmd)
    if not m:
        m = re.search(r"(?:search|play|find) (.+) (?:on|in) youtube", cmd)
    if m:
        return youtube_search(m.group(1))

    # Google/web search
    m = re.search(r"(?:google search|search google|search this on google|search on google|search|look up|find on google)(?: for)? (.+)", cmd)
    if m:
        query = m.group(1)
        if query.startswith("file ") or query.startswith("folder "):
            return local_file_search(query.split(" ", 1)[1])
        return google_search(query)

    # Questions become Google searches.
    if cmd.startswith(("what is ", "who is ", "where is ", "how to ", "how can ", "why ", "when ", "which ")):
        return google_search(cmd)

    # File/folder local search
    m = re.search(r"(?:search file|find file|search folder|find folder|search in pc|find in pc|windows search)(?: for)? (.+)", cmd)
    if m:
        return local_file_search(m.group(1))

    # Settings commands
    m = re.search(r"open (.+?)(?: settings| setting)$", cmd)
    if m:
        return open_setting(m.group(1))
    if cmd.endswith("settings") or cmd in SETTINGS:
        return open_setting(cmd)

    # Folder/app commands
    m = re.search(r"open (.+?)(?: folder)?$", cmd)
    if m:
        target = m.group(1).strip()
        if open_folder(target) or open_app(target):
            return True

    if cmd in APPS:
        return open_app(cmd)

    say("I will search this on Windows.")
    return fallback_windows_search(cmd)



def handle_command(text: str):
    """Wrapper that saves command result status to the account database."""
    try:
        result = _handle_command_core(text)
        save_command_to_database(text, result_text="executed", status="completed")
        return result
    except Exception as e:
        save_command_to_database(text, result_text=str(e), status="error")
        raise


def listen_once() -> str:
    device_id, sample_rate = load_config()
    print("\nListening...")
    record_wav("command.wav", seconds=5, device_id=device_id, sample_rate=sample_rate)
    text = recognize_wav("command.wav")
    if text:
        print(f"You: {text}")
    else:
        print("Speech not understood.")
    return text


def voice_loop():
    if not require_account_login():
        return
    say("FRIDAY V8 Multitasking Control is online.")
    print("\nVOICE MODE. Speak after the recording line appears.")
    print("Examples: switch to chrome, minimize current window, next tab, find tab youtube, restore all windows, exit.")
    while True:
        text = listen_once()
        if not text:
            say("I did not hear clearly. Please say it again.")
            continue
        keep_running = handle_command(text)
        if not keep_running:
            break


def text_loop():
    if not require_account_login():
        return
    say("FRIDAY V8 text mode is online.")
    print("Type commands. Examples: switch to chrome, bring whatsapp to front, minimize current window, next tab, open new tab and search python, restore all windows, exit")
    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if not handle_command(text):
            break


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--voice", action="store_true")
    parser.add_argument("--text", action="store_true")
    args = parser.parse_args()
    if args.text:
        text_loop()
    else:
        voice_loop()


if __name__ == "__main__":
    main()
