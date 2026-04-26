import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import webbrowser
from pathlib import Path

import psutil

from audio_utils import load_config, record_wav, recognize_wav

BASE_DIR = Path(__file__).resolve().parent
NOTES_DIR = BASE_DIR / "notes"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
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


def clean_command(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("chrome", "chrome")
    text = re.sub(r"[^a-z0-9 .:/\\_-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Remove wake words and filler phrases without destroying the real command.
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
    # Windows start command works for apps, protocols, folders and control panel applets.
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
        # Try fuzzy contains
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
    "whatsapp": "whatsapp:",
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


def fallback_windows_search(app_name: str):
    if pyautogui is None:
        say(f"I cannot use Windows search because pyautogui is not installed. Searching Google for {app_name} instead.")
        google_search(app_name)
        return True
    try:
        say(f"Searching Windows for {app_name}.")
        pyautogui.hotkey("win")
        time.sleep(0.7)
        pyautogui.write(app_name, interval=0.02)
        time.sleep(0.5)
        pyautogui.press("enter")
        return True
    except Exception as exc:
        say(f"Windows search failed: {exc}")
        return False


def open_app(name: str):
    raw = name.strip().replace(" app", "").replace(" application", "")
    raw = raw.replace("chrome browser", "chrome").strip()
    if not raw:
        say("Which app should I open?")
        return True

    # Folder support inside open command.
    if raw.endswith("folder") or raw in ["desktop", "downloads", "documents", "pictures", "videos", "music", "screenshots"]:
        if open_folder(raw):
            return True

    # Settings support inside open command.
    if raw.endswith("settings") or raw in SETTINGS:
        return open_setting(raw)

    target = APPS.get(raw)
    if target:
        if target.startswith("http"):
            say(f"Opening {raw}.")
            open_url(target)
        else:
            say(f"Opening {raw}.")
            start_target(target)
        return True

    # Fuzzy app mapping.
    for key, target in APPS.items():
        if key in raw or raw in key:
            if target.startswith("http"):
                say(f"Opening {key}.")
                open_url(target)
            else:
                say(f"Opening {key}.")
                start_target(target)
            return True

    # Universal app fallback: Start Menu search.
    return fallback_windows_search(raw)


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
        say(f"Screenshot saved in screenshots folder.")
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


def handle_command(original: str) -> bool:
    cmd = clean_command(original)
    if not cmd:
        say("I did not hear clearly. Please say it again.")
        return True

    print(f"Clean command: {cmd}")

    # Exit
    if cmd in ["exit", "quit", "stop", "close", "goodbye", "bye"] or "stop friday" in cmd:
        say("Goodbye bro.")
        return False

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
        # Avoid local file searches accidentally.
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

    # Folder commands
    m = re.search(r"open (.+?)(?: folder)?$", cmd)
    if m:
        target = m.group(1).strip()
        if open_folder(target) or open_app(target):
            return True

    # Direct app names also work: "notepad", "calculator", "youtube".
    if cmd in APPS:
        return open_app(cmd)

    # Last fallback: search Windows Start Menu.
    say("I will search this on Windows.")
    return fallback_windows_search(cmd)


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
    say("FRIDAY V5 Universal Windows Control is online.")
    print("\nVOICE MODE. Speak after the recording line appears.")
    print("Examples: open chrome, open chrome and search AI projects, open bluetooth settings, search file resume, exit.")
    while True:
        text = listen_once()
        if not text:
            say("I did not hear clearly. Please say it again.")
            continue
        keep_running = handle_command(text)
        if not keep_running:
            break


def text_loop():
    say("FRIDAY V5 text mode is online.")
    print("Type commands. Examples: open chrome, open settings, youtube search python tutorial, exit")
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
