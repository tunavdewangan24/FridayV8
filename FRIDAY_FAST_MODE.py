import os, json, time, subprocess, urllib.parse
from pathlib import Path

try: import pyautogui
except Exception: pyautogui = None
try: import pyperclip
except Exception: pyperclip = None
try: import pyttsx3
except Exception: pyttsx3 = None
try: import speech_recognition as sr
except Exception: sr = None

APP = Path(os.getenv("APPDATA") or Path.home()) / "FridayFast"
APP.mkdir(parents=True, exist_ok=True)
STATE = APP / "state.json"
MIC = APP / "mic.json"
VOICE = APP / "voice.json"

DEFAULT_STATE = {"paused": False, "browser": "brave", "current_app": "desktop", "last_contact": "", "pending_message": ""}
DEFAULT_VOICE = {"enabled": True, "rate": 178, "volume": 1.0}

def load(path, default):
    if not path.exists():
        path.write_text(json.dumps(default, indent=4), encoding="utf-8")
        return default.copy()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        d = default.copy(); d.update(data); return d
    except Exception:
        return default.copy()

def save(path, data): path.write_text(json.dumps(data, indent=4), encoding="utf-8")
def st(): return load(STATE, DEFAULT_STATE)
def ust(**kw):
    d = st(); d.update(kw); save(STATE, d); return d
def mic():
    if not MIC.exists(): return None
    try:
        x = json.loads(MIC.read_text(encoding="utf-8")).get("mic")
        return None if x in ("", None, "default") else int(x)
    except Exception: return None

_engine = None
def say(msg, speak=True):
    global _engine
    print("FRIDAY:", msg)
    if not speak or pyttsx3 is None: return
    cfg = load(VOICE, DEFAULT_VOICE)
    if not cfg.get("enabled", True): return
    try:
        if _engine is None:
            _engine = pyttsx3.init()
            _engine.setProperty("rate", int(cfg.get("rate",178)))
            _engine.setProperty("volume", float(cfg.get("volume",1.0)))
        _engine.say(msg); _engine.runAndWait()
    except Exception: pass

def shell(cmd): subprocess.Popen(cmd, shell=True)
def paste(txt):
    if not (pyautogui and pyperclip):
        say("pyautogui or pyperclip missing."); return False
    pyperclip.copy(txt); pyautogui.hotkey("ctrl","v"); return True

BROWSER_PATHS = {
 "brave":[r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe", r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"],
 "chrome":[r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
 "edge":[r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]
}
BROWSER_TITLE = {"brave":"Brave","chrome":"Chrome","edge":"Edge"}

def focus(title_list):
    if not pyautogui: return False
    if isinstance(title_list, str): title_list=[title_list]
    for title in title_list:
        try:
            for w in pyautogui.getWindowsWithTitle(title):
                try:
                    if getattr(w, "isMinimized", False): w.restore()
                    w.activate(); time.sleep(.3); return True
                except Exception: pass
        except Exception: pass
    return False

def open_browser(name=None):
    name=(name or st().get("browser","brave")).lower()
    for p in BROWSER_PATHS.get(name, []):
        if Path(p).exists():
            say(f"Opening {name}"); subprocess.Popen([p], shell=False); ust(browser=name,current_app="browser"); time.sleep(1); return True
    fb={"brave":"start brave","chrome":"start chrome","edge":"start msedge"}.get(name)
    if fb:
        say(f"Opening {name}"); shell(fb); ust(browser=name,current_app="browser"); time.sleep(1); return True
    say("Browser not found."); return False

def focus_browser():
    b=st().get("browser","brave")
    return focus([BROWSER_TITLE.get(b,b), b]) or (open_browser(b) and focus([BROWSER_TITLE.get(b,b), b]))

def url_same(url):
    if not (pyautogui and pyperclip): say("Browser control packages missing."); return
    focus_browser(); pyautogui.hotkey("ctrl","l"); time.sleep(.15); paste(url); pyautogui.press("enter")
def url_new(url):
    if not (pyautogui and pyperclip): say("Browser control packages missing."); return
    focus_browser(); pyautogui.hotkey("ctrl","t"); time.sleep(.15); paste(url); pyautogui.press("enter")
def google(q,new=False):
    say(f"Searching {q} on Google"); ust(current_app="google")
    (url_new if new else url_same)("https://www.google.com/search?q="+urllib.parse.quote(q))
def youtube(q,new=False):
    say(f"Searching {q} on YouTube"); ust(current_app="youtube")
    (url_new if new else url_same)("https://www.youtube.com/results?search_query="+urllib.parse.quote(q))

def open_whatsapp():
    say("Opening WhatsApp"); ust(current_app="whatsapp"); shell("start whatsapp:"); time.sleep(2)
    if not focus(["WhatsApp","Whatsapp"]): url_same("https://web.whatsapp.com")
def focus_whatsapp():
    return focus(["WhatsApp","Whatsapp"]) or (open_whatsapp() or focus(["WhatsApp","Whatsapp"]))
def wa_search(contact):
    if not contact: say("Contact empty."); return
    say(f"Searching {contact} in WhatsApp"); ust(current_app="whatsapp", last_contact=contact)
    if not (pyautogui and pyperclip): say("WhatsApp control package missing."); return
    focus_whatsapp(); pyautogui.hotkey("ctrl","f"); time.sleep(.25); paste(contact); time.sleep(.4); pyautogui.press("enter")
def parse_wa(raw):
    t=raw.lower().strip()
    for p in ("wa ","text ","message ","send "):
        if t.startswith(p): t=t.replace(p,"",1).strip(); break
    if t.startswith("to ") and " saying " in t:
        c,m=t.replace("to ","",1).split(" saying ",1); return c.strip(),m.strip()
    if " saying " in t:
        c,m=t.split(" saying ",1); return c.strip(),m.strip()
    if " to " in t:
        m,c=t.rsplit(" to ",1); return c.strip(),m.strip()
    parts=t.split(" ",1)
    if len(parts)==2: return parts[0].strip(),parts[1].strip()
    return st().get("last_contact",""), t.strip()
def wa_prepare(raw):
    c,m=parse_wa(raw)
    if not m: say("Message empty. Example: wa sonu hello"); return
    if c: wa_search(c); time.sleep(.8)
    ust(current_app="whatsapp", pending_message=m, last_contact=c or st().get("last_contact",""))
    say("Message ready. Say send to confirm."); print("Pending:", m)
def wa_send():
    m=st().get("pending_message","")
    if not m: say("No pending message."); return
    if not (pyautogui and pyperclip): say("WhatsApp control package missing."); return
    focus_whatsapp()
    try:
        w,h=pyautogui.size(); pyautogui.click(w//2,h-45); time.sleep(.2)
    except Exception: pass
    paste(m); pyautogui.press("enter"); ust(pending_message=""); say("Message sent.")

def norm(x):
    x=x.lower().strip()
    for a,b in {"opem":"open","opne":"open","serach":"search","seach":"search","you tube":"youtube","youtbe":"youtube","whats app":"whatsapp","watsapp":"whatsapp","minimise":"minimize"}.items():
        x=x.replace(a,b)
    return " ".join(x.split())

def help_text():
    print("""
FRIDAY FAST MODE COMMANDS

FAST:
  yt python tutorial
  g ai tools
  wa sonu hello
  send
  tabs / next / prev / close tab / new tab
  back / min / min all / restore / desktop

APPS:
  brave / chrome / edge / youtube / google / whatsapp / chatgpt / note / calc

WHATSAPP:
  wa sonu hello
  send hello to sonu
  send

FRIDAY:
  friday stop / friday start / friday exit
  voice on / voice off / louder / softer

RULE:
  No options. No guessing. Unclear command = ignored.
""")

def execute(text):
    cmd=norm(text)
    if not cmd: return True
    if cmd in ("hello","hi","hey"): say("Hello boss. I am ready."); return True
    if cmd in ("who are you","what are you"): say("I am Friday Fast Mode, your fast desktop assistant."); return True
    if cmd in ("help","commands"): help_text(); return True
    if cmd in ("friday exit","exit friday"): say("Goodbye boss."); return False
    if cmd in ("exit","quit","stop friday"): say("Say friday exit to close me."); return True
    if cmd in ("friday stop","stop","pause"): ust(paused=True); say("Paused. Say friday start."); return True
    if cmd in ("friday start","start","resume"): ust(paused=False); say("Resumed."); return True
    if st().get("paused",False): print("FRIDAY: Paused. Say friday start or friday exit."); return True

    if cmd in ("voice on","sound on"):
        c=load(VOICE,DEFAULT_VOICE); c["enabled"]=True; save(VOICE,c); say("Voice is on."); return True
    if cmd in ("voice off","sound off"):
        c=load(VOICE,DEFAULT_VOICE); c["enabled"]=False; save(VOICE,c); print("FRIDAY: Voice is off."); return True
    if cmd=="louder":
        c=load(VOICE,DEFAULT_VOICE); c["volume"]=min(1.0,c.get("volume",1.0)+.2); save(VOICE,c); say("Volume increased."); return True
    if cmd=="softer":
        c=load(VOICE,DEFAULT_VOICE); c["volume"]=max(.2,c.get("volume",1.0)-.2); save(VOICE,c); say("Volume decreased."); return True

    if cmd in ("use brave","set brave"): ust(browser="brave"); say("Default browser Brave."); return True
    if cmd in ("use chrome","set chrome"): ust(browser="chrome"); say("Default browser Chrome."); return True
    if cmd in ("use edge","set edge"): ust(browser="edge"); say("Default browser Edge."); return True
    if cmd in ("brave","open brave"): open_browser("brave"); return True
    if cmd in ("chrome","open chrome"): open_browser("chrome"); return True
    if cmd in ("edge","open edge"): open_browser("edge"); return True
    if cmd in ("youtube","yt","open youtube"): say("Opening YouTube"); ust(current_app="youtube"); url_same("https://www.youtube.com"); return True
    if cmd in ("google","open google"): say("Opening Google"); ust(current_app="google"); url_same("https://www.google.com"); return True
    if cmd in ("chatgpt","open chatgpt"): say("Opening ChatGPT"); ust(current_app="chatgpt"); url_same("https://chatgpt.com"); return True
    if cmd in ("whatsapp","wa","open whatsapp"): open_whatsapp(); return True
    if cmd in ("note","notepad","open notepad"): say("Opening notepad"); shell("notepad"); return True
    if cmd in ("calc","calculator","open calculator"): say("Opening calculator"); shell("calc"); return True

    if cmd.startswith("yt "): youtube(cmd[3:].strip()); return True
    if cmd.startswith("g "): google(cmd[2:].strip()); return True
    if cmd.startswith("new tab search "):
        q=cmd.replace("new tab search","",1).strip()
        if "youtube" in q: youtube(q.replace("on youtube","").replace("youtube","").strip(), True)
        else: google(q.replace("on google","").replace("google","").strip(), True)
        return True
    if cmd.startswith("search "):
        q=cmd.replace("search","",1).strip()
        if "youtube" in q: youtube(q.replace("on youtube","").replace("youtube","").strip()); return True
        if "google" in q: google(q.replace("on google","").replace("google","").strip()); return True
        cur=st().get("current_app")
        if cur=="youtube": youtube(q)
        elif cur=="whatsapp": wa_search(q)
        else: google(q)
        return True

    if cmd=="send": wa_send(); return True
    if cmd.startswith(("wa ","text ","message ","send ")): wa_prepare(cmd); return True

    if cmd in ("tabs","show tabs","show all tabs","show all the tabs"):
        say("Showing browser tabs."); focus_browser(); pyautogui and pyautogui.hotkey("ctrl","shift","a"); return True
    if cmd in ("next","next tab"):
        say("Next tab."); focus_browser(); pyautogui and pyautogui.hotkey("ctrl","tab"); return True
    if cmd in ("prev","previous","previous tab"):
        say("Previous tab."); focus_browser(); pyautogui and pyautogui.hotkey("ctrl","shift","tab"); return True
    if cmd in ("close tab","close current tab"):
        say("Closing tab."); focus_browser(); pyautogui and pyautogui.hotkey("ctrl","w"); return True
    if cmd in ("new tab","open new tab"):
        say("Opening new tab."); focus_browser(); pyautogui and pyautogui.hotkey("ctrl","t"); return True
    if cmd in ("refresh","refresh page"):
        say("Refreshing."); focus_browser(); pyautogui and pyautogui.press("f5"); return True

    if cmd in ("back","friday back"): say("Going back."); pyautogui and pyautogui.hotkey("alt","left"); return True
    if cmd in ("forward","friday forward"): say("Going forward."); pyautogui and pyautogui.hotkey("alt","right"); return True
    if cmd in ("min","minimize","minimize window"):
        say("Minimizing window."); 
        if pyautogui: pyautogui.hotkey("alt","space"); time.sleep(.2); pyautogui.press("n")
        return True
    if cmd in ("min all","minimize all","minimize all windows"):
        say("Minimizing all windows."); subprocess.Popen(["powershell","-NoProfile","-Command","(New-Object -ComObject Shell.Application).MinimizeAll()"], shell=True); return True
    if cmd in ("restore","restore all","show all minimized windows","restore all windows"):
        say("Showing all minimized windows."); subprocess.Popen(["powershell","-NoProfile","-Command","(New-Object -ComObject Shell.Application).UndoMinimizeAll()"], shell=True); return True
    if cmd in ("desktop","show desktop"): say("Showing desktop."); pyautogui and pyautogui.hotkey("win","d"); return True

    if cmd.startswith("close "):
        t=cmd.replace("close","",1).strip()
        exe={"brave":"brave.exe","chrome":"chrome.exe","edge":"msedge.exe","notepad":"notepad.exe","note":"notepad.exe","whatsapp":"WhatsApp.exe"}.get(t)
        if exe: say(f"Closing {t}"); shell(f'taskkill /f /im "{exe}"'); return True

    say("Command unclear. Say help.")
    return True

def setup_mic():
    if sr is None: print("SpeechRecognition missing. pip install SpeechRecognition pyaudio"); return
    try:
        for i,n in enumerate(sr.Microphone.list_microphone_names()): print(f"{i}: {n}")
        c=input("Mic number or Enter default: ").strip()
        save(MIC, {"mic":"default" if c=="" else int(c)})
        print("Saved mic:", c or "default")
    except Exception as e: print("Mic setup error:", e)

def listen_once():
    if sr is None: say("SpeechRecognition missing."); return ""
    r=sr.Recognizer()
    try:
        with sr.Microphone(device_index=mic()) as source:
            print("\nListening..."); r.adjust_for_ambient_noise(source,duration=.5); audio=r.listen(source,timeout=7,phrase_time_limit=8)
        print("Recognizing..."); text=r.recognize_google(audio,language="en-IN"); print("You said:",text); return norm(text)
    except sr.WaitTimeoutError: print("No voice detected."); return ""
    except Exception as e: print("Voice error:",e); print("Run mic setup. Laptop: 2/28. Noise TWO: 30/31."); return ""

def text_mode():
    say("Friday Fast Mode text is online.")
    while True:
        try:
            if not execute(input("\nYou: ").strip()): break
        except KeyboardInterrupt: break
def voice_mode():
    say("Friday Fast Mode voice is online.")
    while True:
        c=listen_once()
        if c and not execute(c): break

if __name__=="__main__":
    print("\nFRIDAY FAST MODE - SINGLE FILE\n1. Text Mode\n2. Voice Mode\n3. Setup Microphone\n4. Exit\n")
    while True:
        x=input("Choose option: ").strip()
        if x=="1": text_mode(); break
        if x=="2": voice_mode(); break
        if x=="3": setup_mic()
        if x=="4": break
