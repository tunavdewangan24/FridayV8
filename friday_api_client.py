import json
import os
import urllib.error
import urllib.request
from pathlib import Path

APP_DATA_DIR = Path(os.getenv("APPDATA") or Path.home()) / "FridayV8"
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

SESSION_FILE = APP_DATA_DIR / "session.json"
API_CONFIG_FILE = APP_DATA_DIR / "api_config.json"

DEFAULT_API_BASE = "http://127.0.0.1:8000"


def get_api_base():
    if API_CONFIG_FILE.exists():
        try:
            return json.loads(API_CONFIG_FILE.read_text(encoding="utf-8")).get("api_base", DEFAULT_API_BASE)
        except Exception:
            pass
    return DEFAULT_API_BASE


def set_api_base(api_base: str):
    API_CONFIG_FILE.write_text(json.dumps({"api_base": api_base}, indent=4), encoding="utf-8")


def _request(path, method="GET", data=None, token=None, timeout=10):
    url = get_api_base().rstrip("/") + path
    body = None
    headers = {"Content-Type": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if data is not None:
        body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8")).get("detail", str(e))
        except Exception:
            detail = str(e)
        raise RuntimeError(detail)
    except Exception as e:
        raise RuntimeError(f"API connection failed: {e}")


def save_session(session):
    SESSION_FILE.write_text(json.dumps(session, indent=4), encoding="utf-8")


def load_session():
    if not SESSION_FILE.exists():
        return None
    try:
        return json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def logout():
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


def register(email, password, name=""):
    data = _request("/auth/register", method="POST", data={"email": email, "password": password, "name": name})
    save_session(data)
    return data


def login(email, password):
    data = _request("/auth/login", method="POST", data={"email": email, "password": password})
    save_session(data)
    return data


def current_user():
    session = load_session()
    if not session:
        return None
    return _request("/me", token=session["access_token"])


def save_history(command_text, result_text="", status="completed"):
    session = load_session()
    if not session:
        return None
    return _request(
        "/history",
        method="POST",
        token=session["access_token"],
        data={
            "command_text": command_text,
            "result_text": result_text,
            "status": status,
            "app_version": "FridayV8",
        },
        timeout=6,
    )


def get_my_history(limit=20):
    session = load_session()
    if not session:
        return []
    return _request(f"/history?limit={limit}", token=session["access_token"])


def save_safety_event(risk_type, severity="medium", action_taken="blocked", command_preview=""):
    session = load_session()
    if not session:
        return None
    return _request(
        "/safety",
        method="POST",
        token=session["access_token"],
        data={
            "risk_type": risk_type,
            "severity": severity,
            "action_taken": action_taken,
            "command_preview": command_preview[:150],
        },
        timeout=6,
    )
