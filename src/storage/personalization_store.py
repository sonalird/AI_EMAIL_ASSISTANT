import json
from pathlib import Path

DATA_DIR = Path("data")
PROFILE_PATH = DATA_DIR / "user_profile.json"
HISTORY_PATH = DATA_DIR / "conversation_history.json"

DEFAULT_PROFILE = {
    "name": "",
    "company": "",
    "preferred_style": "formal"
}

def _ensure_files():
    DATA_DIR.mkdir(exist_ok=True)

    if not PROFILE_PATH.exists():
        PROFILE_PATH.write_text(json.dumps(DEFAULT_PROFILE, indent=2))

    if not HISTORY_PATH.exists():
        HISTORY_PATH.write_text(json.dumps({"messages": []}, indent=2))


def load_user_profile() -> dict:
    _ensure_files()
    return json.loads(PROFILE_PATH.read_text())


def save_user_profile(profile: dict):
    _ensure_files()
    PROFILE_PATH.write_text(json.dumps(profile, indent=2))


def add_message(role: str, content: str, max_messages: int = 10):
    _ensure_files()
    history = json.loads(HISTORY_PATH.read_text())
    history["messages"].append({"role": role, "content": content})
    history["messages"] = history["messages"][-max_messages:]
    HISTORY_PATH.write_text(json.dumps(history, indent=2))


def load_recent_messages(limit: int = 4) -> list:
    _ensure_files()
    history = json.loads(HISTORY_PATH.read_text())
    return history.get("messages", [])[-limit:]
