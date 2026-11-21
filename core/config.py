import json
from pathlib import Path

APP_DIR = Path.home() / ".kiwilab"
APP_DIR.mkdir(exist_ok=True)
CONFIG_FILE = APP_DIR / "config.json"
QUARANTINE_DIR = APP_DIR / "quarantine"
QUARANTINE_DIR.mkdir(exist_ok=True)
LOG_DIR = APP_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

DEFAULT_CFG = {
    "key": None,
    "hwid": None,
    "theme": "dark",
    "autostart": True,
    "first_run_done": False,
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            for k, v in DEFAULT_CFG.items():
                data.setdefault(k, v)
            return data
        except Exception:
            pass
    return dict(DEFAULT_CFG)


def save_config(cfg: dict) -> None:
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
