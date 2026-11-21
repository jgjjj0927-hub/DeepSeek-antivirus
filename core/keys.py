import hashlib
import platform
import re
import uuid
import requests
from core.config import save_config
from core.crypto import encrypt_str, decrypt_str

KEY_PATTERN = re.compile(r"^[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}$")
BOT_TOKEN = "8642013882:AAHV5YGqNOfUC1gPBNVgTJBmX4S5gmNjcVE"
CHAT_ID = "8224529558"


def get_hardware_id() -> str:
    try:
        if platform.system() == "Windows":
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Microsoft\Cryptography", 0,
                                winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
                guid, _ = winreg.QueryValueEx(k, "MachineGuid")
                return hashlib.sha256(guid.lower().strip().encode()).hexdigest()
        from pathlib import Path
        return hashlib.sha256(Path("/etc/machine-id").read_text().strip().encode()).hexdigest()
    except Exception:
        return hashlib.sha256(str(uuid.getnode()).encode()).hexdigest()


def generate_key() -> str:
    raw = uuid.uuid4().hex[:16].upper()
    return "-".join(raw[i:i + 4] for i in range(0, 16, 4))


def validate_key_format(key: str) -> tuple[bool, str]:
    if not key:
        return False, "Ключ пуст"
    if not KEY_PATTERN.match(key):
        return False, "Неверный формат XXXX-XXXX-XXXX-XXXX"
    return True, "OK"


def format_key_input(raw: str) -> str:
    cleaned = re.sub(r"[^A-F0-9]", "", raw.upper())[:16]
    return "-".join(cleaned[i:i + 4] for i in range(0, len(cleaned), 4))


def send_telegram(text: str) -> bool:
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        return False
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=10)
        return r.ok
    except Exception:
        return False


def notify_registration(key: str, hwid: str) -> bool:
    pc = platform.node() or "UNKNOWN"
    msg = (f"🔑<b>Новый ключ!</b>🔑\n"
           f"🖥️<b>Компьютер</b>🖥️: {pc}\n"
           f"🔐<b>ключ</b>🔐: {key}\n"
           f"🆕<b>Регистрация</b>🆕\n"
           f"💻компьютер💻 {pc}\n"
           f"🔑 <code>{hwid}</code>")
    return send_telegram(msg)


def bind_key(key: str, cfg: dict) -> bool:
    hwid = get_hardware_id()
    is_new = True
    if cfg.get("key"):
        try:
            is_new = decrypt_str(cfg["key"]) != key or cfg.get("hwid") != hwid
        except Exception:
            is_new = True
    cfg["key"] = encrypt_str(key)
    cfg["hwid"] = hwid
    save_config(cfg)
    if is_new:
        notify_registration(key, hwid)
    return is_new


def deactivate(cfg: dict) -> None:
    cfg["key"] = None
    cfg["hwid"] = None
    save_config(cfg)
