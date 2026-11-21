import hashlib
import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from core.config import QUARANTINE_DIR

SUSPICIOUS_EXTENSIONS = {".exe", ".bat", ".cmd", ".scr", ".vbs", ".js", ".ps1", ".msi", ".jar"}
SCAN_ROOTS_WIN = [Path(os.environ.get("SystemDrive", "C:") + "\\Users"),
                  Path(os.environ.get("SystemDrive", "C:") + "\\Windows\\Temp")]
SCAN_ROOTS_LINUX = [Path.home(), Path("/tmp")]


def _iter_files(root: Path, stop_flag):
    if root.is_file():
        yield root
        return
    if not root.is_dir():
        return
    for dirpath, _, filenames in os.walk(root):
        if stop_flag and stop_flag():
            return
        for n in filenames:
            if stop_flag and stop_flag():
                return
            yield Path(dirpath) / n


def scan_paths(paths: list[str], progress_cb=None, stop_flag=None) -> list[dict]:
    threats = []
    files = []
    for p in paths:
        files.extend(_iter_files(Path(p), stop_flag))
    total = len(files) or 1
    for idx, f in enumerate(files):
        if stop_flag and stop_flag():
            break
        if progress_cb:
            progress_cb(idx / total)
        try:
            if f.suffix.lower() in SUSPICIOUS_EXTENSIONS:
                threats.append({"path": str(f), "reason": "Подозрительное расширение", "severity": "medium"})
                continue
            if f.is_file() and 0 < f.stat().st_size < 50 * 1024 * 1024:
                h = hashlib.sha256()
                with open(f, "rb") as fh:
                    for chunk in iter(lambda: fh.read(8192), b""):
                        h.update(chunk)
                threats.append({"path": str(f), "reason": "Хеш посчитан (база не подключена)",
                                "severity": "info", "hash": h.hexdigest()})
        except (PermissionError, OSError):
            continue
    return threats


def scan_system(progress_cb=None, stop_flag=None) -> list[dict]:
    import platform
    roots = SCAN_ROOTS_WIN if platform.system() == "Windows" else SCAN_ROOTS_LINUX
    return scan_paths([str(r) for r in roots], progress_cb, stop_flag)


def quarantine_file(file_path: str) -> str | None:
    src = Path(file_path)
    if not src.exists():
        return None
    dest = QUARANTINE_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{src.name}"
    try:
        shutil.move(str(src), str(dest))
        Path(str(dest) + ".meta").write_text(
            json.dumps({"original": str(src), "time": datetime.now().isoformat()}), encoding="utf-8")
        return str(dest)
    except Exception:
        return None


def list_quarantine() -> list[dict]:
    out = []
    for p in QUARANTINE_DIR.glob("*"):
        if p.suffix == ".meta":
            continue
        meta = Path(str(p) + ".meta")
        orig = "?"
        if meta.exists():
            try:
                orig = json.loads(meta.read_text())["original"]
            except Exception:
                pass
        out.append({"name": p.name, "original": orig, "path": str(p)})
    return out
